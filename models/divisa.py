from utilities import ValidadorEntradas
from exceptions import exceptions
from datetime import datetime

class Divisa:
    def __init__(self, codigo: str, nombre: str, valor: float, fecha_actualizacion: datetime):
        self.codigo = codigo.strip().lower()
        self.nombre = nombre.strip()
        self.fecha_actualizacion = fecha_actualizacion

        self._valor = 0.0

        self.valor = valor

    @property
    def valor(self) -> float:
        return self._valor
    @valor.setter
    def valor(self, nuevo_valor: float):
        valor_valido = ValidadorEntradas.validar_decimal(nuevo_valor, 'Valor', minimo= 0)
        self._valor = valor_valido

    def convertir_a_pesos(self, monto_divisa: float) -> int:
        if monto_divisa < 0:
            raise exceptions.ReglaNegocioError('No es posible convertir montos negativos')
        return round(monto_divisa * self.valor)

    def convertir_desde_pesos(self, monto_pesos: float) -> float:
        if monto_pesos < 0:
            raise exceptions.ReglaNegocioError('No es posible convertir montos negativos')
        return round(monto_pesos / self.valor, 2)