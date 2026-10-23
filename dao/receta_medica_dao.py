import sqlite3
from exceptions import exceptions
from database.conexion import ConexionDB
from models.receta_medica import RecetaMedica
from dao.medicamento_dao import MedicamentoDAO
from dao.consulta_dao import ConsultaDAO

class RecetaMedicaDAO:
    def __init__(
        self,
        conexion_db: ConexionDB,
        medicamento_dao: MedicamentoDAO | None = None,
        consulta_dao: ConsultaDAO | None = None
    ):
        self.conexion_db = conexion_db
        self.medicamento_dao = medicamento_dao or MedicamentoDAO(conexion_db)
        self.consulta_dao = consulta_dao or ConsultaDAO(conexion_db)
        self._crear_tabla()

    def _crear_tabla(self) -> None:
        ddl = """
        CREATE TABLE IF NOT EXISTS RECETA_MEDICA (
            id_receta INTEGER PRIMARY KEY AUTOINCREMENT,
            cantidad INTEGER NOT NULL,
            instrucciones TEXT NOT NULL,
            id_medicamento INTEGER NOT NULL,
            id_detalle INTEGER NOT NULL,
            FOREIGN KEY (id_medicamento) REFERENCES MEDICAMENTO(id_medicamento),
            FOREIGN KEY (id_detalle) REFERENCES DETALLE_CONSULTA(id_detalle),
            CONSTRAINT chk_cantidad CHECK (cantidad > 0)
        );
        """
        with self.conexion_db.obtener_conexion() as conn:
            conn.execute(ddl)

    def insertar(self, receta: RecetaMedica) -> int:
        if receta.medicamento is None or receta.medicamento.id_medicamento is None:
            raise exceptions.ReglaNegocioError("La receta médica debe incluir un medicamento con ID.")
        if receta.detalle is None or receta.detalle.id_detalle is None:
            raise exceptions.ReglaNegocioError("La receta médica debe estar asociada a un detalle de consulta con ID.")

        sql = """
        INSERT INTO RECETA_MEDICA (cantidad, instrucciones, id_medicamento, id_detalle)
        VALUES (?, ?, ?, ?);
        """
        try:
            with self.conexion_db.obtener_conexion() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, (
                    receta.cantidad,
                    receta.instrucciones,
                    receta.medicamento.id_medicamento,
                    receta.detalle.id_detalle
                ))
                nuevo_id = cursor.lastrowid
                receta.asignar_id(nuevo_id)
                return nuevo_id
        except sqlite3.IntegrityError as error:
            if "FOREIGN KEY" in str(error).upper():
                raise exceptions.ReferenciaIntegridadError(
                    "El medicamento o el detalle de consulta asociado no existe en la base de datos."
                )
            raise exceptions.PersistenciaError(f"Error de persistencia al registrar receta médica: {error}")

    def obtener_por_id(self, id_receta: int) -> RecetaMedica:
        """Retorna la receta o lanza EntidadNoEncontradaException si no existe."""
        sql = """
        SELECT id_receta, cantidad, instrucciones, id_medicamento, id_detalle
        FROM RECETA_MEDICA
        WHERE id_receta = ?;
        """
        with self.conexion_db.obtener_conexion() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (id_receta,))
            fila = cursor.fetchone()
            if fila is None:
                raise exceptions.EntidadNoEncontradaException("RecetaMedica", id_receta)
            return self._mapear_fila(fila)

    def buscar_por_nombre_medicamento(self, nombre: str) -> list[RecetaMedica]:
        sql = """
        SELECT r.id_receta, r.cantidad, r.instrucciones, r.id_medicamento, r.id_detalle
        FROM RECETA_MEDICA r
        JOIN MEDICAMENTO m ON r.id_medicamento = m.id_medicamento
        WHERE m.nombre_comercial LIKE ?
        ORDER BY r.id_receta DESC;
        """
        patron = f"%{nombre}%"
        with self.conexion_db.obtener_conexion() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (patron,))
            filas = cursor.fetchall()
            return [self._mapear_fila(fila) for fila in filas]

    def listar_todos(self) -> list[RecetaMedica]:
        sql = """
        SELECT id_receta, cantidad, instrucciones, id_medicamento, id_detalle
        FROM RECETA_MEDICA
        ORDER BY id_receta DESC;
        """
        with self.conexion_db.obtener_conexion() as conn:
            cursor = conn.cursor()
            cursor.execute(sql)
            filas = cursor.fetchall()
            return [self._mapear_fila(fila) for fila in filas]

    def listar_por_detalle(self, id_detalle: int) -> list[RecetaMedica]:
        sql = """
        SELECT id_receta, cantidad, instrucciones, id_medicamento, id_detalle
        FROM RECETA_MEDICA
        WHERE id_detalle = ?
        ORDER BY id_receta ASC;
        """
        with self.conexion_db.obtener_conexion() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (id_detalle,))
            filas = cursor.fetchall()
            return [self._mapear_fila(fila) for fila in filas]

    def actualizar(self, receta: RecetaMedica) -> bool:
        """Actualiza la receta y retorna True si afectó filas."""
        if receta.id_receta is None:
            raise exceptions.ReglaNegocioError("No se puede actualizar una receta sin ID asignado.")
        if receta.medicamento is None or receta.medicamento.id_medicamento is None:
            raise exceptions.ReglaNegocioError("La receta debe incluir un medicamento con ID.")
        if receta.detalle is None or receta.detalle.id_detalle is None:
            raise exceptions.ReglaNegocioError("La receta debe incluir un detalle de consulta con ID.")

        sql = """
        UPDATE RECETA_MEDICA
        SET cantidad = ?, instrucciones = ?, id_medicamento = ?, id_detalle = ?
        WHERE id_receta = ?;
        """
        with self.conexion_db.obtener_conexion() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (
                receta.cantidad,
                receta.instrucciones,
                receta.medicamento.id_medicamento,
                receta.detalle.id_detalle,
                receta.id_receta
            ))
            if cursor.rowcount == 0:
                raise exceptions.EntidadNoEncontradaException("RecetaMedica", receta.id_receta)
            return True

    def eliminar(self, id_receta: int) -> bool:
        """Elimina la receta y retorna True si afectó filas."""
        sql = "DELETE FROM RECETA_MEDICA WHERE id_receta = ?;"
        try:
            with self.conexion_db.obtener_conexion() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, (id_receta,))
                if cursor.rowcount == 0:
                    raise exceptions.EntidadNoEncontradaException("RecetaMedica", id_receta)
                return True
        except sqlite3.IntegrityError:
            raise exceptions.ReferenciaIntegridadError(
                f"No es posible eliminar la receta #{id_receta} debido a restricciones de integridad referencial."
            )

    def _mapear_fila(self, fila: tuple) -> RecetaMedica:
        medicamento = self.medicamento_dao.obtener_por_id(fila[3])
        detalle = self.consulta_dao.obtener_detalle_por_id(fila[4])
        return RecetaMedica(
            id_receta=fila[0],
            cantidad=fila[1],
            instrucciones=fila[2],
            medicamento=medicamento,
            detalle=detalle
        )
