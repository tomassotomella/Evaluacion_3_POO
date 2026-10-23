class VetCareException(Exception):
    """Excepción raíz para todo el sistema VetCare."""
    pass


class DominioException(VetCareException):
    """Excepción base para errores propios del dominio."""
    pass


class SinStockException(DominioException):
    def __init__(self, medicamento: str, solicitado: int, disponible: int):
        self.medicamento = medicamento
        self.solicitado = solicitado
        self.disponible = disponible
        super().__init__(
            f"Stock insuficiente para {medicamento}: "
            f"solicitado {solicitado}, disponible {disponible}."
        )


class RutInvalidoException(DominioException):
    def __init__(self, rut: str):
        self.rut = rut
        super().__init__(f"El RUT '{rut}' no es valido.")


class NombreInvalidoException(DominioException):
    def __init__(self, nombre: str, campo: str):
        self.nombre = nombre
        super().__init__(f'El nombre {nombre} no es válido para {campo}, no puede contener caracteres especiales ni números')


class EntidadNoEncontradaException(DominioException):
    def __init__(self, entidad: str, identificador: int | str):
        self.entidad = entidad
        self.identificador = identificador
        super().__init__(
            f"No se encontro ningún registro de tipo entidad {entidad} "
            f"con identificador {identificador}."
        )


class EntradaInvalidaException(DominioException):
    def __init__(self, campo: str, motivo: str):
        self.campo = campo
        self.motivo = motivo
        super().__init__(
            f"Entrada inválida para '{campo}': {motivo}"
        )


class EntidadExistenteException(DominioException):
    def __init__(self, entidad: str, identificador):
        self.entidad = entidad
        self.identificador = identificador
        super().__init__(
            f'{entidad} con ID {identificador} ya existe'
        )


class RelacionInvalidaException(DominioException):
    def __init__(self, origen: str, destino: str, motivo: str):
        self.origen = origen
        self.destino = destino
        self.motivo = motivo
        super().__init__(
            f'Relación inválida entre {origen} y {destino}: {motivo}'
        )


class ReglaNegocioError(DominioException):
    def __init__(self, mensaje: str):
        self.mensaje = mensaje
        super().__init__(f'Error de regla de negocio: {mensaje}')

class PersistenciaError(VetCareException):
    """Excepción base para fallos originados en la capa de persistencia."""
    def __init__(self, mensaje: str):
        self.mensaje = mensaje
        super().__init__(f"Error de persistencia: {mensaje}")


class ReferenciaIntegridadError(PersistenciaError):
    """Lanzada cuando una mutación viola restricciones de claves foráneas en la BD."""
    def __init__(self, mensaje: str):
        super().__init__(f"Violación de integridad referencial: {mensaje}")
