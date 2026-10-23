from utilities import interfaz as ui
from exceptions import exceptions


def main_propietarios(persona_service) -> None:
    """Menú principal del módulo de gestión de propietarios."""
    while True:
        ui.limpiar_y_encabezado("GESTIÓN DE PROPIETARIOS")
        print('''
        1. Registrar Propietario
        2. Ver Propietarios
        3. Actualizar datos
        4. Eliminar Propietario
        0. Volver
        ''')
        opcion = ui.leer_opcion_menu(4)
        match opcion:
            case 1:
                subflujo_registrar(persona_service)
            case 2:
                subflujo_visualizar(persona_service)
            case 3:
                subflujo_actualizar(persona_service)
            case 4:
                subflujo_eliminar(persona_service)
            case 0:
                break


# SUBFLUJOS PRINCIPALES

def subflujo_registrar(persona_service) -> None:
    ui.limpiar_y_encabezado("REGISTRAR PROPIETARIO")
    rut = ui.leer_rut()
    nombre_completo = ui.leer_nombre_alfabetico()
    telefono = ui.leer_telefono()

    try:
        propietario = persona_service.registrar_propietario(
            rut=rut,
            nombre_completo=nombre_completo,
            telefono=telefono
        )
        ui.mostrar_exito(
            f"Propietario con Nombre: {propietario.nombre_completo} "
            f"y RUT: {propietario.rut} registrado exitosamente"
        )
    except (exceptions.EntidadExistenteException, exceptions.ReglaNegocioError) as error:
        ui.mostrar_error(str(error))
    finally:
        ui.pausar()


def subflujo_visualizar(persona_service) -> None:
    while True:
        ui.limpiar_y_encabezado("CONSULTAR PROPIETARIOS")
        print('''
        1. Buscar por RUT
        2. Buscar por Nombre
        3. Listar Todos los Propietarios
        0. Volver
        ''')
        opcion = ui.leer_opcion_menu(3)
        match opcion:
            case 1:
                buscar_por_rut(persona_service)
            case 2:
                buscar_por_nombre(persona_service)
            case 3:
                listar_todos(persona_service)
            case 0:
                break


def subflujo_actualizar(persona_service) -> None:
    while True:
        ui.limpiar_y_encabezado("ACTUALIZAR DATOS DE PROPIETARIO")
        print('''
        1. Cambiar Nombre Completo
        2. Cambiar Teléfono de Contacto
        0. Volver
        ''')
        opcion = ui.leer_opcion_menu(2)
        match opcion:
            case 1:
                cambiar_nombre(persona_service)
            case 2:
                cambiar_contacto(persona_service)
            case 0:
                break


def subflujo_eliminar(persona_service) -> None:
    ui.limpiar_y_encabezado("ELIMINAR PROPIETARIO")
    rut = ui.leer_rut("Ingrese RUT del propietario a eliminar: ")
    ui.mostrar_advertencia("Nota: Solo se pueden eliminar propietarios que NO tengan mascotas registradas.")

    try:
        propietario = persona_service.obtener_propietario_por_rut(rut)
        if ui.leer_confirmacion("¿Está seguro de eliminar a este propietario?"):
            persona_service.eliminar_propietario(propietario.id_propietario)
            ui.mostrar_exito("Propietario eliminado correctamente.")
        else:
            print("\nOperación cancelada.")
    except (exceptions.EntidadNoEncontradaException, exceptions.ReferenciaIntegridadError) as error:
        ui.mostrar_error(str(error))
    finally:
        ui.pausar()


# FUNCIONES  DE APOYO

def buscar_por_rut(persona_service) -> None:
    rut = ui.leer_rut("Ingrese RUT a buscar: ")
    try:
        propietario = persona_service.obtener_propietario_por_rut(rut)
        ui.mostrar_subtitulo("INFORMACIÓN DEL PROPIETARIO")
        print(f"ID:              {propietario.id_propietario or 'N/A'}")
        print(f"RUT:             {propietario.rut}")
        print(f"Nombre Completo: {propietario.nombre_completo}")
        print(f"Teléfono:        {propietario.telefono}")
    except exceptions.EntidadNoEncontradaException as error:
        ui.mostrar_error(str(error))
    finally:
        ui.pausar()


def buscar_por_nombre(persona_service) -> None:
    nombre = ui.leer_nombre_alfabetico("Ingrese coincidencia de nombre a buscar: ")
    propietarios = persona_service.buscar_propietarios(nombre)

    if not propietarios:
        ui.mostrar_advertencia(f"No se encontraron propietarios que coincidan con '{nombre}'.")
    else:
        imprimir_tabla_propietarios(propietarios)
    ui.pausar()


def listar_todos(persona_service) -> None:
    propietarios = persona_service.listar_propietarios()

    if not propietarios:
        ui.mostrar_advertencia("No hay propietarios registrados en el sistema.")
    else:
        imprimir_tabla_propietarios(propietarios)
    ui.pausar()


def cambiar_nombre(persona_service) -> None:
    rut = ui.leer_rut("Ingrese RUT del propietario: ")
    try:
        propietario = persona_service.obtener_propietario_por_rut(rut)
        print(f"\nNombre actual: {propietario.nombre_completo}")

        nuevo_nombre = ui.leer_nombre_alfabetico("Ingrese el nuevo Nombre Completo: ")
        actualizado = persona_service.cambiar_nombre_propietario(
            rut=rut,
            nuevo_nombre=nuevo_nombre
        )
        ui.mostrar_exito(f"Nombre actualizado exitosamente a '{actualizado.nombre_completo}'.")
    except (exceptions.EntidadNoEncontradaException, exceptions.ReglaNegocioError) as error:
        ui.mostrar_error(str(error))
    finally:
        ui.pausar()


def cambiar_contacto(persona_service) -> None:
    rut = ui.leer_rut("Ingrese RUT del propietario: ")
    try:
        propietario = persona_service.obtener_propietario_por_rut(rut)
        print(f"\nPropietario: {propietario.nombre_completo}")
        print(f"Teléfono actual: {propietario.telefono}")

        nuevo_telefono = ui.leer_telefono("Ingrese el nuevo Teléfono: ")
        actualizado = persona_service.cambiar_contacto_propietario(
            rut=rut,
            nuevo_telefono=nuevo_telefono
        )
        ui.mostrar_exito(f"Teléfono actualizado exitosamente a '{actualizado.telefono}'.")
    except (exceptions.EntidadNoEncontradaException, exceptions.ReglaNegocioError) as error:
        ui.mostrar_error(str(error))
    finally:
        ui.pausar()


def imprimir_tabla_propietarios(propietarios: list) -> None:
    print(f"\n{'ID':<6} | {'RUT':<12} | {'NOMBRE COMPLETO':<35} | {'TELÉFONO':<15}")
    print("-" * 75)
    for p in propietarios:
        print(f"{str(p.id_propietario):<6} | {p.rut:<12} | {p.nombre_completo:<35} | {p.telefono:<15}")