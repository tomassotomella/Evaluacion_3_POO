from datetime import date, datetime

from database.conexion import ConexionDB


def activar_feriado() -> None:
    hoy = date.today()
    conexion = ConexionDB()

    with conexion.obtener_conexion() as conn:
        conn.execute("DELETE FROM FERIADO_CACHE WHERE id = 1")
        conn.execute(
            """
            INSERT INTO FERIADO_CACHE
            (id, anio, mes, fecha_actualizacion)
            VALUES (1, ?, ?, ?)
            """,
            (hoy.year, hoy.month, datetime.now().isoformat()),
        )
        conn.execute(
            """
            INSERT OR REPLACE INTO FERIADO
            (fecha, nombre, tipo, es_irrenunciable)
            VALUES (?, ?, ?, ?)
            """,
            (hoy.isoformat(), "Feriado Simulado de Prueba", "Civil", 1),
        )

    print(
        f"\n[OK] La fecha de hoy ({hoy}) fue configurada como feriado "
        "en clinica_vetcare.db."
    )
    print("Ya puedes ejecutar 'python main.py' para probar el modo festivo.")


if __name__ == "__main__":
    activar_feriado()
