from __future__ import annotations
from typing import TYPE_CHECKING
from exceptions import exceptions
from utilities.ValidadorEntradas import ValidadorEntradas
from medicamento import Medicamento

if TYPE_CHECKING:
    from detalle_consulta import DetalleConsulta

class RecetaMedica:
    def __init__(self,
            cantidad: int,
            instrucciones: str,
            medicamento: Medicamento,
            detalle: DetalleConsulta,
            id_receta: int | None = None
            ):
        self._id_receta = ValidadorEntradas.validar_id(id_receta, "receta")

        self._medicamento = None
        self._detalle = None
        self._cantidad = 0
        self._instrucciones = ''

        self.medicamento = medicamento
        self.detalle = detalle
        self.cantidad = cantidad
        self.instrucciones = instrucciones

    @property
    def id_receta(self) -> int | None:
        return self._id_receta

    def asignar_id(self, id_receta: int) -> None:
        if self._id_receta is not None:
            raise exceptions.ReglaNegocioError('La receta ya tiene un ID asignado y no puede ser reasignado.')
        self._id_receta = ValidadorEntradas.validar_id(id_receta, "receta")

    @property
    def cantidad(self) -> int:
        return self._cantidad
    @cantidad.setter
    def cantidad(self, valor: int):
        self._cantidad = ValidadorEntradas.validar_entero(valor, 'Cantidad', minimo = 1)

    @property
    def instrucciones(self) -> str:
        return self._instrucciones
    @instrucciones.setter
    def instrucciones(self, texto: str):
        instruccion = ValidadorEntradas.validar_longitud(
            texto,
            max=4000,
            nombre='Instrucciones'
        )
        self._instrucciones = instruccion

    @property
    def medicamento(self) -> Medicamento:
        return self._medicamento
    @medicamento.setter
    def medicamento(self, valor: Medicamento):
        medicamento_valido = ValidadorEntradas.validar_instancia(valor, Medicamento, 'Medicamento')
        self._medicamento = medicamento_valido

    @property
    def detalle(self) -> DetalleConsulta:
        return self._detalle
    @detalle.setter
    def detalle(self, valor: DetalleConsulta):
        from detalle_consulta import DetalleConsulta

        detalle_valido = ValidadorEntradas.validar_instancia(valor, DetalleConsulta, 'Detalle de Consulta')
        self._detalle = detalle_valido

    def calcular_subtotal(self) -> int:
        return self.cantidad * self.medicamento.precio

    def calcular_subtotal_usd(self) -> float | None:
        """Calcula el subtotal en USD utilizando el precio_usd calculado del medicamento."""
        if self.medicamento and self.medicamento.precio_usd is not None:
            return round(self.cantidad * self.medicamento.precio_usd, 2)
        return None

        