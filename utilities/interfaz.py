import os
from datetime import datetime
from utilities.ValidadorEntradas import ValidadorEntradas
from exceptions import exceptions
import subprocess

def pausar(mensaje: str = "\nPresione [ENTER] para regresar..."):
    # Pausa la ejecución hasta que el usuario presione Enter.
    input(mensaje)

def limpiar_pantalla():
    # Limpia la consola dependiendo del sistema operativo.
    comando = 'cls' if os.name == 'nt' else 'clear'
    subprocess.run(comando, shell=True)

def limpiar_y_encabezado(titulo: str) -> None:
    """Limpia la pantalla y muestra un encabezado centrado."""
    limpiar_pantalla()
    ancho = 60
    print("=" * ancho)
    print(titulo.center(ancho).upper())
    print("=" * ancho)
    print()

def formatear_moneda(monto: int) -> str:
    return f"${monto:,.0f}".replace(",", ".")

def mostrar_exito(mensaje: str) -> None:
    print(f"\n [ÉXITO] {mensaje}")

def mostrar_error(mensaje: str) -> None:
    print(f"\n [ERROR] {mensaje}")

def mostrar_subtitulo(texto: str) -> None:
    print(f"\n--- {texto.strip().upper()} ---")


def mostrar_advertencia(mensaje: str) -> None:
    print(f"\n [ADVERTENCIA] {mensaje}")

def leer_entero(
    mensaje: str,
    nombre_campo: str = "Número",
    minimo: int = None,
    maximo: int = None
) -> int:
    while True:
        entrada = input(f"\n{mensaje}").strip()
        try:
            return ValidadorEntradas.validar_entero(
                valor=entrada,
                nombre=nombre_campo,
                minimo=minimo,
                maximo=maximo
            )
        except exceptions.EntradaInvalidaException as e:
            mostrar_error(str(e))

def leer_opcion_menu(maximo: int) -> int:
    return leer_entero(
        mensaje='Seleccione una opción: ',
        nombre_campo='Opción',
        minimo=0,
        maximo=maximo
    )

def leer_rut(mensaje: str = "Ingrese RUT (ej. 12345678-K): ") -> str:
    while True:
        entrada = input(mensaje)
        try:
            return ValidadorEntradas.validar_rut(entrada)
        except (exceptions.RutInvalidoException, exceptions.EntradaInvalidaException) as error:
            mostrar_error(str(error))


def leer_telefono(
    mensaje: str = "Ingrese teléfono (ej: 912345678): ",
) -> str:
    while True:
        entrada = input(mensaje)
        try:
            return ValidadorEntradas.validar_telefono(entrada)
        except exceptions.EntradaInvalidaException as error:
            mostrar_error(str(error))

def leer_texto(prompt: str, max_longitud: int, nombre_campo: str = "Texto") -> str:
    while True:
        entrada = input(prompt)
        try:
            return ValidadorEntradas.validar_longitud(
                texto=entrada,
                max=max_longitud,
                nombre=nombre_campo
            )
        except exceptions.EntradaInvalidaException as error:
            mostrar_error(str(error))

def leer_nombre_alfabetico(
    prompt: str = "Ingrese nombre: ",
    nombre_campo: str = "Nombre Completo",
    maximo: int = 4000,
) -> str:
    while True:
        entrada = input(prompt)
        try:
            return ValidadorEntradas.validar_nombre_alfabetico(
                nombre=entrada,
                nombre_campo=nombre_campo,
                maximo=maximo
            )
        except (exceptions.NombreInvalidoException, exceptions.EntradaInvalidaException) as error:
            mostrar_error(str(error))

def leer_fecha(mensaje: str = "Ingrese fecha (YYYY-MM-DD HH:MM): ", nombre_campo: str = "Fecha") -> datetime:
    
    while True:
        entrada = input(mensaje)
        try:
            return ValidadorEntradas.validar_fecha(
                valor=entrada,
                nombre=nombre_campo
            )
        except exceptions.EntradaInvalidaException as error:
            mostrar_error(str(error))

def desea_confirmar(mensaje: str) -> bool:
    print(f"\n{mensaje}")
    print("1. Sí")
    print("2. No")

    opcion = leer_entero(
        mensaje="Seleccione una opción (1-2): ",
        nombre_campo="Opción de confirmación",
        minimo=1,
        maximo=2
    )
    return opcion == 1

def leer_confirmacion(mensaje: str = "¿Desea confirmar la acción?") -> bool:
    return desea_confirmar(mensaje)