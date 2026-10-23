from utilities import interfaz as ui
from screens import propietario_screens, veterinario_screens, mascotas_screen, consulta_screens, farmacia_screen


def main_menu(persona_service, mascota_service, consulta_service, farmacia_service) -> None:
    """Menú principal de la aplicación VetCare."""
    while True:
        ui.limpiar_y_encabezado("VETCARE - CLÍNICA VETERINARIA")
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
                consulta_screens.main_consultas(consulta_service, farmacia_service)
            case 5:
                farmacia_screen.main_farmacia(farmacia_service)
            case 0:
                ui.mostrar_subtitulo("Gracias por usar VetCare. ¡Hasta pronto!")
                break
