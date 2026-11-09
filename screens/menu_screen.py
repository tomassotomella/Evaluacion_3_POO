from datetime import date

from utilities import interfaz as ui
from exceptions import exceptions
from screens import (
    propietario_screens,
    veterinario_screens,
    mascotas_screen,
    consulta_screens,
    farmacia_screen,
    urgencia_screen,
)


def _obtener_texto_mercado(economia_service) -> str:
    """Obtiene el texto del mercado cambiario para el encabezado de forma segura."""
    if not economia_service:
        return "[MERCADO CAMBIARIO]: Servicio no configurado"
    try:
        divisa = economia_service.obtener_dolar_actual()
        valor_formateado = ui.formatear_decimal(divisa.valor)
        return f"[MERCADO CAMBIARIO]: Dólar Observado: ${valor_formateado} CLP (Fuente: {economia_service.SERVICIO_NOMBRE})"
    except Exception:
        return "[MERCADO CAMBIARIO]: Dólar Observado: No disponible (Offline)"


def main_menu(
    persona_service,
    mascota_service,
    consulta_service,
    farmacia_service,
    economia_service=None,
    feriado_service=None,
) -> None:
    """Menú principal de la aplicación VetCare."""
    while True:
        ui.limpiar_pantalla()
        ancho = 80
        print("=" * ancho)
        print("VETCARE - CLÍNICA VETERINARIA".center(ancho))
        print("=" * ancho)
        print(_obtener_texto_mercado(economia_service))
        if feriado_service:
            try:
                print(f"[FECHA]: {date.today():%d/%m/%Y}")
                print(
                    "[CALENDARIO]: "
                    f"{feriado_service.obtener_resumen_calendario()}"
                )
            except exceptions.ServicioExternoException:
                print("[CALENDARIO]: No disponible (Offline)")
        print("=" * ancho)
        print('''
        1. Gestión de Propietarios
        2. Gestión de Veterinarios
        3. Gestión de Mascotas
        4. Gestión de Consultas y Atenciones
        5. Gestión de Farmacia
        0. Salir
        ''')
        opcion = ui.leer_opcion_menu(5)
        match opcion:
            case 1:
                propietario_screens.main_propietarios(persona_service)
            case 2:
                veterinario_screens.main_veterinarios(persona_service)
            case 3:
                mascotas_screen.main_mascotas(mascota_service)
            case 4:
                consulta_screens.main_consultas(
                    consulta_service, farmacia_service
                )
            case 5:
                farmacia_screen.main_farmacia(farmacia_service)
            case 0:
                ui.mostrar_subtitulo("Gracias por usar VetCare. ¡Hasta pronto!")
                break
