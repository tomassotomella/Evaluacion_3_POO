from __future__ import annotations

from datetime import date, datetime

from config.configuracion import Configuracion
from dao.feriado_dao import FeriadoDAO
from exceptions import exceptions
from models.feriado import Feriado
from services.cliente_resiliente import ClienteResiliente
from utilities.ValidadorEntradas import ValidadorEntradas
from exceptions.exceptions import (
    ServicioExternoException,
    FormatoRespuestaInvalidoException,
)


class FeriadoService:
    """Consulta feriados, mantiene su caché mensual y aplica reglas de calendario."""

    SERVICIO_NOMBRE = "BoostrHolidays"
    URL_BASE = Configuracion.URL_FERIADOS
    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 "
            "Safari/537.36"
        )
    }

    def __init__(
        self,
        feriado_dao: FeriadoDAO,
        cliente_http: ClienteResiliente | None = None,
    ):
        self.feriado_dao = feriado_dao
        self.cliente_http = cliente_http or ClienteResiliente()

    def _consultar_api_feriados(self) -> list[Feriado]:
        respuesta = self.cliente_http.ejecutar_get(
            self.URL_BASE,
            servicio=self.SERVICIO_NOMBRE,
            cabeceras=self.HEADERS,
        )
        try:
            respuesta_json = respuesta.json()
        except ValueError as error_json:
            raise FormatoRespuestaInvalidoException(
                servicio=self.SERVICIO_NOMBRE,
                motivo=f"La respuesta no es un JSON válido: {error_json}"
            ) from error_json

        if not isinstance(respuesta_json, dict):
            raise FormatoRespuestaInvalidoException(
                servicio=self.SERVICIO_NOMBRE,
                motivo="La respuesta no es un objeto JSON."
            )

        feriados_json = respuesta_json.get("data")
        if not isinstance(feriados_json, list):
            raise FormatoRespuestaInvalidoException(
                servicio=self.SERVICIO_NOMBRE,
                motivo="La respuesta no contiene una lista 'data'."
            )

        feriados: list[Feriado] = []
        for indice, feriado_json in enumerate(feriados_json):
            if not isinstance(feriado_json, dict):
                raise FormatoRespuestaInvalidoException(
                    servicio=self.SERVICIO_NOMBRE,
                    motivo=f"El feriado en posición {indice} no es un objeto."
                )
            try:
                feriados.append(
                    Feriado(
                        fecha=date.fromisoformat(feriado_json["date"]),
                        nombre=feriado_json.get("title", "Feriado Legal"),
                        tipo=feriado_json.get("type", "Legal"),
                        es_irrenunciable=bool(
                            feriado_json.get("inalienable", False)
                        ),
                    )
                )
            except (KeyError, TypeError, ValueError) as error_dato:
                raise FormatoRespuestaInvalidoException(
                    servicio=self.SERVICIO_NOMBRE,
                    motivo=f"Feriado inválido en posición {indice}: {error_dato}"
                ) from error_dato
        return feriados

    def sincronizar_feriados(self, forzar_refresco: bool = False) -> None:
        hoy = date.today()
        if (
            not forzar_refresco
            and self.feriado_dao.cache_corresponde_a(hoy.year, hoy.month)
        ):
            return

        try:
            feriados = self._consultar_api_feriados()
            self.feriado_dao.reemplazar_cache(
                feriados,
                hoy.year,
                hoy.month,
                datetime.now()
            )
        except ServicioExternoException:
            if self.feriado_dao.listar_todos():
                return
            raise

    @staticmethod
    def es_domingo(fecha: date | datetime) -> bool:
        fecha_calendario = ValidadorEntradas.validar_fecha_calendario(fecha)
        return fecha_calendario.weekday() == 6

    def _obtener_feriado(self, fecha_calendario: date) -> Feriado | None:
        self.sincronizar_feriados()
        for feriado in self.feriado_dao.listar_todos():
            if feriado.fecha == fecha_calendario:
                return feriado
        return None

    def es_feriado(self, fecha: date | datetime) -> Feriado | None:
        fecha_calendario = ValidadorEntradas.validar_fecha_calendario(fecha)
        return self._obtener_feriado(fecha_calendario)

    def es_dia_habil(self, fecha: date | datetime) -> bool:
        fecha_calendario = ValidadorEntradas.validar_fecha_calendario(fecha)
        if fecha_calendario.weekday() == 6:
            return False
        return self._obtener_feriado(fecha_calendario) is None

    def validar_urgencia_permitida(self, fecha: date | datetime) -> None:
        fecha_calendario = ValidadorEntradas.validar_fecha_calendario(fecha)
        es_domingo = fecha_calendario.weekday() == 6
        try:
            feriado = self._obtener_feriado(fecha_calendario)
        except ServicioExternoException:
            if es_domingo:
                return
            raise
        if not es_domingo and feriado is None:
            raise exceptions.ReglaNegocioError(
                "Las atenciones de urgencia solo están autorizadas "
                "los días domingo o feriados."
            )
        return None

    def obtener_resumen_calendario(
        self,
        fecha: date | datetime | None = None
    ) -> str:
        fecha_calendario = ValidadorEntradas.validar_fecha_calendario(
            fecha or date.today()
        )
        es_domingo = fecha_calendario.weekday() == 6
        feriado = self._obtener_feriado(fecha_calendario)
        if es_domingo and feriado is not None:
            return f"Domingo y feriado ({feriado.nombre})"
        if es_domingo:
            return "Domingo"
        if feriado is not None:
            return f"Feriado ({feriado.nombre})"
        return "Día hábil"
