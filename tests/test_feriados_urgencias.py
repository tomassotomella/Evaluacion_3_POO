import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from datetime import datetime, date, timedelta
from database.conexion import ConexionDBT
from services.feriado_service import FeriadoService
from dao.feriado_dao import FeriadoDAO
from models.feriado import Feriado
from services.consulta_service import ConsultaService
from services.economia_service import EconomiaService
from services.persona_service import PersonaService
from services.mascota_service import MascotaService
from dao.consulta_dao import ConsultaDAO
from dao.receta_medica_dao import RecetaMedicaDAO
from dao.medicamento_dao import MedicamentoDAO
from dao.divisa_dao import DivisaDAO
from dao.propietario_dao import PropietarioDAO
from dao.veterinario_dao import VeterinarioDAO
from dao.especialidad_dao import EspecialidadDAO
from dao.especie_dao import EspecieDAO
from dao.mascota_dao import MascotaDAO
from models.consulta import Consulta, EstadosConsulta
from exceptions import exceptions


def certificar_feriados_y_urgencias():
    print("=" * 70)
    print("TEST: FERIADOS, RECARGOS Y ATENCIONES DE URGENCIA")
    print("=" * 70)

    conexion = ConexionDBT()
    esp_dao = EspecialidadDAO(conexion)
    prop_dao = PropietarioDAO(conexion)
    vet_dao = VeterinarioDAO(conexion, esp_dao)
    especie_dao = EspecieDAO(conexion)
    mascota_dao = MascotaDAO(conexion, especie_dao, prop_dao)
    med_dao = MedicamentoDAO(conexion)
    consulta_dao = ConsultaDAO(conexion, mascota_dao)
    receta_dao = RecetaMedicaDAO(conexion, med_dao, consulta_dao)
    divisa_dao = DivisaDAO(conexion)

    persona_svc = PersonaService(prop_dao, vet_dao, esp_dao)
    mascota_svc = MascotaService(mascota_dao, especie_dao, persona_svc)
    economia_svc = EconomiaService(divisa_dao)
    feriado_svc = FeriadoService(FeriadoDAO(conexion))

    consulta_svc = ConsultaService(
        consulta_dao,
        receta_dao,
        med_dao,
        persona_svc,
        mascota_svc,
        economia_svc,
        feriado_svc
    )

    # 1. Validar FeriadoService básico y calendario
    print("\n[PASO 1] Validando FeriadoService...")
    # Año Nuevo es feriado
    feriado_ano_nuevo = feriado_svc.es_feriado(date(2026, 1, 1))
    assert feriado_ano_nuevo is not None, "El 1 de enero debe ser feriado."
    print(f" -> 2026-01-01 es feriado legal: {feriado_ano_nuevo.nombre}")

    # Sábado laborable (2026-11-14 es sábado)
    sabado_comun = date(2026, 11, 14)
    assert feriado_svc.es_dia_habil(sabado_comun) is True, "Un sábado no festivo debe ser hábil."
    print(f" -> Sábado {sabado_comun} es día hábil/laborable: OK")

    # Domingo no hábil (2026-11-15 es domingo)
    domingo_comun = date(2026, 11, 15)
    assert feriado_svc.es_domingo(domingo_comun) is True
    assert feriado_svc.es_dia_habil(domingo_comun) is False, "Un domingo no puede ser hábil."
    print(f" -> Domingo {domingo_comun} NO es día hábil: OK")

    # 2. Setup datos de prueba (veterinario y mascota)
    print("\n[PASO 2] Preparando datos de prueba (Veterinario y Mascota)...")
    try:
        esp = esp_dao.obtener_por_id(1)
    except exceptions.EntidadNoEncontradaException:
        esp_dao.insertar("Medicina General")
        esp = esp_dao.obtener_por_id(1)

    rut_vet = "12345678-5"
    try:
        vet = persona_svc.obtener_veterinario_por_rut(rut_vet)
    except exceptions.EntidadNoEncontradaException:
        vet = persona_svc.registrar_veterinario(
            rut=rut_vet,
            nombre_completo="Camila Soto",
            telefono="+56911223344",
            id_especialidad=esp.id_especialidad
        )

    rut_prop = "11111111-1"
    try:
        prop = persona_svc.obtener_propietario_por_rut(rut_prop)
    except exceptions.EntidadNoEncontradaException:
        prop = persona_svc.registrar_propietario(
            rut=rut_prop,
            nombre_completo="Juan Perez",
            telefono="+56987654321"
        )

    try:
        especie = especie_dao.obtener_por_id(1)
    except exceptions.EntidadNoEncontradaException:
        especie = mascota_svc.registrar_especie("Canino", 15)

    mascotas = mascota_dao.listar_por_propietario(prop.id_persona)
    if mascotas:
        mascota = mascotas[0]
    else:
        mascota = mascota_svc.registrar_mascota(
            nombre="Boby",
            fecha_nacimiento=date(2020, 5, 10),
            id_especie=especie.id_especie,
            rut_propietario=rut_prop
        )
    print(f" -> Mascota '{mascota.nombre}' (ID:{mascota.id_mascota}) y Veterinario '{vet.nombre_completo}' listos.")

    # 3. Bloqueo de consultas normales en domingo o feriado
    print("\n[PASO 3] Validando restricción de citas normales en domingos y feriados...")
    # Intento en domingo futuro: 2026-11-15 11:00
    fecha_domingo = datetime(2026, 11, 15, 11, 0)
    bloqueado_domingo = False
    try:
        consulta_svc.registrar_consulta(mascota.id_mascota, fecha_domingo, "Control sano")
    except exceptions.ReglaNegocioError as e:
        bloqueado_domingo = True
        print(f" -> Cita bloqueada en domingo correctamente: {e}")
    assert bloqueado_domingo is True, "Se debió bloquear el agendamiento en domingo."

    # Intento en feriado futuro: 2026-12-08 (Inmaculada Concepción)
    fecha_feriado = datetime(2026, 12, 8, 10, 0)
    bloqueado_feriado = False
    try:
        consulta_svc.registrar_consulta(mascota.id_mascota, fecha_feriado, "Vacuna anual")
    except exceptions.ReglaNegocioError as e:
        bloqueado_feriado = True
        print(f" -> Cita bloqueada en feriado correctamente: {e}")
    assert bloqueado_feriado is True, "Se debió bloquear el agendamiento en día festivo."

    # 4. Agendamiento exitoso en día hábil (Sábado 2026-11-14 10:00)
    print("\n[PASO 4] Agendando consulta normal en día hábil (sábado)...")
    fecha_habil = datetime(2026, 11, 14, 10, 0)
    consulta_normal = consulta_svc.registrar_consulta(mascota.id_mascota, fecha_habil, "Control general")
    assert consulta_normal.id_consulta is not None
    assert consulta_normal.es_urgencia is False
    assert consulta_normal.tarifa_base == 25000
    assert consulta_normal.porcentaje_recargo_feriado == 0.0
    assert consulta_normal.monto_total == 25000
    assert consulta_normal.estado == EstadosConsulta.AGENDADA
    print(f" -> Consulta normal agendada exitosamente ID:{consulta_normal.id_consulta}. Monto: ${consulta_normal.monto_total} CLP")

    # 5. Registro de urgencia: estado EN_ATENCION y fechas iguales a datetime.now()
    print("\n[PASO 5] Validando registro de urgencia (estado EN_ATENCION, fechas simultáneas, recargo único)...")
    # Para simular que hoy califica para urgencia, inyectamos temporalmente hoy como domingo o feriado
    hoy = date.today()
    FeriadoDAO(conexion).reemplazar_cache(
        [Feriado(hoy, "Día Simulado de Feriado", "Civil", False)],
        hoy.year,
        hoy.month,
        datetime.now()
    )

    urgencia = consulta_svc.registrar_urgencia(
        id_mascota=mascota.id_mascota,
        rut_veterinario=rut_vet,
        motivo="Intoxicación por ingestión de chocolate",
        porcentaje_recargo=30.0
    )
    assert urgencia.id_consulta is not None
    assert urgencia.es_urgencia is True
    assert urgencia.estado == EstadosConsulta.EN_ATENCION
    assert urgencia.fecha_agendada == urgencia.fecha_inicio_atencion
    assert urgencia.tarifa_base == 25000
    assert urgencia.porcentaje_recargo_feriado == 30.0
    # Monto total: 25000 + 30% (7500) = 32500
    assert urgencia.monto_total == 32500
    print(f" -> Urgencia registrada con éxito ID:{urgencia.id_consulta}")
    print(f"    Estado: {urgencia.estado.value}")
    print(f"    Tarifa Base: ${urgencia.tarifa_base} CLP | Recargo: {urgencia.porcentaje_recargo_feriado}% | Monto Total: ${urgencia.monto_total} CLP")
    print(f"    Fecha Agendada: {urgencia.fecha_agendada} == Fecha Inicio: {urgencia.fecha_inicio_atencion}")

    # 6. Reanudar atención en espera de exámenes no recalcula el precio
    print("\n[PASO 6] Pausar por exámenes y reanudar sin recalcular precio...")
    consulta_svc.poner_en_espera(urgencia.id_consulta)
    u_espera = consulta_svc.obtener_consulta_por_id(urgencia.id_consulta)
    assert u_espera.estado == EstadosConsulta.EN_ESPERA_EXAMENES

    consulta_svc.reanudar_atencion(urgencia.id_consulta)
    u_reanudada = consulta_svc.obtener_consulta_por_id(urgencia.id_consulta)
    assert u_reanudada.estado == EstadosConsulta.EN_ATENCION
    assert u_reanudada.monto_total == 32500
    print(f" -> Atención reanudada en estado {u_reanudada.estado.value}. Monto conservado intacto: ${u_reanudada.monto_total} CLP")

    # 7. Comprobación de contingencia: fallo de API en domingo permite urgencia
    print("\n[PASO 7] Contingencia ante caída de API en domingo...")
    class FeriadoFallaAPI(FeriadoService):
        def _obtener_feriado(self, fecha):
            raise exceptions.ConexionTimeoutException("BoostrHolidays", 10)

    feriado_caido = FeriadoFallaAPI(FeriadoDAO(conexion))
    svc_contingencia = ConsultaService(
        consulta_dao, receta_dao, med_dao, persona_svc, mascota_svc, economia_svc, feriado_caido
    )

    # Si es domingo y la API falla, debe permitirse sin advertencia
    if date.today().weekday() == 6:
        urg_dom = svc_contingencia.registrar_urgencia(mascota.id_mascota, rut_vet, "Corte profundo")
        assert urg_dom.id_consulta is not None
        print(" -> Urgencia permitida en domingo sin advertencia")
    else:
        # En día que no es domingo, si la API falla, debe bloquearse
        bloqueado_offline = False
        try:
            svc_contingencia.registrar_urgencia(mascota.id_mascota, rut_vet, "Dolor agudo")
        except exceptions.ReglaNegocioError as e:
            bloqueado_offline = True
            print(f" -> Bloqueada correctamente fuera de domingo ante caída de API: {e}")
        assert bloqueado_offline is True

    # 8. Bloqueo de inicio de consulta normal en feriado/domingo
    print("\n[PASO 8] Bloqueo de inicio de atención regular en día festivo/domingo...")
    # Aseguramos que hoy está registrado como festivo en feriado_svc
    feriado_svc.feriado_dao.reemplazar_cache(
        [Feriado(date.today(), "Día Simulado de Feriado", "Civil", False)],
        date.today().year,
        date.today().month,
        datetime.now()
    )
    bloqueado_atencion_festiva = False
    try:
        consulta_svc.iniciar_atencion(consulta_normal.id_consulta, rut_vet)
    except exceptions.ReglaNegocioError as e:
        bloqueado_atencion_festiva = True
        print(f" -> Inicio de consulta normal bloqueado en día festivo: {e}")
    assert bloqueado_atencion_festiva is True, "No se debe permitir iniciar una consulta normal en festivo/domingo."

    print("\n" + "=" * 70)
    print("TODOS LOS REQUERIMIENTOS Y REGLAS CERTIFICADOS CON ÉXITO")
    print("=" * 70)


if __name__ == '__main__':
    certificar_feriados_y_urgencias()
