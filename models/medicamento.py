
from __future__ import annotations
from typing import TYPE_CHECKING
from utilities.ValidadorEntradas import ValidadorEntradas
from exceptions import exceptions

if TYPE_CHECKING:
    from models.divisa import Divisa


class Medicamento:
    stock_critico = 10
    def __init__(
        self,
        nombre_comercial: str,
        precio: int,
        stock: int,
        id_medicamento: int | None = None
    ):
        self._id_medicamento = ValidadorEntradas.validar_id(
            id_medicamento,
            'medicamento'
        )
        # Inicialización de Atributos
        self._nombre_comercial = ''
        self._precio = 0
        self._stock = 0
        self._precio_usd: float | None = None

        #Asignación de Setters
        self.nombre_comercial = nombre_comercial
        self.precio = precio
        self.stock = stock 

        #Encapsulamiento de atributos
    @property
    def id_medicamento(self) -> int | None:
        return self._id_medicamento

    def asignar_id(self, id_medicamento: int) -> None:
        if self._id_medicamento is not None:
            raise exceptions.ReglaNegocioError(
                'El medicamento ya tiene un ID asignado y no puede ser reasignado.'
            )
        self._id_medicamento = ValidadorEntradas.validar_id(
            id_medicamento,
            'medicamento'
        )
    
    @property
    def nombre_comercial(self) -> str:
        return self._nombre_comercial
    @nombre_comercial.setter
    def nombre_comercial(self, valor: str) -> None:
        nombre_limpio = ValidadorEntradas.validar_longitud(
            valor,
            max=4000,
            nombre='Nombre Comercial'
        )
        self._nombre_comercial = nombre_limpio

    @property
    def precio(self) -> int:
        return self._precio
    @precio.setter
    def precio(self, precio: int) -> None:
        precio_valido = ValidadorEntradas.validar_entero(
            precio,
            'precio',
            minimo = 1,
            maximo = 100000 #definir politica de precio máximo
        )
        self._precio = precio_valido

    @property
    def stock(self) -> int:
        return self._stock
    @stock.setter
    def stock(self, valor: int) -> None:
        stock_valido = ValidadorEntradas.validar_entero(
            valor,
            'stock',
            minimo = 0,
            maximo = 1000 #Definir politica de stock
        )
        self._stock = stock_valido

    @property
    def precio_usd(self) -> float | None:
        """Retorna el arancel equivalente en USD calculado en memoria RAM."""
        return self._precio_usd

    def calcular_precio_usd(self, divisa: Divisa) -> float:
        """Calcula y asigna el precio en USD usando la divisa entregada."""
        self._precio_usd = divisa.convertir_desde_pesos(self.precio)
        return self._precio_usd

    #metodos
    def hay_stock_suficiente(self, cantidad: int) -> bool:
        cantidad_valida = ValidadorEntradas.validar_entero(cantidad, 'Cantidad', minimo = 1)
        return self.stock >= cantidad_valida

    def descontar_stock(self, cantidad: int) -> None:
        if not self.hay_stock_suficiente(cantidad):
            raise exceptions.SinStockException(
                self.nombre_comercial,
                cantidad,
                self.stock
            )
        self.stock -= int(cantidad)

    def reponer_stock(self, cantidad: int) -> None:
        cantidad_valida = ValidadorEntradas.validar_entero(cantidad, 'Cantidad', minimo = 1)
        self.stock += cantidad_valida
        
    def es_stock_critico(self) -> bool:
        return self.stock <= Medicamento.stock_critico
    
    def __str__(self) -> str:
        return self.nombre_comercial