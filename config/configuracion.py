from __future__ import annotations

import os

from dotenv import load_dotenv
from exceptions.exceptions import ConfiguracionException
from utilities.ValidadorEntradas import ValidadorEntradas


class Configuracion:
    """Configuración común de servicios externos y de la sucursal."""

    ENV_PATH = ".env"

    URL_BASE_CLIMA: str
    URL_BASE_DOLAR: str
    URL_FERIADOS: str
    TIMEOUT_SEGUNDOS = 10

    @classmethod
    def cargar(cls) -> None:
        """Carga los valores configurables sin almacenar secretos en el código."""
        load_dotenv(cls.ENV_PATH)
        cls.URL_BASE_CLIMA = cls._obtener_requerida("WEATHER_BASE_URL")
        cls.URL_BASE_DOLAR = cls._obtener_requerida("DOLAR_BASE_URL")
        cls.URL_FERIADOS = cls._obtener_requerida("FERIADOS_URL")
        timeout = os.getenv("TIMEOUT_SEGUNDOS")
        if timeout and timeout.strip():
            cls.TIMEOUT_SEGUNDOS = ValidadorEntradas.validar_entero(
                timeout,
                nombre="TIMEOUT_SEGUNDOS",
                minimo=1,
            )
        cls.CIUDAD_DEFECTO_CLINICA = os.getenv("CIUDAD_DEFECTO_CLINICA")

    @staticmethod
    def _obtener_requerida(nombre: str) -> str:
        valor = os.getenv(nombre)
        if valor is None or not valor.strip():
            raise ConfiguracionException(
                f"Falta configurar {nombre} en el archivo .env."
            )
        return valor.strip()


Configuracion.cargar()
