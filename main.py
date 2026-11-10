from config.configuracion import Configuracion
from database.conexion import ConexionDB
from dao.propietario_dao import PropietarioDAO
from dao.veterinario_dao import VeterinarioDAO
from dao.especialidad_dao import EspecialidadDAO
from dao.especie_dao import EspecieDAO
from dao.mascota_dao import MascotaDAO
from dao.medicamento_dao import MedicamentoDAO
from dao.consulta_dao import ConsultaDAO
from dao.receta_medica_dao import RecetaMedicaDAO
from dao.divisa_dao import DivisaDAO
from services.persona_service import PersonaService
from services.mascota_service import MascotaService
from services.consulta_service import ConsultaService
from services.farmacia_service import FarmaciaService
from services.economia_service import EconomiaService
from services.feriado_service import FeriadoService
from dao.feriado_dao import FeriadoDAO
from services.cliente_resiliente import ClienteHTTPResiliente
from services.servicio_clima import ServicioClima
from services.alerta_zoosanitaria_service import AlertaZoosanitariaService
from screens.menu_screen import menu_principal


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
    divisa_dao = DivisaDAO(conexion)
    feriado_dao = FeriadoDAO(conexion)

    # Services (respetando sus dependencias)
    persona_service = PersonaService(propietario_dao, veterinario_dao, especialidad_dao)
    mascota_service = MascotaService(mascota_dao, especie_dao, persona_service)
    cliente_http = ClienteHTTPResiliente(
        timeout=Configuracion.TIMEOUT_SEGUNDOS,
    )
    economia_service = EconomiaService(
        divisa_dao,
        cliente_http=cliente_http,
    )
    feriado_service = FeriadoService(
        feriado_dao,
        cliente_http=cliente_http,
    )
    servicio_clima = ServicioClima(cliente_http)
    servicio_alertas = AlertaZoosanitariaService()
    consulta_service = ConsultaService(
        consulta_dao,
        receta_dao,
        medicamento_dao,
        persona_service,
        mascota_service,
        economia_service,
        feriado_service
    )
    farmacia_service = FarmaciaService(medicamento_dao, consulta_service, economia_service)

    try:
        menu_principal(
            persona_service,
            mascota_service,
            consulta_service,
            farmacia_service,
            economia_service,
            feriado_service,
            servicio_clima,
            servicio_alertas,
        )
    except KeyboardInterrupt:
        print("\n\nSesión interrumpida por el usuario. ¡Hasta pronto!")


if __name__ == '__main__':
    main()