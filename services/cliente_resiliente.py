from __future__ import annotations

import time
import requests

from exceptions.exceptions import (
    ConexionTimeoutException,
    ErrorRespuestaHttpException,
    ServicioExternoException,
)


class ClienteHTTPResiliente:
    """Ejecuta peticiones GET con timeout y reintentos de fallos transitorios."""

    def __init__(
        self,
        timeout: int = 10,
        max_reintentos: int = 3,
    ):
        if timeout <= 0:
            raise ValueError("El timeout debe ser positivo.")
        if max_reintentos < 0:
            raise ValueError("Los reintentos no pueden ser negativos.")
        self.timeout = timeout
        self.max_reintentos = max_reintentos

    def ejecutar_get(
        self,
        url: str,
        parametros: dict[str, object] | None = None,
        cabeceras: dict[str, str] | None = None,
        *,
        servicio: str = "Servicio externo",
    ) -> requests.Response:
        """Obtiene una respuesta o traduce el fallo a una excepción del proyecto."""
        if self.max_reintentos == 0:
            raise ValueError("Debe permitirse al menos un intento.")

        for intento in range(1, self.max_reintentos + 1):
            try:
                respuesta = requests.get(
                    url,
                    params=parametros,
                    headers=cabeceras,
                    timeout=self.timeout,
                )
            except requests.exceptions.Timeout as error_timeout:
                if intento == self.max_reintentos:
                    raise ConexionTimeoutException(
                        servicio=servicio,
                        timeout_segundos=self.timeout,
                    ) from error_timeout
            except requests.exceptions.ConnectionError as error_red:
                if intento == self.max_reintentos:
                    raise ServicioExternoException(
                        servicio=servicio,
                        mensaje=f"Fallo en la conexión de red: {error_red}",
                    ) from error_red
            except requests.exceptions.RequestException as error_red:
                raise ServicioExternoException(
                    servicio=servicio,
                    mensaje=f"Fallo en la petición HTTP: {error_red}",
                ) from error_red
            else:
                es_fallo_transitorio = (
                    respuesta.status_code == 429
                    or 500 <= respuesta.status_code <= 599
                )
                if not es_fallo_transitorio or intento == self.max_reintentos:
                    if respuesta.status_code != 200:
                        raise ErrorRespuestaHttpException(
                            servicio=servicio,
                            status_code=respuesta.status_code,
                            detalle=respuesta.text[:200],
                        )
                    return respuesta

            if intento < self.max_reintentos:
                time.sleep(intento)

        raise ServicioExternoException(
            servicio=servicio,
            mensaje="La petición no produjo una respuesta.",
        )


ClienteResiliente = ClienteHTTPResiliente
