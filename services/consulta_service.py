from __future__ import annotations
from models.consulta import Consulta, EstadosConsulta
from models.detalle_consulta import DetalleConsulta
from models.receta_medica import RecetaMedica
from dao.consulta_dao import ConsultaDAO
from dao.receta_medica_dao import RecetaMedicaDAO
from dao.medicamento_dao import MedicamentoDAO
from services.persona_service import PersonaService
from services.mascota_service import MascotaService
from utilities.ValidadorEntradas import ValidadorEntradas
from exceptions import exceptions
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from services.economia_service import EconomiaService
    from services.feriado_service import FeriadoService

class ConsultaService:
    def __init__(
            self,
            consulta_dao: ConsultaDAO,
            receta_dao: RecetaMedicaDAO,
            medicamento_dao: MedicamentoDAO,
            persona_service: PersonaService,
            mascota_service: MascotaService,
            economia_service: EconomiaService,
            feriado_service: FeriadoService
            ):
        self.consulta_dao = consulta_dao
        self.receta_dao = receta_dao
        self.medicamento_dao = medicamento_dao
        self.persona_service = persona_service
        self.mascota_service = mascota_service
        self.economia_service = economia_service
        self.feriado_service = feriado_service

    def _enriquecer_consulta(self, consulta: Consulta) -> Consulta:
        return self._enriquecer_consultas([consulta])[0]

    def _enriquecer_consultas(self, consultas: list[Consulta]) -> list[Consulta]:
        if consultas and self.economia_service is not None:
            try:
                dolar = self.economia_service.obtener_dolar_actual()
                for consulta in consultas:
                    consulta.calcular_montos_usd(dolar)
            except exceptions.ServicioExternoException:
                pass
        return consultas

    def _validar_fecha_consulta_normal(
        self,
        fecha: datetime,
        contexto: str
    ) -> None:
        try:
            es_habil = self.feriado_service.es_dia_habil(fecha.date())
        except exceptions.ServicioExternoException as error:
            raise exceptions.ReglaNegocioError(
                f"No se pudo verificar el calendario oficial de feriados{contexto}: "
                f"{error}. Por seguridad, la operación ha sido bloqueada."
            ) from error

        if not es_habil:
            raise exceptions.ReglaNegocioError(
                "Las consultas normales solo pueden operar en días hábiles "
                "(lunes a sábado no feriados)."
            )

    def obtener_consulta_por_id(self, id_consulta: int | str) -> Consulta:
        id_valido = ValidadorEntradas.validar_id(id_consulta, 'Consulta')
        return self._enriquecer_consulta(
            self.consulta_dao.obtener_consulta_por_id(id_valido)
        )

    def validar_inicio_atencion(self, consulta: Consulta) -> None:
        """Valida las reglas de calendario antes de solicitar datos clínicos."""
        if not consulta.es_urgencia:
            self._validar_fecha_consulta_normal(
                datetime.now(),
                " para iniciar la atención"
            )

    def listar_veterinarios(self):
        return self.persona_service.listar_veterinarios()

    def listar_consultas(self) -> list[Consulta]:
        return self._enriquecer_consultas(self.consulta_dao.listar_consultas())

    def listar_consultas_por_mascota(self, id_mascota: int | str) -> list[Consulta]:
        mascota = self.mascota_service.obtener_mascota_por_id(id_mascota)
        if mascota.id_mascota is None:
            raise exceptions.ReglaNegocioError(
                'La mascota debe tener un ID asignado.'
            )
        return self._enriquecer_consultas(
            self.consulta_dao.listar_consultas_por_mascota(mascota.id_mascota)
        )

    def listar_consultas_por_estado(
        self,
        estado: EstadosConsulta
    ) -> list[Consulta]:
        estado_valido = ValidadorEntradas.validar_instancia(
            estado,
            EstadosConsulta,
            'Estado de consulta'
        )
        return self._enriquecer_consultas(
            self.consulta_dao.listar_consultas_por_estado(estado_valido)
        )

    def listar_consultas_por_veterinario(
        self,
        rut_veterinario: str
    ) -> list[Consulta]:
        veterinario = self.persona_service.obtener_veterinario_por_rut(rut_veterinario)
        if veterinario.id_persona is None:
            raise exceptions.ReglaNegocioError(
                "El veterinario debe tener un ID asignado."
            )
        return self._enriquecer_consultas(
            self.consulta_dao.listar_consultas_por_veterinario(veterinario.id_persona)
        )

    def registrar_consulta(
        self,
        id_mascota: int | None,
        fecha_agendada: datetime,
        motivo: str | None = None
    ) -> Consulta:
        fecha_valida = ValidadorEntradas.validar_fecha(fecha_agendada)

        self._validar_fecha_consulta_normal(
            fecha_valida,
            ""
        )

        consulta = Consulta(
            mascota=self.mascota_service.obtener_mascota_por_id(id_mascota),
            fecha_agendada=fecha_valida,
            motivo=motivo
        )
        self.consulta_dao.insertar_consulta(consulta)
        return self._enriquecer_consulta(consulta)

    def registrar_atencion(self, consulta: Consulta, rut_veterinario: str) -> Consulta:
        """Registra una consulta ya construida junto con su detalle clínico."""
        veterinario = self.persona_service.obtener_veterinario_por_rut(rut_veterinario)
        detalle = DetalleConsulta(consulta=consulta, veterinario=veterinario)
        consulta.registrar_detalle(detalle)
        self.consulta_dao.insertar_consulta(consulta)
        self.consulta_dao.insertar_detalle(detalle)
        self.consulta_dao.actualizar_consulta(consulta)
        return self._enriquecer_consulta(consulta)

    def registrar_urgencia(
        self,
        id_mascota: int | None,
        rut_veterinario: str,
        motivo: str | None = None,
        porcentaje_recargo: float | None = None,
        tarifa_base: int | None = None,
    ) -> Consulta:
        ahora = datetime.now()
        self.validar_registro_urgencia(ahora)

        consulta = Consulta(
            mascota=self.mascota_service.obtener_mascota_por_id(id_mascota),
            fecha_agendada=ahora,
            fecha_inicio_atencion=ahora,
            estado=EstadosConsulta.EN_ATENCION,
            motivo=motivo,
            es_urgencia=True,
            tarifa_base=(
                Consulta.TARIFA_BASE_PREDETERMINADA
                if tarifa_base is None
                else tarifa_base
            ),
            porcentaje_recargo_feriado=(
                Consulta.PORCENTAJE_RECARGO_URGENCIA_DEFAULT
                if porcentaje_recargo is None
                else porcentaje_recargo
            ),
        )
        return self.registrar_atencion(consulta, rut_veterinario)

    def validar_registro_urgencia(self, fecha: datetime | None = None) -> None:
        fecha_validacion = fecha or datetime.now()
        try:
            self.feriado_service.validar_urgencia_permitida(
                fecha_validacion.date()
            )
        except exceptions.ServicioExternoException as error:
            raise exceptions.ReglaNegocioError(
                f"No se pudo consultar el servicio de feriados: {error}. "
                "La urgencia solo puede autorizarse fuera de domingo si se "
                "confirma que hoy es feriado."
            ) from error

    def iniciar_atencion(self, id_consulta: int | str, rut_veterinario: str) -> Consulta:
        consulta = self.obtener_consulta_por_id(id_consulta)

        self.validar_inicio_atencion(consulta)

        consulta.iniciar_atencion()
        detalle = DetalleConsulta(
            consulta=consulta,
            veterinario= self.persona_service.obtener_veterinario_por_rut(rut_veterinario))
        consulta.registrar_detalle(detalle)
        self.consulta_dao.insertar_detalle(detalle)
        self.consulta_dao.actualizar_consulta(consulta)
        return consulta

    def poner_en_espera(self, id_consulta: int | str) -> Consulta:
        consulta = self.obtener_consulta_por_id(id_consulta)
        consulta.poner_en_espera()
        self.consulta_dao.actualizar_consulta(consulta)
        return consulta

    def reanudar_atencion(self, id_consulta: int | str) -> Consulta:
        consulta = self.obtener_consulta_por_id(id_consulta)
        consulta.reanudar_atencion()
        self.consulta_dao.actualizar_consulta(consulta)
        return consulta

    def cancelar_consulta(self, id_consulta: int| str) -> Consulta:
        consulta = self.obtener_consulta_por_id(id_consulta)
        consulta.cancelar_consulta()
        self.consulta_dao.actualizar_consulta(consulta)
        return consulta

    def registrar_inasistencia(self, id_consulta: int | str) -> Consulta:
        consulta = self.obtener_consulta_por_id(id_consulta)
        consulta.registrar_inasistencia()
        self.consulta_dao.actualizar_consulta(consulta)
        return consulta

    def reagendar_consulta(self, id_consulta: int | str, nueva_fecha: datetime) -> Consulta:
        consulta = self.obtener_consulta_por_id(id_consulta)
        nueva_fecha_valida = ValidadorEntradas.validar_fecha(nueva_fecha)
        if not consulta.es_urgencia:
            self._validar_fecha_consulta_normal(
                nueva_fecha_valida,
                " para reagendar"
            )
        consulta.reagendar_consulta(nueva_fecha_valida)
        self.consulta_dao.actualizar_consulta(consulta)
        return consulta

    def finalizar_atencion(self, id_consulta: int | str) -> Consulta:
        consulta = self.obtener_consulta_por_id(id_consulta)
        consulta.finalizar_atencion()
        self.consulta_dao.actualizar_consulta(consulta)
        return consulta

    def actualizar_motivo(self, id_consulta: int | str, motivo: str) -> Consulta:
        consulta = self.obtener_consulta_por_id(id_consulta)
        consulta.motivo = motivo
        self.consulta_dao.actualizar_consulta(consulta)
        return consulta

    def registrar_detalle(
        self,
        id_consulta: int | str,
        rut_veterinario: str | None = None,
        diagnostico: str | None = None,
        tratamiento: str | None = None,
        observaciones: str | None = None
    ) -> DetalleConsulta:
        consulta = self.obtener_consulta_por_id(id_consulta)

        if consulta.detalle is not None:
            detalle = consulta.detalle
            if diagnostico is not None:
                detalle.actualizar_diagnostico(diagnostico)
            if tratamiento is not None:
                detalle.actualizar_tratamiento(tratamiento)
            if observaciones is not None:
                detalle.actualizar_observaciones(observaciones)
            self.consulta_dao.actualizar_detalle(detalle)
            return detalle

        detalle = DetalleConsulta(
            consulta=consulta,
            veterinario=self.persona_service.obtener_veterinario_por_rut(rut_veterinario),
            diagnostico=diagnostico,
            tratamiento=tratamiento,
            observaciones=observaciones
        )
        consulta.registrar_detalle(detalle)
        self.consulta_dao.insertar_detalle(detalle)
        self.consulta_dao.actualizar_consulta(consulta)
        return detalle

    def obtener_detalle_por_id(self, id_detalle: int | str) -> DetalleConsulta:
        id_valido = ValidadorEntradas.validar_id(id_detalle, 'Detalle de Consulta')
        return self.consulta_dao.obtener_detalle_por_id(id_valido)

    def listar_detalles(self) -> list[DetalleConsulta]:
        return self.consulta_dao.listar_detalles()

    def buscar_detalle_por_veterinario(self, rut_veterinario: int | str) ->list[DetalleConsulta]:
        veterinario = self.persona_service.obtener_veterinario_por_rut(rut_veterinario)
        return self.consulta_dao.buscar_detalles_por_veterinario(veterinario.id_persona)

    def actualizar_diagnostico(self, id_detalle: int | str, diagnostico: str) -> DetalleConsulta:
        detalle = self.obtener_detalle_por_id(id_detalle)
        detalle.actualizar_diagnostico(diagnostico)
        self.consulta_dao.actualizar_detalle(detalle)
        return detalle

    def actualizar_tratamiento(self, id_detalle: int | str, tratamiento: str) -> DetalleConsulta:
        detalle = self.obtener_detalle_por_id(id_detalle)
        detalle.actualizar_tratamiento(tratamiento)
        self.consulta_dao.actualizar_detalle(detalle)
        return detalle

    def actualizar_observaciones(self, id_detalle: int | str, observaciones: str) -> DetalleConsulta:
        detalle = self.obtener_detalle_por_id(id_detalle)
        detalle.actualizar_observaciones(observaciones)
        self.consulta_dao.actualizar_detalle(detalle)
        return detalle

    def registrar_receta(
                self,
                id_detalle: int | str,
                id_medicamento: int | str,
                cantidad: int,
                instrucciones: str
        ) -> RecetaMedica:
            detalle = self.obtener_detalle_por_id(id_detalle)
            id_medicamento_valido = ValidadorEntradas.validar_id(
                id_medicamento,
                'Medicamento'
            )
            medicamento = self.medicamento_dao.obtener_por_id(id_medicamento_valido) # cambiar por lazy import de FarmaciaService?

            receta = detalle.prescribir_medicamento(
                cantidad=cantidad,
                instrucciones=instrucciones,
                medicamento=medicamento
            )
            self.receta_dao.insertar(receta)
            return receta

    def obtener_receta_por_id(self, id_receta: int|str) -> RecetaMedica:
        id_valido = ValidadorEntradas.validar_id(id_receta, 'Receta')
        return self.receta_dao.obtener_por_id(id_valido)

    def listar_recetas(self) -> list[RecetaMedica]:
        return self.receta_dao.listar_todos()

    def listar_recetas_por_detalle(self, id_detalle: int | str) -> list[RecetaMedica]:
        detalle = self.obtener_detalle_por_id(id_detalle)
        return self.receta_dao.listar_por_detalle(detalle.id_detalle)

    def buscar_recetas_por_medicamento(self, nombre: str) -> list[RecetaMedica]:
        return self.receta_dao.buscar_por_nombre_medicamento(nombre)

    def remover_receta(self, id_receta: int | str) -> None:
        receta = self.obtener_receta_por_id(id_receta)
        self.receta_dao.eliminar(receta.id_receta)

    
    
