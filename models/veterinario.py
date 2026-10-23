'''        class Veterinario {
            -especialidad: Especialidad
            -historialAtenciones: List~DetalleConsulta~
            +actualizarEspecialidad(nuevaespecialidad: Especialidad): void
            +obtenerHistorialAtenciones(): List~DetalleConsulta~'''
from __future__ import annotations
from typing import TYPE_CHECKING
from persona import Persona
from especialidad import Especialidad
from exceptions import exceptions
from utilities.ValidadorEntradas import ValidadorEntradas

if TYPE_CHECKING:
    from detalle_consulta import DetalleConsulta

class Veterinario(Persona):
    def __init__(
        self,
        rut: str,
        nombre_completo: str,
        telefono: str,
        especialidad: Especialidad,
        id_veterinario: int | None = None,
    ):
        super().__init__(rut, nombre_completo, telefono, id_veterinario)
        #Inicializar atributos
        self._especialidad = None
        self._historial_atenciones = []
        #
        self.especialidad = especialidad

    @property
    def id_veterinario(self) -> int:
        return self._id_persona

    @property
    def especialidad(self) -> Especialidad:
        return self._especialidad
    @especialidad.setter
    def especialidad(self, valor: Especialidad) -> None:
        especialidad_valida = ValidadorEntradas.validar_instancia(valor, Especialidad, 'Especialidad')
        self._especialidad = especialidad_valida

    @property
    def historial_atenciones(self) -> list[DetalleConsulta]:
        return self._historial_atenciones.copy()
    
    def actualizar_especialidad(self, nueva_especialidad: Especialidad) -> None:
        self.especialidad = nueva_especialidad

    def registrar_atencion(self, detalle: DetalleConsulta) -> None:
        from detalle_consulta import DetalleConsulta

        detalle_valido = ValidadorEntradas.validar_instancia(detalle, DetalleConsulta, 'Detalle Consulta')
        if detalle_valido.veterinario is not self:
            raise exceptions.RelacionInvalidaException('Veterinario', 'Detalle Consulta', 'el detalle no pertenece al veterinario')
        if any(atencion.id_detalle == detalle_valido.id_detalle for atencion in self._historial_atenciones):
            raise exceptions.EntidadExistenteException('DetalleConsulta', detalle_valido.id_detalle)
        self._historial_atenciones.append(detalle_valido)

    '''def obtener_historial(self) -> list[DetalleConsulta]:
        return self._historial_atenciones.copy()'''#Reemplazado por getter (@property) 
