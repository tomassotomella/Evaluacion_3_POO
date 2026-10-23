from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING
from utilities.ValidadorEntradas import ValidadorEntradas
from exceptions import exceptions

if TYPE_CHECKING:
    from mascota import Mascota
    from detalle_consulta import DetalleConsulta

class EstadosConsulta(str, Enum):
    AGENDADA = "AGENDADA"
    CANCELADA = "CANCELADA"
    NO_ASISTIO = "NO ASISTIO"
    EN_ATENCION = 'EN ATENCION'
    EN_ESPERA_EXAMENES = "EN ESPERA EXAMENES"
    FINALIZADA = "FINALIZADA"


class Consulta:
    def __init__(
        self,
        mascota: Mascota,
        fecha_agendada: datetime,
        estado: EstadosConsulta = EstadosConsulta.AGENDADA,
        motivo: str | None = None,
        detalle: DetalleConsulta | None = None,
        fecha_inicio_atencion: datetime | None = None,
        fecha_fin_atencion: datetime | None = None,
        id_consulta: int | None = None,
    ):
        #validar ID
        self._id_consulta = ValidadorEntradas.validar_id(id_consulta, "consulta")
        self._fecha_agendada = None
        self._mascota = None
        
        self._fecha_inicio_atencion = fecha_inicio_atencion
        self._fecha_fin_atencion = fecha_fin_atencion
        self._motivo = ''
        self._estado = ''
        self._detalle = None

        self.fecha_agendada = fecha_agendada
        self.mascota = mascota
        self.detalle = detalle
        self.motivo = motivo
        self._estado = estado

    @property
    def id_consulta(self) -> int | None:
        return self._id_consulta

    @property
    def fecha_agendada(self) -> datetime:
        return self._fecha_agendada
    @fecha_agendada.setter
    def fecha_agendada(self, fecha: datetime) -> None:
        es_nueva = self._id_consulta is None
        self._fecha_agendada = self._validar_fecha_agendada(
            fecha,
            es_nueva
        )

    @property
    def fecha_inicio_atencion(self) -> datetime | None:
        return self._fecha_inicio_atencion

    @property
    def fecha_fin_atencion(self) -> datetime | None:
        return self._fecha_fin_atencion
        
    @property
    def motivo(self) -> str:
        return self._motivo
    @motivo.setter
    def motivo(self, valor: str | None) -> None:
        if valor is None:
            self._motivo = ""
            return
        motivo_limpio = ValidadorEntradas.validar_longitud(valor, max=200, nombre="Motivo")
        self._motivo = motivo_limpio

    @property
    def estado(self) -> EstadosConsulta:
        return self._estado


    @property
    def mascota(self) -> Mascota:
        return self._mascota
    @mascota.setter
    def mascota(self, mascota: Mascota) -> None:
        from mascota import Mascota
        mascota_valida = ValidadorEntradas.validar_instancia(mascota, Mascota, 'Mascota')
        self._mascota = mascota_valida

    @property
    def detalle(self) -> DetalleConsulta | None:
        return self._detalle
    @detalle.setter
    def detalle(self, detalle: DetalleConsulta | None) -> None:
        if detalle is not None:
            from detalle_consulta import DetalleConsulta
            detalle = ValidadorEntradas.validar_instancia(detalle, DetalleConsulta, 'Detalle de la Consulta', True)
        self._detalle = detalle

    def asignar_id(self, id_consulta: int) -> None:
        if self._id_consulta is not None:
            raise exceptions.ReglaNegocioError("La consulta ya tiene un ID asignado y no puede ser reasignado.")
        self._id_consulta = ValidadorEntradas.validar_id(id_consulta, "consulta")

    def _validar_fecha_agendada(self, fecha_agendada: datetime, es_nueva: bool) -> datetime:
        fecha_valida = ValidadorEntradas.validar_fecha(
        fecha_agendada,
            'Fecha y hora agendada para la consulta'
        )
        if es_nueva and fecha_valida <= datetime.now():
            raise exceptions.ReglaNegocioError(
                'La fecha agendada de una consulta nueva debe ser posterior '
                'al momento de su creación.'
            )
        return fecha_valida
    
    def _cambiar_estado(self, nuevo_estado: EstadosConsulta) -> None:
        nuevo_estado = ValidadorEntradas.validar_instancia(nuevo_estado, EstadosConsulta, 'Estado')
        if self.estado == nuevo_estado:
            raise exceptions.ReglaNegocioError(f"No se puede cambiar el estado: la consulta ya se encuentra en '{self.estado.value}'.")
        estados_finales = {
            EstadosConsulta.FINALIZADA,
            EstadosConsulta.CANCELADA,
            EstadosConsulta.NO_ASISTIO
        }
        if self.estado in estados_finales:
            raise exceptions.ReglaNegocioError(f'No se puede cambiar el estado de una consulta que ya está {self.estado}')
        
        if nuevo_estado == EstadosConsulta.FINALIZADA:
            if self.detalle is None:
                raise exceptions.ReglaNegocioError(
                    'No se puede finalizar una consulta sin registrar '
                    'su correspondiente detalle'
                )
            if not self.detalle.esta_completo():
                raise exceptions.ReglaNegocioError(
                    'No se puede finalizar una consulta con el detalle '
                    'incompleto'
                )
        
        self._estado = nuevo_estado

    def iniciar_atencion(self):
        self._cambiar_estado(EstadosConsulta.EN_ATENCION)
        self._fecha_inicio_atencion = datetime.now()

    def finalizar_atencion(self) -> None:
        self._cambiar_estado(EstadosConsulta.FINALIZADA)
        self._fecha_fin_atencion = datetime.now()

    def reagendar_consulta(self, nueva_fecha: datetime) -> None:
        ESTADOS_INCOMPATIBLES = {
            EstadosConsulta.EN_ATENCION,
            EstadosConsulta.FINALIZADA,
            EstadosConsulta.EN_ESPERA_EXAMENES,
            EstadosConsulta.CANCELADA
        }
        if self.estado in ESTADOS_INCOMPATIBLES:
            raise exceptions.ReglaNegocioError(f'no puede reagendar una consulta con el estado {self.estado.value}')
        fecha_valida = self._validar_fecha_agendada(
            nueva_fecha,
            es_nueva=True
        )
        self.fecha_agendada = fecha_valida

    def poner_en_espera(self) -> None:
        if self.estado != EstadosConsulta.EN_ATENCION:
            raise exceptions.ReglaNegocioError(f'no puede poner en espera una consulta con el estado {self.estado.value}')
        self._cambiar_estado(EstadosConsulta.EN_ESPERA_EXAMENES)

    def reanudar_atencion(self) -> None:
        if self.estado != EstadosConsulta.EN_ESPERA_EXAMENES:
            raise exceptions.ReglaNegocioError(f'solo puede reanudar consultas en espera de resultados de examenes')
        self._cambiar_estado(EstadosConsulta.EN_ATENCION)

    def registrar_inasistencia(self) -> None:
        if self.estado != EstadosConsulta.AGENDADA:
            raise exceptions.ReglaNegocioError(f'solo se puede marcar inasistencia en consultas agendadas')
        self._cambiar_estado(EstadosConsulta.NO_ASISTIO)

    def cancelar_consulta(self) -> None:
        ESTADOS_INCOMPATIBLES = {
                    EstadosConsulta.EN_ATENCION,
                    EstadosConsulta.FINALIZADA,
                    EstadosConsulta.EN_ESPERA_EXAMENES,
                    EstadosConsulta.NO_ASISTIO
                }
        if self.estado in ESTADOS_INCOMPATIBLES:
            raise exceptions.ReglaNegocioError(f'no se puede cancelar una consulta en estado {self.estado.value}')
        self._cambiar_estado(EstadosConsulta.CANCELADA)

    def calcular_duracion_minutos(self) -> int | None:
        if self._fecha_fin_atencion and self._fecha_inicio_atencion:
            delta = self._fecha_fin_atencion - self._fecha_inicio_atencion
            return int(delta.total_seconds() // 60)

    def registrar_detalle(self, detalle: DetalleConsulta) -> None:
        estados_permitidos = {
            EstadosConsulta.EN_ATENCION,
            EstadosConsulta.EN_ESPERA_EXAMENES,
        }
        if self.estado not in estados_permitidos:
            raise exceptions.ReglaNegocioError(
                "Solo se puede registrar un detalle durante la atención"
                "o mientras se está en espera de exámenes"
            )

        if self.detalle is not None:
            raise exceptions.ReglaNegocioError(
                "La consulta ya tiene un detalle registrado."
        )
        if self.detalle is None:
            self.detalle = detalle


    