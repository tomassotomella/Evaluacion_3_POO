from datetime import date

from database.conexion import ConexionDB


def restaurar_dia() -> None:
    hoy = date.today().isoformat()
    conexion = ConexionDB()

    with conexion.obtener_conexion() as conn:
        conn.execute("DELETE FROM FERIADO WHERE fecha = ?", (hoy,))

    print(f"\n[OK] El feriado simulado de la fecha ({hoy}) fue eliminado.")
    print("La fecha vuelve a operar como día hábil normal.")


if __name__ == "__main__":
    restaurar_dia()
