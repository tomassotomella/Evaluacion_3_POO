import sqlite3
from exceptions import exceptions
from database.conexion import ConexionDB
from models.especialidad import Especialidad

class EspecialidadDAO:
    def __init__(self, conexion_db: ConexionDB):
        self.conexion_db = conexion_db
        self._crear_tabla()

    def _crear_tabla(self) -> None:
        ddl = """
        CREATE TABLE IF NOT EXISTS ESPECIALIDAD (
            id_especialidad INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre_especialidad TEXT NOT NULL UNIQUE,
            descripcion TEXT NOT NULL
        );
        """
        with self.conexion_db.obtener_conexion() as conn:
            conn.execute(ddl)

    def insertar(self, especialidad: Especialidad) -> int:
        sql = """
        INSERT INTO ESPECIALIDAD (nombre_especialidad, descripcion)
        VALUES (?, ?);
        """
        try:
            with self.conexion_db.obtener_conexion() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, (
                    especialidad.nombre_especialidad,
                    especialidad.descripcion
                ))
                nuevo_id = cursor.lastrowid
                especialidad.asignar_id(nuevo_id)
                return nuevo_id
        except sqlite3.IntegrityError as error:
            if "UNIQUE" in str(error).upper():
                raise exceptions.EntidadExistenteException('Especialidad', especialidad.nombre_especialidad)
            raise exceptions.PersistenciaError(f"Error de persistencia al registrar especialidad: {error}")

    def obtener_por_id(self, id_especialidad: int) -> Especialidad:
        """Retorna la especialidad o lanza EntidadNoEncontradaException si no existe."""
        sql = """
        SELECT id_especialidad, nombre_especialidad, descripcion
        FROM ESPECIALIDAD
        WHERE id_especialidad = ?;
        """
        with self.conexion_db.obtener_conexion() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (id_especialidad,))
            fila = cursor.fetchone()
            if fila is None:
                raise exceptions.EntidadNoEncontradaException("Especialidad", id_especialidad)
            return self._mapear_fila(fila)

    def buscar_por_nombre(self, nombre: str) -> list[Especialidad]:
        """
        Busca especialidades por coincidencia parcial en nombre_especialidad.
        Usa consultas parametrizadas para evitar inyecciones SQL.
        """
        sql = """
        SELECT id_especialidad, nombre_especialidad, descripcion
        FROM ESPECIALIDAD
        WHERE nombre_especialidad LIKE ?
        ORDER BY nombre_especialidad ASC;
        """
        patron = f"%{nombre}%"
        with self.conexion_db.obtener_conexion() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (patron,))
            filas = cursor.fetchall()
            return [self._mapear_fila(fila) for fila in filas]

    def listar_todos(self) -> list[Especialidad]:
        sql = """
        SELECT id_especialidad, nombre_especialidad, descripcion
        FROM ESPECIALIDAD
        ORDER BY nombre_especialidad ASC;
        """
        with self.conexion_db.obtener_conexion() as conn:
            cursor = conn.cursor()
            cursor.execute(sql)
            filas = cursor.fetchall()
            return [self._mapear_fila(fila) for fila in filas]

    def actualizar_descripcion(self, id_especialidad: int, nueva_descripcion: str) -> bool:
        """Actualiza solo la descripción; el nombre es identidad y no se toca."""
        sql = """
        UPDATE ESPECIALIDAD
        SET descripcion = ?
        WHERE id_especialidad = ?;
        """
        with self.conexion_db.obtener_conexion() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (nueva_descripcion, id_especialidad))
            if cursor.rowcount == 0:
                raise exceptions.EntidadNoEncontradaException("Especialidad", id_especialidad)
            return True

    def eliminar(self, id_especialidad: int) -> bool:
        """Elimina la especialidad y retorna True si afectó filas."""
        sql = "DELETE FROM ESPECIALIDAD WHERE id_especialidad = ?;"
        try:
            with self.conexion_db.obtener_conexion() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, (id_especialidad,))
                if cursor.rowcount == 0:
                    raise exceptions.EntidadNoEncontradaException("Especialidad", id_especialidad)
                return True
        except sqlite3.IntegrityError:
            raise exceptions.ReferenciaIntegridadError(
                f"No es posible eliminar la especialidad #{id_especialidad} porque tiene veterinarios asociados."
            )

    def _mapear_fila(self, fila: tuple) -> Especialidad:
        return Especialidad(
            id_especialidad=fila[0],
            nombre_especialidad=fila[1],
            descripcion=fila[2]
        )