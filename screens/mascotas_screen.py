from utilities import interfaz as ui
from exceptions import exceptions


def main_mascotas(mascota_service) -> None:
    """Menú Principal del Módulo de Mascotas y Especies."""
    while True:
        ui.limpiar_y_encabezado("GESTIÓN DE MASCOTAS Y ESPECIES")
        print('''
        1. Gestionar Mascotas
        2. Gestionar Especies
        0. Volver al Menú Principal
        ''')
        opcion = ui.leer_opcion_menu(2)
        match opcion:
            case 1:
                submenu_mascotas(mascota_service)
            case 2:
                submenu_especies(mascota_service)
            case 0:
                break
            
# SUBMENÚ 1: GESTIÓN DE MASCOTAS

def submenu_mascotas(mascota_service) -> None:
    while True:
        ui.limpiar_y_encabezado("GESTIÓN DE MASCOTAS")
        print('''
        1. Registrar Mascota
        2. Ver / Buscar Mascotas
        3. Actualizar Datos de Mascota
        4. Eliminar Mascota
        0. Volver
        ''')
        opcion = ui.leer_opcion_menu(4)
        match opcion:
            case 1:
                registrar_mascota(mascota_service)
            case 2:
                visualizar_mascotas(mascota_service)
            case 3:
                actualizar_mascota(mascota_service)
            case 4:
                eliminar_mascota(mascota_service)
            case 0:
                break


# SUBMENÚ 2: GESTIÓN DE ESPECIES

def submenu_especies(mascota_service) -> None:
    while True:
        ui.limpiar_y_encabezado("GESTIÓN DE ESPECIES")
        print('''
        1. Registrar Especie
        2. Listar Especies
        3. Cambiar Nombre de Especie
        0. Volver
        ''')
        opcion = ui.leer_opcion_menu(3)
        match opcion:
            case 1:
                registrar_especie(mascota_service)
            case 2:
                listar_especies(mascota_service)
            case 3:
                cambiar_nombre_especie(mascota_service)
            case 0:
                break

# ACCIONES DE MASCOTAS

def registrar_mascota(mascota_service) -> None:
    ui.limpiar_y_encabezado("REGISTRAR MASCOTA")

    especies = mascota_service.listar_especies()
    if not especies:
        ui.mostrar_advertencia("No hay especies registradas. Debe registrar al menos una especie primero.")
        ui.pausar()
        return

    rut_propietario = ui.leer_rut("Ingrese RUT del propietario responsable: ")
    nombre = ui.leer_nombre_alfabetico("Ingrese nombre de la mascota: ", nombre_campo="Nombre Mascota", maximo=100)
    fecha_nac = ui.leer_fecha("Ingrese fecha de nacimiento (YYYY-MM-DD): ", nombre_campo="Fecha Nacimiento")

    imprimir_tabla_especies(especies)
    id_especie = ui.leer_entero("Seleccione el ID de la especie: ", nombre_campo="ID Especie")

    try:
        mascota = mascota_service.registrar_mascota(
            nombre=nombre,
            fecha_nacimiento=fecha_nac,
            id_especie=id_especie,
            rut_propietario=rut_propietario
        )
        ui.mostrar_exito(f"Mascota '{mascota.nombre}' registrada exitosamente.")
    except (exceptions.EntidadNoEncontradaException, exceptions.ReglaNegocioError) as error:
        ui.mostrar_error(str(error))
    finally:
        ui.pausar()


def visualizar_mascotas(mascota_service) -> None:
    while True:
        ui.limpiar_y_encabezado("CONSULTAR MASCOTAS")
        print('''
        1. Buscar por Nombre
        2. Buscar por RUT de Propietario
        3. Listar Todas las Mascotas
        0. Volver
        ''')
        opcion = ui.leer_opcion_menu(3)
        match opcion:
            case 1:
                buscar_por_nombre(mascota_service)
            case 2:
                buscar_por_propietario(mascota_service)
            case 3:
                listar_todas_mascotas(mascota_service)
            case 0:
                break


def actualizar_mascota(mascota_service) -> None:
    while True:
        ui.limpiar_y_encabezado("ACTUALIZAR DATOS DE MASCOTA")
        print('''
        1. Cambiar Nombre
        2. Cambiar Propietario
        0. Volver
        ''')
        opcion = ui.leer_opcion_menu(2)
        match opcion:
            case 1:
                cambiar_nombre_mascota(mascota_service)
            case 2:
                cambiar_propietario_mascota(mascota_service)
            case 0:
                break


def eliminar_mascota(mascota_service) -> None:
    ui.limpiar_y_encabezado("ELIMINAR MASCOTA")
    ui.mostrar_advertencia("Nota: Solo se pueden eliminar mascotas sin atenciones asociadas.")

    id_mascota = ui.leer_entero("\nIngrese el ID de la mascota a eliminar: ", nombre_campo="ID Mascota")

    try:
        mascota = mascota_service.obtener_mascota_por_id(id_mascota)

        if ui.desea_confirmar(f"¿Está seguro de eliminar la mascota '{mascota.nombre}'?"):
            mascota_service.eliminar_mascota(id_mascota)
            ui.mostrar_exito("Mascota eliminada correctamente.")
        else:
            print("\nOperación cancelada por el usuario.")

    except exceptions.EntidadNoEncontradaException as error:
        ui.mostrar_error(str(error))
    except (exceptions.ReferenciaIntegridadError, exceptions.ReglaNegocioError) as error:
        ui.mostrar_advertencia(str(error))
    finally:
        ui.pausar()

# ACCIONES DE ESPECIES
def registrar_especie(mascota_service) -> None:
    ui.limpiar_y_encabezado("REGISTRAR ESPECIE")
    nombre_especie = ui.leer_nombre_alfabetico("Ingrese el nombre de la especie: ", nombre_campo="Especie", maximo=100)
    esperanza_vida = ui.leer_entero("Ingrese la esperanza de vida máxima (años): ", nombre_campo="Esperanza de vida", minimo=1, maximo=200)

    try:
        esp = mascota_service.registrar_especie(
            nombre_especie=nombre_especie,
            esperanza_vida_max=esperanza_vida
        )
        ui.mostrar_exito(f"Especie '{esp.nombre_especie}' registrada correctamente.")
    except (exceptions.EntidadExistenteException, exceptions.ReglaNegocioError) as error:
        ui.mostrar_error(str(error))
    finally:
        ui.pausar()


def listar_especies(mascota_service) -> None:
    ui.limpiar_y_encabezado("LISTA DE ESPECIES")
    especies = mascota_service.listar_especies()
    if not especies:
        ui.mostrar_advertencia("No hay especies registradas.")
    else:
        imprimir_tabla_especies(especies)
    ui.pausar()


def cambiar_nombre_especie(mascota_service) -> None:
    ui.limpiar_y_encabezado("CAMBIAR NOMBRE DE ESPECIE")
    especies = mascota_service.listar_especies()
    if not especies:
        ui.mostrar_advertencia("No hay especies registradas.")
        ui.pausar()
        return

    imprimir_tabla_especies(especies)
    id_especie = ui.leer_entero("\nIngrese el ID de la especie a modificar: ", nombre_campo="ID Especie")

    try:
        esp_actual = mascota_service.obtener_especie_por_id(id_especie)
        print(f"\nEspecie seleccionada: {esp_actual.nombre_especie}")

        nuevo_nombre = ui.leer_nombre_alfabetico("Ingrese el nuevo nombre: ", nombre_campo="Especie", maximo=100)

        if ui.desea_confirmar(
            f"¿Está seguro que quiere cambiar el nombre a '{nuevo_nombre}' de la especie {esp_actual.nombre_especie} ID:{esp_actual.id_especie}?"
        ):
            esp_actualizada = mascota_service.cambiar_nombre_especie(id_especie=id_especie, nuevo_nombre=nuevo_nombre)
            ui.mostrar_exito(f"Especie actualizada a '{esp_actualizada.nombre_especie}'.")
        else:
            print("\nOperación cancelada por el usuario.")

    except (exceptions.EntidadNoEncontradaException, exceptions.ReglaNegocioError) as error:
        ui.mostrar_error(str(error))
    finally:
        ui.pausar()

# FUNCIONES  DE APOYO

def buscar_por_nombre(mascota_service) -> None:
    nombre = ui.leer_nombre_alfabetico("Ingrese coincidencia de nombre a buscar: ", nombre_campo="Nombre Mascota")
    mascotas = mascota_service.buscar_mascotas(nombre)

    if not mascotas:
        ui.mostrar_advertencia(f"No se encontraron mascotas con el nombre '{nombre}'.")
    else:
        imprimir_tabla_mascotas(mascotas)
    ui.pausar()


def buscar_por_propietario(mascota_service) -> None:
    rut = ui.leer_rut("Ingrese RUT del propietario: ")
    try:
        mascotas = mascota_service.listar_mascotas_por_propietario(rut)
        if not mascotas:
            ui.mostrar_advertencia("El propietario no tiene mascotas registradas.")
        else:
            imprimir_tabla_mascotas(mascotas)
    except exceptions.EntidadNoEncontradaException as error:
        ui.mostrar_error(str(error))
    finally:
        ui.pausar()


def listar_todas_mascotas(mascota_service) -> None:
    mascotas = mascota_service.listar_mascotas()
    if not mascotas:
        ui.mostrar_advertencia("No hay mascotas registradas en el sistema.")
    else:
        imprimir_tabla_mascotas(mascotas)
    ui.pausar()


def cambiar_nombre_mascota(mascota_service) -> None:
    id_mascota = ui.leer_entero("Ingrese ID de la mascota: ", nombre_campo="ID Mascota")
    try:
        mascota = mascota_service.obtener_mascota_por_id(id_mascota)
        print(f"\nNombre actual: {mascota.nombre}")

        nuevo_nombre = ui.leer_nombre_alfabetico("Ingrese el nuevo nombre: ", nombre_campo="Nuevo Nombre", maximo=100)
        
        if ui.desea_confirmar(
            f"¿Está seguro que quiere cambiar el nombre a '{nuevo_nombre}' de la mascota {mascota.nombre} ID:{mascota.id_mascota}?"
        ):
            actualizada = mascota_service.cambiar_nombre(id_mascota=id_mascota, nuevo_nombre=nuevo_nombre)
            ui.mostrar_exito(f"Nombre actualizado exitosamente a '{actualizada.nombre}'.")
        else:
            print("\nOperación cancelada por el usuario.")

    except (exceptions.EntidadNoEncontradaException, exceptions.ReglaNegocioError) as error:
        ui.mostrar_error(str(error))
    finally:
        ui.pausar()

def cambiar_propietario_mascota(mascota_service) -> None:
    id_mascota = ui.leer_entero("Ingrese ID de la mascota: ", nombre_campo="ID Mascota")
    try:
        mascota = mascota_service.obtener_mascota_por_id(id_mascota)
        print(f"\nMascota: {mascota.nombre}")
        print(f"Propietario actual: {mascota.propietario.nombre_completo} (RUT: {mascota.propietario.rut})")

        nuevo_rut = ui.leer_rut("Ingrese RUT del nuevo propietario: ")

        if ui.desea_confirmar(
            f"¿Está seguro que quiere cambiar el propietario al RUT '{nuevo_rut}' de la mascota {mascota.nombre} ID:{mascota.id_mascota}?"
        ):
            actualizada = mascota_service.cambiar_propietario(id_mascota=id_mascota, rut_propietario=nuevo_rut)
            ui.mostrar_exito(f"Propietario actualizado exitosamente a '{actualizada.propietario.nombre_completo}'.")
        else:
            print("\nOperación cancelada por el usuario.")

    except (exceptions.EntidadNoEncontradaException, exceptions.ReglaNegocioError) as error:
        ui.mostrar_error(str(error))
    finally:
        ui.pausar()


def imprimir_tabla_mascotas(mascotas: list) -> None:
    print(f"\n{'ID':<6} | {'NOMBRE':<20} | {'FECHA NAC.':<12} | {'ESPECIE':<15} | {'PROPIETARIO':<25}")
    print("-" * 85)
    for m in mascotas:
        fecha_str = str(m.fecha_nacimiento)
        nombre_especie = m.especie.nombre_especie if m.especie else "N/A"
        nombre_prop = m.propietario.nombre_completo if m.propietario else "N/A"
        print(f"{m.id_mascota:<6} | {m.nombre:<20} | {fecha_str:<12} | {nombre_especie:<15} | {nombre_prop:<25}")


def imprimir_tabla_especies(especies: list) -> None:
    print(f"\n{'ID':<6} | {'ESPECIE':<25} | {'ESP. VIDA MÁX (AÑOS)':<20}")
    print("-" * 57)
    for e in especies:
        print(f"{e.id_especie:<6} | {e.nombre_especie:<25} | {e.esperanza_vida_max:<20}")