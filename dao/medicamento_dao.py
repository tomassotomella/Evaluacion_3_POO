import sqlite3
from exceptions import exceptions
from database.conexion import ConexionDB
from models.medicamento import Medicamento


class MedicamentoDAO:
    def __init__(self, conexion_db: ConexionDB):
        self.conexion_db = conexion_db
        self._crear_tabla()

    def _crear_tabla(self) -> None:
        ddl = """
        CREATE TABLE IF NOT EXISTS MEDICAMENTO (
            id_medicamento INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre_comercial TEXT NOT NULL UNIQUE,
            precio INTEGER NOT NULL,
            stock INTEGER NOT NULL,
            CONSTRAINT chk_precio CHECK (precio > 0),
            CONSTRAINT chk_stock CHECK (stock >= 0)
        );
        """
        with self.conexion_db.obtener_conexion() as conn:
            conn.execute(ddl)

    # CREATE
    def insertar(self, medicamento: Medicamento) -> int:
        sql = """
        INSERT INTO MEDICAMENTO (nombre_comercial, precio, stock)
        VALUES (?, ?, ?);
        """
        try:
            with self.conexion_db.obtener_conexion() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, (
                    medicamento.nombre_comercial,
                    medicamento.precio,
                    medicamento.stock
                ))
                nuevo_id = cursor.lastrowid
                medicamento.asignar_id(nuevo_id)
                return nuevo_id
        except sqlite3.IntegrityError as error:
            if "UNIQUE" in str(error).upper():
                raise exceptions.EntidadExistenteException("Medicamento", medicamento.nombre_comercial)
            raise exceptions.PersistenciaError(f"Error de persistencia al registrar medicamento: {error}")


    # READ
    def obtener_por_id(self, id_medicamento: int) -> Medicamento:
        """Retorna el medicamento o lanza EntidadNoEncontradaException si no existe."""

        sql = """
        SELECT id_medicamento, nombre_comercial, precio, stock
        FROM MEDICAMENTO
        WHERE id_medicamento = ?;
        """
        with self.conexion_db.obtener_conexion() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (id_medicamento,))
            fila = cursor.fetchone()
            if fila is None:
                raise exceptions.EntidadNoEncontradaException("Medicamento", id_medicamento)
            return self._mapear_fila(fila)

    # READ - Búsqueda segura contra SQL Injection
    def buscar_por_nombre(self, nombre: str) -> list[Medicamento]:
        """
        Busca medicamentos por coincidencia parcial en nombre_comercial.
        Usa consultas parametrizadas para evitar inyecciones SQL.
        """
        sql = """
        SELECT id_medicamento, nombre_comercial, precio, stock
        FROM MEDICAMENTO
        WHERE nombre_comercial LIKE ?
        ORDER BY nombre_comercial ASC;
        """
        patron = f"%{nombre}%"
        with self.conexion_db.obtener_conexion() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (patron,))
            filas = cursor.fetchall()
            return [self._mapear_fila(fila) for fila in filas]

    # READ
    def listar_todos(self) -> list[Medicamento]:
        sql = """
        SELECT id_medicamento, nombre_comercial, precio, stock
        FROM MEDICAMENTO
        ORDER BY nombre_comercial ASC;
        """
        with self.conexion_db.obtener_conexion() as conn:
            cursor = conn.cursor()
            cursor.execute(sql)
            filas = cursor.fetchall()
            return [self._mapear_fila(fila) for fila in filas]

    # UPDATE
    def actualizar(self, medicamento: Medicamento) -> bool:
        """Actualiza el medicamento y retorna True si afectó filas."""
        if medicamento.id_medicamento is None:
            raise exceptions.ReglaNegocioError("No se puede actualizar un medicamento que no posee ID asignado.")

        sql = """
        UPDATE MEDICAMENTO
        SET nombre_comercial = ?, precio = ?, stock = ?
        WHERE id_medicamento = ?;
        """
        with self.conexion_db.obtener_conexion() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (
                medicamento.nombre_comercial,
                medicamento.precio,
                medicamento.stock,
                medicamento.id_medicamento
            ))
            if cursor.rowcount == 0:
                raise exceptions.EntidadNoEncontradaException("Medicamento", medicamento.id_medicamento)
            return True

    # DELETE
    def eliminar(self, id_medicamento: int) -> bool:
        """Elimina el medicamento y retorna True si afectó filas."""
        sql = "DELETE FROM MEDICAMENTO WHERE id_medicamento = ?;"
        try:
            with self.conexion_db.obtener_conexion() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, (id_medicamento,))
                if cursor.rowcount == 0:
                    raise exceptions.EntidadNoEncontradaException("Medicamento", id_medicamento)
                return True
        except sqlite3.IntegrityError:
            raise exceptions.ReferenciaIntegridadError(
                f"No es posible eliminar el medicamento #{id_medicamento} porque ya está asociado a recetas médicas históricas."
            )

    def listar_stock_critico(self) -> list[Medicamento]:
        from models.medicamento import Medicamento

        sql = """
        SELECT id_medicamento, nombre_comercial, precio, stock
        FROM MEDICAMENTO
        WHERE stock <= ?
        ORDER BY stock ASC;
        """
        with self.conexion_db.obtener_conexion() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (Medicamento.stock_critico,))
            filas = cursor.fetchall()
            return [self._mapear_fila(fila) for fila in filas]

    # Mapper
    def _mapear_fila(self, fila: tuple) -> Medicamento:
        from models.medicamento import Medicamento
        return Medicamento(
            id_medicamento=fila[0],
            nombre_comercial=fila[1],
            precio=fila[2],
            stock=fila[3]
        )