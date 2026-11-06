from database.conexion import ConexionDB
from utilities.fechas import sqlite_a_date, date_a_sqlite
from exceptions import exceptions
from models.divisa import Divisa


class DivisaDAO:
    def __init__(self, conexion_db: ConexionDB):
        self.db = conexion_db
        self._crear_tabla()

    def _crear_tabla(self):
        ddl = '''
        CREATE TABLE IF NOT EXISTS DIVISA (
            codigo TEXT PRIMARY KEY,
            nombre TEXT NOT NULL,
            valor REAL NOT NULL,
            fecha_actualizacion TEXT NOT NULL,
            CHECK (valor > 0)
        );
        '''
        with self.db.obtener_conexion() as conn:
            cursor = conn.cursor()
            cursor.execute(ddl)

    def actualizar(self, divisa: Divisa) -> bool:
        sql = '''
        INSERT OR REPLACE INTO DIVISA (codigo, nombre, valor, fecha_actualizacion)
        VALUES (?, ?, ?, ?);
        '''
        with self.db.obtener_conexion() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (
                divisa.codigo.strip().lower(),
                divisa.nombre,
                divisa.valor,
                date_a_sqlite(divisa.fecha_actualizacion)
            ))
            return cursor.rowcount > 0

    def obtener_por_codigo(self, codigo: str) -> Divisa:
        sql = '''
        SELECT codigo, nombre, valor, fecha_actualizacion
        FROM DIVISA
        WHERE codigo = ?;
        '''
        with self.db.obtener_conexion() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (codigo.strip().lower(),))
            fila = cursor.fetchone()
            if fila is None: 
                raise exceptions.EntidadNoEncontradaException("Divisa", codigo)
            return self._mapear_fila(fila)

    def listar_todas(self) -> list[Divisa]:
        sql = '''
        SELECT codigo, nombre, valor, fecha_actualizacion
        FROM DIVISA
        ORDER BY nombre ASC;
        '''
        with self.db.obtener_conexion() as conn:
            cursor = conn.cursor()
            cursor.execute(sql)
            filas = cursor.fetchall()
            return [self._mapear_fila(fila) for fila in filas]

    def _mapear_fila(self, fila: tuple) -> Divisa:
        return Divisa(
            codigo=fila[0],
            nombre=fila[1],
            valor=float(fila[2]),
            fecha_actualizacion=sqlite_a_date(fila[3])
        )
