from __future__ import annotations

from datetime import datetime

from exceptions import exceptions
from utilities.ValidadorEntradas import ValidadorEntradas


class Clima:
    def __init__(
        self,
        localidad: str,
        region: str,
        pais: str,
        temperatura_c: float,
        sensacion_termica_c: float,
        condicion: str,
        humedad_pct: int,
        precipitacion_mm: float,
        observado_en: datetime,
    ):
        self._localidad = ""
        self._region = ""
        self._pais = ""
        self._temperatura_c = 0.0
        self._sensacion_termica_c = 0.0
        self._condicion = ""
        self._humedad_pct = 0
        self._precipitacion_mm = 0.0
        self._observado_en = observado_en

        self.localidad = localidad
        self.region = region
        self.pais = pais
        self.temperatura_c = temperatura_c
        self.sensacion_termica_c = sensacion_termica_c
        self.condicion = condicion
        self.humedad_pct = humedad_pct
        self.precipitacion_mm = precipitacion_mm
        self.observado_en = observado_en

    @property
    def localidad(self) -> str:
        return self._localidad

    @localidad.setter
    def localidad(self, valor: str):
        self._localidad = ValidadorEntradas.validar_no_vacio(valor, "Localidad")

    @property
    def region(self) -> str:
        return self._region

    @region.setter
    def region(self, valor: str):
        self._region = ValidadorEntradas.validar_no_vacio(valor, "Región")

    @property
    def pais(self) -> str:
        return self._pais

    @pais.setter
    def pais(self, valor: str):
        self._pais = ValidadorEntradas.validar_no_vacio(valor, "País")

    @property
    def temperatura_c(self) -> float:
        return self._temperatura_c

    @temperatura_c.setter
    def temperatura_c(self, valor: float):
        self._temperatura_c = ValidadorEntradas.validar_decimal(
            valor,
            "Temperatura",
        )

    @property
    def sensacion_termica_c(self) -> float:
        return self._sensacion_termica_c

    @sensacion_termica_c.setter
    def sensacion_termica_c(self, valor: float):
        self._sensacion_termica_c = ValidadorEntradas.validar_decimal(
            valor,
            "Sensación térmica",
        )

    @property
    def condicion(self) -> str:
        return self._condicion

    @condicion.setter
    def condicion(self, valor: str):
        self._condicion = ValidadorEntradas.validar_no_vacio(valor, "Condición")

    @property
    def humedad_pct(self) -> int:
        return self._humedad_pct

    @humedad_pct.setter
    def humedad_pct(self, valor: int):
        self._humedad_pct = ValidadorEntradas.validar_entero(
            valor,
            "Humedad",
            minimo=0,
            maximo=100,
        )

    @property
    def precipitacion_mm(self) -> float:
        return self._precipitacion_mm

    @precipitacion_mm.setter
    def precipitacion_mm(self, valor: float):
        self._precipitacion_mm = ValidadorEntradas.validar_decimal(
            valor,
            "Precipitación",
            minimo=0,
        )

    @property
    def observado_en(self) -> datetime:
        return self._observado_en

    @observado_en.setter
    def observado_en(self, valor: datetime):
        if not isinstance(valor, datetime):
            raise exceptions.EntradaInvalidaException(
                "Fecha de observación",
                "debe ser un datetime válido",
            )
        self._observado_en = valor
