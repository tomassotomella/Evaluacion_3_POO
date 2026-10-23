'''class Especialidad {
            -idEspecialidad: int
            -nombreEspecialidad: String
            +Especialidad(idEspecialidad: int | None, nombreEspecialidad: String)
            +actualizarNombre(nuevoNombre: String): void
        }'''
from exceptions import exceptions
from utilities.ValidadorEntradas import ValidadorEntradas
class Especialidad:
    def __init__(
        self,
        nombre_especialidad: str,
        descripcion: str,
        id_especialidad: int | None = None
    ):
        self._id_especialidad = ValidadorEntradas.validar_id(
            id_especialidad,
            'especialidad'
        )
        #Inicialización de Atributos
        self._nombre_especialidad = ''
        self._descripcion = ''
        #Asignación de Setters
        self.nombre_especialidad = nombre_especialidad
        self._descripcion = descripcion

    @property
    def id_especialidad(self) -> int | None:
        return self._id_especialidad

    def asignar_id(self, id_especialidad: int) -> None:
        if self._id_especialidad is not None:
            raise exceptions.ReglaNegocioError(
                'La especialidad ya tiene un ID asignado y no puede ser reasignada.'
            )
        self._id_especialidad = ValidadorEntradas.validar_id(
            id_especialidad,
            'especialidad'
        )
    
    @property
    def nombre_especialidad(self) -> str:
        return self._nombre_especialidad

    @nombre_especialidad.setter
    def nombre_especialidad(self, valor: str) -> None:
        nombre_valido = ValidadorEntradas.validar_nombre_alfabetico(
            valor,
            nombre_campo='Nombre de la especialidad'
        )
        self._nombre_especialidad = nombre_valido.title()

    @property
    def descripcion(self) -> str:
        return self._descripcion

    @descripcion.setter
    def descripcion(self, texto: str) -> None:
        descripcion_valida = ValidadorEntradas.validar_longitud(texto, max = 100, nombre = 'descripción')
        self._descripcion = descripcion_valida

    def actualizar_nombre(self, nuevo_nombre: str) -> None:
        self.nombre_especialidad = nuevo_nombre

    def actualizar_descripcion(self, nueva_descripcion: str) -> None:
        self.descripcion = nueva_descripcion

    def __str__(self) -> str:
        return self.nombre_especialidad