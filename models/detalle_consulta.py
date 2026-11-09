
from __future__ import annotations
from typing import TYPE_CHECKING
from utilities.ValidadorEntradas import ValidadorEntradas
from exceptions import exceptions

if TYPE_CHECKING:
    from veterinario import Veterinario
    from medicamento import Medicamento
    from receta_medica import RecetaMedica
    from consulta import Consulta

class DetalleConsulta:

    def __init__(
        self,
        consulta: Consulta,
        veterinario: Veterinario,
        diagnostico: str | None = None,
        tratamiento: str | None = None,
        observaciones: str | None = None,
        id_detalle: int | None = None

    ):
        self._id_detalle = ValidadorEntradas.validar_id(
            id_detalle,
            "detalle de consulta"
        )
        #inicializamos atributos
        self._consulta = None
        self._veterinario = None
        self._diagnostico = None
        self._tratamiento = None
        self._observaciones = None
        self._recetas = []
        #asignamos los setters
        self.consulta = consulta
        self.veterinario = veterinario
        self.diagnostico = diagnostico
        self.tratamiento = tratamiento
        self.observaciones = observaciones

    #ahora van los getters y setters
    #ordenamos por prioridad, importan más consulta y veterinario

    @property
    def id_detalle(self) -> int | None:
        return self._id_detalle

    def asignar_id(self, id_detalle: int) -> None:
        if self._id_detalle is not None:
            raise exceptions.ReglaNegocioError('El detalle de consulta ya tiene un ID asignado y no puede ser reasignado.')
        self._id_detalle = ValidadorEntradas.validar_id(
            id_detalle,
            "detalle de consulta"
        )

    @property
    def consulta(self) -> Consulta | None:
        return self._consulta
    @consulta.setter
    def consulta(self, valor: None | Consulta):
        if valor is None:
            self._consulta = None
            return
        from consulta import Consulta
        consulta_valida = ValidadorEntradas.validar_instancia(valor, Consulta, 'Consulta')
        self._consulta = consulta_valida

    @property
    def veterinario(self) -> Veterinario:
        return self._veterinario
    @veterinario.setter
    def veterinario(self, valor: Veterinario):
        from veterinario import Veterinario
        veterinario_valido = ValidadorEntradas.validar_instancia(valor, Veterinario, 'Veterinario')
        self._veterinario = veterinario_valido

    @property
    def diagnostico(self) -> str | None:
        return self._diagnostico
    @diagnostico.setter
    def diagnostico(self, valor: str | None):
        if valor is None:
            self._diagnostico = None
            return
        diagnostico_valido = ValidadorEntradas.validar_longitud(valor, 100, 'Diagnostico')
        self._diagnostico = diagnostico_valido

    @property
    def tratamiento(self) -> str | None:
        return self._tratamiento
    @tratamiento.setter
    def tratamiento(self, valor: str | None):
        if valor is None:
            self._tratamiento = None
            return
        tratamiento_valido = ValidadorEntradas.validar_longitud(valor, 1000, 'Tratamiento')
        self._tratamiento = tratamiento_valido

    @property
    def observaciones(self) -> str | None:
        return self._observaciones
    @observaciones.setter
    def observaciones(self, valor: str | None):
        if valor is None:
            self._observaciones = None
            return
        observacion_valida = ValidadorEntradas.validar_longitud(valor, 1000, 'Observaciones')
        self._observaciones = observacion_valida

    @property
    def recetas(self) -> list[RecetaMedica]:
        return self._recetas.copy()
    
    def _verificar_modificable(self) -> None:
        from consulta import EstadosConsulta

        estados_permitidos = {
            EstadosConsulta.EN_ATENCION,
            EstadosConsulta.EN_ESPERA_EXAMENES,
        }

        if self.consulta is None:
            raise exceptions.ReglaNegocioError(
                "El detalle debe estar asociado a una consulta."
            )

        if self.consulta.estado not in estados_permitidos:
            raise exceptions.ReglaNegocioError(
                "No se puede modificar el detalle cuando la consulta "
                f"está en estado '{self.consulta.estado.value}'."
            )

    def actualizar_diagnostico(self, nuevo_diagnostico: str) -> None:
        self._verificar_modificable()
        self.diagnostico = nuevo_diagnostico

    def actualizar_tratamiento(self, nuevo_tratamiento: str) -> None:
        self._verificar_modificable()
        self.tratamiento = nuevo_tratamiento

    def actualizar_observaciones(self, nuevas_observaciones: str) -> None:
        self._verificar_modificable()
        self.observaciones = nuevas_observaciones

    def esta_completo(self) -> bool:
        return all((
            self.diagnostico is not None,
            self.tratamiento is not None,
            self.observaciones is not None,
        ))

    def prescribir_medicamento(self, cantidad: int, instrucciones: str, medicamento: Medicamento) -> RecetaMedica:
        self._verificar_modificable()
        
        from receta_medica import RecetaMedica
        nueva_receta = RecetaMedica(
            cantidad = cantidad,
            instrucciones = instrucciones,
            medicamento = medicamento,
            detalle = self
        )
        self._recetas.append(nueva_receta)
        return nueva_receta

    '''def agregar_receta(self, receta: RecetaMedica) -> None:
        from receta_medica import RecetaMedica
        receta_valida = ValidadorEntradas.validar_instancia(receta, RecetaMedica, 'Receta Medica')
        self._recetas.append(receta_valida)'''

    def remover_receta(self, id_receta: int) -> None:
        self._verificar_modificable()
        id_valido = ValidadorEntradas.validar_id(id_receta, 'Receta Medica')
        receta_encontrada = next((receta for receta in self._recetas if receta.id_receta == id_valido), None)
        if not receta_encontrada:
            raise exceptions.EntidadNoEncontradaException('Receta Medica', id_valido)
        self._recetas.remove(receta_encontrada)

    def calcular_costo_total_tratamiento(self) -> int:
        return sum(receta.calcular_subtotal() for receta in self._recetas)
