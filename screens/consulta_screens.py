from utilities import interfaz as ui
from exceptions import exceptions
from models.consulta import EstadosConsulta
from screens import veterinario_screens


def main_consultas(consulta_service, farmacia_service, feriado_service=None) -> None:
    """Menú Principal del Módulo de Consultas y Atenciones."""
    while True:
        ui.limpiar_y_encabezado("GESTIÓN DE CONSULTAS Y ATENCIONES MÉDICAS")
        print('''
        1. Módulo Recepción y Agenda (Citas)
        2. Módulo de Atención Clínica (Box)
        3. Historial Médico (Buscador Clínico)
        4. Modo Guardia (Urgencias y pacientes en espera)
        0. Volver al Menú Principal
        ''')
        opcion = ui.leer_opcion_menu(4)
        match opcion:
            case 1:
                submenu_recepcion_agenda(
                    consulta_service,
                    farmacia_service,
                    feriado_service,
                )
            case 2:
                submenu_atencion(consulta_service, farmacia_service)
            case 3:
                submenu_historial_medico(consulta_service)
            case 4:
                from screens import urgencia_screen
                urgencia_screen.main_guardia(consulta_service, farmacia_service)
            case 0:
                break


# =============================================================================
# MÓDULO 1: RECEPCIÓN Y AGENDA
# =============================================================================

def submenu_recepcion_agenda(
    consulta_service,
    farmacia_service=None,
    feriado_service=None,
) -> None:
    while True:
        ui.limpiar_y_encabezado("RECEPCIÓN Y AGENDA DE CITAS")
        print('''
        1. Agendar Nueva Cita (Días Hábiles)
        2. Reagendar Cita
        3. Cancelar Cita
        4. Ver Agenda / Consultas
        5. Buscar Consulta por ID
        0. Volver
        ''')
        opcion = ui.leer_opcion_menu(5)
        match opcion:
            case 1:
                agendar_consulta(consulta_service, feriado_service)
            case 2:
                reagendar_consulta(consulta_service)
            case 3:
                cancelar_consulta(consulta_service)
            case 4:
                subopciones_agenda(consulta_service)
            case 5:
                buscar_consulta_por_id(consulta_service)
            case 0:
                break


def subopciones_agenda(consulta_service) -> None:
    while True:
        ui.limpiar_y_encabezado("CONSULTAR AGENDA")
        print('''
        1. Listar Todas las Citas
        2. Citas por Estado (Agendada, En Espera, Cancelada, etc.)
        3. Citas por Veterinario
        0. Volver
        ''')
        opcion = ui.leer_opcion_menu(3)
        match opcion:
            case 1:
                listar_todas_consultas(consulta_service)
            case 2:
                listar_consultas_por_estado(consulta_service)
            case 3:
                listar_consultas_por_veterinario(consulta_service)
            case 0:
                break


# =============================================================================
# MÓDULO 2: ATENCIÓN CLÍNICA (BOX)
# =============================================================================

def submenu_atencion(consulta_service, farmacia_service) -> None:
    while True:
        ui.limpiar_y_encabezado("MÓDULO DE ATENCIÓN CLÍNICA (BOX)")
        print('''
        1. Iniciar Atención (Pacientes Agendados)
        2. Reanudar Atención (Pacientes en Espera)
        3. Marcar Inasistencia
        0. Volver
        ''')
        opcion = ui.leer_opcion_menu(3)
        match opcion:
            case 1:
                iniciar_atencion(consulta_service, farmacia_service)
            case 2:
                reanudar_atencion(consulta_service, farmacia_service)
            case 3:
                marcar_inasistencia(consulta_service)
            case 0:
                break


def seleccionar_consulta_de_lista(consultas: list, accion: str):
    """Obliga a seleccionar una consulta de la lista mostrada. 0 cancela."""
    while True:
        id_consulta = ui.leer_entero(
            f"\nIngrese el ID de la consulta a {accion} (0 para cancelar): ",
            nombre_campo="ID Consulta",
            minimo=0
        )
        if id_consulta == 0:
            return None
        seleccionada = next((c for c in consultas if c.id_consulta == id_consulta), None)
        if seleccionada is None:
            ui.mostrar_advertencia(f"El ID {id_consulta} no corresponde a ninguna consulta listada.")
            continue
        return seleccionada


def mostrar_veterinarios_disponibles(consulta_service) -> bool:
    veterinarios = consulta_service.listar_veterinarios()
    if not veterinarios:
        ui.mostrar_advertencia("No hay veterinarios registrados para atender.")
        ui.pausar()
        return False
    veterinario_screens.imprimir_tabla_veterinarios(veterinarios)
    return True


def iniciar_atencion(consulta_service, farmacia_service) -> None:
    ui.limpiar_y_encabezado("INICIAR ATENCIÓN (PACIENTES AGENDADOS)")
    consultas = consulta_service.listar_consultas_por_estado(EstadosConsulta.AGENDADA)
    if not consultas:
        ui.mostrar_advertencia("No hay consultas agendadas para atender.")
        ui.pausar()
        return

    imprimir_tabla_consultas(consultas)
    seleccionada = seleccionar_consulta_de_lista(consultas, "atender")
    if seleccionada is None:
        print("\nOperación cancelada.")
        ui.pausar()
        return

    try:
        consulta_service.validar_inicio_atencion(seleccionada)
    except exceptions.ReglaNegocioError as error:
        ui.mostrar_error(str(error))
        ui.pausar()
        return

    if not mostrar_veterinarios_disponibles(consulta_service):
        return

    rut_vet = ui.leer_rut("Ingrese RUT del veterinario que atenderá: ")

    try:
        consulta_activa = consulta_service.iniciar_atencion(seleccionada.id_consulta, rut_vet)
        ui.mostrar_exito(
            f"Atención iniciada para '{consulta_activa.mascota.nombre}' a cargo de "
            f"{consulta_activa.detalle.veterinario.nombre_completo}."
        )
        ui.pausar()
        atencion_activa_screen(consulta_service, farmacia_service, consulta_activa)
    except (exceptions.EntidadNoEncontradaException, exceptions.ReglaNegocioError) as error:
        ui.mostrar_error(str(error))
        ui.pausar()


def reanudar_atencion(consulta_service, farmacia_service) -> None:
    ui.limpiar_y_encabezado("REANUDAR ATENCIÓN (PACIENTES EN ESPERA)")
    consultas = consulta_service.listar_consultas_por_estado(EstadosConsulta.EN_ESPERA_EXAMENES)
    if not consultas:
        ui.mostrar_advertencia("No hay atenciones en espera para reanudar.")
        ui.pausar()
        return

    imprimir_tabla_consultas(consultas)
    seleccionada = seleccionar_consulta_de_lista(consultas, "reanudar")
    if seleccionada is None:
        print("\nOperación cancelada.")
        ui.pausar()
        return

    try:
        consulta_activa = consulta_service.reanudar_atencion(seleccionada.id_consulta)
        ui.mostrar_exito(f"Atención reanudada para '{consulta_activa.mascota.nombre}'.")
        ui.pausar()
        atencion_activa_screen(consulta_service, farmacia_service, consulta_activa)
    except (exceptions.EntidadNoEncontradaException, exceptions.ReglaNegocioError) as error:
        ui.mostrar_error(str(error))
        ui.pausar()


def listar_consultas_en_espera(consulta_service) -> None:
    """Muestra las consultas pausadas por espera de exámenes."""
    consultas = consulta_service.listar_consultas_por_estado(
        EstadosConsulta.EN_ESPERA_EXAMENES
    )
    if not consultas:
        ui.mostrar_advertencia("No hay atenciones en espera.")
    else:
        imprimir_tabla_consultas(consultas)
    ui.pausar()


def marcar_inasistencia(consulta_service) -> None:
    ui.limpiar_y_encabezado("MARCAR INASISTENCIA (PACIENTES AGENDADOS)")
    consultas = consulta_service.listar_consultas_por_estado(EstadosConsulta.AGENDADA)
    if not consultas:
        ui.mostrar_advertencia("No hay consultas agendadas.")
        ui.pausar()
        return

    imprimir_tabla_consultas(consultas)
    seleccionada = seleccionar_consulta_de_lista(consultas, "marcar inasistencia")
    if seleccionada is None:
        print("\nOperación cancelada.")
        ui.pausar()
        return

    if ui.desea_confirmar(
        f"¿Confirma registrar la inasistencia de '{seleccionada.mascota.nombre}' "
        f"en la consulta ID:{seleccionada.id_consulta}?"
    ):
        try:
            actualizada = consulta_service.registrar_inasistencia(seleccionada.id_consulta)
            ui.mostrar_exito(f"Consulta ID:{actualizada.id_consulta} registrada como '{actualizada.estado.value}'.")
        except (exceptions.EntidadNoEncontradaException, exceptions.ReglaNegocioError) as error:
            ui.mostrar_error(str(error))
    else:
        print("\nOperación cancelada.")
    ui.pausar()


def atencion_activa_screen(consulta_service, farmacia_service, consulta_activa) -> None:
    """Menú de Atención en Atención: opera en tiempo real sobre la consulta activa."""
    detalle_activo = consulta_activa.detalle
    if detalle_activo is None:
        ui.mostrar_error("La consulta activa no posee detalle médico asociado.")
        ui.pausar()
        return

    while True:
        ui.limpiar_y_encabezado(
            f"ATENCIÓN ACTIVA - {consulta_activa.mascota.nombre} (CONSULTA ID:{consulta_activa.id_consulta})"
        )
        print('''
        1. Ver Ficha de la Mascota
        2. Gestionar Motivo
        3. Gestionar Diagnóstico
        4. Gestionar Tratamiento
        5. Gestionar Observaciones
        6. Agregar Receta Médica
        7. Eliminar Receta Médica
        8. Ver Resumen de la Atención
        9. Pausar Atención (Pasar a Espera)
        10. Finalizar Atención
        ''')
        opcion = ui.leer_entero("Seleccione una acción: ", nombre_campo="Opción", minimo=1, maximo=10)
        match opcion:
            case 1:
                ver_ficha_mascota(consulta_service, consulta_activa)
            case 2:
                consulta_activa = gestionar_motivo(consulta_service, consulta_activa)
            case 3:
                detalle_activo = gestionar_diagnostico(consulta_service, detalle_activo)
            case 4:
                detalle_activo = gestionar_tratamiento(consulta_service, detalle_activo)
            case 5:
                detalle_activo = gestionar_observaciones(consulta_service, detalle_activo)
            case 6:
                agregar_receta(consulta_service, farmacia_service, detalle_activo)
            case 7:
                eliminar_receta(consulta_service, detalle_activo)
            case 8:
                ver_resumen_atencion(consulta_service, consulta_activa, detalle_activo)
            case 9:
                if pausar_atencion(consulta_service, consulta_activa):
                    return
            case 10:
                if finalizar_atencion(consulta_service, consulta_activa, detalle_activo):
                    return


# =============================================================================
# MÓDULO 3: HISTORIAL MÉDICO Y BUSCADORES
# =============================================================================

def submenu_historial_medico(consulta_service) -> None:
    while True:
        ui.limpiar_y_encabezado("MÓDULO DE HISTORIAL Y CONSULTAS")
        print('''
        1. Historial Clínico de Paciente
        2. Reportes de Atenciones Médicas
        3. Consultas de Recetas y Farmacia
        0. Volver
        ''')
        opcion = ui.leer_opcion_menu(3)
        match opcion:
            case 1:
                submenu_fichas_paciente(consulta_service)
            case 2:
                submenu_reportes_atenciones(consulta_service)
            case 3:
                submenu_recetas_farmacia(consulta_service)
            case 0:
                break


# SUBMENÚ 1: FICHAS CLÍNICAS

def submenu_fichas_paciente(consulta_service) -> None:
    while True:
        ui.limpiar_y_encabezado("HISTORIAL CLÍNICO DE PACIENTE")
        print('''
        1. Historial Completo por Mascota
        2. Buscar Ficha / Detalle por ID
        0. Volver
        ''')
        opcion = ui.leer_opcion_menu(2)
        match opcion:
            case 1:
                listar_consultas_por_mascota(consulta_service)
            case 2:
                obtener_detalle_por_id(consulta_service)
            case 0:
                break


# SUBMENÚ 2: ATENCIONES

def submenu_reportes_atenciones(consulta_service) -> None:
    while True:
        ui.limpiar_y_encabezado("REPORTES DE ATENCIONES MÉDICAS")
        print('''
        1. Listar Todos los Detalles Médicos
        2. Buscar Detalles por Veterinario
        0. Volver
        ''')
        opcion = ui.leer_opcion_menu(2)
        match opcion:
            case 1:
                listar_todos_detalles(consulta_service)
            case 2:
                buscar_detalles_por_veterinario(consulta_service)
            case 0:
                break


# SUBMENÚ 3: FARMACIA

def submenu_recetas_farmacia(consulta_service) -> None:
    while True:
        ui.limpiar_y_encabezado("CONSULTA DE RECETAS Y FARMACIA")
        print('''
        1. Listar Todas las Recetas
        2. Buscar Recetas por Medicamento
        3. Ver Recetas de una Atención (ID Detalle)
        0. Volver
        ''')
        opcion = ui.leer_opcion_menu(3)
        match opcion:
            case 1:
                listar_todas_recetas(consulta_service)
            case 2:
                buscar_recetas_por_medicamento(consulta_service)
            case 3:
                listar_recetas_de_detalle(consulta_service)
            case 0:
                break


# =============================================================================
# IMPLEMENTACIÓN DE ACCIONES
# =============================================================================

def _mostrar_proximos_feriados(feriado_service, limite: int = 3) -> None:
    if feriado_service is None:
        return
    try:
        proximos_feriados = feriado_service.obtener_proximos_feriados(limite)
    except exceptions.ServicioExternoException as error:
        ui.mostrar_advertencia(
            f"No se pudieron cargar los próximos feriados: {error}"
        )
        return

    if not proximos_feriados:
        print("\nNo hay próximos feriados registrados.")
        return

    ui.mostrar_advertencia(
        "Tenga en consideración los próximos feriados:"
    )
    for feriado in proximos_feriados:
        irrenunciable = " (irrenunciable)" if feriado.es_irrenunciable else ""
        print(
            f"  - {feriado.fecha:%d/%m/%Y}: "
            f"{feriado.nombre}{irrenunciable}"
        )


def agendar_consulta(consulta_service, feriado_service=None) -> None:
    ui.limpiar_y_encabezado("AGENDAR NUEVA CITA (DÍAS HÁBILES: LUNES A SÁBADO)")
    print("Nota: No se permite agendar citas normales en domingos ni festivos (solo urgencias).")
    _mostrar_proximos_feriados(feriado_service)
    id_mascota = ui.leer_entero("Ingrese ID de la mascota: ", nombre_campo="ID Mascota")
    fecha_agendada = ui.leer_fecha("Ingrese fecha y hora (YYYY-MM-DD HH:MM): ", nombre_campo="Fecha Agendada")
    motivo = ui.leer_texto("Ingrese motivo de la consulta: ", max_longitud=200, nombre_campo="Motivo")

    try:
        consulta = consulta_service.registrar_consulta(
            id_mascota=id_mascota,
            fecha_agendada=fecha_agendada,
            motivo=motivo
        )
        ui.mostrar_exito(f"Cita ID:{consulta.id_consulta} agendada para la mascota '{consulta.mascota.nombre}'.")
    except (exceptions.EntidadNoEncontradaException, exceptions.ReglaNegocioError) as error:
        ui.mostrar_error(str(error))
    finally:
        ui.pausar()


def buscar_consulta_por_id(consulta_service) -> None:
    id_consulta = ui.leer_entero("Ingrese ID de la consulta: ", nombre_campo="ID Consulta")

    try:
        consulta = consulta_service.obtener_consulta_por_id(id_consulta)
        est_actual = consulta.estado.value
        ui.mostrar_subtitulo("INFORMACIÓN DE LA CONSULTA")
        print(f"ID Consulta:      {consulta.id_consulta}")
        print(f"Mascota:          {consulta.mascota.nombre}")
        print(f"Propietario:      {consulta.mascota.propietario.nombre_completo} (RUT: {consulta.mascota.propietario.rut})")
        print(f"Tipo Atención:    {'URGENCIA (Festivo/Domingo)' if consulta.es_urgencia else 'NORMAL'}")
        print(f"Fecha Agendada:   {consulta.fecha_agendada}")
        print(f"Estado:           {est_actual}")
        tarifa_usd_str = f" (~${consulta.tarifa_base_usd:,.2f} USD)" if consulta.tarifa_base_usd is not None else ""
        print(f"Tarifa Base:      ${consulta.tarifa_base:,} CLP{tarifa_usd_str}")
        if consulta.es_urgencia:
            print(f"Recargo Festivo:  {consulta.porcentaje_recargo_feriado}%")
        monto_usd_str = f" (~${consulta.monto_total_usd:,.2f} USD)" if consulta.monto_total_usd is not None else ""
        print(f"Monto Total:      ${consulta.monto_total:,} CLP{monto_usd_str}")
        print(f"Motivo:           {consulta.motivo or 'N/A'}")
        print(f"Inicio Atención:  {consulta.fecha_inicio_atencion or 'N/A'}")
        print(f"Fin Atención:     {consulta.fecha_fin_atencion or 'N/A'}")
        if consulta.detalle is not None:
            print(f"Detalle Médico:   ID {consulta.detalle.id_detalle}")
    except exceptions.EntidadNoEncontradaException as error:
        ui.mostrar_error(str(error))
    finally:
        ui.pausar()


def reagendar_consulta(consulta_service) -> None:
    ui.limpiar_y_encabezado("REAGENDAR CITA")
    id_consulta = ui.leer_entero("Ingrese ID de la consulta: ", nombre_campo="ID Consulta")

    try:
        consulta = consulta_service.obtener_consulta_por_id(id_consulta)
        print(f"\nMascota: {consulta.mascota.nombre} | Fecha actual: {consulta.fecha_agendada}")

        nueva_fecha = ui.leer_fecha("Ingrese nueva fecha y hora (YYYY-MM-DD HH:MM): ", nombre_campo="Nueva Fecha")

        if ui.desea_confirmar(f"¿Desea cambiar la fecha de la consulta ID:{consulta.id_consulta} de {consulta.mascota.nombre} a '{nueva_fecha}'?"):
            actualizada = consulta_service.reagendar_consulta(id_consulta=id_consulta, nueva_fecha=nueva_fecha)
            ui.mostrar_exito(f"Consulta ID:{actualizada.id_consulta} reagendada para {actualizada.fecha_agendada}.")
        else:
            print("\nOperación cancelada.")

    except (exceptions.EntidadNoEncontradaException, exceptions.ReglaNegocioError) as error:
        ui.mostrar_error(str(error))
    finally:
        ui.pausar()


def cancelar_consulta(consulta_service) -> None:
    ui.limpiar_y_encabezado("CANCELAR CONSULTA")
    id_consulta = ui.leer_entero("Ingrese ID de la consulta a cancelar: ", nombre_campo="ID Consulta")

    try:
        consulta = consulta_service.obtener_consulta_por_id(id_consulta)
        est_actual = consulta.estado.value
        print(f"\nMascota: {consulta.mascota.nombre} | Estado actual: {est_actual}")

        if ui.desea_confirmar(f"¿Confirma cancelar la consulta ID:{consulta.id_consulta} de {consulta.mascota.nombre}?"):
            actualizada = consulta_service.cancelar_consulta(id_consulta)
            ui.mostrar_exito(f"Consulta ID:{actualizada.id_consulta} cancelada correctamente.")
        else:
            print("\nOperación cancelada.")

    except (exceptions.EntidadNoEncontradaException, exceptions.ReglaNegocioError) as error:
        ui.mostrar_error(str(error))
    finally:
        ui.pausar()


# GESTIÓN DE LA ATENCIÓN ACTIVA

def ver_ficha_mascota(consulta_service, consulta_activa) -> None:
    """Despliega en modo solo lectura el historial de atenciones finalizadas de la mascota."""
    mascota = consulta_activa.mascota
    ui.limpiar_y_encabezado(f"FICHA MÉDICA - {mascota.nombre}")

    print(f"Nombre:        {mascota.nombre}")
    print(f"Especie:       {mascota.especie.nombre_especie if mascota.especie else 'N/A'}")
    print(f"Nacimiento:    {mascota.fecha_nacimiento}")
    print(f"Propietario:   {mascota.propietario.nombre_completo} (RUT: {mascota.propietario.rut})")

    try:
        consultas = consulta_service.listar_consultas_por_mascota(mascota.id_mascota)
    except exceptions.EntidadNoEncontradaException as error:
        ui.mostrar_error(str(error))
        ui.pausar()
        return

    finalizadas = [c for c in consultas if c.estado == EstadosConsulta.FINALIZADA]
    if not finalizadas:
        ui.mostrar_advertencia("La mascota no tiene atenciones finalizadas registradas.")
    else:
        for consulta in finalizadas:
            ui.mostrar_subtitulo(f"ATENCIÓN ID {consulta.id_consulta}")
            print(f"Fecha Agendada:   {consulta.fecha_agendada}")
            print(f"Inicio Atención:  {consulta.fecha_inicio_atencion or 'N/A'}")
            print(f"Fin Atención:     {consulta.fecha_fin_atencion or 'N/A'}")
            print(f"Motivo:           {consulta.motivo or 'N/A'}")

            if consulta.detalle is None:
                print("Detalle médico:   N/A")
                continue

            print(f"Veterinario:      {consulta.detalle.veterinario.nombre_completo} (RUT: {consulta.detalle.veterinario.rut})")
            print(f"Diagnóstico:      {consulta.detalle.diagnostico or 'N/A'}")

            try:
                recetas = consulta_service.listar_recetas_por_detalle(consulta.detalle.id_detalle)
            except exceptions.EntidadNoEncontradaException:
                recetas = []
            if recetas:
                imprimir_tabla_recetas(recetas)
            else:
                print("Recetas:          Sin recetas asociadas.")
    ui.pausar()


def gestionar_motivo(consulta_service, consulta_activa):
    ui.limpiar_y_encabezado("GESTIONAR MOTIVO DE LA CONSULTA")

    motivo_actual = consulta_activa.motivo
    if motivo_actual:
        print(f"\nMotivo registrado: {motivo_actual}")
        if not ui.desea_confirmar("¿Desea modificar el motivo registrado?"):
            return consulta_activa

    nuevo_motivo = ui.leer_texto("Ingrese el motivo de la consulta: ", max_longitud=200, nombre_campo="Motivo")

    try:
        actualizada = consulta_service.actualizar_motivo(consulta_activa.id_consulta, nuevo_motivo)
        ui.mostrar_exito("Motivo registrado exitosamente.")
        return actualizada
    except (exceptions.ReglaNegocioError, exceptions.EntradaInvalidaException) as error:
        ui.mostrar_error(str(error))
        return consulta_activa


def gestionar_diagnostico(consulta_service, detalle_activo):
    return gestionar_campo_detalle(
        consulta_service,
        detalle_activo,
        titulo="GESTIONAR DIAGNÓSTICO",
        mensaje="Ingrese el diagnóstico médico: ",
        nombre_campo="Diagnóstico",
        max_longitud=100,
        valor_actual=detalle_activo.diagnostico,
        metodo_actualizar=consulta_service.actualizar_diagnostico,
        mensaje_confirmacion="¿Desea modificar el diagnóstico registrado?"
    )


def gestionar_tratamiento(consulta_service, detalle_activo):
    return gestionar_campo_detalle(
        consulta_service,
        detalle_activo,
        titulo="GESTIONAR TRATAMIENTO",
        mensaje="Ingrese el tratamiento indicado: ",
        nombre_campo="Tratamiento",
        max_longitud=1000,
        valor_actual=detalle_activo.tratamiento,
        metodo_actualizar=consulta_service.actualizar_tratamiento,
        mensaje_confirmacion="¿Desea modificar el tratamiento registrado?"
    )


def gestionar_observaciones(consulta_service, detalle_activo):
    return gestionar_campo_detalle(
        consulta_service,
        detalle_activo,
        titulo="GESTIONAR OBSERVACIONES",
        mensaje="Ingrese las observaciones de la atención: ",
        nombre_campo="Observaciones",
        max_longitud=1000,
        valor_actual=detalle_activo.observaciones,
        metodo_actualizar=consulta_service.actualizar_observaciones,
        mensaje_confirmacion="¿Desea modificar las observaciones registradas?"
    )


def gestionar_campo_detalle(consulta_service, detalle_activo, titulo: str, mensaje: str, nombre_campo: str, max_longitud: int, valor_actual, metodo_actualizar, mensaje_confirmacion: str):
    ui.limpiar_y_encabezado(titulo)

    if valor_actual is not None:
        print(f"\n{nombre_campo} registrado: {valor_actual}")
        if not ui.desea_confirmar(mensaje_confirmacion):
            return detalle_activo

    nuevo_valor = ui.leer_texto(mensaje, max_longitud=max_longitud, nombre_campo=nombre_campo)

    try:
        actualizado = metodo_actualizar(detalle_activo.id_detalle, nuevo_valor)
        ui.mostrar_exito(f"{nombre_campo} registrado exitosamente.")
        return actualizado
    except (exceptions.ReglaNegocioError, exceptions.EntradaInvalidaException) as error:
        ui.mostrar_error(str(error))
        return detalle_activo


def agregar_receta(consulta_service, farmacia_service, detalle_activo) -> None:
    ui.limpiar_y_encabezado("AGREGAR RECETA MÉDICA")

    medicamentos = farmacia_service.listar_medicamentos()
    if not medicamentos:
        ui.mostrar_advertencia("No hay medicamentos registrados en la farmacia. Debe registrarlos antes de prescribir.")
        ui.pausar()
        return

    imprimir_catalogo_medicamentos(medicamentos)
    id_medicamento = ui.leer_entero("Ingrese ID del medicamento a prescribir: ", nombre_campo="ID Medicamento")
    cantidad = ui.leer_entero("Ingrese cantidad recetada: ", nombre_campo="Cantidad", minimo=1)
    instrucciones = ui.leer_texto("Ingrese instrucciones / posología: ", max_longitud=500, nombre_campo="Instrucciones")

    try:
        receta = consulta_service.registrar_receta(
            id_detalle=detalle_activo.id_detalle,
            id_medicamento=id_medicamento,
            cantidad=cantidad,
            instrucciones=instrucciones
        )
        ui.mostrar_exito(
            f"Receta ID:{receta.id_receta} agregada a la atención "
            f"({receta.medicamento.nombre_comercial} x{receta.cantidad})."
        )
    except (exceptions.EntidadNoEncontradaException, exceptions.ReglaNegocioError) as error:
        ui.mostrar_error(str(error))
    finally:
        ui.pausar()


def eliminar_receta(consulta_service, detalle_activo) -> None:
    ui.limpiar_y_encabezado("ELIMINAR RECETA MÉDICA")

    try:
        recetas = consulta_service.listar_recetas_por_detalle(detalle_activo.id_detalle)
    except exceptions.EntidadNoEncontradaException as error:
        ui.mostrar_error(str(error))
        ui.pausar()
        return

    if not recetas:
        ui.mostrar_advertencia("No hay recetas asociadas a esta atención.")
        ui.pausar()
        return

    imprimir_tabla_recetas(recetas)
    id_receta = ui.leer_entero("Ingrese el ID de la receta a eliminar (0 para cancelar): ", nombre_campo="ID Receta", minimo=0)
    if id_receta == 0:
        print("\nOperación cancelada.")
        ui.pausar()
        return

    seleccionada = next((r for r in recetas if r.id_receta == id_receta), None)
    if seleccionada is None:
        ui.mostrar_advertencia(f"El ID {id_receta} no corresponde a ninguna receta listada.")
        ui.pausar()
        return

    if ui.desea_confirmar(
        f"¿Confirma eliminar la receta ID:{seleccionada.id_receta} "
        f"({seleccionada.medicamento.nombre_comercial} x{seleccionada.cantidad})?"
    ):
        try:
            consulta_service.remover_receta(id_receta)
            ui.mostrar_exito("Receta eliminada correctamente.")
        except exceptions.EntidadNoEncontradaException as error:
            ui.mostrar_error(str(error))
    else:
        print("\nOperación cancelada.")
    ui.pausar()


def ver_resumen_atencion(consulta_service, consulta_activa, detalle_activo) -> None:
    ui.limpiar_y_encabezado(f"RESUMEN DE LA ATENCIÓN - CONSULTA ID:{consulta_activa.id_consulta}")

    print(f"Mascota:       {consulta_activa.mascota.nombre}")
    print(f"Propietario:   {consulta_activa.mascota.propietario.nombre_completo} (RUT: {consulta_activa.mascota.propietario.rut})")
    print(f"Veterinario:   {detalle_activo.veterinario.nombre_completo} (RUT: {detalle_activo.veterinario.rut})")
    print(f"Motivo:        {consulta_activa.motivo or 'N/A'}")
    print(f"Diagnóstico:   {detalle_activo.diagnostico or 'N/A'}")
    print(f"Tratamiento:   {detalle_activo.tratamiento or 'N/A'}")
    print(f"Observaciones: {detalle_activo.observaciones or 'N/A'}")

    try:
        recetas = consulta_service.listar_recetas_por_detalle(detalle_activo.id_detalle)
    except exceptions.EntidadNoEncontradaException:
        recetas = []
    if recetas:
        imprimir_tabla_recetas(recetas)
    else:
        print("Recetas:       Sin recetas asociadas.")
    ui.pausar()


def pausar_atencion(consulta_service, consulta_activa) -> bool:
    if not ui.desea_confirmar(
        f"¿Desea pausar la atención de '{consulta_activa.mascota.nombre}' y ponerla en espera?"
    ):
        return False

    try:
        consulta_service.poner_en_espera(consulta_activa.id_consulta)
        ui.mostrar_exito("Atención pausada: la consulta quedó en espera de exámenes.")
        return True
    except exceptions.ReglaNegocioError as error:
        ui.mostrar_error(str(error))
        return False


def finalizar_atencion(consulta_service, consulta_activa, detalle_activo) -> bool:
    ui.limpiar_y_encabezado("FINALIZAR ATENCIÓN")

    campos_pendientes = []
    if not consulta_activa.motivo:
        campos_pendientes.append("Motivo")
    if detalle_activo.diagnostico is None:
        campos_pendientes.append("Diagnóstico")
    if detalle_activo.tratamiento is None:
        campos_pendientes.append("Tratamiento")
    if detalle_activo.observaciones is None:
        campos_pendientes.append("Observaciones")

    if campos_pendientes:
        ui.mostrar_advertencia(
            "No se puede finalizar la atención. Campos pendientes: "
            + ", ".join(campos_pendientes)
        )
        ui.pausar()
        return False

    if not ui.desea_confirmar(
        f"¿Confirma finalizar la atención de '{consulta_activa.mascota.nombre}' (Consulta ID:{consulta_activa.id_consulta})?"
    ):
        return False

    try:
        consulta_service.finalizar_atencion(consulta_activa.id_consulta)
        ui.mostrar_exito("Atención finalizada correctamente.")
        return True
    except exceptions.ReglaNegocioError as error:
        ui.mostrar_error(str(error))
        return False


def imprimir_catalogo_medicamentos(medicamentos: list) -> None:
    print(f"\n{'ID':<6} | {'NOMBRE COMERCIAL':<30} | {'PRECIO':<12} | {'STOCK':<8}")
    print("-" * 62)
    for m in medicamentos:
        print(f"{m.id_medicamento:<6} | {m.nombre_comercial:<30} | {ui.formatear_moneda(m.precio):<12} | {m.stock:<8}")


# =============================================================================
# FUNCIONES AUXILIARES DE TABLAS Y VISTAS
# =============================================================================

def listar_todas_consultas(consulta_service) -> None:
    consultas = consulta_service.listar_consultas()
    if not consultas:
        ui.mostrar_advertencia("No hay consultas registradas.")
    else:
        imprimir_tabla_consultas(consultas)
    ui.pausar()


def listar_consultas_por_mascota(consulta_service) -> None:
    id_mascota = ui.leer_entero("Ingrese ID de la mascota: ", nombre_campo="ID Mascota")
    try:
        consultas = consulta_service.listar_consultas_por_mascota(id_mascota)
        if not consultas:
            ui.mostrar_advertencia(f"La mascota ID:{id_mascota} no posee consultas registradas.")
        else:
            imprimir_tabla_consultas(consultas)
    except exceptions.EntidadNoEncontradaException as error:
        ui.mostrar_error(str(error))
    finally:
        ui.pausar()


def listar_consultas_por_veterinario(consulta_service) -> None:
    rut_vet = ui.leer_rut("Ingrese RUT del veterinario: ")
    try:
        consultas = consulta_service.listar_consultas_por_veterinario(rut_vet)
        if not consultas:
            ui.mostrar_advertencia(f"El veterinario RUT:{rut_vet} no posee atenciones registradas.")
        else:
            imprimir_tabla_consultas(consultas)
    except exceptions.EntidadNoEncontradaException as error:
        ui.mostrar_error(str(error))
    finally:
        ui.pausar()


def listar_consultas_por_estado(consulta_service) -> None:
    ui.limpiar_y_encabezado("FILTRAR CONSULTAS POR ESTADO")
    estados = list(EstadosConsulta)
    for idx, est in enumerate(estados, start=1):
        lbl = est.value
        print(f"{idx}. {lbl}")

    opcion = ui.leer_entero("Seleccione estado: ", nombre_campo="Estado", minimo=1, maximo=len(estados))
    estado_sel = estados[opcion - 1]

    consultas = consulta_service.listar_consultas_por_estado(estado_sel)
    if not consultas:
        lbl_sel = estado_sel.value
        ui.mostrar_advertencia(f"No hay consultas en estado '{lbl_sel}'.")
    else:
        imprimir_tabla_consultas(consultas)
    ui.pausar()


def listar_todos_detalles(consulta_service) -> None:
    detalles = consulta_service.listar_detalles()
    if not detalles:
        ui.mostrar_advertencia("No hay detalles médicos registrados en el sistema.")
    else:
        imprimir_tabla_detalles(detalles)
    ui.pausar()


def buscar_detalles_por_veterinario(consulta_service) -> None:
    rut_vet = ui.leer_rut("Ingrese RUT del veterinario: ")
    try:
        detalles = consulta_service.buscar_detalle_por_veterinario(rut_vet)
        if not detalles:
            ui.mostrar_advertencia(f"El veterinario RUT:{rut_vet} no posee detalles médicos registrados.")
        else:
            imprimir_tabla_detalles(detalles)
    except exceptions.EntidadNoEncontradaException as error:
        ui.mostrar_error(str(error))
    finally:
        ui.pausar()


def listar_todas_recetas(consulta_service) -> None:
    recetas = consulta_service.listar_recetas()
    if not recetas:
        ui.mostrar_advertencia("No hay recetas médicas registradas en el sistema.")
    else:
        imprimir_tabla_recetas(recetas)
    ui.pausar()


def listar_recetas_de_detalle(consulta_service) -> None:
    id_detalle = ui.leer_entero("Ingrese ID del detalle médico: ", nombre_campo="ID Detalle")
    try:
        recetas = consulta_service.listar_recetas_por_detalle(id_detalle)
        if not recetas:
            ui.mostrar_advertencia(f"El detalle ID:{id_detalle} no tiene recetas asociadas.")
        else:
            imprimir_tabla_recetas(recetas)
    except exceptions.EntidadNoEncontradaException as error:
        ui.mostrar_error(str(error))
    finally:
        ui.pausar()


def buscar_recetas_por_medicamento(consulta_service) -> None:
    nombre_med = ui.leer_nombre_alfabetico("Ingrese nombre del medicamento: ", nombre_campo="Medicamento")
    recetas = consulta_service.buscar_recetas_por_medicamento(nombre_med)

    if not recetas:
        ui.mostrar_advertencia(f"No se encontraron recetas para '{nombre_med}'.")
    else:
        imprimir_tabla_recetas(recetas)
    ui.pausar()


def obtener_detalle_por_id(consulta_service) -> None:
    id_det = ui.leer_entero("Ingrese ID del detalle médico: ", nombre_campo="ID Detalle")
    try:
        d = consulta_service.obtener_detalle_por_id(id_det)
        ui.mostrar_subtitulo("DETALLE MÉDICO DE LA CONSULTA")
        print(f"ID Detalle:    {d.id_detalle}")
        print(f"ID Consulta:   {d.consulta.id_consulta}")
        print(f"Mascota:       {d.consulta.mascota.nombre}")
        print(f"Veterinario:   {d.veterinario.nombre_completo} (RUT: {d.veterinario.rut})")
        print(f"Diagnóstico:   {d.diagnostico or 'N/A'}")
        print(f"Tratamiento:   {d.tratamiento or 'N/A'}")
        print(f"Observaciones: {d.observaciones or 'N/A'}")
    except exceptions.EntidadNoEncontradaException as error:
        ui.mostrar_error(str(error))
    finally:
        ui.pausar()


def imprimir_tabla_consultas(consultas: list) -> None:
    print(f"\n{'ID':<6} | {'TIPO':<8} | {'MASCOTA':<18} | {'FECHA AGENDADA':<19} | {'ESTADO':<15} | {'TOTAL (CLP)':<12}")
    print("-" * 88)
    for c in consultas:
        est_str = c.estado.value
        tipo_str = "URGENCIA" if c.es_urgencia else "NORMAL"
        print(f"{c.id_consulta:<6} | {tipo_str:<8} | {c.mascota.nombre:<18} | {str(c.fecha_agendada):<19} | {est_str:<15} | ${c.monto_total:<11,}")


def imprimir_tabla_detalles(detalles: list) -> None:
    print(f"\n{'ID DET.':<8} | {'ID CONS.':<9} | {'MASCOTA':<20} | {'VETERINARIO':<25} | {'DIAGNÓSTICO':<25}")
    print("-" * 92)
    for d in detalles:
        mascota = d.consulta.mascota.nombre if d.consulta.mascota else "N/A"
        print(f"{d.id_detalle:<8} | {d.consulta.id_consulta:<9} | {mascota:<20} | {d.veterinario.nombre_completo:<25} | {(d.diagnostico or 'N/A'):<25}")


def imprimir_tabla_recetas(recetas: list) -> None:
    print(f"\n{'ID REC.':<8} | {'ID DET.':<8} | {'MEDICAMENTO':<22} | {'CANT.':<6} | {'INSTRUCCIONES':<35}")
    print("-" * 85)
    for r in recetas:
        print(f"{r.id_receta:<8} | {r.detalle.id_detalle:<8} | {r.medicamento.nombre_comercial:<22} | {r.cantidad:<6} | {r.instrucciones:<35}")