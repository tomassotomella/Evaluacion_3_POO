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
from services.alerta_zoosanitaria_service import AlertaZoosanitariaService
from services.consulta_service import ConsultaService
from services.farmacia_service import FarmaciaService
from services.mascota_service import MascotaService
from services.persona_service import PersonaService
from services.servicio_clima import ServicioClima


def _obtener_texto_mercado(economia_service) -> str:
    """Obtiene el texto del mercado cambiario para el encabezado de forma segura."""
    if not economia_service:
        return "[MERCADO CAMBIARIO]: Servicio no configurado"
    try:
        divisa = economia_service.obtener_dolar_actual()
        valor_formateado = ui.formatear_decimal(divisa.valor)
        return f"[MERCADO CAMBIARIO]: Dólar Observado: ${valor_formateado} CLP (Fuente: {economia_service.SERVICIO_NOMBRE})"
    except (
        exceptions.ConfiguracionException,
        exceptions.ServicioExternoException,
    ):
        return "[MERCADO CAMBIARIO]: Dólar Observado: No disponible (Offline)"


def _obtener_texto_clima(
    servicio_clima: ServicioClima | None,
    comuna: str = "Los Ángeles, Chile",
) -> str:
    if not servicio_clima:
        return "[CLIMA EN VIVO]: No disponible (Offline)"
    try:
        clima = servicio_clima.obtener_clima(comuna)
        return (
            f"[CLIMA EN VIVO]: {clima.temperatura_c:.1f} °C, "
            f"{clima.condicion}"
        )
    except (
        exceptions.ConfiguracionException,
        exceptions.ServicioExternoException,
    ):
        return "[CLIMA EN VIVO]: No disponible (Offline)"


def menu_principal(
    persona_service: PersonaService,
    mascota_service: MascotaService,
    consulta_service: ConsultaService,
    farmacia_service: FarmaciaService,
    economia_service=None,
    feriado_service=None,
    servicio_clima: ServicioClima | None = None,
    servicio_alertas: AlertaZoosanitariaService | None = None,
) -> None:
    """Menú principal de la aplicación VetCare."""
    while True:
        ui.limpiar_pantalla()
        ancho = 80
        print("=" * ancho)
        print("VETCARE - CLÍNICA VETERINARIA".center(ancho))
        print("=" * ancho)
        print("[SUCURSAL VETCARE]: Los Ángeles, Chile")
        print(_obtener_texto_clima(servicio_clima))
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
                propietario_screens.menu_propietarios(
                    persona_service,
                    servicio_clima=servicio_clima,
                    servicio_alertas=servicio_alertas,
                    mascota_service=mascota_service,
                )
            case 2:
                veterinario_screens.main_veterinarios(persona_service)
            case 3:
                mascotas_screen.main_mascotas(mascota_service)
            case 4:
                consulta_screens.main_consultas(
                    consulta_service,
                    farmacia_service,
                    feriado_service,
                )
            case 5:
                farmacia_screen.main_farmacia(farmacia_service)
            case 0:
                ui.mostrar_subtitulo("Gracias por usar VetCare. ¡Hasta pronto!")
                break
