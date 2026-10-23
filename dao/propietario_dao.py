import sqlite3
from exceptions import exceptions
from database.conexion import ConexionDB
from models.propietario import Propietario

class PropietarioDAO:
    def __init__(self, conexion_db: ConexionDB):
        self.conexion_db = conexion_db
        self._crear_tabla()

    def _crear_tabla(self) -> None:
        ddl = """
        CREATE TABLE IF NOT EXISTS PROPIETARIO (
            id_propietario INTEGER PRIMARY KEY AUTOINCREMENT,
            rut TEXT UNIQUE NOT NULL,
            nombre_completo TEXT NOT NULL,
            telefono TEXT NOT NULL
        );
        """
        with self.conexion_db.obtener_conexion() as conn:
            conn.execute(ddl)

    def insertar(self, propietario: Propietario) -> int:
        sql = """
        INSERT INTO PROPIETARIO (rut, nombre_completo, telefono)
        VALUES (?, ?, ?);
        """
        try:
            with self.conexion_db.obtener_conexion() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, (
                    propietario.rut,
                    propietario.nombre_completo,
                    propietario.telefono
                ))
                nuevo_id = cursor.lastrowid
                propietario.asignar_id(nuevo_id)
                return nuevo_id
        except sqlite3.IntegrityError as error:
            if "UNIQUE" in str(error).upper():
                raise exceptions.EntidadExistenteException("Propietario", propietario.rut)
            raise exceptions.PersistenciaError(f"Error de persistencia al registrar propietario: {error}")

    def obtener_por_id(self, id_propietario: int) -> Propietario:
        """Retorna el propietario o lanza EntidadNoEncontradaException si no existe."""
        sql = """
        SELECT id_propietario, rut, nombre_completo, telefono
        FROM PROPIETARIO
        WHERE id_propietario = ?;
        """
        with self.conexion_db.obtener_conexion() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (id_propietario,))
            fila = cursor.fetchone()
            if fila is None:
                raise exceptions.EntidadNoEncontradaException("Propietario", id_propietario)
            return self._mapear_fila(fila)

    def obtener_por_rut(self, rut: str) -> Propietario:
        """Retorna el propietario o lanza EntidadNoEncontradaException si no existe."""
        sql = """
        SELECT id_propietario, rut, nombre_completo, telefono
        FROM PROPIETARIO
        WHERE rut = ?;
        """
        with self.conexion_db.obtener_conexion() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (rut,))
            fila = cursor.fetchone()
            if fila is None:
                raise exceptions.EntidadNoEncontradaException("Propietario", rut)
            return self._mapear_fila(fila)

    def buscar_por_nombre(self, nombre: str) -> list[Propietario]:
        """
        Busca propietarios por coincidencia parcial en nombre_completo.
        Usa consultas parametrizadas para evitar inyecciones SQL.
        """
        sql = """
        SELECT id_propietario, rut, nombre_completo, telefono
        FROM PROPIETARIO
        WHERE nombre_completo LIKE ?
        ORDER BY nombre_completo ASC;
        """
        patron = f"%{nombre}%"
        with self.conexion_db.obtener_conexion() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (patron,))
            filas = cursor.fetchall()
            return [self._mapear_fila(fila) for fila in filas]

    def listar_todos(self) -> list[Propietario]:
        sql = """
        SELECT id_propietario, rut, nombre_completo, telefono
        FROM PROPIETARIO
        ORDER BY nombre_completo ASC;
        """
        with self.conexion_db.obtener_conexion() as conn:
            cursor = conn.cursor()
            cursor.execute(sql)
            filas = cursor.fetchall()
            return [self._mapear_fila(fila) for fila in filas]

    def actualizar(self, propietario: Propietario) -> bool:
        """Actualiza el propietario y retorna True si afectó filas."""
        if propietario.id_persona is None:
            raise exceptions.ReglaNegocioError("No se puede actualizar un propietario que no posee ID asignado.")

        sql = """
        UPDATE PROPIETARIO
        SET rut = ?, nombre_completo = ?, telefono = ?
        WHERE id_propietario = ?;
        """
        with self.conexion_db.obtener_conexion() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (
                propietario.rut,
                propietario.nombre_completo,
                propietario.telefono,
                propietario.id_persona
            ))
            if cursor.rowcount == 0:
                raise exceptions.EntidadNoEncontradaException("Propietario", propietario.id_persona)
            return True

    def eliminar(self, id_propietario: int) -> bool:
        """Elimina el propietario y retorna True si afectó filas."""
        sql = "DELETE FROM PROPIETARIO WHERE id_propietario = ?;"
        try:
            with self.conexion_db.obtener_conexion() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, (id_propietario,))
                if cursor.rowcount == 0:
                    raise exceptions.EntidadNoEncontradaException("Propietario", id_propietario)
                return True
        except sqlite3.IntegrityError:
            raise exceptions.ReferenciaIntegridadError(
                f"No es posible eliminar el propietario #{id_propietario} porque tiene mascotas asociadas."
            )

    def _mapear_fila(self, fila: tuple) -> Propietario:
        return Propietario(
            id_propietario=fila[0],
            rut=fila[1],
            nombre_completo=fila[2],
            telefono=fila[3]
        )

