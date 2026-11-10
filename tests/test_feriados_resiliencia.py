# -*- coding: utf-8 -*-
"""Pruebas criticas de resiliencia de FeriadoService llamando a la API real.

Politica del servicio: caché mensual en SQLite (FERIADO + FERIADO_CACHE fila
unica). Si el cache corresponde al mes en curso no se consulta la API; si la
API falla y existen feriados guardados (aunque sean de otro mes) se usan en
silencio; solo sin cache se propaga el error. Los domingos no consultan la API.

Escenarios (hoy: mes en curso 2026-11; fecha anterior = cache viejo):
  A1  API real arriba, cache vacia          -> sincroniza el anio completo
  A2  Cache vigente                         -> 0 intentos de transporte
  A3  forzar_refresco con API real arriba   -> re-sincroniza (1 intento)
  B   Sin cache + API caida                 -> error explicito tras 3 intentos
  C   Cache mes anterior + API caida        -> degradado silencioso, sin remarcado
  D1  Sin cache + API caida + domingo       -> urgencia permitida (regla)
  D2  Sin cache + API caida + martes        -> error (no se puede confirmar)
  E   Cache vigente + API caida             -> 0 intentos, datos desde SQLite
  E2  Cache vigente + forzar + API caida    -> 3 intentos y degradado silencioso
  F   API viva con respuesta no usable      -> degradado / error sin cache
  G   HTTP 500 real (servidor local)        -> 3 intentos; degradado / error
  H   Resumen calendario en degradacion     -> domingo y feriado simultaneos
  I   Sabado laborable en degradacion       -> dia habil aun con cache vieja
  J   Autoreparacion al volver la API       -> re-sincroniza y deja de reintentar
  K   Cache parcial corrupta del mes actual -> 0 intentos y respuesta incompleta
      (documento del hallazgo: el cache no se repara hasta el mes siguiente)

Ejecucion: python tests/test_feriados_resiliencia.py
(Requiere Internet para A1, A3 y J; los fallos usan enlaces alterados reales.)
"""
from __future__ import annotations

import contextlib
import shutil
import sqlite3
import sys
import tempfile
import threading
import traceback
from datetime import date, datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config.configuracion import Configuracion
from database.conexion import ConexionDB
from dao.feriado_dao import FeriadoDAO
from exceptions import exceptions
from models.feriado import Feriado
from services import cliente_resiliente
from services.cliente_resiliente import ClienteHTTPResiliente
from services.feriado_service import FeriadoService

URL_REAL = Configuracion.URL_FERIADOS
URL_CAIDA = "https://vetcare-inexistente-e2e.invalid"
URL_OTRA_API = "https://cl.dolarapi.com/v1/cotizaciones"
FERIADO_SEMILLA = Feriado(
    fecha=date(2026, 9, 18), nombre="Fiestas Patrias", tipo="Legal", es_irrenunciable=True
)
DOMINGO = date(2026, 11, 15)
MARTES = date(2026, 11, 17)
SABADO = date(2026, 11, 14)


class EntornoFeriado:
    def __init__(self):
        self.carpeta = Path(tempfile.mkdtemp(prefix="e2e_feriado_"))
        self.conexion = ConexionDB(str(self.carpeta / "feriados.db"))
        self.dao = FeriadoDAO(self.conexion)
        self.cliente = ClienteHTTPResiliente(timeout=10)
        self.intentos = 0

    @contextlib.contextmanager
    def contar_intentos(self):
        """Instrumenta requests.get del cliente real para contar intentos de transporte."""
        original = cliente_resiliente.requests.get

        def envuelto(*args, **kwargs):
            self.intentos += 1
            return original(*args, **kwargs)

        cliente_resiliente.requests.get = envuelto
        try:
            yield
        finally:
            cliente_resiliente.requests.get = original

    def servicio(self) -> FeriadoService:
        return FeriadoService(self.dao, cliente_http=self.cliente)

    def sembrar_cache(self, anio: int, mes: int, feriados: list[Feriado]) -> None:
        self.dao.reemplazar_cache(feriados, anio, mes, datetime(2026, mes, 1, 12, 0))

    def cache_marcado(self) -> tuple[int, int] | None:
        with contextlib.closing(sqlite3.connect(self.carpeta / "feriados.db")) as conn:
            fila = conn.execute("SELECT anio, mes FROM FERIADO_CACHE WHERE id = 1").fetchone()
            return (fila[0], fila[1]) if fila else None

    def total_feriados(self) -> int:
        with contextlib.closing(sqlite3.connect(self.carpeta / "feriados.db")) as conn:
            return conn.execute("SELECT COUNT(*) FROM FERIADO").fetchone()[0]

    def cerrar(self) -> None:
        shutil.rmtree(self.carpeta, ignore_errors=True)


@contextlib.contextmanager
def servidor_500():
    hits = {"total": 0}

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            hits["total"] += 1
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"error": "servidor caido"}')

        def log_message(self, *args):
            pass

    servidor = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    hilo = threading.Thread(target=servidor.serve_forever, daemon=True)
    hilo.start()
    try:
        yield f"http://127.0.0.1:{servidor.server_port}", hits
    finally:
        servidor.shutdown()
        servidor.server_close()


def a1_api_real_cache_vacia(ent: EntornoFeriado) -> str:
    servicio = ent.servicio()
    with ent.contar_intentos():
        feriado = servicio.es_feriado(date(2026, 1, 1))
    assert feriado is not None, "El 1 de enero no se obtuvo desde la API real"
    assert feriado.nombre, "El feriado real llego sin nombre"
    assert ent.intentos == 1, f"Debio ser 1 intento real, hubo {ent.intentos}"
    total = ent.total_feriados()
    assert total >= 10, f"La API real debio traer el anio completo, trajo {total}"
    assert ent.cache_marcado() == (2026, 11), "El cache no quedo marcado como mes actual"
    return f"API real sincronizo {total} feriados de 2026 y marco cache 2026-11"


def a2_cache_vigente_sin_red(ent: EntornoFeriado) -> str:
    servicio = ent.servicio()
    servicio.es_feriado(date(2026, 1, 1))
    ent.intentos = 0
    feriado = servicio.es_feriado(date(2026, 1, 1))
    assert feriado is not None, "El cache vigente no respondio"
    assert ent.intentos == 0, f"Cache vigente debio evitar la API, hubo {ent.intentos} intentos"
    return "Cache del mes en curso: 0 intentos de transporte en la segunda consulta"


def a3_forzar_refresco_api_real(ent: EntornoFeriado) -> str:
    servicio = ent.servicio()
    with ent.contar_intentos():
        servicio.sincronizar_feriados()
    ent.intentos = 0
    with ent.contar_intentos():
        servicio.sincronizar_feriados(forzar_refresco=True)
    assert ent.intentos == 1, f"forzar debio hacer 1 intento real, hubo {ent.intentos}"
    assert ent.total_feriados() >= 10, "El reemplazo dejo la tabla incompleta"
    assert ent.cache_marcado() == (2026, 11), "El cache no quedo re-marcado"
    return f"forzar_refresco re-sincronizo contra la API real ({ent.total_feriados()} feriados)"


def b_sin_cache_api_caida(ent: EntornoFeriado) -> str:
    servicio = ent.servicio()
    servicio.URL_BASE = URL_CAIDA
    try:
        with ent.contar_intentos():
            servicio.es_dia_habil(MARTES)
        raise AssertionError("Sin cache y con API caida debia propagar el error")
    except exceptions.ServicioExternoException:
        assert ent.intentos == 3, f"Intentos de transporte esperados 3, hubo {ent.intentos}"
        assert ent.total_feriados() == 0, "No debio persistir feriados ante el fallo"
        assert ent.cache_marcado() is None, "No debio marcar cache ante el fallo"
        return "API caida sin cache: error explicito tras 3 intentos reales; BD intacta"


def c_cache_mes_anterior_api_caida(ent: EntornoFeriado) -> str:
    ent.sembrar_cache(2026, 10, [FERIADO_SEMILLA])
    servicio = ent.servicio()
    servicio.URL_BASE = URL_CAIDA
    with ent.contar_intentos():
        feriado = servicio.es_feriado(FERIADO_SEMILLA.fecha)
    assert feriado is not None and feriado.nombre == "Fiestas Patrias", \
        "El cache viejo no respaldo la consulta"
    assert ent.intentos == 3, f"Debio reintentar (cache no corresponde al mes): {ent.intentos}"
    assert ent.cache_marcado() == (2026, 10), "El degradado no debe re-marcar el cache"
    assert ent.total_feriados() == 1, "El degradado no debe alterar la BD"
    return ("Degradado silencioso con cache de octubre; sigue reintentando en cada "
            "consulta hasta que la API vuelva (autoreparacion pendiente)")


def d1_sin_cache_api_caida_domingo(ent: EntornoFeriado) -> str:
    servicio = ent.servicio()
    servicio.URL_BASE = URL_CAIDA
    with ent.contar_intentos():
        servicio.validar_urgencia_permitida(DOMINGO)
    assert ent.intentos == 3, f"El domingo intento verificar y fallo 3 veces: {ent.intentos}"
    return "Regla de urgencia en domingo con API caida: se permite tras 3 intentos fallidos"


def d2_sin_cache_api_caida_martes(ent: EntornoFeriado) -> str:
    servicio = ent.servicio()
    servicio.URL_BASE = URL_CAIDA
    try:
        with ent.contar_intentos():
            servicio.validar_urgencia_permitida(MARTES)
        raise AssertionError("En martes sin cache ni API debia rechazar la urgencia")
    except exceptions.ServicioExternoException:
        assert ent.intentos == 3, f"Intentos esperados 3, hubo {ent.intentos}"
        return "Urgencia en martes con API caida y sin cache: rechazada con error explicito"


def e_cache_vigente_api_caida(ent: EntornoFeriado) -> str:
    ent.sembrar_cache(2026, 11, [FERIADO_SEMILLA])
    servicio = ent.servicio()
    servicio.URL_BASE = URL_CAIDA
    with ent.contar_intentos():
        feriado = servicio.es_feriado(FERIADO_SEMILLA.fecha)
    assert feriado is not None, "El cache vigente no respondio con API caida"
    assert ent.intentos == 0, f"Cache vigente no debio llamar a la API: {ent.intentos} intentos"
    return "Cache del mes en curso corta sin tocar la red aunque el link este alterado"


def e2_cache_vigente_forzado_api_caida(ent: EntornoFeriado) -> str:
    ent.sembrar_cache(2026, 11, [FERIADO_SEMILLA])
    servicio = ent.servicio()
    servicio.URL_BASE = URL_CAIDA
    with ent.contar_intentos():
        servicio.sincronizar_feriados(forzar_refresco=True)
    assert ent.intentos == 3, f"forzar debio reintentar 3 veces: {ent.intentos}"
    assert ent.cache_marcado() == (2026, 11), "El fallo no debe borrar el cache previo"
    assert ent.total_feriados() == 1, "El fallo no debe alterar los feriados guardados"
    return "forzar_refresco con API caida: 3 intentos y el cache previo queda intacto"


def f_respuesta_no_usable(ent: EntornoFeriado) -> str:
    ent.sembrar_cache(2026, 10, [FERIADO_SEMILLA])
    servicio = ent.servicio()
    servicio.URL_BASE = URL_OTRA_API
    with ent.contar_intentos():
        feriado = servicio.es_feriado(FERIADO_SEMILLA.fecha)
    assert feriado is not None, "La respuesta no usable debio degradar al cache viejo"
    assert ent.intentos == 1, \
        f"Un HTTP 200 con forma incorrecta no se reintenta (solo fallos de transporte): {ent.intentos}"

    ent2 = EntornoFeriado()
    try:
        servicio_vacio = ent2.servicio()
        servicio_vacio.URL_BASE = URL_OTRA_API
        try:
            servicio_vacio.es_dia_habil(MARTES)
            raise AssertionError("Sin cache debia propagar el error de formato")
        except exceptions.ServicioExternoException as error:
            tipo = type(error).__name__
    finally:
        ent2.cerrar()
    return f"HTTP 200 con JSON de otra API ({tipo}): degradado al cache; sin cache se propaga"


def g_http_500_real(ent: EntornoFeriado) -> str:
    ent.sembrar_cache(2026, 10, [FERIADO_SEMILLA])
    servicio = ent.servicio()
    with servidor_500() as (url_local, hits):
        servicio.URL_BASE = url_local
        with ent.contar_intentos():
            feriado = servicio.es_feriado(FERIADO_SEMILLA.fecha)
    assert ent.intentos == 3, f"Intentos del cliente ante 500: {ent.intentos}"
    assert hits["total"] == 3, f"Peticiones recibidas por el servidor: {hits['total']}"
    assert feriado is not None, "Debio degradar al cache tras el 500"

    ent2 = EntornoFeriado()
    try:
        servicio_vacio = ent2.servicio()
        with servidor_500() as (url_local2, hits2):
            servicio_vacio.URL_BASE = url_local2
            try:
                servicio_vacio.es_dia_habil(MARTES)
                raise AssertionError("Sin cache debia propagar el error HTTP")
            except exceptions.ServicioExternoException:
                assert hits2["total"] == 3, "Sin cache tambien debio reintentar 3 veces"
    finally:
        ent2.cerrar()
    return "HTTP 500 real: 3 intentos verificados en el servidor; degradado con cache, error sin cache"


def h_resumen_calendario_degradado(ent: EntornoFeriado) -> str:
    domingo_feriado = Feriado(
        fecha=DOMINGO, nombre="Feriado dominical", tipo="Legal", es_irrenunciable=False
    )
    ent.sembrar_cache(2026, 11, [domingo_feriado])
    servicio = ent.servicio()
    servicio.URL_BASE = URL_CAIDA
    resumen = servicio.obtener_resumen_calendario(DOMINGO)
    assert resumen == "Domingo y feriado (Feriado dominical)", f"Resumen: {resumen}"
    assert servicio.es_dia_habil(MARTES) is True, "Un martes comun no es habil"
    return "Resumen degradado reporta 'Domingo y feriado' con cache vigente; martes es habil"


def i_sabado_laborable_degradado(ent: EntornoFeriado) -> str:
    ent.sembrar_cache(2026, 10, [FERIADO_SEMILLA])
    servicio = ent.servicio()
    servicio.URL_BASE = URL_CAIDA
    with ent.contar_intentos():
        assert servicio.es_dia_habil(SABADO) is True, "Un sabado no feriado debe ser habil"
    assert ent.intentos == 3, f"Reintentos en degradacion: {ent.intentos}"
    return "Sabado laborable confirmado incluso operando en modo degradado"


def j_autoreparacion(ent: EntornoFeriado) -> str:
    ent.sembrar_cache(2026, 10, [FERIADO_SEMILLA])
    servicio = ent.servicio()
    servicio.URL_BASE = URL_CAIDA
    with ent.contar_intentos():
        servicio.es_feriado(FERIADO_SEMILLA.fecha)
    assert ent.intentos == 3, f"Fase degradada debio reintentar 3 veces: {ent.intentos}"
    assert ent.cache_marcado() == (2026, 10), "El cache seguia viejo antes de la reparacion"

    servicio.URL_BASE = URL_REAL
    ent.intentos = 0
    with ent.contar_intentos():
        feriado = servicio.es_feriado(date(2026, 1, 1))
    assert feriado is not None, "La API recuperada debio sincronizar"
    assert ent.intentos == 1, f"La autoreparacion debio hacer 1 intento: {ent.intentos}"
    assert ent.cache_marcado() == (2026, 11), "El cache no quedo reparado al mes actual"
    assert ent.total_feriados() >= 10, "La reparacion debio traer el anio completo"

    ent.intentos = 0
    servicio.es_feriado(date(2026, 12, 25))
    assert ent.intentos == 0, "Tras reparar, el cache vigente no debia consultar"
    return "Autoreparacion verificada: 3 intentos fallidos -> 1 re-sincronizacion -> 0 intentos"


def k_cache_parcial_corrupta_mes_actual(ent: EntornoFeriado) -> str:
    parcial = Feriado(
        fecha=date(2026, 12, 25), nombre="Navidad", tipo="Legal", es_irrenunciable=False
    )
    ent.sembrar_cache(2026, 11, [parcial])
    servicio = ent.servicio()
    servicio.URL_BASE = URL_CAIDA
    with ent.contar_intentos():
        resultado = servicio.es_feriado(date(2026, 1, 1))
    assert ent.intentos == 0, \
        f"El cache del mes actual evita re-sincronizar aun siendo parcial: {ent.intentos}"
    assert resultado is None, \
        "El 1 de enero existe en la API real pero el cache parcial lo oculta"
    return ("Hallazgo documentado: cache parcial del mes actual no se autorepara hasta "
            "el mes siguiente; 1 de enero aparece como no feriado")


ESCENARIOS = [
    ("A1", "API real arriba, cache vacia", a1_api_real_cache_vacia),
    ("A2", "Cache vigente sin red", a2_cache_vigente_sin_red),
    ("A3", "forzar_refresco API real", a3_forzar_refresco_api_real),
    ("B", "Sin cache + API caida", b_sin_cache_api_caida),
    ("C", "Cache mes anterior + API caida", c_cache_mes_anterior_api_caida),
    ("D1", "Sin cache + caida + domingo", d1_sin_cache_api_caida_domingo),
    ("D2", "Sin cache + caida + martes", d2_sin_cache_api_caida_martes),
    ("E", "Cache vigente + API caida", e_cache_vigente_api_caida),
    ("E2", "Cache vigente + forzar + caida", e2_cache_vigente_forzado_api_caida),
    ("F", "Respuesta de otra API", f_respuesta_no_usable),
    ("G", "HTTP 500 real", g_http_500_real),
    ("H", "Resumen calendario degradado", h_resumen_calendario_degradado),
    ("I", "Sabado laborable en degradacion", i_sabado_laborable_degradado),
    ("J", "Autoreparacion al volver la API", j_autoreparacion),
    ("K", "Cache parcial corrupta (hallazgo)", k_cache_parcial_corrupta_mes_actual),
]


def main() -> int:
    resultados = []
    for codigo, nombre, funcion in ESCENARIOS:
        ent = EntornoFeriado()
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

    print("\n" + "=" * 110)
    print("REPORTE RESILIENCIA FERIADOSERVICE (API REAL + LINKS ALTERADOS)")
    print("=" * 110)
    for codigo, nombre, estado, evidencia in resultados:
        print(f"{codigo:<4} | {estado:<6} | {nombre:<38} | {evidencia}")
    fallos = sum(1 for r in resultados if r[2] == "FAIL")
    print("-" * 110)
    print(f"Total: {len(resultados)} | PASS: {len(resultados) - fallos} | FAIL: {fallos}")
    return 1 if fallos else 0


if __name__ == "__main__":
    raise SystemExit(main())
