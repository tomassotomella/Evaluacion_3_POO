import sqlite3
from exceptions import exceptions
from database.conexion import ConexionDB
from models.consulta import Consulta, EstadosConsulta
from models.detalle_consulta import DetalleConsulta
from dao.mascota_dao import MascotaDAO
from dao.veterinario_dao import VeterinarioDAO
from utilities.fechas import (
    datetime_a_sqlite,
    sqlite_a_datetime,
)

class ConsultaDAO:
    def __init__(
        self,
        conexion_db: ConexionDB,
        mascota_dao: MascotaDAO | None = None
    ):
        self.conexion_db = conexion_db
        self.mascota_dao = mascota_dao or MascotaDAO(conexion_db)
        self.veterinario_dao = VeterinarioDAO(conexion_db)
        self._crear_tablas()

    def _crear_tablas(self) -> None:
        ddl_consulta = """
        CREATE TABLE IF NOT EXISTS CONSULTA (
            id_consulta INTEGER PRIMARY KEY AUTOINCREMENT,
            id_mascota INTEGER NOT NULL,
            fecha_agendada TEXT NOT NULL,
            estado TEXT NOT NULL,
            motivo TEXT,
            fecha_inicio_atencion TEXT,
            fecha_fin_atencion TEXT,
            id_detalle INTEGER UNIQUE,
            FOREIGN KEY (id_mascota) REFERENCES MASCOTA(id_mascota),
            FOREIGN KEY (id_detalle) REFERENCES DETALLE_CONSULTA(id_detalle)
        );
        """
        ddl_detalle = """
        CREATE TABLE IF NOT EXISTS DETALLE_CONSULTA (
            id_detalle INTEGER PRIMARY KEY AUTOINCREMENT,
            id_consulta INTEGER NOT NULL UNIQUE,
            id_veterinario INTEGER NOT NULL,
            diagnostico TEXT,
            tratamiento TEXT,
            observaciones TEXT,
            FOREIGN KEY (id_consulta) REFERENCES CONSULTA(id_consulta),
            FOREIGN KEY (id_veterinario) REFERENCES VETERINARIO(id_veterinario)
        );
        """
        with self.conexion_db.obtener_conexion() as conn:
            conn.execute(ddl_consulta)
            conn.execute(ddl_detalle)

    # CRUD de consultas
    def insertar_consulta(self, consulta: Consulta) -> int:
        if consulta.mascota is None or consulta.mascota.id_mascota is None:
            raise exceptions.ReglaNegocioError("La consulta debe tener una mascota con ID asignado.")

        fecha_agendada_str = datetime_a_sqlite(consulta.fecha_agendada)
        estado_str = consulta.estado.value
        inicio_str = datetime_a_sqlite(consulta.fecha_inicio_atencion, permitir_nulo=True)
        fin_str = datetime_a_sqlite(consulta.fecha_fin_atencion, permitir_nulo=True)

        sql = """
        INSERT INTO CONSULTA (
            id_mascota, fecha_agendada, estado, motivo, fecha_inicio_atencion,
            fecha_fin_atencion, id_detalle
        )
        VALUES (?, ?, ?, ?, ?, ?, ?);
        """
        try:
            with self.conexion_db.obtener_conexion() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, (
                    consulta.mascota.id_mascota,
                    fecha_agendada_str,
                    estado_str,
                    consulta.motivo,
                    inicio_str,
                    fin_str,
                    None
                ))
                nuevo_id = cursor.lastrowid
                consulta.asignar_id(nuevo_id)
                return nuevo_id
        except sqlite3.IntegrityError as error:
            if "FOREIGN KEY" in str(error).upper():
                raise exceptions.ReferenciaIntegridadError(
                    "La mascota asociada no existe en la base de datos."
                )
            raise exceptions.PersistenciaError(f"Error de persistencia al registrar consulta: {error}")

    def obtener_consulta_por_id(self, id_consulta: int) -> Consulta:
        """Retorna la consulta o lanza EntidadNoEncontradaException si no existe."""
        sql = """
        SELECT id_consulta, id_mascota, fecha_agendada, estado, motivo,
               fecha_inicio_atencion, fecha_fin_atencion, id_detalle
        FROM CONSULTA
        WHERE id_consulta = ?;
        """
        with self.conexion_db.obtener_conexion() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (id_consulta,))
            fila = cursor.fetchone()
            if fila is None:
                raise exceptions.EntidadNoEncontradaException("Consulta", id_consulta)
            return self._mapear_consulta_desde_fila(fila, cargar_detalle=True)

    def listar_consultas_por_mascota(self, id_mascota: int) -> list[Consulta]:
        sql = """
        SELECT id_consulta, id_mascota, fecha_agendada,
            estado, motivo, fecha_inicio_atencion, fecha_fin_atencion, id_detalle
        FROM CONSULTA
        WHERE id_mascota = ?
        ORDER BY fecha_agendada DESC;
        """

        with self.conexion_db.obtener_conexion() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (id_mascota,))
            filas = cursor.fetchall()
            return [
                self._mapear_consulta_desde_fila(fila, cargar_detalle=True)
                for fila in filas
            ]

    def listar_consultas_por_estado(
        self,
        estado: EstadosConsulta
    ) -> list[Consulta]:
        sql = """
        SELECT id_consulta, id_mascota, fecha_agendada,
            estado, motivo, fecha_inicio_atencion, fecha_fin_atencion, id_detalle
        FROM CONSULTA
        WHERE estado = ?
        ORDER BY fecha_agendada DESC;
        """

        with self.conexion_db.obtener_conexion() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (estado.value,))
            filas = cursor.fetchall()
            return [
                self._mapear_consulta_desde_fila(fila, cargar_detalle=True)
                for fila in filas
            ]

    def buscar_consultas_por_nombre_mascota(self, nombre: str) -> list[Consulta]:
        """
        Busca consultas por coincidencia con el nombre de la mascota.
        Usa consultas parametrizadas para evitar inyecciones SQL.
        """
        sql = """
        SELECT c.id_consulta, c.id_mascota, c.fecha_agendada, c.estado, c.motivo,
               c.fecha_inicio_atencion, c.fecha_fin_atencion, c.id_detalle
        FROM CONSULTA c
        JOIN MASCOTA m ON c.id_mascota = m.id_mascota
        WHERE m.nombre LIKE ?
        ORDER BY c.fecha_agendada DESC;
        """
        patron = f"%{nombre}%"
        with self.conexion_db.obtener_conexion() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (patron,))
            filas = cursor.fetchall()
            return [
                self._mapear_consulta_desde_fila(fila, cargar_detalle=True)
                for fila in filas
            ]

    def listar_consultas(self) -> list[Consulta]:
        sql = """
        SELECT id_consulta, id_mascota, fecha_agendada, estado, motivo,
               fecha_inicio_atencion, fecha_fin_atencion, id_detalle
        FROM CONSULTA
        ORDER BY fecha_agendada DESC;
        """
        with self.conexion_db.obtener_conexion() as conn:
            cursor = conn.cursor()
            cursor.execute(sql)
            filas = cursor.fetchall()
            return [
                self._mapear_consulta_desde_fila(fila, cargar_detalle=True)
                for fila in filas
            ]
        
    def listar_consultas_por_veterinario(
        self,
        id_veterinario: int
    ) -> list[Consulta]:
        sql = """
        SELECT c.id_consulta,
            c.id_mascota,
            c.fecha_agendada,
            c.estado,
            c.motivo,
            c.fecha_inicio_atencion,
            c.fecha_fin_atencion,
            c.id_detalle
        FROM CONSULTA c
        INNER JOIN DETALLE_CONSULTA dc
            ON dc.id_consulta = c.id_consulta
        WHERE dc.id_veterinario = ?
        ORDER BY c.fecha_agendada DESC;
        """

        with self.conexion_db.obtener_conexion() as conn:
            filas = conn.execute(sql, (id_veterinario,)).fetchall()

        return [
            self._mapear_consulta_desde_fila(
                fila,
                cargar_detalle=True
            )
            for fila in filas
        ]

    def actualizar_consulta(self, consulta: Consulta) -> bool:
        """Actualiza la consulta y retorna True si afectó filas."""
        if consulta.id_consulta is None:
            raise exceptions.ReglaNegocioError("No se puede actualizar una consulta sin ID asignado.")

        fecha_agendada_str = datetime_a_sqlite(consulta.fecha_agendada)
        estado_str = consulta.estado.value
        inicio_str = datetime_a_sqlite(consulta.fecha_inicio_atencion, permitir_nulo=True)
        fin_str = datetime_a_sqlite(consulta.fecha_fin_atencion, permitir_nulo=True)

        sql = """
        UPDATE CONSULTA
        SET id_mascota = ?, fecha_agendada = ?, estado = ?,
            motivo = ?, fecha_inicio_atencion = ?, fecha_fin_atencion = ?,
            id_detalle = ?
        WHERE id_consulta = ?;
        """
        with self.conexion_db.obtener_conexion() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (
                consulta.mascota.id_mascota,
                fecha_agendada_str,
                estado_str,
                consulta.motivo,
                inicio_str,
                fin_str,
                consulta.detalle.id_detalle if consulta.detalle is not None else None,
                consulta.id_consulta
            ))
            if cursor.rowcount == 0:
                raise exceptions.EntidadNoEncontradaException("Consulta", consulta.id_consulta)
            return True

    def eliminar_consulta(self, id_consulta: int) -> bool:
        """Elimina la consulta y retorna True si afectó filas."""
        sql = "DELETE FROM CONSULTA WHERE id_consulta = ?;"
        try:
            with self.conexion_db.obtener_conexion() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, (id_consulta,))
                if cursor.rowcount == 0:
                    raise exceptions.EntidadNoEncontradaException(
                        "Consulta", id_consulta
                    )
                return True
        except sqlite3.IntegrityError:
            raise exceptions.ReferenciaIntegridadError(
                f"No es posible eliminar la consulta #{id_consulta} "
                "debido a restricciones de integridad referencial."
            )

    # CRUD de detalles
    def insertar_detalle(self, detalle: DetalleConsulta) -> int:
        if detalle.consulta is None or detalle.consulta.id_consulta is None:
            raise exceptions.ReglaNegocioError(
                "El detalle debe tener una consulta con ID asignado."
            )
        if detalle.veterinario is None or detalle.veterinario.id_persona is None:
            raise exceptions.ReglaNegocioError(
                "El detalle debe tener un veterinario con ID asignado."
            )

        sql = """
        INSERT INTO DETALLE_CONSULTA (
            id_consulta, id_veterinario, diagnostico, tratamiento, observaciones
        )
        VALUES (?, ?, ?, ?, ?);
        """
        try:
            with self.conexion_db.obtener_conexion() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, (
                    detalle.consulta.id_consulta,
                    detalle.veterinario.id_persona,
                    detalle.diagnostico,
                    detalle.tratamiento,
                    detalle.observaciones
                ))
                nuevo_id = cursor.lastrowid
                detalle.asignar_id(nuevo_id)
                cursor.execute(
                    "UPDATE CONSULTA SET id_detalle = ? WHERE id_consulta = ?;",
                    (nuevo_id, detalle.consulta.id_consulta)
                )
                return nuevo_id
        except sqlite3.IntegrityError as error:
            if "UNIQUE" in str(error).upper():
                raise exceptions.ReglaNegocioError(
                    f"La consulta #{detalle.consulta.id_consulta} ya tiene un detalle."
                )
            if "FOREIGN KEY" in str(error).upper():
                raise exceptions.ReferenciaIntegridadError(
                    "La consulta o el veterinario asociado no existe."
                )
            raise exceptions.PersistenciaError(
                f"Error al registrar detalle de consulta: {error}"
            )

    def obtener_detalle_por_id(self, id_detalle: int) -> DetalleConsulta:
        """Retorna el detalle o lanza EntidadNoEncontradaException si no existe."""
        sql = """
        SELECT id_detalle, id_consulta, id_veterinario, diagnostico,
               tratamiento, observaciones
        FROM DETALLE_CONSULTA
        WHERE id_detalle = ?;
        """
        with self.conexion_db.obtener_conexion() as conn:
            fila = conn.execute(sql, (id_detalle,)).fetchone()
        if fila is None:
            raise exceptions.EntidadNoEncontradaException("DetalleConsulta", id_detalle)
        consulta = self._obtener_consulta_por_id(fila[1])
        return self._mapear_detalle_desde_fila(fila, consulta)

    def listar_detalles(self) -> list[DetalleConsulta]:
        sql = """
        SELECT id_detalle, id_consulta, id_veterinario, diagnostico,
               tratamiento, observaciones
                FROM DETALLE_CONSULTA;
        """
        with self.conexion_db.obtener_conexion() as conn:
            cursor = conn.cursor()
            cursor.execute(sql)
            filas = cursor.fetchall()
            return [
                self._mapear_detalle_desde_fila(fila)
                for fila in filas
            ] 

    def buscar_detalles_por_veterinario(self, id_veterinario: int) -> list[DetalleConsulta]:
            sql = """
            SELECT id_detalle, id_consulta, id_veterinario, diagnostico,
                   tratamiento, observaciones
            FROM DETALLE_CONSULTA
            WHERE id_veterinario = ?
            ORDER BY id_detalle ASC;
            """
            with self.conexion_db.obtener_conexion() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, (id_veterinario,))
                filas = cursor.fetchall()
                return [
                    self._mapear_detalle_desde_fila(fila)
                    for fila in filas
                ] 

    def actualizar_detalle(self, detalle: DetalleConsulta) -> bool:
        """Actualiza el detalle y retorna True si afectó filas."""
        if detalle.id_detalle is None:
            raise exceptions.ReglaNegocioError(
                "No se puede actualizar un detalle sin ID."
            )
        if detalle.veterinario is None or detalle.veterinario.id_persona is None:
            raise exceptions.ReglaNegocioError(
                "El detalle debe tener un veterinario asignado."
            )
        sql = """
        UPDATE DETALLE_CONSULTA
        SET id_veterinario = ?, diagnostico = ?, tratamiento = ?,
            observaciones = ?
        WHERE id_detalle = ?;
        """
        with self.conexion_db.obtener_conexion() as conn:
            cursor = conn.execute(sql, (
                detalle.veterinario.id_persona,
                detalle.diagnostico,
                detalle.tratamiento,
                detalle.observaciones,
                detalle.id_detalle
            ))
            if cursor.rowcount == 0:
                raise exceptions.EntidadNoEncontradaException(
                    "DetalleConsulta", detalle.id_detalle
                )
            return True

    def eliminar_detalle(self, id_detalle: int) -> bool:
        """Elimina el detalle (y su vínculo con la consulta) y retorna True si afectó filas."""
        try:
            with self.conexion_db.obtener_conexion() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE CONSULTA SET id_detalle = NULL WHERE id_detalle = ?;",
                    (id_detalle,)
                )
                cursor.execute(
                    "DELETE FROM DETALLE_CONSULTA WHERE id_detalle = ?;",
                    (id_detalle,)
                )
                if cursor.rowcount == 0:
                    raise exceptions.EntidadNoEncontradaException(
                        "DetalleConsulta", id_detalle
                    )
                return True
        except sqlite3.IntegrityError as error:
            raise exceptions.ReferenciaIntegridadError(
                f"No se puede eliminar el detalle #{id_detalle}: {error}"
            )

    # Mappers y helpers internos
    def _mapear_consulta_desde_fila(
        self,
        fila: tuple,
        cargar_detalle: bool
    ) -> Consulta:
        mascota = self.mascota_dao.obtener_por_id(fila[1])
        
        estado = EstadosConsulta(fila[3])

        # Parseo fechas
        fecha_agendada = sqlite_a_datetime(fila[2])
        inicio = sqlite_a_datetime(fila[5], permitir_nulo=True)
        fin = sqlite_a_datetime(fila[6], permitir_nulo=True)

        consulta = Consulta(
            id_consulta=fila[0],
            mascota=mascota,
            fecha_agendada=fecha_agendada,
            estado=estado,
            motivo=fila[4],
            detalle=None,
            fecha_inicio_atencion=inicio,
            fecha_fin_atencion=fin
        )
        if cargar_detalle and fila[7] is not None:
            consulta.detalle = self._obtener_detalle(fila[7], consulta)
        return consulta

    def _obtener_consulta_por_id(self, id_consulta: int) -> Consulta:
        sql = """
        SELECT id_consulta, id_mascota, fecha_agendada, estado, motivo,
               fecha_inicio_atencion, fecha_fin_atencion, id_detalle
        FROM CONSULTA
        WHERE id_consulta = ?;
        """
        with self.conexion_db.obtener_conexion() as conn:
            fila = conn.execute(sql, (id_consulta,)).fetchone()
        if fila is None:
            raise exceptions.EntidadNoEncontradaException("Consulta", id_consulta)
        return self._mapear_consulta_desde_fila(fila, cargar_detalle=False)

    def _obtener_detalle(
        self,
        id_detalle: int,
        consulta: Consulta
    ) -> DetalleConsulta:
        sql = """
        SELECT id_detalle, id_consulta, id_veterinario, diagnostico,
               tratamiento, observaciones
        FROM DETALLE_CONSULTA
        WHERE id_detalle = ?;
        """
        with self.conexion_db.obtener_conexion() as conn:
            fila = conn.execute(sql, (id_detalle,)).fetchone()
        if fila is None:
            raise exceptions.ReferenciaIntegridadError(
                f"El detalle #{id_detalle} asociado a la consulta no existe."
            )
        return self._mapear_detalle_desde_fila(fila, consulta)

    def _mapear_detalle_desde_fila(
        self,
        fila: tuple,
        consulta: Consulta | None = None
    ) -> DetalleConsulta:
        if consulta is None:
            consulta = self._obtener_consulta_por_id(fila[1])
        return DetalleConsulta(
            id_detalle=fila[0],
            consulta=consulta,
            veterinario=self.veterinario_dao.obtener_por_id(fila[2]),
            diagnostico=fila[3],
            tratamiento=fila[4],
            observaciones=fila[5]
        )
