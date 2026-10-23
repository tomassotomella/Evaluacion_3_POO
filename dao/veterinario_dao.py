import sqlite3
from exceptions import exceptions
from database.conexion import ConexionDB
from models.veterinario import Veterinario
from dao.especialidad_dao import EspecialidadDAO

class VeterinarioDAO:
    def __init__(self, conexion_db: ConexionDB, especialidad_dao: EspecialidadDAO | None = None):
        self.conexion_db = conexion_db
        self.especialidad_dao = especialidad_dao or EspecialidadDAO(conexion_db)
        self._crear_tabla()

    def _crear_tabla(self) -> None:
        ddl = """
        CREATE TABLE IF NOT EXISTS VETERINARIO (
            id_veterinario INTEGER PRIMARY KEY AUTOINCREMENT,
            rut TEXT UNIQUE NOT NULL,
            nombre_completo TEXT NOT NULL,
            telefono TEXT NOT NULL,
            id_especialidad INTEGER NOT NULL,
            FOREIGN KEY (id_especialidad) REFERENCES ESPECIALIDAD(id_especialidad)
        );
        """
        with self.conexion_db.obtener_conexion() as conn:
            conn.execute(ddl)

    def insertar(self, veterinario: Veterinario) -> int:
        if veterinario.especialidad is None or veterinario.especialidad.id_especialidad is None:
            raise exceptions.ReglaNegocioError("El veterinario debe tener una especialidad registrada con ID.")

        sql = """
        INSERT INTO VETERINARIO (rut, nombre_completo, telefono, id_especialidad)
        VALUES (?, ?, ?, ?);
        """
        try:
            with self.conexion_db.obtener_conexion() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, (
                    veterinario.rut,
                    veterinario.nombre_completo,
                    veterinario.telefono,
                    veterinario.especialidad.id_especialidad
                ))
                nuevo_id = cursor.lastrowid
                veterinario.asignar_id(nuevo_id)
                return nuevo_id
        except sqlite3.IntegrityError as error:
            if "UNIQUE" in str(error).upper():
                raise exceptions.EntidadExistenteException("Veterinario", veterinario.rut)
            if "FOREIGN KEY" in str(error).upper():
                raise exceptions.ReferenciaIntegridadError(
                    f"La especialidad #{veterinario.especialidad.id_especialidad} no existe en la base de datos."
                )
            raise exceptions.PersistenciaError(f"Error de persistencia al registrar veterinario: {error}")

    def obtener_por_id(self, id_veterinario: int) -> Veterinario:
        """Retorna el veterinario o lanza EntidadNoEncontradaException si no existe."""
        sql = """
        SELECT id_veterinario, rut, nombre_completo, telefono, id_especialidad
        FROM VETERINARIO
        WHERE id_veterinario = ?;
        """
        with self.conexion_db.obtener_conexion() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (id_veterinario,))
            fila = cursor.fetchone()
            if fila is None:
                raise exceptions.EntidadNoEncontradaException("Veterinario", id_veterinario)
            return self._mapear_fila(fila)

    def obtener_por_rut(self, rut: str) -> Veterinario:
        """Retorna el veterinario o lanza EntidadNoEncontradaException si no existe."""
        sql = """
        SELECT id_veterinario, rut, nombre_completo, telefono, id_especialidad
        FROM VETERINARIO
        WHERE rut = ?;
        """
        with self.conexion_db.obtener_conexion() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (rut,))
            fila = cursor.fetchone()
            if fila is None:
                raise exceptions.EntidadNoEncontradaException("Veterinario", rut)
            return self._mapear_fila(fila)

    def buscar_por_nombre(self, nombre: str) -> list[Veterinario]:
        """
        Busca veterinarios por coincidencia parcial en nombre_completo.
        Usa consultas parametrizadas para evitar inyecciones SQL.
        """
        sql = """
        SELECT id_veterinario, rut, nombre_completo, telefono, id_especialidad
        FROM VETERINARIO
        WHERE nombre_completo LIKE ?
        ORDER BY nombre_completo ASC;
        """
        patron = f"%{nombre}%"
        with self.conexion_db.obtener_conexion() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (patron,))
            filas = cursor.fetchall()
            return [self._mapear_fila(fila) for fila in filas]

    def listar_todos(self) -> list[Veterinario]:
        sql = """
        SELECT id_veterinario, rut, nombre_completo, telefono, id_especialidad
        FROM VETERINARIO
        ORDER BY nombre_completo ASC;
        """
        with self.conexion_db.obtener_conexion() as conn:
            cursor = conn.cursor()
            cursor.execute(sql)
            filas = cursor.fetchall()
            return [self._mapear_fila(fila) for fila in filas]

    def actualizar(self, veterinario: Veterinario) -> bool:
        """Actualiza el veterinario y retorna True si afectó filas."""
        if veterinario.id_persona is None:
            raise exceptions.ReglaNegocioError("No se puede actualizar un veterinario que no posee ID asignado.")
        if veterinario.especialidad is None or veterinario.especialidad.id_especialidad is None:
            raise exceptions.ReglaNegocioError("El veterinario debe poseer una especialidad con ID asignado.")

        sql = """
        UPDATE VETERINARIO
        SET rut = ?, nombre_completo = ?, telefono = ?, id_especialidad = ?
        WHERE id_veterinario = ?;
        """
        with self.conexion_db.obtener_conexion() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (
                veterinario.rut,
                veterinario.nombre_completo,
                veterinario.telefono,
                veterinario.especialidad.id_especialidad,
                veterinario.id_persona
            ))
            if cursor.rowcount == 0:
                raise exceptions.EntidadNoEncontradaException("Veterinario", veterinario.id_persona)
            return True

    def eliminar(self, id_veterinario: int) -> bool:
        """Elimina el veterinario y retorna True si afectó filas."""
        sql = "DELETE FROM VETERINARIO WHERE id_veterinario = ?;"
        try:
            with self.conexion_db.obtener_conexion() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, (id_veterinario,))
                if cursor.rowcount == 0:
                    raise exceptions.EntidadNoEncontradaException("Veterinario", id_veterinario)
                return True
        except sqlite3.IntegrityError:
            raise exceptions.ReferenciaIntegridadError(
                f"No es posible eliminar el veterinario #{id_veterinario} porque tiene registros de atención histórica."
            )

    def _mapear_fila(self, fila: tuple) -> Veterinario:
        especialidad = self.especialidad_dao.obtener_por_id(fila[4])
        return Veterinario(
            id_veterinario=fila[0],
            rut=fila[1],
            nombre_completo=fila[2],
            telefono=fila[3],
            especialidad=especialidad
        )

