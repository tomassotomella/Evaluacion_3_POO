from datetime import date, datetime

from exceptions import exceptions
from utilities.ValidadorEntradas import ValidadorEntradas


FORMATO_SQLITE_FECHA = "%Y-%m-%d"
FORMATO_SQLITE_DATETIME = "%Y-%m-%d %H:%M:%S"


def date_a_sqlite(valor: date | None, permitir_nulo: bool = False) -> str | None:
    """Convierte una fecha Python al formato ISO usado por SQLite."""
    if valor is None:
        if permitir_nulo:
            return None
        raise exceptions.EntradaInvalidaException("Fecha", "no puede estar vacía")

    if isinstance(valor, datetime):
        raise TypeError("Se esperaba un date, no un datetime.")

    valor_validado = ValidadorEntradas.validar_instancia(
        valor,
        date,
        "Fecha",
        permitir_nulo=permitir_nulo
    )
    if valor_validado is None:
        return None

    return valor_validado.strftime(FORMATO_SQLITE_FECHA)


def datetime_a_sqlite(valor: datetime | None, permitir_nulo: bool = False) -> str | None:
    """Convierte un datetime Python al formato de fecha y hora de SQLite."""
    if valor is None:
        if permitir_nulo:
            return None
        raise exceptions.EntradaInvalidaException("Fecha y hora", "no puede estar vacía")

    valor_validado = ValidadorEntradas.validar_instancia(
        valor,
        datetime,
        "Fecha y hora",
        permitir_nulo=permitir_nulo
    )
    if valor_validado is None:
        return None

    return valor_validado.strftime(FORMATO_SQLITE_DATETIME)


def sqlite_a_date(valor: str | date | None, permitir_nulo: bool = False) -> date | None:
    """Convierte una fecha ISO almacenada como TEXT en SQLite a date."""
    if valor is None:
        if permitir_nulo:
            return None
        raise exceptions.EntradaInvalidaException(
            "Fecha almacenada en SQLite",
            "no puede estar vacía"
        )

    if isinstance(valor, datetime):
        raise TypeError("Se esperaba un date o texto SQLite, no un datetime.")

    if isinstance(valor, date):
        return valor

    valor_limpio = ValidadorEntradas.validar_no_vacio(
        valor,
        "Fecha almacenada en SQLite"
    )
    try:
        return date.fromisoformat(valor_limpio)
    except ValueError:
        try:
            return datetime.strptime(valor_limpio, FORMATO_SQLITE_FECHA).date()
        except ValueError as error:
            raise exceptions.EntradaInvalidaException(
                "Fecha almacenada en SQLite",
                "no tiene un formato ISO válido"
            ) from error


def sqlite_a_datetime(valor: str | datetime | None, permitir_nulo: bool = False) -> datetime | None:
    """Convierte una fecha y hora ISO almacenada como TEXT en SQLite a datetime."""
    if valor is None:
        if permitir_nulo:
            return None
        raise exceptions.EntradaInvalidaException(
            "Fecha y hora almacenada en SQLite",
            "no puede estar vacía"
        )

    if isinstance(valor, datetime):
        return valor

    valor_limpio = ValidadorEntradas.validar_no_vacio(
        valor,
        "Fecha y hora almacenada en SQLite"
    )
    try:
        return datetime.fromisoformat(valor_limpio)
    except ValueError:
        try:
            return datetime.strptime(valor_limpio, FORMATO_SQLITE_DATETIME)
        except ValueError as error:
            raise exceptions.EntradaInvalidaException(
                "Fecha y hora almacenada en SQLite",
                "no tiene un formato ISO válido"
            ) from error


def date_opcional_a_sqlite(valor: date | None) -> str | None:
    """Convierte una fecha opcional a TEXT de SQLite o None."""
    return date_a_sqlite(valor, permitir_nulo=True)


def datetime_opcional_a_sqlite(valor: datetime | None) -> str | None:
    """Convierte un datetime opcional a TEXT de SQLite o None."""
    return datetime_a_sqlite(valor, permitir_nulo=True)


def sqlite_a_date_opcional(valor: str | date | None) -> date | None:
    """Convierte un TEXT opcional de SQLite a date o None."""
    return sqlite_a_date(valor, permitir_nulo=True)


def sqlite_a_datetime_opcional(valor: str | datetime | None) -> datetime | None:
    """Convierte un TEXT opcional de SQLite a datetime o None."""
    return sqlite_a_datetime(valor, permitir_nulo=True)
