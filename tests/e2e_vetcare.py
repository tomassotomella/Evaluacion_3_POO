# -*- coding: utf-8 -*-
"""Pruebas de extremo a extremo de VetCare.

Recorre flujos reales pantalla -> servicio -> SQLite usando:
- Una base de datos temporal por escenario (nunca la base de desarrollo).
- Un cliente HTTP simulado para feriados y dolar (sin Internet ni API keys).
- Entrada de teclado simulada y captura de salida para las pantallas.

Ejecucion:  python tests/e2e_vetcare.py
Con pytest: pip install pytest ; pytest tests\\e2e_vetcare.py -v  (pendiente instalar)
"""
from __future__ import annotations

import builtins
import contextlib
import io
import shutil
import sqlite3
import sys
import tempfile
import traceback
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import utilities.interfaz as ui
from config.configuracion import Configuracion
from database.conexion import ConexionDB
from dao.consulta_dao import ConsultaDAO
from dao.divisa_dao import DivisaDAO
from dao.especialidad_dao import EspecialidadDAO
from dao.especie_dao import EspecieDAO
from dao.feriado_dao import FeriadoDAO
from dao.mascota_dao import MascotaDAO
from dao.medicamento_dao import MedicamentoDAO
from dao.propietario_dao import PropietarioDAO
from dao.receta_medica_dao import RecetaMedicaDAO
from dao.veterinario_dao import VeterinarioDAO
from exceptions import exceptions
from models.especialidad import Especialidad
from models.especie import Especie
from screens import (
    consulta_screens,
    farmacia_screen,
    mascotas_screen,
    propietario_screens,
    urgencia_screen,
    veterinario_screens,
)
from services.consulta_service import ConsultaService
from services.economia_service import EconomiaService
from services.farmacia_service import FarmaciaService
from services.feriado_service import FeriadoService
from services.mascota_service import MascotaService
from services.persona_service import PersonaService

RUT_VET = "12345678-5"
RUT_PROP = "19876543-2"
DOLAR_VALOR = 950.5


# ----------------------------------------------------------------------------
# Infraestructura de simulacion
# ----------------------------------------------------------------------------

class RespuestaSimulada:
    def __init__(self, payload):
        self._payload = payload

    def json(self):
        return self._payload


class ClienteHTTPSimulado:
    """Sustituto de ClienteHTTPResiliente para feriados y dolar."""

    def __init__(self, fechas_feriados: list[date] | None = None, fallar: bool = False):
        self.fechas_feriados = [f.isoformat() for f in (fechas_feriados or [])]
        self.fallar = fallar
        self.llamadas: list[str] = []

    def ejecutar_get(self, url, parametros=None, cabeceras=None, *, servicio="Servicio externo"):
        self.llamadas.append(url)
        if self.fallar:
            raise exceptions.ConexionTimeoutException(servicio=servicio, timeout_segundos=10)
        if "holidays" in url or "feriado" in url.lower():
            return RespuestaSimulada({
                "data": [
                    {
                        "date": fecha,
                        "title": "Feriado simulado",
                        "type": "Legal",
                        "inalienable": False,
                    }
                    for fecha in self.fechas_feriados
                ]
            })
        return RespuestaSimulada({
            "moneda": "usd",
            "nombre": "Dolar observado",
            "venta": DOLAR_VALOR,
            "fechaActualizacion": "2026-11-09T16:00:00",
        })


class Entorno:
    """Composicion de dependencias equivalente a main.py, con BD temporal."""

    def __init__(self, fechas_feriados: list[date] | None = None, fallar_api: bool = False):
        self.carpeta = Path(tempfile.mkdtemp(prefix="e2e_vetcare_"))
        self.ruta_db = self.carpeta / "e2e.db"
        self.conexion = ConexionDB(str(self.ruta_db))

        especialidad_dao = EspecialidadDAO(self.conexion)
        propietario_dao = PropietarioDAO(self.conexion)
        veterinario_dao = VeterinarioDAO(self.conexion, especialidad_dao)
        especie_dao = EspecieDAO(self.conexion)
        mascota_dao = MascotaDAO(self.conexion, especie_dao, propietario_dao)
        medicamento_dao = MedicamentoDAO(self.conexion)
        consulta_dao = ConsultaDAO(self.conexion, mascota_dao)
        receta_dao = RecetaMedicaDAO(self.conexion, medicamento_dao, consulta_dao)
        divisa_dao = DivisaDAO(self.conexion)
        feriado_dao = FeriadoDAO(self.conexion)

        self.cliente = ClienteHTTPSimulado(fechas_feriados, fallar_api)
        self.persona_service = PersonaService(propietario_dao, veterinario_dao, especialidad_dao)
        self.mascota_service = MascotaService(mascota_dao, especie_dao, self.persona_service)
        self.economia_service = EconomiaService(divisa_dao, cliente_http=self.cliente)
        self.feriado_service = FeriadoService(feriado_dao, cliente_http=self.cliente)
        self.consulta_service = ConsultaService(
            consulta_dao, receta_dao, medicamento_dao,
            self.persona_service, self.mascota_service,
            self.economia_service, self.feriado_service,
        )
        self.farmacia_service = FarmaciaService(medicamento_dao, self.consulta_service, self.economia_service)

    def sql(self, consulta: str, parametros: tuple = ()) -> list[tuple]:
        with contextlib.closing(sqlite3.connect(self.ruta_db)) as conn:
            return conn.execute(consulta, parametros).fetchall()

    def cerrar(self) -> None:
        shutil.rmtree(self.carpeta, ignore_errors=True)


class DomingoSimulado(datetime):
    """datetime.now() fijo en domingo 2026-11-15 12:00."""

    @classmethod
    def now(cls, tz=None):  # type: ignore[override]
        return cls(2026, 11, 15, 12, 0, 0)


class SimulacionTeclado:
    """Sustituye input() y limpiar_pantalla(); captura la salida visible."""

    def __init__(self, entradas: list[str]):
        self.entradas = list(entradas)
        self.salida = io.StringIO()
        self._input_original = builtins.input
        self._limpiar_original = ui.limpiar_pantalla

    def __enter__(self):
        cola = iter(self.entradas)

        def input_simulado(prompt=""):
            try:
                return next(cola)
            except StopIteration:
                raise AssertionError(
                    "La pantalla pidio mas entradas de las provistas: "
                    f"entradas={self.entradas}"
                )

        builtins.input = input_simulado
        ui.limpiar_pantalla = lambda: None
        self._ctx_stdout = contextlib.redirect_stdout(self.salida)
        self._ctx_stdout.__enter__()
        return self

    def __exit__(self, *exc):
        self._ctx_stdout.__exit__(*exc)
        builtins.input = self._input_original
        ui.limpiar_pantalla = self._limpiar_original
        return False

    def texto(self) -> str:
        return self.salida.getvalue()


# ----------------------------------------------------------------------------
# Semillas de datos reutilizables
# ----------------------------------------------------------------------------

def sembrar_propietario_y_especie(ent: Entorno) -> None:
    ent.persona_service.registrar_propietario(
        rut=RUT_PROP, nombre_completo="Maria Lopez", telefono="912345678", comuna="Los Angeles"
    )
    ent.mascota_service.registrar_especie(nombre_especie="Canino", esperanza_vida_max=15)


def sembrar_veterinario(ent: Entorno) -> None:
    especialidad = ent.persona_service.registrar_especialidad("Medicina General", "Atencion general")
    ent.persona_service.registrar_veterinario(
        rut=RUT_VET, nombre_completo="Camila Soto", telefono="911223344",
        id_especialidad=especialidad.id_especialidad,
    )


def sembrar_mascota(ent: Entorno) -> int:
    sembrar_propietario_y_especie(ent)
    mascota = ent.mascota_service.registrar_mascota(
        nombre="Boby", fecha_nacimiento=date(2020, 5, 10),
        id_especie=1, rut_propietario=RUT_PROP, raza="Mestizo",
    )
    return mascota.id_mascota


def sembrar_medicamento(ent: Entorno, stock: int = 5) -> int:
    medicamento = ent.farmacia_service.registrar_medicamento(
        nombre_comercial="Amoxicilina", precio=12000, stock=stock
    )
    return medicamento.id_medicamento


# ----------------------------------------------------------------------------
# Escenarios E2E
# ----------------------------------------------------------------------------

def e01_menu_principal_navegacion(ent: Entorno) -> str:
    sembrar_veterinario(ent)
    with SimulacionTeclado(["4", "0", "0"]) as sim:
        from screens.menu_screen import menu_principal
        menu_principal(
            ent.persona_service, ent.mascota_service, ent.consulta_service,
            ent.farmacia_service, ent.economia_service, ent.feriado_service,
            servicio_clima=None, servicio_alertas=None,
        )
    salida = sim.texto()
    assert "VETCARE - CL" in salida, "No se mostro el encabezado principal"
    assert "[CLIMA EN VIVO]: No disponible (Offline)" in salida, "Clima offline no mostrado"
    assert "950,50" in salida, "El dolar simulado no aparecio en el encabezado"
    assert "[CALENDARIO]: D" in salida, "El calendario de feriados no aparecio"
    assert "GRACIAS POR USAR VETCARE" in salida, "La salida limpia del menu no ocurrio"
    return "Menu completo navegable; encabezado con clima offline, dolar y calendario"


def e02_propietarios_crud(ent: Entorno) -> str:
    with SimulacionTeclado([RUT_PROP, "Maria Lopez", "912345678", "Los Angeles", ""]) as sim:
        propietario_screens.registrar_propietario(ent.persona_service)
    assert "registrado exitosamente" in sim.texto()
    filas = ent.sql("SELECT COUNT(*) FROM PROPIETARIO WHERE rut = ?", (RUT_PROP,))
    assert filas[0][0] == 1, "El propietario no quedo persistido"

    with SimulacionTeclado([RUT_PROP, "Maria Lopez Silva", ""]) as sim:
        propietario_screens.cambiar_nombre(ent.persona_service)
    assert "Nombre actualizado" in sim.texto()
    nombre = ent.sql("SELECT nombre_completo FROM PROPIETARIO WHERE rut = ?", (RUT_PROP,))[0][0]
    assert nombre == "Maria Lopez Silva", "El cambio de nombre no se persistio"

    with SimulacionTeclado([""]) as sim:
        propietario_screens.listar_propietarios(ent.persona_service)
    assert "Maria Lopez Silva" in sim.texto(), "El listado no muestra al propietario"

    with SimulacionTeclado([RUT_PROP, "1", ""]) as sim:
        propietario_screens.eliminar_propietario(ent.persona_service)
    assert "eliminado correctamente" in sim.texto()
    restantes = ent.sql("SELECT COUNT(*) FROM PROPIETARIO WHERE rut = ?", (RUT_PROP,))
    assert restantes[0][0] == 0, "El propietario eliminado sigue en la base"
    return "Registro, actualizacion, listado y eliminacion verificados en pantalla y BD"


def e03_especie_mascota_registro(ent: Entorno) -> str:
    sembrar_propietario_y_especie(ent)
    with SimulacionTeclado([RUT_PROP, "Boby", "2020-05-10", "Mestizo", "1", ""]) as sim:
        mascotas_screen.registrar_mascota(ent.mascota_service)
    assert "registrada exitosamente" in sim.texto()
    filas = ent.sql(
        "SELECT m.nombre, p.rut, e.nombre_especie FROM MASCOTA m "
        "JOIN PROPIETARIO p ON m.id_propietario = p.id_propietario "
        "JOIN ESPECIE e ON m.id_especie = e.id_especie"
    )
    assert filas and filas[0][0] == "Boby" and filas[0][1] == RUT_PROP, "Mascota mal persistida"
    return "Mascota registrada por pantalla con especie y propietario correctos en BD"


def e04_consulta_normal_dia_habil(ent: Entorno) -> str:
    id_mascota = sembrar_mascota(ent)
    sembrar_veterinario(ent)
    with SimulacionTeclado([str(id_mascota), "2026-11-14 10:00", "Control anual", ""]) as sim:
        consulta_screens.agendar_consulta(ent.consulta_service)
    assert "agendada para la mascota" in sim.texto()
    fila = ent.sql(
        "SELECT estado, es_urgencia, tarifa_base, porcentaje_recargo_feriado, monto_total "
        "FROM CONSULTA WHERE id_mascota = ?", (id_mascota,)
    )[0]
    assert fila[0] == "AGENDADA", f"Estado persistido incorrecto: {fila[0]}"
    assert fila[1] == 0 and fila[2] == 25000 and fila[3] == 0.0 and fila[4] == 25000, \
        f"Tarifas persistidas incorrectas: {fila}"
    return "Cita de sabado agendada; persisten tarifa 25000, recargo 0 y monto 25000"


def e05_bloqueo_domingo(ent: Entorno) -> str:
    id_mascota = sembrar_mascota(ent)
    sembrar_veterinario(ent)
    antes = ent.sql("SELECT COUNT(*) FROM CONSULTA")[0][0]
    with SimulacionTeclado([str(id_mascota), "2026-11-15 10:00", "Intento domingo", ""]) as sim:
        consulta_screens.agendar_consulta(ent.consulta_service)
    salida = sim.texto()
    assert "solo pueden operar en d" in salida, "No se mostro el bloqueo por domingo"
    despues = ent.sql("SELECT COUNT(*) FROM CONSULTA")[0][0]
    assert antes == despues, "Se inserto una consulta en domingo"
    return "Cita en domingo rechazada por pantalla y sin persistencia"


def e06_bloqueo_feriado(ent: Entorno) -> str:
    id_mascota = sembrar_mascota(ent)
    sembrar_veterinario(ent)
    antes = ent.sql("SELECT COUNT(*) FROM CONSULTA")[0][0]
    with SimulacionTeclado([str(id_mascota), "2026-12-25 10:00", "Navidad", ""]) as sim:
        consulta_screens.agendar_consulta(ent.consulta_service)
    assert "solo pueden operar en d" in sim.texto(), "No se mostro el bloqueo por feriado"
    despues = ent.sql("SELECT COUNT(*) FROM CONSULTA")[0][0]
    assert antes == despues, "Se inserto una consulta en feriado"
    return "Cita en feriado (viernes 25-dic simulado) rechazada y sin persistencia"


def e07_api_caida_consulta_bloqueada(ent: Entorno) -> str:
    id_mascota = sembrar_mascota(ent)
    sembrar_veterinario(ent)
    antes = ent.sql("SELECT COUNT(*) FROM CONSULTA")[0][0]
    with SimulacionTeclado([str(id_mascota), "2026-11-14 10:00", "Control", ""]) as sim:
        consulta_screens.agendar_consulta(ent.consulta_service)
    salida = sim.texto()
    assert "No se pudo verificar el calendario" in salida, "Falta el mensaje de contingencia"
    assert "bloqueada" in salida, "Falta el aviso de bloqueo por seguridad"
    despues = ent.sql("SELECT COUNT(*) FROM CONSULTA")[0][0]
    assert antes == despues, "La consulta se inserto pese a la caida de la API"
    return "API caida: consulta normal bloqueada con mensaje explicito y sin insercion"


def e08_urgencia_bloqueada_dia_habil(ent: Entorno) -> str:
    id_mascota = sembrar_mascota(ent)
    sembrar_veterinario(ent)
    antes = ent.sql("SELECT COUNT(*) FROM CONSULTA")[0][0]
    with SimulacionTeclado([str(id_mascota), ""]) as sim:
        urgencia_screen.registrar_urgencia(ent.consulta_service, ent.farmacia_service)
    salida = sim.texto()
    assert "solo est" in salida or "autorizadas" in salida, \
        "No se mostro el rechazo de urgencia en dia habil"
    despues = ent.sql("SELECT COUNT(*) FROM CONSULTA")[0][0]
    assert antes == despues, "Se registro una urgencia en martes"
    return "Urgencia rechazada en martes (no domingo ni feriado), sin insercion"


def e09_urgencia_domingo_en_atencion(ent: Entorno) -> str:
    id_mascota = sembrar_mascota(ent)
    sembrar_veterinario(ent)
    original_datetime = sys.modules["services.consulta_service"].datetime
    sys.modules["services.consulta_service"].datetime = DomingoSimulado
    try:
        with SimulacionTeclado(["1", str(id_mascota), RUT_VET, "Convulsion", "9", "1", "0"]) as sim:
            urgencia_screen.main_guardia(ent.consulta_service, ent.farmacia_service)
        assert "iniciada para" in sim.texto(), "La urgencia no se inicio por pantalla"
    finally:
        sys.modules["services.consulta_service"].datetime = original_datetime

    fila = ent.sql(
        "SELECT estado, es_urgencia, tarifa_base, porcentaje_recargo_feriado, monto_total, "
        "fecha_agendada, fecha_inicio_atencion, id_detalle FROM CONSULTA"
    )[0]
    assert fila[1] == 1, "es_urgencia no se persistio"
    assert fila[2] == 25000 and fila[3] == 30.0 and fila[4] == 32500, \
        f"Politica de tarifa incorrecta: {fila[2:5]}"
    assert fila[5] == fila[6], f"fecha_agendada {fila[5]} difiere de fecha_inicio {fila[6]}"
    assert fila[7] is not None, "La urgencia no tiene detalle vinculado"

    # Flujo 6: mientras la atencion esta activa el estado persistido es EN ATENCION.
    id_consulta = ent.sql("SELECT id_consulta FROM CONSULTA")[0][0]
    reanudada = ent.consulta_service.reanudar_atencion(id_consulta)
    assert reanudada.estado.value == "EN ATENCION", "Reanudacion no devolvio EN ATENCION"
    estado_db = ent.sql("SELECT estado FROM CONSULTA WHERE id_consulta = ?", (id_consulta,))[0][0]
    assert estado_db == "EN ATENCION", f"Estado persistido tras reanudar: {estado_db}"
    ent.consulta_service.poner_en_espera(id_consulta)
    return ("Urgencia de domingo: EN ATENCION verificado en BD, fechas simultaneas, "
            "tarifa 25000 + recargo 30% = 32500 persistidos")


def e10_espera_y_reanudacion(ent: Entorno) -> str:
    id_mascota = sembrar_mascota(ent)
    sembrar_veterinario(ent)
    original_datetime = sys.modules["services.consulta_service"].datetime
    sys.modules["services.consulta_service"].datetime = DomingoSimulado
    try:
        consulta = ent.consulta_service.registrar_urgencia(id_mascota, RUT_VET, "Fractura")
        ent.consulta_service.poner_en_espera(consulta.id_consulta)
    finally:
        sys.modules["services.consulta_service"].datetime = original_datetime
    id_consulta = consulta.id_consulta

    monto_antes = ent.sql("SELECT monto_total, porcentaje_recargo_feriado FROM CONSULTA WHERE id_consulta = ?", (id_consulta,))[0]

    with SimulacionTeclado(["2", "", "3", str(id_consulta), "", "3", "Otitis externa",
                            "4", "Antibiotico topico", "5", "Control en 7 dias", "10", "1", "0"]) as sim:
        urgencia_screen.main_guardia(ent.consulta_service, ent.farmacia_service)
    salida = sim.texto()
    assert "Atenci" in salida and "reanudada" in salida, "La pantalla de reanudacion no se ejecuto"

    fila = ent.sql(
        "SELECT estado, monto_total, porcentaje_recargo_feriado, fecha_fin_atencion, tarifa_base "
        "FROM CONSULTA WHERE id_consulta = ?", (id_consulta,)
    )[0]
    assert fila[0] == "FINALIZADA", f"Estado final inesperado: {fila[0]}"
    assert (fila[1], fila[2]) == monto_antes, \
        f"El monto se recalculo en la reanudacion: antes {monto_antes}, despues {fila[1:3]}"
    assert fila[3] is not None, "No se registro fecha de fin"
    assert fila[4] == 25000, "La tarifa base historica cambio"
    return "Pausa en espera, reanudacion por Modo Guardia y finalizacion sin recalcular precio"


def e11_domingo_y_feriado_recargo_unico(ent: Entorno) -> str:
    id_mascota = sembrar_mascota(ent)
    sembrar_veterinario(ent)
    original_datetime = sys.modules["services.consulta_service"].datetime
    sys.modules["services.consulta_service"].datetime = DomingoSimulado
    try:
        consulta = ent.consulta_service.registrar_urgencia(id_mascota, RUT_VET, "Caida grave")
    finally:
        sys.modules["services.consulta_service"].datetime = original_datetime
    porcentaje, monto = ent.sql(
        "SELECT porcentaje_recargo_feriado, monto_total FROM CONSULTA WHERE id_consulta = ?",
        (consulta.id_consulta,)
    )[0]
    assert porcentaje == 30.0, f"Recargo duplicado o incorrecto: {porcentaje}"
    assert monto == 32500, f"Monto con recargo unico esperado 32500, obtenido {monto}"
    resumen = ent.feriado_service.obtener_resumen_calendario(datetime(2026, 11, 15))
    assert "Domingo y feriado" in resumen, f"Calendario no reconoce coincidencia: {resumen}"
    return "Domingo + feriado simultaneos: un unico recargo del 30% y calendario que lo reporta"


def e12_farmacia_stock_y_despacho(ent: Entorno) -> str:
    id_mascota = sembrar_mascota(ent)
    sembrar_veterinario(ent)

    with SimulacionTeclado(["Amoxicilina", "12000", "5", ""]) as sim:
        farmacia_screen.registrar_medicamento(ent.farmacia_service)
    assert "registrado exitosamente" in sim.texto(), "El medicamento no se registro por pantalla"
    id_med = ent.sql("SELECT id_medicamento FROM MEDICAMENTO WHERE nombre_comercial = 'Amoxicilina'")[0][0]

    with SimulacionTeclado([str(id_med), ""]) as sim:
        farmacia_screen.buscar_medicamento_por_id(ent.farmacia_service)
    detalle = sim.texto()
    assert "PRECIO USD" in detalle and "Tipo de cambio aplicado" in detalle, \
        "La ficha no mostro precios bimonetarios"

    original_datetime = sys.modules["services.consulta_service"].datetime
    sys.modules["services.consulta_service"].datetime = DomingoSimulado
    try:
        consulta = ent.consulta_service.registrar_urgencia(id_mascota, RUT_VET, "Infeccion")
        detalle_id = consulta.detalle.id_detalle
        receta = ent.consulta_service.registrar_receta(
            id_detalle=detalle_id, id_medicamento=id_med, cantidad=2, instrucciones="Cada 8 horas"
        )
    finally:
        sys.modules["services.consulta_service"].datetime = original_datetime

    stock_pre = ent.sql("SELECT stock FROM MEDICAMENTO WHERE id_medicamento = ?", (id_med,))[0][0]
    assert stock_pre == 5, "La receta no debe descontar stock hasta el despacho"

    with SimulacionTeclado([str(receta.id_receta), "1", ""]) as sim:
        farmacia_screen.despachar_receta(ent.farmacia_service)
    comprobante = sim.texto()
    assert "TOTAL COBRADO" in comprobante and "24.000 CLP" in comprobante, \
        "El comprobante no mostro el total CLP correcto"
    assert "EQUIVALENTE USD" in comprobante, "El comprobante no mostro el equivalente USD"
    stock_post = ent.sql("SELECT stock FROM MEDICAMENTO WHERE id_medicamento = ?", (id_med,))[0][0]
    assert stock_post == 3, f"Stock esperado 3 tras despacho, obtenido {stock_post}"

    # Doble despacho de la misma receta (sin marca de despacho).
    with SimulacionTeclado([str(receta.id_receta), "1", ""]) as sim:
        farmacia_screen.despachar_receta(ent.farmacia_service)
    stock_repetido = ent.sql("SELECT stock FROM MEDICAMENTO WHERE id_medicamento = ?", (id_med,))[0][0]
    assert stock_repetido == 1, "El despacho repetido no desconto stock (comportamiento a reportar)"
    return ("Despacho bimonetario correcto y stock 5->3; defecto detectado: "
            "la misma receta puede despacharse de nuevo (stock 3->1) sin control")


def e13_errores_api_externos(ent: Entorno) -> str:
    sembrar_veterinario(ent)
    sembrar_medicamento(ent)
    with SimulacionTeclado(["0"]) as sim:
        from screens.menu_screen import menu_principal
        menu_principal(
            ent.persona_service, ent.mascota_service, ent.consulta_service,
            ent.farmacia_service, ent.economia_service, ent.feriado_service,
            servicio_clima=None, servicio_alertas=None,
        )
    salida = sim.texto()
    assert "Dolar Observado: No disponible (Offline)" in salida or \
        "Dólar Observado: No disponible (Offline)" in salida, "Mercado no degrado a offline"
    assert "[CALENDARIO]: No disponible (Offline)" in salida, "Calendario no degrado a offline"

    with SimulacionTeclado(["1", ""]) as sim:
        farmacia_screen.buscar_medicamento_por_id(ent.farmacia_service)
    assert "No disponible (Offline)" in sim.texto(), "La ficha no mostro USD offline ante caida"

    id_mascota = sembrar_mascota(ent)
    original_datetime = sys.modules["services.consulta_service"].datetime
    sys.modules["services.consulta_service"].datetime = DomingoSimulado
    try:
        antes = ent.sql("SELECT COUNT(*) FROM CONSULTA")[0][0]
        with SimulacionTeclado(["1", str(id_mascota), RUT_VET, "Corte profundo", "9", "1", "0"]) as sim:
            urgencia_screen.main_guardia(ent.consulta_service, ent.farmacia_service)
        despues = ent.sql("SELECT COUNT(*) FROM CONSULTA")[0][0]
        assert despues == antes + 1, "La urgencia en domingo con API caida no se permitio"
        advertencia = "Advertencia" in sim.texto() or "ADVERTENCIA" in sim.texto()
    finally:
        sys.modules["services.consulta_service"].datetime = original_datetime
    hallazgo = "" if advertencia else "; hallazgo: la urgencia se permite pero SIN advertencia exigida"
    return "Caida de API: mercado y calendario offline, ficha sin USD, urgencia dominical permitida" + hallazgo


def e14_usd_solo_en_memoria(ent: Entorno) -> str:
    id_mascota = sembrar_mascota(ent)
    sembrar_veterinario(ent)
    columnas = [f[1] for f in ent.sql("PRAGMA table_info(CONSULTA)")]
    usd_en_bd = [c for c in columnas if "usd" in c.lower()]
    assert not usd_en_bd, f"La tabla CONSULTA persiste columnas USD: {usd_en_bd}"

    original_datetime = sys.modules["services.consulta_service"].datetime
    sys.modules["services.consulta_service"].datetime = DomingoSimulado
    try:
        consulta = ent.consulta_service.registrar_urgencia(id_mascota, RUT_VET, "Emergencia")
    finally:
        sys.modules["services.consulta_service"].datetime = original_datetime
    assert consulta.tarifa_base_usd is not None, "El USD no se calculo en memoria"
    assert consulta.monto_total_usd is not None, "El monto USD no se calculo en memoria"
    fila_bd = ent.sql("SELECT tarifa_base, monto_total FROM CONSULTA WHERE id_consulta = ?", (consulta.id_consulta,))[0]
    assert fila_bd == (25000, 32500), "La BD no conserva la politica historica en CLP"
    return "USD calculados solo en memoria; BD conserva CLP y politica historica"


# ----------------------------------------------------------------------------
# Escenarios E2E de actualizacion, reagendado y protecciones
# ----------------------------------------------------------------------------

@contextlib.contextmanager
def domingo_simulado():
    """Fija datetime.now() del servicio de consultas en domingo 2026-11-15 12:00."""
    modulo = sys.modules["services.consulta_service"]
    original = modulo.datetime
    modulo.datetime = DomingoSimulado
    try:
        yield
    finally:
        modulo.datetime = original


RUT_PROP2 = "15234567-6"
RUT_VET2 = "14234567-4"


def e15_reagendar_consulta(ent: Entorno) -> str:
    id_mascota = sembrar_mascota(ent)
    sembrar_veterinario(ent)
    c1 = ent.consulta_service.registrar_consulta(
        id_mascota, datetime(2026, 11, 14, 10, 0), "Control anual"
    )
    c2 = ent.consulta_service.registrar_consulta(
        id_mascota, datetime(2026, 11, 14, 16, 0), "Vacunacion"
    )

    with SimulacionTeclado([str(c1.id_consulta), "2026-11-21 15:00", "1", ""]) as sim:
        consulta_screens.reagendar_consulta(ent.consulta_service)
    assert "reagendada para" in sim.texto(), "La pantalla no confirmo el reagendado"
    fecha_db = ent.sql(
        "SELECT fecha_agendada FROM CONSULTA WHERE id_consulta = ?", (c1.id_consulta,)
    )[0][0]
    assert fecha_db.startswith("2026-11-21 15:00"), f"Fecha no persistida: {fecha_db}"

    ent.consulta_service.cancelar_consulta(c2.id_consulta)
    with SimulacionTeclado([str(c2.id_consulta), "2026-11-28 10:00", "1", ""]) as sim:
        consulta_screens.reagendar_consulta(ent.consulta_service)
    salida = sim.texto()
    assert "no puede reagendar" in salida, "La pantalla no rechazo reagendar una cancelada"
    fecha_c2 = ent.sql(
        "SELECT fecha_agendada FROM CONSULTA WHERE id_consulta = ?", (c2.id_consulta,)
    )[0][0]
    assert fecha_c2.startswith("2026-11-14"), "La fecha de la cancelada cambio"
    return "Reagendado exitoso persistido; reagendado de CANCELADA rechazado por pantalla"


def e16_cancelar_e_inasistencia(ent: Entorno) -> str:
    id_mascota = sembrar_mascota(ent)
    sembrar_veterinario(ent)
    c1 = ent.consulta_service.registrar_consulta(
        id_mascota, datetime(2026, 11, 14, 9, 0), "Control"
    )
    c2 = ent.consulta_service.registrar_consulta(
        id_mascota, datetime(2026, 11, 14, 17, 0), "Consulta"
    )

    with SimulacionTeclado([str(c1.id_consulta), "1", ""]) as sim:
        consulta_screens.cancelar_consulta(ent.consulta_service)
    assert "cancelada correctamente" in sim.texto()
    estado1 = ent.sql(
        "SELECT estado FROM CONSULTA WHERE id_consulta = ?", (c1.id_consulta,)
    )[0][0]
    assert estado1 == "CANCELADA", f"Estado persistido: {estado1}"

    with SimulacionTeclado([str(c2.id_consulta), "1", ""]) as sim:
        consulta_screens.marcar_inasistencia(ent.consulta_service)
    assert "NO ASISTIO" in sim.texto(), "La pantalla no confirmo la inasistencia"
    estado2 = ent.sql(
        "SELECT estado FROM CONSULTA WHERE id_consulta = ?", (c2.id_consulta,)
    )[0][0]
    assert estado2 == "NO ASISTIO", f"Estado persistido: {estado2}"
    return "Cancelacion y registro de inasistencia por pantalla persistidos en BD"


def e17_mascotas_actualizacion_y_protecciones(ent: Entorno) -> str:
    id_mascota = sembrar_mascota(ent)
    ent.persona_service.registrar_propietario(
        rut=RUT_PROP2, nombre_completo="Pedro Naranjo", telefono="966677788",
        comuna="Santa Barbara",
    )
    mascota2 = ent.mascota_service.registrar_mascota(
        nombre="Luna", fecha_nacimiento=date(2021, 3, 15),
        id_especie=1, rut_propietario=RUT_PROP, raza="Beagle",
    )

    with SimulacionTeclado([str(id_mascota), "Rocco", "1", ""]) as sim:
        mascotas_screen.cambiar_nombre_mascota(ent.mascota_service)
    assert "Nombre actualizado" in sim.texto()
    nombre = ent.sql("SELECT nombre FROM MASCOTA WHERE id_mascota = ?", (id_mascota,))[0][0]
    assert nombre == "Rocco", f"Nombre no persistido: {nombre}"

    with SimulacionTeclado([str(id_mascota), "Pug", ""]) as sim:
        mascotas_screen.cambiar_raza_mascota(ent.mascota_service)
    assert "Raza actualizada" in sim.texto()
    raza = ent.sql("SELECT raza FROM MASCOTA WHERE id_mascota = ?", (id_mascota,))[0][0]
    assert raza == "Pug", f"Raza no persistida: {raza}"

    with SimulacionTeclado([str(id_mascota), RUT_PROP2, "1", ""]) as sim:
        mascotas_screen.cambiar_propietario_mascota(ent.mascota_service)
    assert "Propietario actualizado" in sim.texto()
    rut_db = ent.sql(
        "SELECT p.rut FROM MASCOTA m JOIN PROPIETARIO p "
        "ON m.id_propietario = p.id_propietario WHERE m.id_mascota = ?",
        (id_mascota,),
    )[0][0]
    assert rut_db == RUT_PROP2, f"Propietario no persistido: {rut_db}"

    with SimulacionTeclado([str(id_mascota), "1", ""]) as sim:
        mascotas_screen.eliminar_mascota(ent.mascota_service)
    assert "eliminada correctamente" in sim.texto()
    restante = ent.sql("SELECT COUNT(*) FROM MASCOTA WHERE id_mascota = ?", (id_mascota,))
    assert restante[0][0] == 0, "La mascota eliminada sigue en la base"

    ent.consulta_service.registrar_consulta(
        mascota2.id_mascota, datetime(2026, 11, 14, 11, 0), "Control"
    )
    with SimulacionTeclado([str(mascota2.id_mascota), "1", ""]) as sim:
        mascotas_screen.eliminar_mascota(ent.mascota_service)
    assert "No es posible eliminar" in sim.texto(), "Falta la proteccion de mascota con consultas"
    protegida = ent.sql("SELECT COUNT(*) FROM MASCOTA WHERE id_mascota = ?", (mascota2.id_mascota,))
    assert protegida[0][0] == 1, "La mascota con consultas fue eliminada"

    with SimulacionTeclado([RUT_PROP, "1", ""]) as sim:
        propietario_screens.eliminar_propietario(ent.persona_service)
    assert "No es posible eliminar" in sim.texto(), "Falta la proteccion de propietario con mascotas"
    prop = ent.sql("SELECT COUNT(*) FROM PROPIETARIO WHERE rut = ?", (RUT_PROP,))
    assert prop[0][0] == 1, "El propietario con mascotas fue eliminado"
    return ("Nombre, raza y propietario de mascota actualizados y persistidos; "
            "eliminacion bloqueada para mascota con consultas y propietario con mascotas")


def e18_especies_dato_estatico(ent: Entorno) -> str:
    sembrar_propietario_y_especie(ent)
    with SimulacionTeclado(["Felino", "12", ""]) as sim:
        mascotas_screen.registrar_especie(ent.mascota_service)
    assert "registrada correctamente" in sim.texto()
    id_felino = ent.sql(
        "SELECT id_especie FROM ESPECIE WHERE nombre_especie = 'Felino'"
    )[0][0]

    with SimulacionTeclado(["2", "", "0"]) as sim:
        mascotas_screen.submenu_especies(ent.mascota_service)
    salida = sim.texto()
    assert "Felino" in salida, "El listado de especies no se mostro"
    assert "Cambiar Nombre" not in salida, "La opcion de renombrado sigue en el submenu"

    assert not hasattr(ent.mascota_service, "cambiar_nombre_especie"), \
        "El servicio aun expone el renombrado de especies"
    assert not hasattr(Especie, "actualizar_nombre"), "El modelo de especie aun permite renombrar"
    assert not hasattr(Especialidad, "actualizar_nombre"), "El modelo de especialidad aun permite renombrar"
    assert not hasattr(EspecieDAO, "actualizar"), "El DAO de especie aun expone UPDATE"
    assert not hasattr(EspecialidadDAO, "actualizar"), "El DAO de especialidad aun expone UPDATE"

    nombre = ent.sql(
        "SELECT nombre_especie FROM ESPECIE WHERE id_especie = ?", (id_felino,)
    )[0][0]
    assert nombre == "Felino", "La especie debia permanecer inmutable"
    return ("Especie tratada como dato catalogo estatico: renombrado extirpado en "
            "pantalla, servicio, modelo y DAO; especialidad se reemplaza, no renombra")


def e19_veterinarios_actualizacion_y_protecciones(ent: Entorno) -> str:
    sembrar_veterinario(ent)
    esp2 = ent.persona_service.registrar_especialidad("Cirugia", "Procedimientos")
    vet2 = ent.persona_service.registrar_veterinario(
        rut=RUT_VET2, nombre_completo="Diego Fuentes",
        telefono="933444555", id_especialidad=esp2.id_especialidad,
    )

    with SimulacionTeclado([RUT_VET2, "Diego Fuentealba", ""]) as sim:
        veterinario_screens.cambiar_nombre_vet(ent.persona_service)
    assert "Nombre actualizado" in sim.texto()
    nombre = ent.sql(
        "SELECT nombre_completo FROM VETERINARIO WHERE rut = ?", (RUT_VET2,)
    )[0][0]
    assert nombre == "Diego Fuentealba", f"Nombre no persistido: {nombre}"

    with SimulacionTeclado([RUT_VET2, "955666777", ""]) as sim:
        veterinario_screens.cambiar_contacto_vet(ent.persona_service)
    assert "Tel" in sim.texto() and "actualizado" in sim.texto()
    tel = ent.sql("SELECT telefono FROM VETERINARIO WHERE rut = ?", (RUT_VET2,))[0][0]
    assert tel == "+56955666777", f"Telefono no persistido: {tel}"

    with SimulacionTeclado([RUT_VET2, "1", ""]) as sim:
        veterinario_screens.cambiar_especialidad_vet(ent.persona_service)
    assert "Especialidad actualizada" in sim.texto()
    esp_db = ent.sql(
        "SELECT e.nombre_especialidad FROM VETERINARIO v "
        "JOIN ESPECIALIDAD e ON v.id_especialidad = e.id_especialidad "
        "WHERE v.rut = ?", (RUT_VET2,)
    )[0][0]
    assert esp_db == "Medicina General", f"Especialidad no persistida: {esp_db}"

    with SimulacionTeclado([RUT_VET2, "1", ""]) as sim:
        veterinario_screens.eliminar_veterinario(ent.persona_service)
    assert "eliminado correctamente" in sim.texto()
    restante = ent.sql("SELECT COUNT(*) FROM VETERINARIO WHERE rut = ?", (RUT_VET2,))
    assert restante[0][0] == 0, "El veterinario eliminado sigue en la base"

    id_mascota = sembrar_mascota(ent)
    with domingo_simulado():
        ent.consulta_service.registrar_urgencia(id_mascota, RUT_VET, "Emergencia")
    with SimulacionTeclado([RUT_VET, "1", ""]) as sim:
        veterinario_screens.eliminar_veterinario(ent.persona_service)
    assert "No es posible eliminar al veterinario" in sim.texto(), \
        "Falta la proteccion de veterinario con atenciones"
    protegido = ent.sql("SELECT COUNT(*) FROM VETERINARIO WHERE rut = ?", (RUT_VET,))
    assert protegido[0][0] == 1, "El veterinario con atenciones fue eliminado"
    return ("Nombre, telefono y especialidad de veterinario actualizados; eliminacion "
            "exitosa sin atenciones y bloqueada con atenciones")


def e20_farmacia_stock_actualizaciones(ent: Entorno) -> str:
    id_med = sembrar_medicamento(ent, stock=10)

    with SimulacionTeclado([str(id_med), "5", "1", ""]) as sim:
        farmacia_screen.reponer_stock(ent.farmacia_service)
    assert "Stock actualizado a 15" in sim.texto(), "El repuesto no se aplico"
    stock = ent.sql("SELECT stock FROM MEDICAMENTO WHERE id_medicamento = ?", (id_med,))[0][0]
    assert stock == 15, f"Stock tras reponer: {stock}"

    with SimulacionTeclado([str(id_med), "3", "1", ""]) as sim:
        farmacia_screen.descontar_stock(ent.farmacia_service)
    assert "Stock actualizado a 12" in sim.texto(), "El descuento no se aplico"
    stock = ent.sql("SELECT stock FROM MEDICAMENTO WHERE id_medicamento = ?", (id_med,))[0][0]
    assert stock == 12, f"Stock tras descontar: {stock}"

    with SimulacionTeclado([str(id_med), "9999", "1", ""]) as sim:
        farmacia_screen.descontar_stock(ent.farmacia_service)
    assert "Stock insuficiente" in sim.texto(), "Falta la validacion de stock insuficiente"
    stock = ent.sql("SELECT stock FROM MEDICAMENTO WHERE id_medicamento = ?", (id_med,))[0][0]
    assert stock == 12, "El descuento excesivo altero el stock"

    with SimulacionTeclado([str(id_med), "1", ""]) as sim:
        farmacia_screen.eliminar_medicamento(ent.farmacia_service)
    assert "eliminado correctamente" in sim.texto()
    restante = ent.sql("SELECT COUNT(*) FROM MEDICAMENTO WHERE id_medicamento = ?", (id_med,))
    assert restante[0][0] == 0, "El medicamento eliminado sigue en la base"

    id_med2 = ent.farmacia_service.registrar_medicamento(
        nombre_comercial="Meloxican", precio=18000, stock=4
    ).id_medicamento
    id_mascota = sembrar_mascota(ent)
    sembrar_veterinario(ent)
    with domingo_simulado():
        consulta = ent.consulta_service.registrar_urgencia(id_mascota, RUT_VET, "Dolor")
    ent.consulta_service.registrar_receta(
        id_detalle=consulta.detalle.id_detalle,
        id_medicamento=id_med2, cantidad=1, instrucciones="Cada 24 horas",
    )
    with SimulacionTeclado([str(id_med2), "1", ""]) as sim:
        farmacia_screen.eliminar_medicamento(ent.farmacia_service)
    assert "no es posible eliminar el medicamento" in sim.texto().lower(), \
        "Falta la proteccion de medicamento con recetas"
    protegido = ent.sql("SELECT COUNT(*) FROM MEDICAMENTO WHERE id_medicamento = ?", (id_med2,))
    assert protegido[0][0] == 1, "El medicamento con recetas fue eliminado"
    return ("Repuesto, descuento y eliminacion de medicamento funcionales; stock insuficiente "
            "validado; eliminacion bloqueada para medicamento con recetas")




def e21_recetas_crud_pantalla(ent: Entorno) -> str:
    id_mascota = sembrar_mascota(ent)
    sembrar_veterinario(ent)
    id_med = sembrar_medicamento(ent)
    with domingo_simulado():
        consulta = ent.consulta_service.registrar_urgencia(id_mascota, RUT_VET, "Infeccion")
    detalle_id = consulta.detalle.id_detalle

    with SimulacionTeclado([str(id_med), "3", "Cada 12 horas", ""]) as sim:
        consulta_screens.agregar_receta(ent.consulta_service, ent.farmacia_service, consulta.detalle)
    assert "agregada a la atenci" in sim.texto(), "La pantalla no confirmo la receta"
    fila = ent.sql(
        "SELECT cantidad, instrucciones FROM RECETA_MEDICA WHERE id_detalle = ?", (detalle_id,)
    )[0]
    assert fila[0] == 3 and "12 horas" in fila[1], f"Receta persistida incorrecta: {fila}"
    id_receta = ent.sql(
        "SELECT id_receta FROM RECETA_MEDICA WHERE id_detalle = ?", (detalle_id,)
    )[0][0]

    with SimulacionTeclado([str(id_receta), "1", ""]) as sim:
        consulta_screens.eliminar_receta(ent.consulta_service, consulta.detalle)
    assert "Receta eliminada correctamente" in sim.texto(), "La pantalla no confirmo la eliminacion"
    restante = ent.sql("SELECT COUNT(*) FROM RECETA_MEDICA WHERE id_receta = ?", (id_receta,))
    assert restante[0][0] == 0, "La receta eliminada sigue en la base"
    return "Alta y baja de receta por pantalla verificadas en BD"


def e22_veterinarios_y_especialidades_pantalla(ent: Entorno) -> str:
    sembrar_veterinario(ent)
    with SimulacionTeclado(["Cirugia", "Procedimientos", ""]) as sim:
        veterinario_screens.registrar_especialidad(ent.persona_service)
    assert "registrada correctamente" in sim.texto()
    esp_cirugia = ent.sql(
        "SELECT id_especialidad FROM ESPECIALIDAD WHERE nombre_especialidad = 'Cirugia'"
    )[0][0]

    with SimulacionTeclado([RUT_VET2, "Diego Fuentes", "933444555", str(esp_cirugia), ""]) as sim:
        veterinario_screens.registrar_veterinario(ent.persona_service)
    assert "registrado con" in sim.texto(), "La pantalla no confirmo el veterinario"
    fila = ent.sql("SELECT nombre_completo FROM VETERINARIO WHERE rut = ?", (RUT_VET2,))
    assert fila and fila[0][0] == "Diego Fuentes", "Veterinario no persistido"

    with SimulacionTeclado([str(esp_cirugia), "Cirugias de tejidos blandos", ""]) as sim:
        veterinario_screens.actualizar_descripcion_especialidad(ent.persona_service)
    assert "actualizada exitosamente" in sim.texto(), "La pantalla no confirmo la descripcion"
    esp_db = ent.sql(
        "SELECT descripcion, nombre_especialidad FROM ESPECIALIDAD WHERE id_especialidad = ?",
        (esp_cirugia,),
    )[0]
    assert esp_db[0] == "Cirugias de tejidos blandos", f"Descripcion no persistida: {esp_db[0]}"
    assert esp_db[1] == "Cirugia", "El nombre no debia cambiar al actualizar la descripcion"

    esp_libre = ent.persona_service.registrar_especialidad("Laboratorio", "Analisis")
    with SimulacionTeclado([str(esp_libre.id_especialidad), "1", ""]) as sim:
        veterinario_screens.eliminar_especialidad(ent.persona_service)
    assert "eliminada correctamente" in sim.texto()
    assert ent.sql(
        "SELECT COUNT(*) FROM ESPECIALIDAD WHERE id_especialidad = ?", (esp_libre.id_especialidad,)
    )[0][0] == 0, "La especialidad eliminada sigue en la base"

    id_esp1 = ent.sql(
        "SELECT id_especialidad FROM ESPECIALIDAD WHERE nombre_especialidad = 'Medicina General'"
    )[0][0]
    with SimulacionTeclado([str(id_esp1), "1", ""]) as sim:
        veterinario_screens.eliminar_especialidad(ent.persona_service)
    assert "No es posible eliminar la especialidad" in sim.texto(), \
        "Falta la proteccion de especialidad con veterinarios"
    assert ent.sql(
        "SELECT COUNT(*) FROM ESPECIALIDAD WHERE id_especialidad = ?", (id_esp1,)
    )[0][0] == 1, "La especialidad con veterinarios fue eliminada"
    return ("Veterinario y especialidad registrados por pantalla; descripcion de especialidad "
            "actualizable sin tocar el nombre; especialidad se elimina solo sin veterinarios")


def e23_iniciar_atencion_y_paneles(ent: Entorno) -> str:
    id_mascota = sembrar_mascota(ent)
    sembrar_veterinario(ent)
    consulta = ent.consulta_service.registrar_consulta(
        id_mascota, datetime(2026, 11, 14, 10, 0), "Control anual"
    )
    entradas = [
        str(consulta.id_consulta), RUT_VET, "",
        "2", "1", "Motivo actualizado", "8", "", "1", "", "9", "1",
    ]
    with SimulacionTeclado(entradas) as sim:
        consulta_screens.iniciar_atencion(ent.consulta_service, ent.farmacia_service)
    salida = sim.texto()
    assert "iniciada para" in salida, "La pantalla no inicio la atencion"
    assert "RESUMEN DE LA ATENCI" in salida, "El resumen de atencion no se mostro"
    assert "FICHA M" in salida, "La ficha medica no se mostro"
    assert "no tiene atenciones finalizadas" in salida, "La ficha no reporto historial vacio"
    fila = ent.sql(
        "SELECT estado, motivo, fecha_inicio_atencion FROM CONSULTA WHERE id_consulta = ?",
        (consulta.id_consulta,),
    )[0]
    assert fila[0] == "EN ESPERA EXAMENES", f"Estado final: {fila[0]}"
    assert fila[1] == "Motivo actualizado", f"Motivo no persistido: {fila[1]}"
    assert fila[2] is not None, "No se registro fecha de inicio"
    return "Inicio de atencion por pantalla + motivo/resumen/ficha operativos; pausa persistida"


def e24_lecturas_personas_mascotas(ent: Entorno) -> str:
    id_mascota = sembrar_mascota(ent)
    sembrar_veterinario(ent)

    with SimulacionTeclado([RUT_PROP, ""]) as sim:
        propietario_screens.consultar_propietario_por_rut(
            ent.persona_service, None, None, ent.mascota_service
        )
    salida = sim.texto()
    assert "INFORMACI" in salida and "Maria Lopez" in salida, "Ficha por RUT fallo"

    with SimulacionTeclado(["Maria", ""]) as sim:
        propietario_screens.consultar_propietarios_por_nombre(ent.persona_service)
    assert "Maria" in sim.texto(), "Busqueda de propietarios por nombre fallo"

    with SimulacionTeclado([RUT_PROP, "944555666", ""]) as sim:
        propietario_screens.cambiar_contacto(ent.persona_service)
    assert "actualizado" in sim.texto()
    tel = ent.sql("SELECT telefono FROM PROPIETARIO WHERE rut = ?", (RUT_PROP,))[0][0]
    assert tel == "+56944555666", f"Telefono no persistido: {tel}"

    with SimulacionTeclado([RUT_PROP, "Quilaco", ""]) as sim:
        propietario_screens.cambiar_comuna(ent.persona_service)
    assert "actualizada" in sim.texto()
    comuna = ent.sql("SELECT comuna FROM PROPIETARIO WHERE rut = ?", (RUT_PROP,))[0][0]
    assert comuna == "Quilaco", f"Comuna no persistida: {comuna}"

    with SimulacionTeclado([RUT_VET, ""]) as sim:
        veterinario_screens.buscar_vet_por_rut(ent.persona_service)
    assert "INFORMACI" in sim.texto() and "Camila" in sim.texto()

    with SimulacionTeclado(["Camila", ""]) as sim:
        veterinario_screens.buscar_vet_por_nombre(ent.persona_service)
    assert "Camila" in sim.texto()

    with SimulacionTeclado([""]) as sim:
        veterinario_screens.listar_todos_veterinarios(ent.persona_service)
    assert "Camila" in sim.texto()

    with SimulacionTeclado(["Boby", ""]) as sim:
        mascotas_screen.buscar_por_nombre(ent.mascota_service)
    assert "Boby" in sim.texto()

    with SimulacionTeclado([RUT_PROP, ""]) as sim:
        mascotas_screen.buscar_por_propietario(ent.mascota_service)
    assert "Boby" in sim.texto()

    with SimulacionTeclado([""]) as sim:
        mascotas_screen.listar_todas_mascotas(ent.mascota_service)
    assert "Boby" in sim.texto()

    with SimulacionTeclado([""]) as sim:
        mascotas_screen.listar_especies(ent.mascota_service)
    assert "Canino" in sim.texto()
    assert ent.sql("SELECT COUNT(*) FROM MASCOTA WHERE id_mascota = ?", (id_mascota,))[0][0] == 1
    return ("Busquedas y listados de propietarios, veterinarios, mascotas y especies; "
            "telefono y comuna de propietario actualizados")


def e25_lecturas_clinicas_y_despachos_lote(ent: Entorno) -> str:
    id_mascota = sembrar_mascota(ent)
    sembrar_veterinario(ent)
    id_med1 = sembrar_medicamento(ent, stock=5)
    id_med2 = ent.farmacia_service.registrar_medicamento(
        nombre_comercial="Meloxican", precio=18000, stock=3
    ).id_medicamento
    c1 = ent.consulta_service.registrar_consulta(
        id_mascota, datetime(2026, 11, 14, 10, 0), "Control"
    )
    with domingo_simulado():
        urg = ent.consulta_service.registrar_urgencia(id_mascota, RUT_VET, "Dolor")
    detalle_id = urg.detalle.id_detalle
    r1 = ent.consulta_service.registrar_receta(detalle_id, id_med1, 2, "Cada 8 horas")
    r2 = ent.consulta_service.registrar_receta(detalle_id, id_med2, 1, "Cada 24 horas")

    with SimulacionTeclado([str(c1.id_consulta), ""]) as sim:
        consulta_screens.buscar_consulta_por_id(ent.consulta_service)
    assert "INFORMACI" in sim.texto() and "Boby" in sim.texto()

    with SimulacionTeclado([""]) as sim:
        consulta_screens.listar_todas_consultas(ent.consulta_service)
    assert "Boby" in sim.texto()

    with SimulacionTeclado([str(id_mascota), ""]) as sim:
        consulta_screens.listar_consultas_por_mascota(ent.consulta_service)
    assert "Boby" in sim.texto()

    with SimulacionTeclado(["1", ""]) as sim:
        consulta_screens.listar_consultas_por_estado(ent.consulta_service)
    assert "Boby" in sim.texto(), "El filtro AGENDADA no mostro la cita"

    with SimulacionTeclado([RUT_VET, ""]) as sim:
        consulta_screens.listar_consultas_por_veterinario(ent.consulta_service)
    assert "Boby" in sim.texto()

    with SimulacionTeclado([""]) as sim:
        consulta_screens.listar_todos_detalles(ent.consulta_service)
    assert "Camila" in sim.texto()

    with SimulacionTeclado([RUT_VET, ""]) as sim:
        consulta_screens.buscar_detalles_por_veterinario(ent.consulta_service)
    assert "Camila" in sim.texto()

    with SimulacionTeclado([str(detalle_id), ""]) as sim:
        consulta_screens.obtener_detalle_por_id(ent.consulta_service)
    assert "DETALLE M" in sim.texto()

    with SimulacionTeclado([""]) as sim:
        consulta_screens.listar_todas_recetas(ent.consulta_service)
    assert "Amoxicilina" in sim.texto()

    with SimulacionTeclado([str(detalle_id), ""]) as sim:
        consulta_screens.listar_recetas_de_detalle(ent.consulta_service)
    assert "Amoxicilina" in sim.texto()

    with SimulacionTeclado(["Amoxicilina", ""]) as sim:
        consulta_screens.buscar_recetas_por_medicamento(ent.consulta_service)
    assert "Amoxicilina" in sim.texto()

    with SimulacionTeclado(["Meloxican", ""]) as sim:
        farmacia_screen.buscar_medicamentos_por_nombre(ent.farmacia_service)
    assert "Meloxican" in sim.texto()

    with SimulacionTeclado([""]) as sim:
        farmacia_screen.listar_medicamentos(ent.farmacia_service)
    assert "Amoxicilina" in sim.texto() and "Meloxican" in sim.texto()

    with SimulacionTeclado([""]) as sim:
        farmacia_screen.listar_stock_critico(ent.farmacia_service)
    assert "Meloxican" in sim.texto() and "CR" in sim.texto(), "Stock critico no detectado"

    with SimulacionTeclado([str(r1.id_receta), str(r2.id_receta), "0", ""]) as sim:
        farmacia_screen.despachar_recetas_seleccionadas(ent.farmacia_service)
    assert "TOTAL COBRADO" in sim.texto(), "El comprobante de despacho por lote fallo"
    stock1 = ent.sql("SELECT stock FROM MEDICAMENTO WHERE id_medicamento = ?", (id_med1,))[0][0]
    stock2 = ent.sql("SELECT stock FROM MEDICAMENTO WHERE id_medicamento = ?", (id_med2,))[0][0]
    assert (stock1, stock2) == (3, 2), f"Stocks tras despacho por lote: {stock1}, {stock2}"

    with domingo_simulado():
        urg2 = ent.consulta_service.registrar_urgencia(id_mascota, RUT_VET, "Recaida")
    ent.consulta_service.registrar_receta(
        urg2.detalle.id_detalle, id_med1, 1, "Una vez al dia"
    )
    with SimulacionTeclado([str(urg2.detalle.id_detalle), "1", ""]) as sim:
        farmacia_screen.despachar_recetas_de_detalle(ent.farmacia_service)
    assert "TOTAL COBRADO" in sim.texto(), "El despacho por detalle fallo"
    stock_final = ent.sql(
        "SELECT stock FROM MEDICAMENTO WHERE id_medicamento = ?", (id_med1,)
    )[0][0]
    assert stock_final == 2, f"Stock final esperado 2, obtenido {stock_final}"
    return ("Lecturas de consultas, detalles, recetas y catalogo operativas; despacho por "
            "seleccion y por detalle con stock verificado")




ESCENARIOS = [
    ("E01", "Menu principal y navegacion", e01_menu_principal_navegacion),
    ("E02", "CRUD propietarios por pantalla", e02_propietarios_crud),
    ("E03", "Registro especie y mascota", e03_especie_mascota_registro),
    ("E04", "Consulta normal en dia habil", e04_consulta_normal_dia_habil),
    ("E05", "Bloqueo de cita en domingo", e05_bloqueo_domingo),
    ("E06", "Bloqueo de cita en feriado", e06_bloqueo_feriado),
    ("E07", "API caida bloquea consulta", e07_api_caida_consulta_bloqueada),
    ("E08", "Urgencia bloqueada en dia habil", e08_urgencia_bloqueada_dia_habil),
    ("E09", "Urgencia domingo EN_ATENCION", e09_urgencia_domingo_en_atencion),
    ("E10", "Espera por examenes y reanudacion", e10_espera_y_reanudacion),
    ("E11", "Domingo y feriado recargo unico", e11_domingo_y_feriado_recargo_unico),
    ("E12", "Farmacia stock y despacho", e12_farmacia_stock_y_despacho),
    ("E13", "Errores de APIs externas", e13_errores_api_externos),
    ("E14", "USD solo en memoria", e14_usd_solo_en_memoria),
    ("E15", "Reagendar consulta", e15_reagendar_consulta),
    ("E16", "Cancelar e inasistencia", e16_cancelar_e_inasistencia),
    ("E17", "Mascotas: actualizar y proteger", e17_mascotas_actualizacion_y_protecciones),
    ("E18", "Especies: dato catalogo estatico", e18_especies_dato_estatico),
    ("E19", "Veterinarios: actualizar y proteger", e19_veterinarios_actualizacion_y_protecciones),
    ("E20", "Farmacia: stock y protecciones", e20_farmacia_stock_actualizaciones),
    ("E21", "Recetas: alta y baja por pantalla", e21_recetas_crud_pantalla),
    ("E22", "Veterinarios/especialidades por pantalla", e22_veterinarios_y_especialidades_pantalla),
    ("E23", "Iniciar atencion y paneles", e23_iniciar_atencion_y_paneles),
    ("E24", "Lecturas personas y mascotas", e24_lecturas_personas_mascotas),
    ("E25", "Lecturas clinicas y despachos por lote", e25_lecturas_clinicas_y_despachos_lote),
]


def main() -> int:
    resultados = []
    for codigo, nombre, funcion in ESCENARIOS:
        ent = Entorno(
            fechas_feriados=[date(2026, 12, 25), date(2026, 11, 15)]
            if codigo == "E11" else [date(2026, 12, 25)],
            fallar_api=(codigo in ("E07", "E13")),
        )
        try:
            evidencia = funcion(ent)
            resultados.append((codigo, nombre, "PASS", evidencia))
            print(f"[PASS] {codigo} {nombre}")
        except Exception as error:  # noqa: BLE001 - el corredor reporta cada fallo
            resultados.append((codigo, nombre, "FAIL", f"{type(error).__name__}: {error}"))
            print(f"[FAIL] {codigo} {nombre} -> {type(error).__name__}: {error}")
            traceback.print_exc(limit=6, file=sys.stderr)
        finally:
            ent.cerrar()

    print("\n" + "=" * 100)
    print("REPORTE E2E VETCARE")
    print("=" * 100)
    for codigo, nombre, estado, evidencia in resultados:
        print(f"{codigo:<5} | {estado:<6} | {nombre:<40} | {evidencia}")
    fallos = sum(1 for r in resultados if r[2] == "FAIL")
    print("-" * 100)
    print(f"Total: {len(resultados)} | PASS: {len(resultados) - fallos} | FAIL: {fallos}")
    return 1 if fallos else 0


if __name__ == "__main__":
    raise SystemExit(main())
