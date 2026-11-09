from __future__ import annotations

import sqlite3
from datetime import date, datetime

from database.conexion import ConexionDB
from exceptions import exceptions
from models.feriado import Feriado
from utilities.fechas import date_a_sqlite, sqlite_a_date


class FeriadoDAO:
    def __init__(self, conexion_db: ConexionDB):
        self.db = conexion_db
        self._crear_tablas()

    def _crear_tablas(self) -> None:
        ddl_feriado = """
        CREATE TABLE IF NOT EXISTS FERIADO (
            fecha TEXT PRIMARY KEY,
            nombre TEXT NOT NULL,
            tipo TEXT NOT NULL,
            es_irrenunciable INTEGER NOT NULL CHECK (es_irrenunciable IN (0, 1))
        );
        """
        ddl_cache = """
        CREATE TABLE IF NOT EXISTS FERIADO_CACHE (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            anio INTEGER NOT NULL,
            mes INTEGER NOT NULL,
            fecha_actualizacion TEXT NOT NULL
        );
        """
        with self.db.obtener_conexion() as conn:
            conn.execute(ddl_feriado)
            conn.execute(ddl_cache)

    def cache_corresponde_a(self, anio: int, mes: int) -> bool:
        sql = """
        SELECT 1
        FROM FERIADO_CACHE
        WHERE id = 1 AND anio = ? AND mes = ?;
        """
        with self.db.obtener_conexion() as conn:
            return conn.execute(sql, (anio, mes)).fetchone() is not None

    def reemplazar_cache(
        self,
        feriados: list[Feriado],
        anio: int,
        mes: int,
        fecha_actualizacion: datetime
    ) -> None:
        try:
            with self.db.obtener_conexion() as conn:
                conn.execute("DELETE FROM FERIADO;")
                conn.executemany(
                    """
                    INSERT INTO FERIADO
                    (fecha, nombre, tipo, es_irrenunciable)
                    VALUES (?, ?, ?, ?);
                    """,
                    [
                        (
                            date_a_sqlite(feriado.fecha),
                            feriado.nombre,
                            feriado.tipo,
                            int(feriado.es_irrenunciable),
                        )
                        for feriado in feriados
                    ],
                )
                conn.execute(
                    """
                    INSERT OR REPLACE INTO FERIADO_CACHE
                    (id, anio, mes, fecha_actualizacion)
                    VALUES (1, ?, ?, ?);
                    """,
                    (anio, mes, fecha_actualizacion.isoformat()),
                )
        except sqlite3.Error as error:
            raise exceptions.PersistenciaError(
                f"No se pudo actualizar la caché de feriados: {error}"
            ) from error

    def listar_todos(self) -> list[Feriado]:
        sql = """
        SELECT fecha, nombre, tipo, es_irrenunciable
        FROM FERIADO
        ORDER BY fecha ASC;
        """
        with self.db.obtener_conexion() as conn:
            filas = conn.execute(sql).fetchall()
        return [
            Feriado(
                fecha=sqlite_a_date(fila[0]),
                nombre=fila[1],
                tipo=fila[2],
                es_irrenunciable=bool(fila[3]),
            )
            for fila in filas
        ]
