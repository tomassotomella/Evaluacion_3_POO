from __future__ import annotations

import math
from datetime import datetime
from pathlib import Path
from typing import Any, cast

from dotenv import dotenv_values

from config.configuracion import Configuracion
from exceptions.exceptions import (
    ConfiguracionException,
    ConexionTimeoutException,
    ErrorRespuestaHttpException,
    ErrorWeatherAPIException,
    FormatoRespuestaInvalidoException,
    ServicioExternoException,
)
from models.clima import Clima
from services.cliente_resiliente import ClienteHTTPResiliente
from utilities.ValidadorEntradas import ValidadorEntradas


class ServicioClima:
    SERVICIO_NOMBRE = "WeatherAPI"
    URL_ACTUAL = f"{Configuracion.URL_BASE_CLIMA}/current.json"
    ENV_PATH = Path(__file__).resolve().parents[1] / ".env"

    def __init__(
        self,
        cliente_http: ClienteHTTPResiliente,
    ) -> None:
        self.cliente_http = cliente_http
        self._api_key = dotenv_values(self.ENV_PATH).get("WEATHER_API_KEY")

    def obtener_clima(
        self,
        comuna: str = Configuracion.CIUDAD_DEFECTO_CLINICA,
    ) -> Clima:
        api_key = self._obtener_api_key()
        comuna_limpia = ValidadorEntradas.validar_longitud(
            comuna,
            max=120,
            nombre="Comuna",
        )

        error_cliente: ServicioExternoException | None = None
        respuesta: Any | None = None
        try:
            respuesta = self.cliente_http.ejecutar_get(
                self.URL_ACTUAL,
                parametros={
                    "key": api_key,
                    "q": comuna_limpia,
                    "lang": "es",
                },
                servicio=self.SERVICIO_NOMBRE,
            )
        except ConexionTimeoutException as error_timeout:
            error_cliente = ConexionTimeoutException(
                self.SERVICIO_NOMBRE,
                error_timeout.timeout_segundos,
            )
        except ErrorRespuestaHttpException as error_http:
            error_cliente = ErrorWeatherAPIException(
                self._mensaje_http(error_http.status_code),
                status_code=error_http.status_code,
            )
        except ServicioExternoException:
            error_cliente = ErrorWeatherAPIException(
                "No fue posible establecer conexión con WeatherAPI.",
            )

        if error_cliente is not None:
            raise error_cliente
        if respuesta is None:
            raise ServicioExternoException(
                self.SERVICIO_NOMBRE,
                "La petición no produjo una respuesta.",
            )

        try:
            payload: object = respuesta.json()
        except ValueError:
            raise FormatoRespuestaInvalidoException(
                servicio=self.SERVICIO_NOMBRE,
                motivo="La respuesta no contiene JSON válido.",
            ) from None

        if not isinstance(payload, dict):
            raise FormatoRespuestaInvalidoException(
                servicio=self.SERVICIO_NOMBRE,
                motivo="La respuesta no es un objeto JSON.",
            )
        payload_dict = cast(dict[str, Any], payload)

        if "error" in payload_dict:
            error_raw = payload_dict["error"]
            if not isinstance(error_raw, dict):
                raise FormatoRespuestaInvalidoException(
                    servicio=self.SERVICIO_NOMBRE,
                    motivo="El error devuelto por WeatherAPI tiene un formato inválido.",
                )
            error_api = cast(dict[str, object], error_raw)
            codigo = error_api.get("code")
            if isinstance(codigo, bool) or not isinstance(codigo, int):
                raise FormatoRespuestaInvalidoException(
                    servicio=self.SERVICIO_NOMBRE,
                    motivo="El error de WeatherAPI no contiene un código válido.",
                )
            raise ErrorWeatherAPIException(
                self._mensaje_codigo_api(codigo),
                codigo_api=codigo,
            )

        return self._mapear_clima(payload_dict)

    def _obtener_api_key(self) -> str:
        if not isinstance(self._api_key, str) or not self._api_key.strip():
            raise ConfiguracionException(
                "Falta configurar WEATHER_API_KEY en el archivo .env."
            )
        return self._api_key.strip()

    def _mapear_clima(self, payload: dict[str, Any]) -> Clima:
        try:
            ubicacion_raw = payload["location"]
            actual_raw = payload["current"]
            if not isinstance(ubicacion_raw, dict) or not isinstance(actual_raw, dict):
                raise TypeError

            ubicacion = cast(dict[str, object], ubicacion_raw)
            actual = cast(dict[str, object], actual_raw)
            condicion_raw = actual["condition"]
            if not isinstance(condicion_raw, dict):
                raise TypeError
            condicion_json = cast(dict[str, object], condicion_raw)

            localidad = self._texto_requerido(ubicacion["name"])
            region = self._texto_requerido(ubicacion["region"])
            pais = self._texto_requerido(ubicacion["country"])
            condicion = self._texto_requerido(condicion_json["text"])
            temperatura = self._numero_requerido(actual["temp_c"])
            sensacion = self._numero_requerido(actual["feelslike_c"])
            humedad = actual["humidity"]
            if isinstance(humedad, bool) or not isinstance(humedad, int):
                raise TypeError
            precipitacion = self._numero_requerido(actual["precip_mm"])
            observado_en = datetime.fromisoformat(
                self._texto_requerido(actual["last_updated"])
            )
        except (KeyError, TypeError, ValueError, OverflowError):
            raise FormatoRespuestaInvalidoException(
                servicio=self.SERVICIO_NOMBRE,
                motivo="Faltan datos climáticos obligatorios o tienen un formato inválido.",
            ) from None

        if (
            not 0 <= humedad <= 100
            or not math.isfinite(temperatura)
            or not math.isfinite(sensacion)
            or not math.isfinite(precipitacion)
            or precipitacion < 0
        ):
            raise FormatoRespuestaInvalidoException(
                servicio=self.SERVICIO_NOMBRE,
                motivo="Los valores de humedad o precipitación están fuera de rango.",
            )

        return Clima(
            localidad=localidad,
            region=region,
            pais=pais,
            temperatura_c=temperatura,
            sensacion_termica_c=sensacion,
            condicion=condicion,
            humedad_pct=humedad,
            precipitacion_mm=precipitacion,
            observado_en=observado_en,
        )

    @staticmethod
    def _texto_requerido(valor: object) -> str:
        if not isinstance(valor, str) or not valor.strip():
            raise TypeError
        return valor.strip()

    @staticmethod
    def _numero_requerido(valor: object) -> float:
        if isinstance(valor, bool) or not isinstance(valor, (int, float)):
            raise TypeError
        return float(valor)

    @staticmethod
    def _mensaje_http(status_code: int) -> str:
        mensajes = {
            401: "WeatherAPI rechazó las credenciales configuradas.",
            403: "WeatherAPI denegó el acceso a la consulta.",
            404: "WeatherAPI no encontró la localidad solicitada.",
        }
        return mensajes.get(
            status_code,
            f"WeatherAPI respondió con el código HTTP {status_code}.",
        )

    @staticmethod
    def _mensaje_codigo_api(codigo: int) -> str:
        mensajes = {
            1002: "WeatherAPI no recibió una clave de acceso válida.",
            1003: "WeatherAPI rechazó la clave de acceso.",
            1006: "WeatherAPI no encontró la localidad solicitada.",
            2006: "La clave de WeatherAPI no es válida.",
            2007: "La clave de WeatherAPI excedió su cuota.",
            2008: "La clave de WeatherAPI está deshabilitada.",
            2009: "La clave de WeatherAPI no tiene acceso a este recurso.",
        }
        return mensajes.get(codigo, f"WeatherAPI devolvió el error {codigo}.")
