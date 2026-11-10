# -*- coding: utf-8 -*-
"""Pruebas criticas de resiliencia de EconomiaService llamando a la API real.

Escenarios (fecha habil esperada = hoy habil; fecha anterior = cache viejo):
  A1  API real arriba sin cache               -> valor fresco persistido en BD y RAM
  A2  Segundo llamado tras API real           -> 0 llamadas nuevas (L1/L2 corta)
  A3  forzar_refresco con API real arriba     -> nueva llamada real y re-persistencia
  B   Sin cache alguno + API caida            -> error explicito, BD intacta
  C   SQLite antiguo + API caida              -> modo degradado con valor historico
  D1  RAM antiguo inyectado + BD vacia        -> la RAM vieja NO respalda (error)
  D2  RAM antiguo + SQLite antiguo + API caida-> SQLite gana la contingencia
  D3  RAM vigente inyectado + API caida       -> retorna RAM sin llamar API
  E   SQLite vigente + API caida              -> retorna SQLite sin llamar API
  E2  SQLite vigente + forzar + API caida     -> 3 reintentos y degradado
  F   Link alterado a otra API (respuesta no usable) -> degradado / error explicito
  G   HTTP 500 real (servidor local)          -> 3 reintentos y degradado

Ejecucion: python tests/test_economia_resiliencia.py  (requiere Internet solo
para A1-A3 y F; los escenarios de caida usan enlaces alterados reales).
"""
from __future__ import annotations

import contextlib
import shutil
import sqlite3
import sys
import tempfile
import threading
import traceback
from datetime import date
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config.configuracion import Configuracion
from database.conexion import ConexionDB
from dao.divisa_dao import DivisaDAO
from exceptions import exceptions
from models.divisa import Divisa
from services import cliente_resiliente
from services.cliente_resiliente import ClienteHTTPResiliente
from services.economia_service import EconomiaService

URL_REAL = Configuracion.URL_BASE_DOLAR
URL_CAIDA = "https://vetcare-inexistente-e2e.invalid"
URL_OTRA_API = "https://api.boostr.cl/holidays.json"
VALOR_VIEJO = 900.0
VALOR_RAM_VIEJO = 800.0


class ClienteContador:
    """Envuelve al cliente real (HTTP verdadero) contando cada llamada."""

    def __init__(self, base: ClienteHTTPResiliente):
        self.base = base
        self.llamadas: list[str] = []

    def ejecutar_get(self, url, parametros=None, cabeceras=None, *, servicio="Servicio externo"):
        self.llamadas.append(url)
        return self.base.ejecutar_get(url, parametros, cabeceras, servicio=servicio)


class EntornoDivisa:
    def __init__(self):
        self.carpeta = Path(tempfile.mkdtemp(prefix="e2e_divisa_"))
        self.conexion = ConexionDB(str(self.carpeta / "divisas.db"))
        self.dao = DivisaDAO(self.conexion)
        self.contador = ClienteContador(ClienteHTTPResiliente(timeout=10))
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

    def servicio(self) -> EconomiaService:
        return EconomiaService(self.dao, cliente_http=self.contador)

    def sembrar(self, valor: float, fecha: date) -> None:
        self.dao.actualizar(Divisa(
            codigo="usd", nombre="Dolar observado", valor=valor, fecha_actualizacion=fecha
        ))

    def inyectar_ram(self, servicio: EconomiaService, valor: float, fecha: date) -> None:
        servicio._cache["usd"] = Divisa(
            codigo="usd", nombre="Dolar observado", valor=valor, fecha_actualizacion=fecha
        )

    def valor_bd(self) -> float | None:
        with contextlib.closing(sqlite3.connect(self.carpeta / "divisas.db")) as conn:
            fila = conn.execute("SELECT valor FROM DIVISA WHERE codigo = 'usd'").fetchone()
            return fila[0] if fila else None

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


def a1_api_real_sin_cache(ent: EntornoDivisa) -> str:
    servicio = ent.servicio()
    divisa = servicio.obtener_dolar_actual()
    esperada = EconomiaService._obtener_fecha_habil_esperada(date.today())
    assert divisa.valor > 0, "El valor de la API real no es positivo"
    assert ent.contador.llamadas == [f"{URL_REAL}/usd"], f"Llamadas reales: {ent.contador.llamadas}"
    assert ent.valor_bd() == divisa.valor, "La divisa no se persistio en SQLite"
    assert "usd" in servicio._cache, "La divisa no quedo en RAM"
    vigencia = "vigente" if divisa.fecha_actualizacion >= esperada else \
        f"con fecha publicada {divisa.fecha_actualizacion} (anterior al habil esperado {esperada})"
    return f"API real consultada; valor {divisa.valor} CLP {vigencia}; persistido en BD y RAM"


def a2_segundo_llamado_sin_red_llamada(ent: EntornoDivisa) -> str:
    servicio = ent.servicio()
    primera = servicio.obtener_dolar_actual()
    llamadas_previas = len(ent.contador.llamadas)
    segunda = servicio.obtener_dolar_actual()
    nuevas = len(ent.contador.llamadas) - llamadas_previas
    esperada = EconomiaService._obtener_fecha_habil_esperada(date.today())
    if primera.fecha_actualizacion >= esperada:
        assert nuevas == 0, f"Se volvieron a llamar {nuevas} veces con cache vigente"
        detalle = "L1/L2 corto sin llamar a la API (cache vigente)"
    else:
        detalle = (
            f"La API publica con fecha {primera.fecha_actualizacion} anterior al "
            f"habil esperado {esperada}: el sistema reintenta la fuente por diseño"
        )
    assert segunda.valor == primera.valor, "El valor no es consistente"
    return f"Segundo llamado: {nuevas} llamadas nuevas; {detalle}"


def a3_forzar_refresco_api_real(ent: EntornoDivisa) -> str:
    servicio = ent.servicio()
    primera = servicio.obtener_dolar_actual()
    llamadas_previas = len(ent.contador.llamadas)
    forzada = servicio.obtener_dolar_actual(forzar_refresco=True)
    nuevas = len(ent.contador.llamadas) - llamadas_previas
    assert nuevas == 1, f"forzar_refresco debio llamar 1 vez, llamo {nuevas}"
    assert forzada.valor > 0, "El valor forzado no es positivo"
    assert ent.valor_bd() == forzada.valor, "La divisa forzada no se re-persistio"
    return f"forzar_refresco consulto la API real de nuevo ({nuevas} llamada) y re-persistio {forzada.valor} CLP"


def b_sin_cache_y_api_caida(ent: EntornoDivisa) -> str:
    servicio = ent.servicio()
    servicio.URL_BASE = URL_CAIDA
    try:
        with ent.contar_intentos():
            servicio.obtener_dolar_actual()
        raise AssertionError("Se esperaba ServicioExternoException sin cache y con API caida")
    except exceptions.ServicioExternoException as error:
        tipo = type(error).__name__
        assert ent.intentos == 3, \
            f"Se esperaban 3 intentos de transporte reales, hubo {ent.intentos}"
        assert ent.valor_bd() is None, "No debio persistir nada sin cache y sin API"
        assert not servicio._cache, "No debio poblar la RAM ante error sin historico"
        return f"API caida tras link alterado: {tipo} tras 3 intentos de transporte reales; BD y RAM intactas"


def c_sqlite_antiguo_y_api_caida(ent: EntornoDivisa) -> str:
    ent.sembrar(VALOR_VIEJO, date(2026, 11, 9))
    servicio = ent.servicio()
    servicio.URL_BASE = URL_CAIDA
    with ent.contar_intentos():
        divisa = servicio.obtener_dolar_actual()
    assert divisa.valor == VALOR_VIEJO, f"Degradado devolvio {divisa.valor}, esperado {VALOR_VIEJO}"
    assert ent.intentos == 3, f"Reintentos de transporte reales: {ent.intentos}"
    assert ent.valor_bd() == VALOR_VIEJO, "El modo degradado no debe reescribir la BD"
    assert servicio._cache["usd"].valor == VALOR_VIEJO, "El historico no quedo en RAM"
    return f"Modo degradado: devuelve el historico SQLite ({VALOR_VIEJO} CLP) tras 3 intentos reales"


def d1_ram_antigua_bd_vacia_api_caida(ent: EntornoDivisa) -> str:
    servicio = ent.servicio()
    servicio.URL_BASE = URL_CAIDA
    ent.inyectar_ram(servicio, VALOR_RAM_VIEJO, date(2026, 11, 5))
    try:
        servicio.obtener_dolar_actual()
        raise AssertionError("La RAM vieja no debia usarse como respaldo con BD vacia")
    except exceptions.ServicioExternoException as error:
        tipo = type(error).__name__
        assert ent.valor_bd() is None, "No debio persistir nada"
        return f"Hallazgo de diseno confirmado: RAM vieja no respalda con BD vacia -> {tipo}"


def d2_ram_antigua_y_sqlite_antiguo_api_caida(ent: EntornoDivisa) -> str:
    ent.sembrar(VALOR_VIEJO, date(2026, 11, 9))
    servicio = ent.servicio()
    servicio.URL_BASE = URL_CAIDA
    ent.inyectar_ram(servicio, VALOR_RAM_VIEJO, date(2026, 11, 5))
    divisa = servicio.obtener_dolar_actual()
    assert divisa.valor == VALOR_VIEJO, \
        f"La contingencia debio tomar SQLite ({VALOR_VIEJO}), tomo {divisa.valor}"
    assert divisa.valor != VALOR_RAM_VIEJO, "La RAM vieja tomo prioridad indebida"
    return "Contingencia correcta: SQLite antiguo (900 CLP) gana sobre RAM antigua (800 CLP)"


def d3_ram_vigente_api_caida(ent: EntornoDivisa) -> str:
    esperada = EconomiaService._obtener_fecha_habil_esperada(date.today())
    servicio = ent.servicio()
    servicio.URL_BASE = URL_CAIDA
    ent.inyectar_ram(servicio, VALOR_RAM_VIEJO + 100, esperada)
    divisa = servicio.obtener_dolar_actual()
    assert divisa.valor == VALOR_RAM_VIEJO + 100, "La RAM vigente no se retorno"
    assert not ent.contador.llamadas, "L1 vigente no debio llamar a la API"
    return f"L1 corta con RAM vigente ({VALOR_RAM_VIEJO + 100} CLP) sin tocar la red"


def e_sqlite_vigente_api_caida(ent: EntornoDivisa) -> str:
    esperada = EconomiaService._obtener_fecha_habil_esperada(date.today())
    ent.sembrar(VALOR_RAM_VIEJO + 200, esperada)
    servicio = ent.servicio()
    servicio.URL_BASE = URL_CAIDA
    divisa = servicio.obtener_dolar_actual()
    assert divisa.valor == VALOR_RAM_VIEJO + 200, "L2 vigente no se retorno"
    assert not ent.contador.llamadas, "L2 vigente no debio llamar a la API"
    assert servicio._cache["usd"].valor == VALOR_RAM_VIEJO + 200, "L2 no subio a RAM"
    return f"L2 corto con cache vigente ({VALOR_RAM_VIEJO + 200} CLP) sin tocar la red"


def e2_sqlite_vigente_forzado_api_caida(ent: EntornoDivisa) -> str:
    esperada = EconomiaService._obtener_fecha_habil_esperada(date.today())
    ent.sembrar(VALOR_RAM_VIEJO + 200, esperada)
    servicio = ent.servicio()
    servicio.URL_BASE = URL_CAIDA
    with ent.contar_intentos():
        divisa = servicio.obtener_dolar_actual(forzar_refresco=True)
    assert ent.intentos == 3, \
        f"forzar debio reintentar 3 veces contra el link alterado: {ent.intentos}"
    assert divisa.valor == VALOR_RAM_VIEJO + 200, \
        "El degradado debio devolver el valor historico de SQLite"
    return "forzar_refresco con API caida: 3 intentos de transporte reales y degradacion al historico vigente"


def f_link_otra_api_respuesta_no_usable(ent: EntornoDivisa) -> str:
    ent.sembrar(VALOR_VIEJO, date(2026, 11, 9))
    servicio = ent.servicio()
    servicio.URL_BASE = URL_OTRA_API
    divisa = servicio.obtener_dolar_actual()
    assert divisa.valor == VALOR_VIEJO, f"Debio degradar al historico, devolvio {divisa.valor}"
    assert ent.valor_bd() == VALOR_VIEJO, "El degradado no debe reescribir la BD"

    ent2 = EntornoDivisa()
    try:
        servicio_vacio = ent2.servicio()
        servicio_vacio.URL_BASE = URL_OTRA_API
        try:
            servicio_vacio.obtener_dolar_actual()
            raise AssertionError("Sin historico debia propagar el error de respuesta no usable")
        except exceptions.ServicioExternoException as error:
            tipo = type(error).__name__
    finally:
        ent2.cerrar()
    return f"Respuesta 200 de otra API no usable ({tipo}): degradada al historico; sin historico se propaga"


def g_http_500_real_con_reintentos(ent: EntornoDivisa) -> str:
    ent.sembrar(VALOR_VIEJO, date(2026, 11, 9))
    servicio = ent.servicio()
    with servidor_500() as (url_local, hits):
        servicio.URL_BASE = url_local
        with ent.contar_intentos():
            divisa = servicio.obtener_dolar_actual()
    assert ent.intentos == 3, f"Reintentos del cliente ante 500: {ent.intentos}"
    assert hits["total"] == 3, f"Peticiones recibidas por el servidor: {hits['total']}"
    assert divisa.valor == VALOR_VIEJO, "Debio degradar al historico tras el 500"
    return (f"HTTP 500 real: 3 intentos verificados en el servidor y degradacion "
            f"al historico ({VALOR_VIEJO} CLP)")


ESCENARIOS = [
    ("A1", "API real arriba, sin cache", a1_api_real_sin_cache),
    ("A2", "Segundo llamado sin red", a2_segundo_llamado_sin_red_llamada),
    ("A3", "forzar_refresco con API real", a3_forzar_refresco_api_real),
    ("B", "Sin cache + API caida", b_sin_cache_y_api_caida),
    ("C", "SQLite antiguo + API caida", c_sqlite_antiguo_y_api_caida),
    ("D1", "RAM antigua + BD vacia + caida", d1_ram_antigua_bd_vacia_api_caida),
    ("D2", "RAM antigua + SQLite + caida", d2_ram_antigua_y_sqlite_antiguo_api_caida),
    ("D3", "RAM vigente + API caida", d3_ram_vigente_api_caida),
    ("E", "SQLite vigente + API caida", e_sqlite_vigente_api_caida),
    ("E2", "SQLite vigente + forzar + caida", e2_sqlite_vigente_forzado_api_caida),
    ("F", "Respuesta de otra API", f_link_otra_api_respuesta_no_usable),
    ("G", "HTTP 500 real con reintentos", g_http_500_real_con_reintentos),
]


def main() -> int:
    resultados = []
    for codigo, nombre, funcion in ESCENARIOS:
        ent = EntornoDivisa()
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
    print("REPORTE RESILIENCIA ECONOMIASERVICE (API REAL + LINKS ALTERADOS)")
    print("=" * 110)
    for codigo, nombre, estado, evidencia in resultados:
        print(f"{codigo:<4} | {estado:<6} | {nombre:<36} | {evidencia}")
    fallos = sum(1 for r in resultados if r[2] == "FAIL")
    print("-" * 110)
    print(f"Total: {len(resultados)} | PASS: {len(resultados) - fallos} | FAIL: {fallos}")
    return 1 if fallos else 0


if __name__ == "__main__":
    raise SystemExit(main())
