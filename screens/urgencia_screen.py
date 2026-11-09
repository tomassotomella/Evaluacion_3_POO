from utilities import interfaz as ui
from exceptions import exceptions
from screens import consulta_screens


def main_guardia(consulta_service, farmacia_service) -> None:
    while True:
        ui.limpiar_y_encabezado("MODO GUARDIA: URGENCIAS Y PACIENTES EN ESPERA")
        print("""
        1. Registrar atención de urgencia
        2. Ver pacientes en espera
        3. Reanudar atención
        0. Volver
        """)
        opcion = ui.leer_opcion_menu(3)
        match opcion:
            case 1:
                registrar_urgencia(consulta_service, farmacia_service)
            case 2:
                ver_pacientes_en_espera(consulta_service)
            case 3:
                reanudar_atencion(consulta_service, farmacia_service)
            case 0:
                return


def registrar_urgencia(consulta_service, farmacia_service) -> None:
    ui.limpiar_y_encabezado("REGISTRO DE ATENCIÓN DE URGENCIA")
    id_mascota = ui.leer_entero("Ingrese ID de la mascota: ", nombre_campo="ID Mascota")
    try:
        consulta_service.validar_registro_urgencia()
    except exceptions.ReglaNegocioError as error:
        ui.mostrar_error(str(error))
        ui.pausar()
        return
    if not consulta_screens.mostrar_veterinarios_disponibles(consulta_service):
        return
    rut_veterinario = ui.leer_rut("Ingrese RUT del veterinario que atenderá: ")
    motivo = ui.leer_texto("Ingrese motivo de la urgencia: ", max_longitud=200, nombre_campo="Motivo")
    try:
        consulta = consulta_service.registrar_urgencia(
            id_mascota, rut_veterinario, motivo
        )
        ui.mostrar_exito(
            f"Urgencia ID:{consulta.id_consulta} iniciada para '{consulta.mascota.nombre}'."
        )
        consulta_screens.atencion_activa_screen(
            consulta_service, farmacia_service, consulta
        )
    except (exceptions.EntidadNoEncontradaException, exceptions.ReglaNegocioError) as error:
        ui.mostrar_error(str(error))
        ui.pausar()


def ver_pacientes_en_espera(consulta_service) -> None:
    consulta_screens.listar_consultas_en_espera(
        consulta_service
    )


def reanudar_atencion(consulta_service, farmacia_service) -> None:
    consulta_screens.reanudar_atencion(
        consulta_service,
        farmacia_service
    )
