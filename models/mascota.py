from __future__ import annotations
from datetime import datetime, timedelta, date
from typing import TYPE_CHECKING
from especie import Especie
from utilities.ValidadorEntradas import ValidadorEntradas
from exceptions import exceptions

if TYPE_CHECKING:
    from consulta import Consulta
    from propietario import Propietario

class Mascota:
    def __init__(
        self,
        nombre: str,
        fecha_nacimiento: date,
        especie: Especie,
        propietario: Propietario,
        id_mascota: int | None = None,
        raza: str = "Sin especificar",
    ):
        self._id_mascota = ValidadorEntradas.validar_id(id_mascota, "mascota")
        #Inicialización de atributos privados
        self._nombre = ""
        self._especie = None
        self._fecha_nacimiento = None
        self._propietario = None
        self._consultas = []
        self._raza = ""

        # Asignación de valores a los atributos privados con validación
        self.nombre = nombre
        self.especie = especie
        self.fecha_nacimiento = fecha_nacimiento
        self.propietario = propietario
        self.raza = raza
    
    @property
    def id_mascota(self) -> int | None:
        return self._id_mascota

    def asignar_id(self, id_mascota: int) -> None:
        if self._id_mascota is not None:
            raise exceptions.ReglaNegocioError('La mascota ya tiene un ID asignado y no puede ser reasignado.')
        self._id_mascota = ValidadorEntradas.validar_id(id_mascota, "mascota")
    @property
    def nombre(self) -> str:
        return self._nombre 
    @nombre.setter
    def nombre(self, valor: str):
        nombre_limpio = ValidadorEntradas.validar_longitud(
            valor,
            max=4000,
            nombre='Nombre de mascota'
        )
        self._nombre = nombre_limpio

    @property
    def raza(self) -> str:
        return self._raza

    @raza.setter
    def raza(self, valor: str) -> None:
        self._raza = ValidadorEntradas.validar_longitud(
            valor,
            max=100,
            nombre="Raza",
        )

    @property
    def fecha_nacimiento(self) -> date:
        return self._fecha_nacimiento
    @fecha_nacimiento.setter
    def fecha_nacimiento(self, fecha: str | date | datetime):
        self._fecha_nacimiento = self.validar_fecha_nacimiento(fecha, self.especie.esperanza_vida_max)

    @property
    def especie(self) -> Especie:
        return self._especie
    @especie.setter
    def especie(self, valor: Especie):
        especie_valida = ValidadorEntradas.validar_instancia(valor, Especie, 'Especie')
        self._especie = especie_valida

    @property
    def propietario(self) -> Propietario:
        return self._propietario
    @propietario.setter
    def propietario(self, valor: Propietario):
        propietario_valido = self._validar_propietario(valor)
        self._propietario = propietario_valido

    @staticmethod
    def _validar_propietario(valor: Propietario) -> Propietario:
        from propietario import Propietario

        return ValidadorEntradas.validar_instancia(
            valor,
            Propietario,
            'propietario'
        )

    @property
    def consultas(self) -> list[Consulta]:
        return self._consultas.copy()

    @staticmethod
    def validar_fecha_nacimiento(fecha: str | date | datetime, expectativa_vida_maxima: int) -> date:
        fecha_valida = ValidadorEntradas.validar_fecha(fecha, 'Fecha de nacimiento').date()
        hoy = datetime.now().date()
        if fecha_valida > hoy:
            raise exceptions.ReglaNegocioError('No se puede registrar una mascota con fecha de nacimiento en el futuro.')
        anio_limite = hoy.year - expectativa_vida_maxima
        if fecha_valida.year < anio_limite:
            raise exceptions.ReglaNegocioError(
                f'La fecha de nacimiento supera la esperanza de vida máxima de la especie ({expectativa_vida_maxima} años).'
            )
        return fecha_valida
    '''def obtener_fecha_actual(self) -> str:''' #Eliminada por sobreingenieria

    def actualizar_nombre(self, nuevo_nombre: str) -> None:
            self.nombre = nuevo_nombre

    def edad(self) -> tuple[int, int, int]:
        hoy = date.today()
        anios = hoy.year - self.fecha_nacimiento.year
        meses = hoy.month - self.fecha_nacimiento.month
        dias = hoy.day - self.fecha_nacimiento.day
        if dias < 0:
            meses -= 1
            dias += (date(hoy.year, hoy.month, 1) - timedelta(days=1)).day
        if meses < 0:
            anios -= 1
            meses += 12
        return anios, meses, dias
    
    def calcular_edad_anios(self) -> int:
        return self.edad()[0]
    
    def agregar_consulta(self, consulta: Consulta) -> None:
        from consulta import Consulta
        consulta_valida = ValidadorEntradas.validar_instancia(consulta, Consulta, 'Consulta')
        if consulta_valida.mascota is not self:
            raise exceptions.RelacionInvalidaException('Mascota','Consulta', 'la consulta no pertenece a la mascota')
        if any(
            consulta_previa is consulta_valida
            or (
                consulta_previa.id_consulta is not None
                and consulta_previa.id_consulta == consulta_valida.id_consulta
            )
            for consulta_previa in self._consultas
        ):
            raise exceptions.EntidadExistenteException('Consulta', consulta.id_consulta)
        self._consultas.append(consulta_valida)
        
    '''def obtener_historial(self) -> list[Consulta]:
        return self._consultas.copy()''' # reemplazado por un getter (@property)
    
    def cambiar_propietario(self, nuevo_propietario: Propietario) -> None:
        propietario_valido = self._validar_propietario(nuevo_propietario)

        if propietario_valido is self._propietario:
            raise exceptions.ReglaNegocioError('no se puede cambiar el propietario si el propietario actual y el nuevo son el mismo')

        # Los objetos hidratados desde la BD no repueblan la lista de mascotas
        # del propietario, por lo que solo se desvincula si la mascota figura
        # registrada en el propietario actual.
        if any(mascota is self for mascota in self._propietario.mascotas):
            self.propietario.eliminar_mascota(self.id_mascota)

        propietario_valido.agregar_mascota(self)
        self.propietario = propietario_valido