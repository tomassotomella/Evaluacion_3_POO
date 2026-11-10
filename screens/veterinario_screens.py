from utilities import interfaz as ui
from exceptions import exceptions


def main_veterinarios(persona_service) -> None:
    """Menú Principal del Módulo de Veterinarios y Especialidades."""
    while True:
        ui.limpiar_y_encabezado("GESTIÓN DE VETERINARIOS Y ESPECIALIDADES")
        print('''
        1. Gestionar Veterinarios
        2. Gestionar Especialidades
        0. Volver al Menú Principal
        ''')
        opcion = ui.leer_opcion_menu(2)
        match opcion:
            case 1:
                submenu_veterinarios(persona_service)
            case 2:
                submenu_especialidades(persona_service)
            case 0:
                break


# SUBMENÚ 1: GESTIÓN DE VETERINARIOS

def submenu_veterinarios(persona_service) -> None:
    while True:
        ui.limpiar_y_encabezado("GESTIÓN DE VETERINARIOS")
        print('''
        1. Registrar Veterinario
        2. Visualizar Veterinarios
        3. Actualizar datos de Veterinario
        4. Eliminar Veterinario
        0. Volver
        ''')
        opcion = ui.leer_opcion_menu(4)
        match opcion:
            case 1:
                registrar_veterinario(persona_service)
            case 2:
                visualizar_veterinarios(persona_service)
            case 3:
                actualizar_veterinario(persona_service)
            case 4:
                eliminar_veterinario(persona_service)
            case 0:
                break


# =============================================================================
# SUBMENÚ 2: GESTIÓN DE ESPECIALIDADES
# =============================================================================

def submenu_especialidades(persona_service) -> None:
    while True:
        ui.limpiar_y_encabezado("GESTIÓN DE ESPECIALIDADES")
        print('''
        1. Registrar Especialidad
        2. Listar Especialidades
        3. Actualizar Descripción
        4. Eliminar Especialidad
        0. Volver
        ''')
        opcion = ui.leer_opcion_menu(4)
        match opcion:
            case 1:
                registrar_especialidad(persona_service)
            case 2:
                listar_especialidades(persona_service)
            case 3:
                actualizar_descripcion_especialidad(persona_service)
            case 4:
                eliminar_especialidad(persona_service)
            case 0:
                break


# ACCIONES DE VETERINARIOS

def registrar_veterinario(persona_service) -> None:
    ui.limpiar_y_encabezado("REGISTRAR VETERINARIO")

    especialidades = persona_service.listar_especialidades()
    if not especialidades:
        ui.mostrar_advertencia(
            "No hay especialidades registradas en el sistema. "
            "Debe registrar al menos una especialidad antes de ingresar un veterinario."
        )
        ui.pausar()
        return

    rut = ui.leer_rut()
    nombre_completo = ui.leer_nombre_alfabetico(prompt="Ingrese Nombre Completo: ", nombre_campo="Nombre Completo")
    telefono = ui.leer_telefono()

    imprimir_tabla_especialidades(especialidades)
    id_especialidad = ui.leer_entero("Seleccione el ID de la especialidad: ", nombre_campo="ID Especialidad")

    try:
        vet = persona_service.registrar_veterinario(
            rut=rut,
            nombre_completo=nombre_completo,
            telefono=telefono,
            id_especialidad=id_especialidad
        )
        ui.mostrar_exito(
            f"Veterinario '{vet.nombre_completo}' (RUT: {vet.rut}) "
            f"registrado con éxito en '{vet.especialidad.nombre_especialidad}'."
        )
    except (exceptions.EntidadExistenteException, exceptions.EntidadNoEncontradaException, exceptions.ReglaNegocioError) as error:
        ui.mostrar_error(str(error))
    finally:
        ui.pausar()


def visualizar_veterinarios(persona_service) -> None:
    while True:
        ui.limpiar_y_encabezado("CONSULTAR VETERINARIOS")
        print('''
        1. Buscar por RUT
        2. Buscar por Nombre
        3. Listar Todos los Veterinarios
        0. Volver
        ''')
        opcion = ui.leer_opcion_menu(3)
        match opcion:
            case 1:
                buscar_vet_por_rut(persona_service)
            case 2:
                buscar_vet_por_nombre(persona_service)
            case 3:
                listar_todos_veterinarios(persona_service)
            case 0:
                break


def actualizar_veterinario(persona_service) -> None:
    while True:
        ui.limpiar_y_encabezado("ACTUALIZAR DATOS DE VETERINARIO")
        print('''
        1. Cambiar Nombre Completo
        2. Cambiar Teléfono de Contacto
        3. Cambiar Especialidad
        0. Volver
        ''')
        opcion = ui.leer_opcion_menu(3)
        match opcion:
            case 1:
                cambiar_nombre_vet(persona_service)
            case 2:
                cambiar_contacto_vet(persona_service)
            case 3:
                cambiar_especialidad_vet(persona_service)
            case 0:
                break


def eliminar_veterinario(persona_service) -> None:
    ui.limpiar_y_encabezado("ELIMINAR VETERINARIO")
    ui.mostrar_advertencia("Nota: Solo se pueden eliminar veterinarios sin detalles asociados.")

    rut = ui.leer_rut("\nIngrese RUT del veterinario a eliminar: ")

    try:
        vet = persona_service.obtener_veterinario_por_rut(rut)

        if ui.desea_confirmar(f"¿Está seguro de eliminar al Dr(a). '{vet.nombre_completo}'?"):
            id_vet = vet.id_veterinario
            persona_service.eliminar_veterinario(id_vet)
            ui.mostrar_exito("Veterinario eliminado correctamente.")
        else:
            print("\nOperación cancelada.")

    except exceptions.EntidadNoEncontradaException as error:
        ui.mostrar_error(str(error))
    except (exceptions.ReferenciaIntegridadError, exceptions.ReglaNegocioError):
        ui.mostrar_advertencia(
            f"No es posible eliminar al veterinario '{vet.nombre_completo}' "
            f"porque posee detalles asociados."
        )
    finally:
        ui.pausar()


# ACCIONES DE ESPECIALIDADES

def registrar_especialidad(persona_service) -> None:
    ui.limpiar_y_encabezado("REGISTRAR ESPECIALIDAD")
    nombre = ui.leer_nombre_alfabetico(prompt="Ingrese nombre de la especialidad: ", nombre_campo="Especialidad", maximo=100)
    descripcion = ui.leer_texto(prompt="Ingrese descripción breve: ", max_longitud=100, nombre_campo="Descripción")

    try:
        esp = persona_service.registrar_especialidad(nombre=nombre, descripcion=descripcion)
        ui.mostrar_exito(f"Especialidad '{esp.nombre_especialidad}' registrada correctamente.")
    except (exceptions.EntidadExistenteException, exceptions.ReglaNegocioError) as error:
        ui.mostrar_error(str(error))
    finally:
        ui.pausar()


def listar_especialidades(persona_service) -> None:
    ui.limpiar_y_encabezado("LISTA DE ESPECIALIDADES")
    especialidades = persona_service.listar_especialidades()
    if not especialidades:
        ui.mostrar_advertencia("No hay especialidades registradas.")
    else:
        imprimir_tabla_especialidades(especialidades)
    ui.pausar()


def eliminar_especialidad(persona_service) -> None:
    ui.limpiar_y_encabezado("ELIMINAR ESPECIALIDAD")
    ui.mostrar_advertencia("Nota: Solo se pueden eliminar especialidades sin veterinarios asociados.")

    especialidades = persona_service.listar_especialidades()
    if not especialidades:
        ui.mostrar_advertencia("No hay especialidades registradas.")
        ui.pausar()
        return

    imprimir_tabla_especialidades(especialidades)
    id_especialidad = ui.leer_entero("Ingrese el ID de la especialidad a eliminar: ", nombre_campo="ID Especialidad")

    try:
        esp = persona_service.obtener_especialidad(id_especialidad)

        if ui.desea_confirmar(f"¿Está seguro de eliminar la especialidad '{esp.nombre_especialidad}'?"):
            persona_service.eliminar_especialidad(esp.id_especialidad)
            ui.mostrar_exito("Especialidad eliminada correctamente.")
        else:
            print("\nOperación cancelada.")

    except exceptions.EntidadNoEncontradaException as error:
        ui.mostrar_error(str(error))
    except (exceptions.ReferenciaIntegridadError, exceptions.ReglaNegocioError) as error:
        ui.mostrar_advertencia(
            f"No es posible eliminar la especialidad '{esp.nombre_especialidad}': {error}"
        )
    finally:
        ui.pausar()


def actualizar_descripcion_especialidad(persona_service) -> None:
    ui.limpiar_y_encabezado("ACTUALIZAR DESCRIPCIÓN DE ESPECIALIDAD")

    especialidades = persona_service.listar_especialidades()
    if not especialidades:
        ui.mostrar_advertencia("No hay especialidades registradas.")
        ui.pausar()
        return

    imprimir_tabla_especialidades(especialidades)
    id_especialidad = ui.leer_entero(
        "\nIngrese el ID de la especialidad a modificar: ",
        nombre_campo="ID Especialidad"
    )

    try:
        esp = persona_service.obtener_especialidad(id_especialidad)
        print(f"\nEspecialidad: {esp.nombre_especialidad}")
        print(f"Descripción actual: {esp.descripcion}")

        nueva_descripcion = ui.leer_texto(
            "Ingrese la nueva descripción: ",
            max_longitud=100,
            nombre_campo="Descripción",
        )
        actualizada = persona_service.actualizar_descripcion_especialidad(
            id_especialidad=esp.id_especialidad,
            nueva_descripcion=nueva_descripcion,
        )
        ui.mostrar_exito(
            f"Descripción actualizada exitosamente a '{actualizada.descripcion}'."
        )
    except (
        exceptions.EntidadNoEncontradaException,
        exceptions.ReglaNegocioError,
        exceptions.EntradaInvalidaException,
    ) as error:
        ui.mostrar_error(str(error))
    finally:
        ui.pausar()


# FUNCIONES AUXILIARES DE BÚSQUEDA Y FORMATO

def buscar_vet_por_rut(persona_service) -> None:
    rut = ui.leer_rut("Ingrese RUT del veterinario: ")
    try:
        vet = persona_service.obtener_veterinario_por_rut(rut)
        id_vet = vet.id_veterinario
        ui.mostrar_subtitulo("INFORMACIÓN DEL VETERINARIO")
        print(f"ID:           {id_vet}")
        print(f"RUT:          {vet.rut}")
        print(f"Nombre:       {vet.nombre_completo}")
        print(f"Teléfono:     {vet.telefono}")
        print(f"Especialidad: {vet.especialidad.nombre_especialidad}")
    except exceptions.EntidadNoEncontradaException as error:
        ui.mostrar_error(str(error))
    finally:
        ui.pausar()


def buscar_vet_por_nombre(persona_service) -> None:
    nombre = ui.leer_nombre_alfabetico("Ingrese coincidencia de nombre a buscar: ", nombre_campo="Nombre")
    vets = persona_service.buscar_veterinarios(nombre)

    if not vets:
        ui.mostrar_advertencia(f"No se encontraron veterinarios que coincidan con '{nombre}'.")
    else:
        imprimir_tabla_veterinarios(vets)
    ui.pausar()


def listar_todos_veterinarios(persona_service) -> None:
    vets = persona_service.listar_veterinarios()
    if not vets:
        ui.mostrar_advertencia("No hay veterinarios registrados en el sistema.")
    else:
        imprimir_tabla_veterinarios(vets)
    ui.pausar()


def cambiar_nombre_vet(persona_service) -> None:
    rut = ui.leer_rut("Ingrese RUT del veterinario: ")
    try:
        vet = persona_service.obtener_veterinario_por_rut(rut)
        print(f"\nNombre actual: {vet.nombre_completo}")

        nuevo_nombre = ui.leer_nombre_alfabetico("Ingrese nuevo Nombre Completo: ", nombre_campo="Nuevo Nombre")
        actualizado = persona_service.cambiar_nombre_veterinario(rut=rut, nuevo_nombre=nuevo_nombre)
        ui.mostrar_exito(f"Nombre actualizado a '{actualizado.nombre_completo}'.")
    except (exceptions.EntidadNoEncontradaException, exceptions.ReglaNegocioError) as error:
        ui.mostrar_error(str(error))
    finally:
        ui.pausar()


def cambiar_contacto_vet(persona_service) -> None:
    rut = ui.leer_rut("Ingrese RUT del veterinario: ")
    try:
        vet = persona_service.obtener_veterinario_por_rut(rut)
        print(f"\nVeterinario: {vet.nombre_completo}")
        print(f"Teléfono actual: {vet.telefono}")

        nuevo_tel = ui.leer_telefono("Ingrese nuevo Teléfono: ")
        actualizado = persona_service.cambiar_contacto_veterinario(rut=rut, nuevo_telefono=nuevo_tel)
        ui.mostrar_exito(f"Teléfono actualizado a '{actualizado.telefono}'.")
    except (exceptions.EntidadNoEncontradaException, exceptions.ReglaNegocioError) as error:
        ui.mostrar_error(str(error))
    finally:
        ui.pausar()


def cambiar_especialidad_vet(persona_service) -> None:
    rut = ui.leer_rut("Ingrese RUT del veterinario: ")
    try:
        vet = persona_service.obtener_veterinario_por_rut(rut)
        print(f"\nVeterinario: {vet.nombre_completo}")
        print(f"Especialidad actual: {vet.especialidad.nombre_especialidad if vet.especialidad else 'Sin asignar'}")

        especialidades = persona_service.listar_especialidades()
        if not especialidades:
            ui.mostrar_advertencia("No hay especialidades disponibles.")
            return

        imprimir_tabla_especialidades(especialidades)
        id_nueva_esp = ui.leer_entero("Ingrese el ID de la nueva especialidad: ", nombre_campo="ID Especialidad")

        actualizado = persona_service.cambiar_especialidad_veterinario(rut=rut, id_especialidad=id_nueva_esp)
        ui.mostrar_exito(f"Especialidad actualizada a '{actualizado.especialidad.nombre_especialidad}'.")
    except (exceptions.EntidadNoEncontradaException, exceptions.ReglaNegocioError) as error:
        ui.mostrar_error(str(error))
    finally:
        ui.pausar()


def imprimir_tabla_veterinarios(vets: list) -> None:
    print(f"\n{'ID':<6} | {'RUT':<12} | {'NOMBRE COMPLETO':<30} | {'TELÉFONO':<15} | {'ESPECIALIDAD':<20}")
    print("-" * 90)
    for v in vets:
        print(f"{str(v.id_veterinario):<6} | {v.rut:<12} | {v.nombre_completo:<30} | {v.telefono:<15} | {v.especialidad.nombre_especialidad:<20}")


def imprimir_tabla_especialidades(especialidades: list) -> None:
    print(f"\n{'ID':<6} | {'ESPECIALIDAD':<25} | {'DESCRIPCIÓN':<40}")
    print("-" * 77)
    for e in especialidades:
        print(f"{str(e.id_especialidad):<6} | {e.nombre_especialidad:<25} | {e.descripcion:<40}")