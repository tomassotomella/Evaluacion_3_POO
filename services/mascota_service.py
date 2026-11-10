from models.mascota import Mascota
from models.especie import Especie
from dao.mascota_dao import MascotaDAO
from dao.especie_dao import EspecieDAO
from exceptions import exceptions
from utilities.ValidadorEntradas import ValidadorEntradas
from datetime import date
from services.persona_service import PersonaService

class MascotaService:
    def __init__(
        self,
        mascota_dao: MascotaDAO,
        especie_dao: EspecieDAO,
        persona_service: PersonaService
    ):
        self.mascota_dao = mascota_dao
        self.especie_dao = especie_dao
        self.persona_service = persona_service

    #Especies
    def registrar_especie(
            self,
            nombre_especie: str,
            esperanza_vida_max: int
    ) -> Especie:
        especie = Especie(
            esperanza_vida_max = esperanza_vida_max,
            nombre_especie = nombre_especie,
        )
        self.especie_dao.insertar(especie)
        return especie

    def obtener_especie_por_id (self, id_especie: int | str) -> Especie:
        id_valido = ValidadorEntradas.validar_id(id_especie, 'Especie')
        return self.especie_dao.obtener_por_id(id_valido)

    def listar_especies(self) -> list[Especie]:
        return self.especie_dao.listar_todos()  

    #Mascotas
    def registrar_mascota(
            self,
            nombre: str,
            fecha_nacimiento: date,
            id_especie: int | str,
            rut_propietario: str,
            raza: str = "Sin especificar",
    ) -> Mascota:
        mascota = Mascota(
            nombre = nombre,
            fecha_nacimiento = fecha_nacimiento,
            especie = self.obtener_especie_por_id(id_especie),
            propietario = self.persona_service.obtener_propietario_por_rut(rut_propietario),
            raza = raza,
        )
        self.mascota_dao.insertar(mascota)
        return mascota

    def obtener_mascota_por_id(self, id_mascota: int | str) -> Mascota:
        id_valido = ValidadorEntradas.validar_id(id_mascota, 'Mascota')
        return self.mascota_dao.obtener_por_id(id_valido)

    def buscar_mascotas(self, nombre: str) -> list[Mascota]:
        return self.mascota_dao.buscar_por_nombre(nombre)

    def listar_mascotas(self) -> list[Mascota]:
        return self.mascota_dao.listar_todos()
    
    def listar_mascotas_por_propietario (self, rut_propietario: str) -> list[Mascota]:
        propietario = self.persona_service.obtener_propietario_por_rut(rut_propietario)
        if propietario.id_persona is None:
            raise exceptions.ReglaNegocioError(
                "El propietario debe tener un ID asignado."
            )
        return self.mascota_dao.listar_por_propietario(propietario.id_persona)

    def eliminar_mascota(self, id_mascota: int | str) -> None:
        mascota = self.obtener_mascota_por_id(id_mascota)
        if mascota.id_mascota is None:
            raise exceptions.ReglaNegocioError(
                "La mascota debe tener un ID asignado."
            )
        self.mascota_dao.eliminar(mascota.id_mascota)

    def cambiar_nombre(self, id_mascota: int | str, nuevo_nombre: str) -> Mascota:
        mascota = self.obtener_mascota_por_id(id_mascota)
        mascota.actualizar_nombre(nuevo_nombre)
        self.mascota_dao.actualizar(mascota)
        return mascota

    def cambiar_raza(self, id_mascota: int | str, nueva_raza: str) -> Mascota:
        mascota = self.obtener_mascota_por_id(id_mascota)
        mascota.raza = nueva_raza
        self.mascota_dao.actualizar(mascota)
        return mascota
    
    def cambiar_propietario(self, id_mascota: int | str, rut_propietario: str) -> Mascota:
        mascota = self.obtener_mascota_por_id(id_mascota)
        nuevo_propietario = self.persona_service.obtener_propietario_por_rut(rut_propietario)
        mascota.cambiar_propietario(nuevo_propietario)
        self.mascota_dao.actualizar(mascota)
        return mascota


    