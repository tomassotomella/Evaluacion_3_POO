
from exceptions import exceptions
from datetime import datetime, date
import re
class ValidadorEntradas:
    def __init__(self):
        pass

    @staticmethod
    def sanitizar_texto(texto: str) -> str:
        if not isinstance(texto, str):
            raise exceptions.EntradaInvalidaException(texto ,"debe ser una cadena de caracteres.")

        return " ".join(texto.strip().split())
    
    @staticmethod
    def validar_no_vacio(texto: str, nombre: str = "Texto") -> str:
        texto_limpio = ValidadorEntradas.sanitizar_texto(texto)

        if not texto_limpio:
            raise exceptions.EntradaInvalidaException(
                nombre,
                "no puede estar vacío"
            )

        return texto_limpio
    @staticmethod
    def validar_longitud(texto: str, max: int, nombre: str = 'Texto') -> str:
        texto_valido = ValidadorEntradas.validar_no_vacio(texto, nombre)
        if len(texto_valido) > max:
            raise exceptions.EntradaInvalidaException(
                nombre,
                f"no puede tener más de {max} caracteres"
            )
        return texto_valido

    @staticmethod
    def validar_entero(valor: str | int, nombre: str = "Número", minimo: int = None, maximo: int = None) -> int:
        try:
            valor = int(valor)
        except (ValueError, TypeError):
            raise exceptions.EntradaInvalidaException(
                nombre,
                "debe ser un número entero"
            )
        if minimo is not None and valor < minimo:
            raise exceptions.EntradaInvalidaException(
                nombre,
                f"debe ser mayor o igual a {minimo}"
            )
        if maximo is not None and valor > maximo:
            raise exceptions.EntradaInvalidaException(
                nombre,
                f"debe ser menor o igual a {maximo}"
            )
        return valor

    @staticmethod
    def validar_decimal(valor: str | float, nombre: str = "Número", minimo: float = None, maximo: float = None) -> float:
        try:
            valor = float(valor)
        except (ValueError, TypeError):
            raise exceptions.EntradaInvalidaException(
                nombre,
                "debe ser un número decimal"
            )
        if minimo is not None and valor < minimo:
            raise exceptions.EntradaInvalidaException(
                nombre,
                f"debe ser mayor o igual a {minimo}"
            )
        if maximo is not None and valor > maximo:
            raise exceptions.EntradaInvalidaException(
                nombre,
                f"debe ser menor o igual a {maximo}"
            )
        return valor

    @staticmethod
    def validar_id(valor: str | int | None, entidad: str = "Entidad") -> int | None:
        """Valida un ID generado por la base de datos o aún no asignado."""
        if valor is None:
            return None
        return ValidadorEntradas.validar_entero(
            valor,
            f"ID de {entidad}",
            minimo=1
        )

    @staticmethod
    def validar_fecha(valor, nombre: str = "Fecha") -> datetime:
        if isinstance(valor, datetime):
            return valor

        if isinstance(valor, date):
            return datetime.combine(valor, datetime.min.time())

        if isinstance(valor, str):
            try:
                return datetime.fromisoformat(valor.strip())
            except ValueError as error:
                raise exceptions.EntradaInvalidaException(
                    nombre,
                    "formato inválido. Use YYYY-MM-DD o YYYY-MM-DD HH:MM"
                ) from error

        raise exceptions.EntradaInvalidaException(
            nombre,
            "formato inválido. Use YYYY-MM-DD o YYYY-MM-DD HH:MM"
        )
    @staticmethod
    def validar_instancia(valor, tipo, nombre: str = "Entidad", permitir_nulo: bool = False):
        if valor is None:
            if permitir_nulo:
                return None
        if not isinstance(valor, tipo):
            raise exceptions.EntradaInvalidaException(nombre, f'debe ser una instancia de tipo {tipo.__name__}') 
        return valor 

    @staticmethod
    def validar_nombre_alfabetico(
        nombre: str,
        nombre_campo: str = 'Nombre Completo',
        maximo: int = 4000
    ) -> str:
        nombre_limpio = ValidadorEntradas.validar_longitud(
            nombre,
            max=maximo,
            nombre=nombre_campo
        )
        patron = r"^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s'-]+$"
        if not re.fullmatch(patron, nombre_limpio):
            raise exceptions.NombreInvalidoException(nombre_limpio, nombre_campo)
        return nombre_limpio  
    
    @staticmethod
    def validar_rut( rut: str) -> str:
        rut_sin_puntos = rut.replace(".", "")
        rut_limpio = ValidadorEntradas.validar_no_vacio(rut_sin_puntos, 'RUT').upper()
        patron = r"^[0-9]{7,8}-[0-9K]$"
        if not re.fullmatch(patron, rut_limpio):
            raise exceptions.RutInvalidoException(rut_limpio)
        return rut_limpio
    
    @staticmethod
    def validar_telefono(telefono:str) -> str:
        fono_limpio = ValidadorEntradas.validar_no_vacio(telefono, 'Teléfono')
        if fono_limpio.startswith("+56"):
            fono_limpio = fono_limpio[3:]
        patron = r"^9[0-9]{8}$"
        if not re.fullmatch(patron, fono_limpio):
            raise exceptions.EntradaInvalidaException('teléfono', 'no cumple con el formato (+56) 9 XXXX XXXX')
        return f'+56{fono_limpio}'