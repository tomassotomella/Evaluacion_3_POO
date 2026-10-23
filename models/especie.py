'''class Especie {
            -idEspecie: int
            -nombreEspecie: String
            +Especie(idEspecie: int | None, nombreEspecie: String)
            +actualizarNombre(nuevonombre: String): void
        }'''
from utilities.ValidadorEntradas import ValidadorEntradas
from exceptions import exceptions
class Especie:
    def __init__(
        self,
        esperanza_vida_max: int,
        nombre_especie: str,
        id_especie: int | None = None
    ):
        self._id_especie = ValidadorEntradas.validar_id(id_especie, 'especie')
        
        self._nombre_especie = ''
        self._esperanza_vida_maxima = 0

        self.nombre_especie = nombre_especie
        self.esperanza_vida_max = esperanza_vida_max


    @property
    def id_especie(self) -> int | None:
        return self._id_especie

    def asignar_id(self, id_especie: int) -> None:
        if self._id_especie is not None:
            raise exceptions.ReglaNegocioError(
                'La especie ya tiene un ID asignado y no puede ser reasignado.'
            )
        self._id_especie = ValidadorEntradas.validar_id(id_especie, 'especie')

    @property
    def nombre_especie(self) -> str:
        return self._nombre_especie
    @nombre_especie.setter
    def nombre_especie(self, nombre: str) -> None:
        nombre_valido = ValidadorEntradas.validar_nombre_alfabetico(
                    nombre,
                    nombre_campo='Nombre de la Especie'
                )
        self._nombre_especie = nombre_valido

    @property
    def esperanza_vida_max(self) -> int:
        return self._esperanza_vida_maxima
    @esperanza_vida_max.setter
    def esperanza_vida_max(self, anios: int) -> None:
        esperanza = ValidadorEntradas.validar_entero(anios,'Esperanza de Vida Máxima', minimo = 1)
        if esperanza > 200:
            raise exceptions.ReglaNegocioError('La esperanza de vida máxima no puede superar los 200 años.')
        self._esperanza_vida_maxima = esperanza

    def actualizar_nombre(self, nuevo_nombre: str) -> None:
        self.nombre_especie = nuevo_nombre