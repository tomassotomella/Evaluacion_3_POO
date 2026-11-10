import sqlite3
from exceptions import exceptions
from database.conexion import ConexionDB
from models.mascota import Mascota
from dao.especie_dao import EspecieDAO
from dao.propietario_dao import PropietarioDAO
from utilities.fechas import date_a_sqlite, sqlite_a_date

class MascotaDAO:
    def __init__(
        self,
        conexion_db: ConexionDB,
        especie_dao: EspecieDAO | None = None,
        propietario_dao: PropietarioDAO | None = None
    ):
        self.conexion_db = conexion_db
        self.especie_dao = especie_dao or EspecieDAO(conexion_db)
        self.propietario_dao = propietario_dao or PropietarioDAO(conexion_db)
        self._crear_tabla()

    def _crear_tabla(self) -> None:
        ddl = """
        CREATE TABLE IF NOT EXISTS MASCOTA (
            id_mascota INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            fecha_nacimiento TEXT NOT NULL,
            id_especie INTEGER NOT NULL,
            id_propietario INTEGER NOT NULL,
            raza TEXT NOT NULL DEFAULT 'Sin especificar',
            FOREIGN KEY (id_especie) REFERENCES ESPECIE(id_especie),
            FOREIGN KEY (id_propietario) REFERENCES PROPIETARIO(id_propietario)
        );
        """
        with self.conexion_db.obtener_conexion() as conn:
            conn.execute(ddl)
            columnas = {
                fila[1]
                for fila in conn.execute("PRAGMA table_info(MASCOTA)")
            }
            if "raza" not in columnas:
                conn.execute(
                    "ALTER TABLE MASCOTA ADD COLUMN raza TEXT "
                    "NOT NULL DEFAULT 'Sin especificar';"
                )

    def insertar(self, mascota: Mascota) -> int:
        if mascota.especie is None or mascota.especie.id_especie is None:
            raise exceptions.ReglaNegocioError("La mascota debe tener una especie válida con ID asignado.")
        if mascota.propietario is None or mascota.propietario.id_persona is None:
            raise exceptions.ReglaNegocioError("La mascota debe tener un propietario válido con ID asignado.")

        sql = """
        INSERT INTO MASCOTA (nombre, fecha_nacimiento, id_especie, id_propietario, raza)
        VALUES (?, ?, ?, ?, ?);
        """
        try:
            with self.conexion_db.obtener_conexion() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, (
                    mascota.nombre,
                    date_a_sqlite(mascota.fecha_nacimiento),
                    mascota.especie.id_especie,
                    mascota.propietario.id_persona,
                    mascota.raza,
                ))
                nuevo_id = cursor.lastrowid
                mascota.asignar_id(nuevo_id)
                return nuevo_id
        except sqlite3.IntegrityError as error:
            if "FOREIGN KEY" in str(error).upper():
                raise exceptions.ReferenciaIntegridadError(
                    "La especie o el propietario asignado no existe en la base de datos."
                )
            raise exceptions.PersistenciaError(f"Error de persistencia al registrar mascota: {error}")

    def obtener_por_id(self, id_mascota: int) -> Mascota:
        """Retorna la mascota o lanza EntidadNoEncontradaException si no existe."""
        sql = """
        SELECT id_mascota, nombre, fecha_nacimiento, id_especie, id_propietario, raza
        FROM MASCOTA
        WHERE id_mascota = ?;
        """
        with self.conexion_db.obtener_conexion() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (id_mascota,))
            fila = cursor.fetchone()
            if fila is None:
                raise exceptions.EntidadNoEncontradaException("Mascota", id_mascota)
            return self._mapear_fila(fila)

    def buscar_por_nombre(self, nombre: str) -> list[Mascota]:
        """
        Busca mascotas por coincidencia parcial en nombre.
        Usa consultas parametrizadas para evitar inyecciones SQL.
        """
        sql = """
        SELECT id_mascota, nombre, fecha_nacimiento, id_especie, id_propietario, raza
        FROM MASCOTA
        WHERE nombre LIKE ?
        ORDER BY nombre ASC;
        """
        patron = f"%{nombre}%"
        with self.conexion_db.obtener_conexion() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (patron,))
            filas = cursor.fetchall()
            return [self._mapear_fila(fila) for fila in filas]

    def listar_todos(self) -> list[Mascota]:
        sql = """
        SELECT id_mascota, nombre, fecha_nacimiento, id_especie, id_propietario, raza
        FROM MASCOTA
        ORDER BY nombre ASC;
        """
        with self.conexion_db.obtener_conexion() as conn:
            cursor = conn.cursor()
            cursor.execute(sql)
            filas = cursor.fetchall()
            return [self._mapear_fila(fila) for fila in filas]

    def listar_por_propietario(self, id_propietario: int) -> list[Mascota]:
        sql = """
        SELECT id_mascota, nombre, fecha_nacimiento, id_especie, id_propietario, raza
        FROM MASCOTA
        WHERE id_propietario = ?
        ORDER BY nombre ASC;
        """
        with self.conexion_db.obtener_conexion() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (id_propietario,))
            filas = cursor.fetchall()
            return [self._mapear_fila(fila) for fila in filas]

    def actualizar(self, mascota: Mascota) -> bool:
        """Actualiza la mascota y retorna True si afectó filas."""
        if mascota.id_mascota is None:
            raise exceptions.ReglaNegocioError("No se puede actualizar una mascota que no posee ID asignado.")
        if mascota.especie is None or mascota.especie.id_especie is None:
            raise exceptions.ReglaNegocioError("La mascota debe tener una especie válida con ID asignado.")
        if mascota.propietario is None or mascota.propietario.id_persona is None:
            raise exceptions.ReglaNegocioError("La mascota debe tener un propietario válido con ID asignado.")

        sql = """
        UPDATE MASCOTA
        SET nombre = ?, fecha_nacimiento = ?, id_especie = ?, id_propietario = ?, raza = ?
        WHERE id_mascota = ?;
        """
        with self.conexion_db.obtener_conexion() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (
                mascota.nombre,
                date_a_sqlite(mascota.fecha_nacimiento),
                mascota.especie.id_especie,
                mascota.propietario.id_persona,
                mascota.raza,
                mascota.id_mascota
            ))
            if cursor.rowcount == 0:
                raise exceptions.EntidadNoEncontradaException("Mascota", mascota.id_mascota)
            return True

    def eliminar(self, id_mascota: int) -> bool:
        """Elimina la mascota y retorna True si afectó filas."""
        sql = "DELETE FROM MASCOTA WHERE id_mascota = ?;"
        try:
            with self.conexion_db.obtener_conexion() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, (id_mascota,))
                if cursor.rowcount == 0:
                    raise exceptions.EntidadNoEncontradaException("Mascota", id_mascota)
                return True
        except sqlite3.IntegrityError:
            raise exceptions.ReferenciaIntegridadError(
                f"No es posible eliminar la mascota #{id_mascota} porque tiene consultas médicas registradas."
            )

    def _mapear_fila(self, fila: tuple) -> Mascota:
        especie = self.especie_dao.obtener_por_id(fila[3])
        propietario = self.propietario_dao.obtener_por_id(fila[4])
        return Mascota(
            id_mascota=fila[0],
            nombre=fila[1],
            fecha_nacimiento=sqlite_a_date(fila[2]),
            especie=especie,
            propietario=propietario,
            raza=fila[5]
        )
