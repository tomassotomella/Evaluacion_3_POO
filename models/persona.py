'''        class Persona {
            <<abstract>>
            #idPersona: int
            #rut: String
            #nombreCompleto: String
            #telefono: String
            #Persona(idPersona: int, rut: String, nombreCompleto: String, telefono: String): void
            -validarRut$(rut: String): boolean
            -validarTelefono$(telefono: String): boolean
            +crearPropietario(idPropietario: int, rut: String, nombreCompleto: String, telefono: String) Propietario
            +crearVeterinario(id: int, rut: String, nombre: String, tel: String, esp: Especialidad) Veterinario
            +actualizarContacto(nuevotelefono: String): void
        }'''
import re
from utilities.ValidadorEntradas import ValidadorEntradas
from exceptions import exceptions

class Persona:
    def __init__(
        self,
        rut: str,
        nombre_completo: str,
        telefono: str,
        id_persona: int | None = None
    ):
        self._id_persona = ValidadorEntradas.validar_id(id_persona, "persona")
        #Inicializar atributos
        self._rut = ''
        self._nombre_completo = ''
        self._telefono = ''
        #Asignación de setters
        self.rut = rut
        self.nombre_completo = nombre_completo
        self.telefono = telefono

    @property
    def id_persona(self) -> int | None:
        return self._id_persona

    def asignar_id(self, id_persona: int) -> None:
        if self._id_persona is not None:
            raise exceptions.ReglaNegocioError("La persona ya tiene un ID asignado y no puede ser reasignado.")
        self._id_persona = ValidadorEntradas.validar_id(id_persona, "persona")
    @property
    def rut(self) -> str:
        return self._rut
    @rut.setter
    def rut(self, valor: str) -> None:
        rut_valido = ValidadorEntradas.validar_rut(valor)
        self._rut = rut_valido

    @property
    def nombre_completo(self) -> str:
        return self._nombre_completo
    @nombre_completo.setter
    def nombre_completo(self, valor: str) -> None:
        nombre_valido = ValidadorEntradas.validar_nombre_alfabetico(
            valor,
            nombre_campo='Nombre Completo'
        )
        self._nombre_completo = nombre_valido

    @property
    def telefono(self) -> str:
        return self._telefono
    @telefono.setter
    def telefono(self, valor: str) -> None:
        fono_valido = ValidadorEntradas.validar_telefono(valor)
        self._telefono = fono_valido
    
    
    def __str__(self) -> str:
        return self.nombre_completo

    def actualizar_nombre(self, nuevo_nombre: str) -> None:
        self.nombre_completo = nuevo_nombre

    def actualizar_contacto(self, nuevo_telefono: str) -> None:
        self.telefono = nuevo_telefono

    