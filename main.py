from database.conexion import ConexionDB
from dao.propietario_dao import PropietarioDAO
from dao.veterinario_dao import VeterinarioDAO
from dao.especialidad_dao import EspecialidadDAO
from dao.especie_dao import EspecieDAO
from dao.mascota_dao import MascotaDAO
from dao.medicamento_dao import MedicamentoDAO
from dao.consulta_dao import ConsultaDAO
from dao.receta_medica_dao import RecetaMedicaDAO
from services.persona_service import PersonaService
from services.mascota_service import MascotaService
from services.consulta_service import ConsultaService
from services.farmacia_service import FarmaciaService
from screens.menu_screen import main_menu


def main() -> None:
    """Punto de entrada de la aplicación VetCare."""
    conexion = ConexionDB()

    # DAOs (en orden de dependencia, sin duplicar instancias)
    especialidad_dao = EspecialidadDAO(conexion)
    propietario_dao = PropietarioDAO(conexion)
    veterinario_dao = VeterinarioDAO(conexion, especialidad_dao)
    especie_dao = EspecieDAO(conexion)
    mascota_dao = MascotaDAO(conexion, especie_dao, propietario_dao)
    medicamento_dao = MedicamentoDAO(conexion)
    consulta_dao = ConsultaDAO(conexion, mascota_dao)
    receta_dao = RecetaMedicaDAO(conexion, medicamento_dao, consulta_dao)

    # Services (respetando sus dependencias)
    persona_service = PersonaService(propietario_dao, veterinario_dao, especialidad_dao)
    mascota_service = MascotaService(mascota_dao, especie_dao, persona_service)
    consulta_service = ConsultaService(consulta_dao, receta_dao, medicamento_dao, persona_service, mascota_service)
    farmacia_service = FarmaciaService(medicamento_dao, consulta_service)

    try:
        main_menu(persona_service, mascota_service, consulta_service, farmacia_service)
    except KeyboardInterrupt:
        print("\n\nSesión interrumpida por el usuario. ¡Hasta pronto!")


if __name__ == '__main__':
    main()