from datetime import date

from exceptions import exceptions
from utilities.ValidadorEntradas import ValidadorEntradas


class Feriado:
    def __init__(
        self,
        fecha: date,
        nombre: str,
        tipo: str,
        es_irrenunciable: bool,
    ):
        self._fecha = None
        self._nombre = ""
        self._tipo = ""
        self._es_irrenunciable = False

        self.fecha = fecha
        self.nombre = nombre
        self.tipo = tipo
        self.es_irrenunciable = es_irrenunciable

    @property
    def fecha(self) -> date:
        return self._fecha

    @fecha.setter
    def fecha(self, valor: date) -> None:
        self._fecha = ValidadorEntradas.validar_fecha_calendario(
            valor,
            "Fecha del feriado"
        )

    @property
    def nombre(self) -> str:
        return self._nombre

    @nombre.setter
    def nombre(self, valor: str) -> None:
        self._nombre = ValidadorEntradas.validar_no_vacio(
            valor,
            "Nombre del feriado"
        )

    @property
    def tipo(self) -> str:
        return self._tipo

    @tipo.setter
    def tipo(self, valor: str) -> None:
        self._tipo = ValidadorEntradas.validar_no_vacio(
            valor,
            "Tipo de feriado"
        )

    @property
    def es_irrenunciable(self) -> bool:
        return self._es_irrenunciable

    @es_irrenunciable.setter
    def es_irrenunciable(self, valor: bool) -> None:
        self._es_irrenunciable = ValidadorEntradas.validar_instancia(
            valor,
            bool,
            "Feriado irrenunciable"
        )
