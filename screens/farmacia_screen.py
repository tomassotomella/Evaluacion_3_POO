from utilities import interfaz as ui
from exceptions import exceptions


def main_farmacia(farmacia_service) -> None:
    """Menú Principal del Módulo de Farmacia."""
    while True:
        ui.limpiar_y_encabezado("GESTIÓN DE FARMACIA")
        print('''
        1. Gestionar Catálogo
        2. Visualizar Catálogo
        3. Vender Receta
        0. Volver al Menú Principal
        ''')
        opcion = ui.leer_opcion_menu(3)
        match opcion:
            case 1:
                submenu_gestionar_catalogo(farmacia_service)
            case 2:
                submenu_visualizar_catalogo(farmacia_service)
            case 3:
                submenu_vender_receta(farmacia_service)
            case 0:
                break


# SUBMENÚ 1: GESTIÓN DE CATÁLOGO

def submenu_gestionar_catalogo(farmacia_service) -> None:
    while True:
        ui.limpiar_y_encabezado("GESTIONAR CATÁLOGO DE MEDICAMENTOS")
        print('''
        1. Registrar Medicamento
        2. Eliminar Medicamento
        3. Reponer Stock
        0. Volver
        ''')
        opcion = ui.leer_opcion_menu(4)
        match opcion:
            case 1:
                registrar_medicamento(farmacia_service)
            case 2:
                eliminar_medicamento(farmacia_service)
            case 3:
                reponer_stock(farmacia_service)
            case 0:
                break


# SUBMENÚ 2: VISUALIZACIÓN DE CATÁLOGO

def submenu_visualizar_catalogo(farmacia_service) -> None:
    while True:
        ui.limpiar_y_encabezado("VISUALIZAR CATÁLOGO DE MEDICAMENTOS")
        print('''
        1. Buscar Medicamento por ID
        2. Buscar Medicamentos por Nombre
        3. Listar Medicamentos
        4. Medicamentos con Stock Crítico
        0. Volver
        ''')
        opcion = ui.leer_opcion_menu(4)
        match opcion:
            case 1:
                buscar_medicamento_por_id(farmacia_service)
            case 2:
                buscar_medicamentos_por_nombre(farmacia_service)
            case 3:
                listar_medicamentos(farmacia_service)
            case 4:
                listar_stock_critico(farmacia_service)
            case 0:
                break


# SUBMENÚ 3: VENTA / DESPACHO DE RECETAS

def submenu_vender_receta(farmacia_service) -> None:
    while True:
        ui.limpiar_y_encabezado("VENDER RECETA")
        print('''
        1. Despachar Receta
        2. Despachar Recetas Seleccionadas
        3. Despachar Recetas de un Detalle de Consulta
        0. Volver
        ''')
        opcion = ui.leer_opcion_menu(3)
        match opcion:
            case 1:
                despachar_receta(farmacia_service)
            case 2:
                despachar_recetas_seleccionadas(farmacia_service)
            case 3:
                despachar_recetas_de_detalle(farmacia_service)
            case 0:
                break


# ACCIONES DE MEDICAMENTOS

def registrar_medicamento(farmacia_service) -> None:
    ui.limpiar_y_encabezado("REGISTRAR MEDICAMENTO")
    nombre_comercial = ui.leer_texto("Ingrese nombre comercial del medicamento: ", max_longitud=100, nombre_campo="Nombre Comercial")
    precio = ui.leer_entero("Ingrese precio unitario ($): ", nombre_campo="Precio", minimo=1, maximo=100000)
    stock = ui.leer_entero("Ingrese stock inicial: ", nombre_campo="Stock", minimo=0, maximo=1000)

    try:
        medicamento = farmacia_service.registrar_medicamento(
            nombre_comercial=nombre_comercial,
            precio=precio,
            stock=stock
        )
        ui.mostrar_exito(f"Medicamento '{medicamento.nombre_comercial}' registrado exitosamente.")
    except (exceptions.EntidadExistenteException, exceptions.ReglaNegocioError) as error:
        ui.mostrar_error(str(error))
    finally:
        ui.pausar()


def mostrar_detalle_medicamento(medicamento, farmacia_service=None) -> None:
    """Muestra la ficha detallada de un medicamento con sus precios en CLP y USD."""
    ancho = 80
    print("=" * ancho)
    print("CATÁLOGO DE FARMACIA - DETALLE DE PRODUCTO".center(ancho))
    print("=" * ancho)
    print(f"ID Medicamento : #{medicamento.id_medicamento}")
    print(f"Nombre         : {medicamento.nombre_comercial}")
    print(f"Stock en Bodega: {medicamento.stock} unidades")
    print("-" * ancho)
    texto_clp = ui.formatear_clp(medicamento.precio)
    texto_usd = ui.formatear_usd(medicamento.precio_usd) if medicamento.precio_usd is not None else "No disponible (Offline)"
    print(f"PRECIO CLP     : {texto_clp}")
    print(f"PRECIO USD     : {texto_usd}")
    print("-" * ancho)
    if farmacia_service and medicamento.precio_usd is not None:
        try:
            dolar = farmacia_service.economia_service.obtener_dolar_actual()
            tasa_str = ui.formatear_decimal(dolar.valor)
            print(f"[INFO]: Tipo de cambio aplicado: 1 USD = ${tasa_str} CLP.")
            print("-" * ancho)
        except (
            exceptions.ConfiguracionException,
            exceptions.ServicioExternoException,
        ):
            pass
    if medicamento.es_stock_critico():
        ui.mostrar_advertencia("El medicamento se encuentra con stock crítico.")


def buscar_medicamento_por_id(farmacia_service) -> None:
    id_medicamento = ui.leer_entero("Ingrese ID del medicamento: ", nombre_campo="ID Medicamento")

    try:
        medicamento = farmacia_service.obtener_medicamento_por_id(id_medicamento)
        mostrar_detalle_medicamento(medicamento, farmacia_service)
    except exceptions.EntidadNoEncontradaException as error:
        ui.mostrar_error(str(error))
    finally:
        ui.pausar()


def buscar_medicamentos_por_nombre(farmacia_service) -> None:
    nombre = ui.leer_texto("Ingrese coincidencia de nombre a buscar: ", max_longitud=100, nombre_campo="Medicamento")
    medicamentos = farmacia_service.buscar_medicamentos_por_nombre(nombre)

    if not medicamentos:
        ui.mostrar_advertencia(f"No se encontraron medicamentos que coincidan con '{nombre}'.")
    else:
        imprimir_tabla_medicamentos(medicamentos)
    ui.pausar()


def listar_medicamentos(farmacia_service) -> None:
    medicamentos = farmacia_service.listar_medicamentos()

    if not medicamentos:
        ui.mostrar_advertencia("No hay medicamentos registrados en el sistema.")
    else:
        imprimir_tabla_medicamentos(medicamentos)
    ui.pausar()


def eliminar_medicamento(farmacia_service) -> None:
    ui.limpiar_y_encabezado("ELIMINAR MEDICAMENTO")
    id_medicamento = ui.leer_entero("Ingrese ID del medicamento a eliminar: ", nombre_campo="ID Medicamento")

    try:
        medicamento = farmacia_service.obtener_medicamento_por_id(id_medicamento)

        if ui.desea_confirmar(f"¿Está seguro de eliminar el medicamento '{medicamento.nombre_comercial}'?"):
            farmacia_service.eliminar_medicamento(id_medicamento)
            ui.mostrar_exito("Medicamento eliminado correctamente.")
        else:
            print("\nOperación cancelada por el usuario.")

    except exceptions.EntidadNoEncontradaException as error:
        ui.mostrar_error(str(error))
    except (exceptions.ReferenciaIntegridadError, exceptions.ReglaNegocioError) as error:
        ui.mostrar_advertencia(str(error))
    finally:
        ui.pausar()


# GESTIÓN DE STOCK

def reponer_stock(farmacia_service) -> None:
    ui.limpiar_y_encabezado("REPONER STOCK")
    id_medicamento = ui.leer_entero("Ingrese ID del medicamento: ", nombre_campo="ID Medicamento")

    try:
        medicamento = farmacia_service.obtener_medicamento_por_id(id_medicamento)
        print(f"\nMedicamento: {medicamento.nombre_comercial} | Stock actual: {medicamento.stock}")

        cantidad = ui.leer_entero("Ingrese cantidad a reponer: ", nombre_campo="Cantidad", minimo=1)

        if ui.desea_confirmar(f"¿Confirma reponer {cantidad} unidades de '{medicamento.nombre_comercial}'?"):
            actualizado = farmacia_service.reponer_stock(id_medicamento, cantidad)
            ui.mostrar_exito(f"Stock actualizado a {actualizado.stock} unidades.")
        else:
            print("\nOperación cancelada.")

    except exceptions.EntidadNoEncontradaException as error:
        ui.mostrar_error(str(error))
    except (exceptions.ReglaNegocioError, exceptions.EntradaInvalidaException) as error:
        ui.mostrar_error(str(error))
    finally:
        ui.pausar()


def descontar_stock(farmacia_service) -> None:
    ui.limpiar_y_encabezado("DESCONTAR STOCK")
    id_medicamento = ui.leer_entero("Ingrese ID del medicamento: ", nombre_campo="ID Medicamento")

    try:
        medicamento = farmacia_service.obtener_medicamento_por_id(id_medicamento)
        print(f"\nMedicamento: {medicamento.nombre_comercial} | Stock actual: {medicamento.stock}")

        cantidad = ui.leer_entero("Ingrese cantidad a descontar: ", nombre_campo="Cantidad", minimo=1)

        if ui.desea_confirmar(f"¿Confirma descontar {cantidad} unidades de '{medicamento.nombre_comercial}'?"):
            actualizado = farmacia_service.descontar_stock(id_medicamento, cantidad)
            ui.mostrar_exito(f"Stock actualizado a {actualizado.stock} unidades.")
        else:
            print("\nOperación cancelada.")

    except (exceptions.SinStockException, exceptions.EntidadNoEncontradaException, exceptions.ReglaNegocioError) as error:
        ui.mostrar_error(str(error))
    finally:
        ui.pausar()


def listar_stock_critico(farmacia_service) -> None:
    ui.limpiar_y_encabezado("MEDICAMENTOS CON STOCK CRÍTICO")
    medicamentos = farmacia_service.listar_stock_critico()

    if not medicamentos:
        ui.mostrar_exito("No hay medicamentos con stock crítico.")
    else:
        ui.mostrar_advertencia("Los siguientes medicamentos requieren reposición:")
        imprimir_tabla_medicamentos(medicamentos)
    ui.pausar()


# GESTIÓN DE VENTAS / DESPACHO

def mostrar_comprobante_despacho(total_clp: int, economia_service) -> None:
    """Muestra el comprobante final de venta bimonetario con la tasa de cambio aplicada."""
    ancho = 80
    ui.mostrar_exito("Despacho realizado exitosamente.")
    print("-" * ancho)
    print(f"TOTAL COBRADO  : {ui.formatear_clp(total_clp)}")
    if economia_service:
        try:
            total_usd, divisa = economia_service.convertir_clp_a_usd(total_clp)
            tasa_str = ui.formatear_decimal(divisa.valor)
            print(f"EQUIVALENTE USD: {ui.formatear_usd(total_usd)}")
            print(f"[INFO]: Tipo de cambio aplicado: 1 USD = ${tasa_str} CLP.")
        except (
            exceptions.ConfiguracionException,
            exceptions.ServicioExternoException,
        ):
            print("EQUIVALENTE USD: No disponible (Offline)")
    print("-" * ancho)


def mostrar_recetas_disponibles_para_despacho(farmacia_service) -> bool:
    recetas = farmacia_service.listar_recetas_disponibles_para_despacho()
    if not recetas:
        ui.mostrar_advertencia("No hay recetas registradas para despachar.")
        ui.pausar()
        return False
    imprimir_tabla_recetas(recetas)
    return True


def despachar_receta(farmacia_service) -> None:
    ui.limpiar_y_encabezado("DESPACHAR RECETA")
    if not mostrar_recetas_disponibles_para_despacho(farmacia_service):
        return
    id_receta = ui.leer_entero("Ingrese ID de la receta a despachar: ", nombre_campo="ID Receta")

    try:
        receta = farmacia_service.obtener_receta_para_despacho(id_receta)
        subtotal_clp = receta.calcular_subtotal()
        subtotal_usd = receta.calcular_subtotal_usd()
        texto_usd = f" ({ui.formatear_usd(subtotal_usd)})" if subtotal_usd is not None else ""

        print(f"\nReceta ID:{receta.id_receta} | Medicamento: {receta.medicamento.nombre_comercial} "
              f"| Cantidad: {receta.cantidad} | Stock disponible: {receta.medicamento.stock}")
        print(f"Total a cobrar : {ui.formatear_clp(subtotal_clp)}{texto_usd}")

        if ui.desea_confirmar(f"¿Confirma el despacho de la receta ID:{receta.id_receta}?"):
            total_clp = farmacia_service.despachar_receta(id_receta)
            mostrar_comprobante_despacho(total_clp, farmacia_service.economia_service)
        else:
            print("\nOperación cancelada.")

    except (exceptions.SinStockException, exceptions.EntidadNoEncontradaException, exceptions.ReglaNegocioError) as error:
        ui.mostrar_error(str(error))
    finally:
        ui.pausar()


def despachar_recetas_seleccionadas(farmacia_service) -> None:
    ui.limpiar_y_encabezado("DESPACHAR RECETAS SELECCIONADAS")
    if not mostrar_recetas_disponibles_para_despacho(farmacia_service):
        return
    ui.mostrar_advertencia("Ingrese los IDs de las recetas a despachar. Finalice con 0.")

    ids_recetas = []
    while True:
        id_receta = ui.leer_entero("Ingrese ID de receta (0 para terminar): ", nombre_campo="ID Receta", minimo=0)
        if id_receta == 0:
            break
        ids_recetas.append(id_receta)

    if not ids_recetas:
        ui.mostrar_advertencia("No se seleccionó ninguna receta para despachar.")
        ui.pausar()
        return

    try:
        total_clp = farmacia_service.despachar_recetas_seleccionadas(ids_recetas)
        mostrar_comprobante_despacho(total_clp, farmacia_service.economia_service)
    except (exceptions.SinStockException, exceptions.EntidadNoEncontradaException, exceptions.ReglaNegocioError) as error:
        ui.mostrar_error(str(error))
    finally:
        ui.pausar()


def despachar_recetas_de_detalle(farmacia_service) -> None:
    ui.limpiar_y_encabezado("DESPACHAR RECETAS DE UN DETALLE DE CONSULTA")
    id_detalle = ui.leer_entero("Ingrese ID del detalle de consulta: ", nombre_campo="ID Detalle")

    try:
        recetas = farmacia_service.listar_recetas_para_despacho(id_detalle)
        if not recetas:
            ui.mostrar_advertencia(f"El detalle ID:{id_detalle} no tiene recetas asociadas.")
            ui.pausar()
            return

        imprimir_tabla_recetas(recetas)

        total_clp = sum(r.calcular_subtotal() for r in recetas)
        total_usd = sum(r.calcular_subtotal_usd() or 0.0 for r in recetas)
        texto_usd = f" ({ui.formatear_usd(total_usd)})" if total_usd > 0 else ""

        if ui.desea_confirmar(f"¿Confirma el despacho de todas las recetas por {ui.formatear_clp(total_clp)}{texto_usd}?"):
            total = farmacia_service.despachar_todas_recetas_de_detalle(id_detalle)
            mostrar_comprobante_despacho(total, farmacia_service.economia_service)
        else:
            print("\nOperación cancelada.")

    except (exceptions.SinStockException, exceptions.EntidadNoEncontradaException, exceptions.ReglaNegocioError) as error:
        ui.mostrar_error(str(error))
    finally:
        ui.pausar()


# FUNCIONES AUXILIARES DE TABLAS

def imprimir_tabla_medicamentos(medicamentos: list) -> None:
    print(f"\n{'ID':<6} | {'NOMBRE COMERCIAL':<28} | {'PRECIO CLP':<14} | {'PRECIO USD':<14} | {'STOCK':<8}")
    print("-" * 78)
    for m in medicamentos:
        critico = " (CRÍTICO)" if m.es_stock_critico() else ""
        usd_str = ui.formatear_usd(m.precio_usd) if m.precio_usd is not None else "N/D"
        clp_str = ui.formatear_clp(m.precio)
        print(f"{m.id_medicamento:<6} | {m.nombre_comercial:<28} | {clp_str:<14} | {usd_str:<14} | {m.stock:<8}{critico}")


def imprimir_tabla_recetas(recetas: list) -> None:
    print(f"\n{'ID REC.':<8} | {'MEDICAMENTO':<24} | {'CANT.':<6} | {'P. UNIT (CLP)':<14} | {'SUBTOTAL CLP':<14} | {'SUBTOTAL USD':<14}")
    print("-" * 88)
    total_clp = 0
    total_usd = 0.0
    hay_usd = False

    for r in recetas:
        subtotal_clp = r.calcular_subtotal()
        total_clp += subtotal_clp
        subtotal_usd = r.calcular_subtotal_usd()
        
        clp_unit = ui.formatear_clp(r.medicamento.precio)
        clp_sub = ui.formatear_clp(subtotal_clp)
        if subtotal_usd is not None:
            usd_sub = ui.formatear_usd(subtotal_usd)
            total_usd += subtotal_usd
            hay_usd = True
        else:
            usd_sub = "N/D"

        print(f"{r.id_receta:<8} | {r.medicamento.nombre_comercial:<24} | {r.cantidad:<6} | {clp_unit:<14} | {clp_sub:<14} | {usd_sub:<14}")
    
    print("-" * 88)
    usd_total_str = f" | {ui.formatear_usd(total_usd)}" if hay_usd else ""
    print(f"{'TOTAL ESTIMADO:':<58} {ui.formatear_clp(total_clp)}{usd_total_str}")