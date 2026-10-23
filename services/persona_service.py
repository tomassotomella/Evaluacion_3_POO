from __future__ import annotations

from models.especialidad import Especialidad
from models.propietario import Propietario
from models.veterinario import Veterinario
from dao.especialidad_dao import EspecialidadDAO
from dao.propietario_dao import PropietarioDAO
from dao.veterinario_dao import VeterinarioDAO
from exceptions import exceptions
from utilities.ValidadorEntradas import ValidadorEntradas


class PersonaService:
    def __init__(
        self,
        propietario_dao: PropietarioDAO,
        veterinario_dao: VeterinarioDAO,
        especialidad_dao: EspecialidadDAO
    ):
        self.propietario_dao = propietario_dao
        self.veterinario_dao = veterinario_dao
        self.especialidad_dao = especialidad_dao

    # Especialidades
    def registrar_especialidad(
        self,
        nombre: str,
        descripcion: str
    ) -> Especialidad:
        especialidad = Especialidad(
            nombre_especialidad=nombre,
            descripcion=descripcion
        )
        self.especialidad_dao.insertar(especialidad)
        return especialidad

    def obtener_especialidad(self, id_especialidad: int | str) -> Especialidad:
        id_valido = ValidadorEntradas.validar_id(
            id_especialidad,
            "especialidad"
        )
        return self.especialidad_dao.obtener_por_id(id_valido)

    def listar_especialidades(self) -> list[Especialidad]:
        return self.especialidad_dao.listar_todos()

    def eliminar_especialidad(self, id_especialidad: int | str) -> None:
        especialidad = self.obtener_especialidad(id_especialidad)
        self.especialidad_dao.eliminar(especialidad.id_especialidad)

    # Propietarios
    def registrar_propietario(
        self,
        rut: str,
        nombre_completo: str,
        telefono: str
    ) -> Propietario:
        propietario = Propietario(
            rut=rut,
            nombre_completo=nombre_completo,
            telefono=telefono
        )
        self.propietario_dao.insertar(propietario)
        return propietario

    def obtener_propietario_por_id(
        self,
        id_propietario: int | str
    ) -> Propietario:
        id_valido = ValidadorEntradas.validar_id(
            id_propietario,
            "propietario"
        )
        return self.propietario_dao.obtener_por_id(id_valido)

    def obtener_propietario_por_rut(self, rut: str) -> Propietario:
        return self.propietario_dao.obtener_por_rut(rut)

    def buscar_propietarios(self, nombre: str) -> list[Propietario]:
        return self.propietario_dao.buscar_por_nombre(nombre)

    def listar_propietarios(self) -> list[Propietario]:
        return self.propietario_dao.listar_todos()


    def cambiar_nombre_propietario(
        self,
        rut: str,
        nuevo_nombre: str
    ) -> Propietario:
        propietario = self.obtener_propietario_por_rut(rut)
        propietario.actualizar_nombre(nuevo_nombre)
        self.propietario_dao.actualizar(propietario)
        return propietario

    def cambiar_contacto_propietario(
        self,
        rut: str,
        nuevo_telefono: str
    ) -> Propietario:
        propietario = self.obtener_propietario_por_rut(rut)
        propietario.actualizar_contacto(nuevo_telefono)
        self.propietario_dao.actualizar(propietario)
        return propietario

    def eliminar_propietario(self, id_propietario: int) -> None:
        self.propietario_dao.eliminar(id_propietario)

    # Veterinarios
    def registrar_veterinario(
        self,
        rut: str,
        nombre_completo: str,
        telefono: str,
        id_especialidad: int
    ) -> Veterinario:
        especialidad = self.obtener_especialidad(id_especialidad)
        veterinario = Veterinario(
            rut=rut,
            nombre_completo=nombre_completo,
            telefono=telefono,
            especialidad=especialidad
        )
        self.veterinario_dao.insertar(veterinario)
        return veterinario

    def obtener_veterinario_por_id(
        self,
        id_veterinario: int | str
    ) -> Veterinario:
        id_valido = ValidadorEntradas.validar_id(
            id_veterinario,
            "veterinario"
        )
        return self.veterinario_dao.obtener_por_id(id_valido)

    def obtener_veterinario_por_rut(self, rut: str) -> Veterinario:
        return self.veterinario_dao.obtener_por_rut(rut)

    def buscar_veterinarios(self, nombre: str) -> list[Veterinario]:
        return self.veterinario_dao.buscar_por_nombre(nombre)

    def listar_veterinarios(self) -> list[Veterinario]:
        return self.veterinario_dao.listar_todos()

    def actualizar_veterinario(self, veterinario: Veterinario) -> None:
        if veterinario.especialidad.id_especialidad is None:
            raise exceptions.ReglaNegocioError(
                "El veterinario debe tener una especialidad persistida."
            )
        self.obtener_especialidad(veterinario.especialidad.id_especialidad)
        self.veterinario_dao.actualizar(veterinario)

    def cambiar_nombre_veterinario(
        self,
        rut: str,
        nuevo_nombre: str
    ) -> Veterinario:
        veterinario = self.obtener_veterinario_por_rut(rut)
        veterinario.actualizar_nombre(nuevo_nombre)
        self.veterinario_dao.actualizar(veterinario)
        return veterinario

    def cambiar_contacto_veterinario(
        self,
        rut: str,
        nuevo_telefono: str
    ) -> Veterinario:
        veterinario = self.obtener_veterinario_por_rut(rut)
        veterinario.actualizar_contacto(nuevo_telefono)
        self.veterinario_dao.actualizar(veterinario)
        return veterinario

    def cambiar_especialidad_veterinario(
        self,
        rut: str,
        id_especialidad: int | str
    ) -> Veterinario:
        veterinario = self.obtener_veterinario_por_rut(rut)
        nueva_especialidad = self.obtener_especialidad(id_especialidad)
        veterinario.actualizar_especialidad(nueva_especialidad)
        self.veterinario_dao.actualizar(veterinario)
        return veterinario

    def eliminar_veterinario(self, id_veterinario: int) -> None:
        self.veterinario_dao.eliminar(id_veterinario)