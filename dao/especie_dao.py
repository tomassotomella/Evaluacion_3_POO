import sqlite3
from exceptions import exceptions
from database.conexion import ConexionDB
from models.especie import Especie

class EspecieDAO:
    def __init__(self, conexion_db: ConexionDB):
        self.conexion_db = conexion_db
        self._crear_tabla()

    def _crear_tabla(self) -> None:
        ddl = """
        CREATE TABLE IF NOT EXISTS ESPECIE (
            id_especie INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre_especie TEXT NOT NULL UNIQUE,
            esperanza_vida_max INTEGER NOT NULL
        );
        """
        with self.conexion_db.obtener_conexion() as conn:
            conn.execute(ddl)

    def insertar(self, especie: Especie) -> int:
        sql = """
        INSERT INTO ESPECIE (nombre_especie, esperanza_vida_max)
        VALUES (?, ?);
        """
        try:
            with self.conexion_db.obtener_conexion() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, (
                    especie.nombre_especie,
                    especie.esperanza_vida_max
                ))
                nuevo_id = cursor.lastrowid
                especie.asignar_id(nuevo_id)
                return nuevo_id
        except sqlite3.IntegrityError as error:
            if "UNIQUE" in str(error).upper():
                raise exceptions.EntidadExistenteException("Especie", especie.nombre_especie)
            raise exceptions.PersistenciaError(f"Error de persistencia al registrar especie: {error}")

    def obtener_por_id(self, id_especie: int) -> Especie:
        """Retorna la especie o lanza EntidadNoEncontradaException si no existe."""
        sql = """
        SELECT id_especie, esperanza_vida_max, nombre_especie
        FROM ESPECIE
        WHERE id_especie = ?;
        """
        with self.conexion_db.obtener_conexion() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (id_especie,))
            fila = cursor.fetchone()
            if fila is None:
                raise exceptions.EntidadNoEncontradaException("Especie", id_especie)
            return self._mapear_fila(fila)

    def buscar_por_nombre(self, nombre: str) -> list[Especie]:
        """
        Busca especies por coincidencia parcial en nombre_especie.
        Usa consultas parametrizadas para evitar inyecciones SQL.
        """
        sql = """
        SELECT id_especie, esperanza_vida_max, nombre_especie
        FROM ESPECIE
        WHERE nombre_especie LIKE ?
        ORDER BY nombre_especie ASC;
        """
        patron = f"%{nombre}%"
        with self.conexion_db.obtener_conexion() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (patron,))
            filas = cursor.fetchall()
            return [self._mapear_fila(fila) for fila in filas]

    def listar_todos(self) -> list[Especie]:
        sql = """
        SELECT id_especie, esperanza_vida_max, nombre_especie
        FROM ESPECIE
        ORDER BY nombre_especie ASC;
        """
        with self.conexion_db.obtener_conexion() as conn:
            cursor = conn.cursor()
            cursor.execute(sql)
            filas = cursor.fetchall()
            return [self._mapear_fila(fila) for fila in filas]

    def eliminar(self, id_especie: int) -> bool:
        """Elimina la especie y retorna True si afectó filas."""
        sql = "DELETE FROM ESPECIE WHERE id_especie = ?;"
        try:
            with self.conexion_db.obtener_conexion() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, (id_especie,))
                if cursor.rowcount == 0:
                    raise exceptions.EntidadNoEncontradaException("Especie", id_especie)
                return True
        except sqlite3.IntegrityError:
            raise exceptions.ReferenciaIntegridadError(
                f"No es posible eliminar la especie #{id_especie} porque tiene mascotas asociadas."
            )

    def _mapear_fila(self, fila: tuple) -> Especie:
        return Especie(
            id_especie=fila[0],
            esperanza_vida_max=fila[1],
            nombre_especie=fila[2]
        )


EspecieDao = EspecieDAO

