'''        class Propietario {
            -mascotas: List~Mascota~
            +agregarMascota(mascota: Mascota): void
            +eliminarMascota(idmascota: int): boolean #ajustado para que pueda ejecutar errores
            +buscarMascota(idmascota: int): Mascota'''

from __future__ import annotations
from typing import TYPE_CHECKING
from persona import Persona
from utilities.ValidadorEntradas import ValidadorEntradas
from exceptions import exceptions

if TYPE_CHECKING:
    from mascota import Mascota

class Propietario(Persona):
    def __init__(
            self, 
            rut: str, 
            nombre_completo: str, 
            telefono: str,
            id_propietario: int | None = None,
            ):
        super().__init__(rut, nombre_completo, telefono, id_propietario)
        self._mascotas = []

    @property
    def id_propietario(self) -> int:
        return self._id_persona

    @property
    def mascotas(self) -> list[Mascota]:
        return self._mascotas.copy()
    
    def agregar_mascota(self, mascota: Mascota) -> None:
        from mascota import Mascota
        mascota_valida = ValidadorEntradas.validar_instancia(mascota, Mascota, 'Mascota')
        if mascota_valida in self._mascotas:
            raise exceptions.EntidadExistenteException('Mascota', mascota_valida.id_mascota)
        self._mascotas.append(mascota_valida)
        
    def eliminar_mascota(self, id_mascota: int) -> bool:
        """Remueve la mascota de la lista y retorna True si la eliminó."""
        id_valido = ValidadorEntradas.validar_entero(id_mascota, 'ID de mascota', minimo = 1)
        for mascota in self._mascotas:
            if mascota.id_mascota == id_valido:
                self._mascotas.remove(mascota)
                return True
        raise exceptions.EntidadNoEncontradaException('Mascota', id_valido)

    def buscar_mascota(self, id_mascota: int) -> Mascota:
        id_valido = ValidadorEntradas.validar_entero(id_mascota, 'ID de mascota', minimo = 1)
        for mascota in self._mascotas:
            if mascota.id_mascota == id_valido:
                return mascota
        raise exceptions.EntidadNoEncontradaException('Mascota', id_valido)