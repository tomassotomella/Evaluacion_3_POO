import sqlite3
from contextlib import contextmanager

class ConexionDB:
    def __init__(self, ruta_db: str = 'database/clinica_vetcare.db'):
        self.ruta_db = ruta_db

    @contextmanager
    def obtener_conexion(self):
        conn = sqlite3.connect(self.ruta_db)
        #habilitar soporte para claves foráneas en SQLite
        conn.execute("PRAGMA foreign_keys = ON;")
        try:
            yield conn
            conn.commit() # confirma si todo el bloque 'with' termina sin excepciones
        except Exception as error:
            conn.rollback() # revierte si ocurre alguna excepción
            raise error
        finally:
            conn.close() #Se ejecuta SIEMPRE, previniendo Database Locked


class ConexionDBT:
    def __init__(self, ruta_db: str = 'database/clinica_vetcare_test.db'):
        self.ruta_db = ruta_db

    @contextmanager
    def obtener_conexion(self):
        conn = sqlite3.connect(self.ruta_db)
        #habilitar soporte para claves foráneas en SQLite
        conn.execute("PRAGMA foreign_keys = ON;")
        try:
            yield conn
            conn.commit() # confirma si todo el bloque 'with' termina sin excepciones
        except Exception as error:
            conn.rollback() # revierte si ocurre alguna excepción
            raise error
        finally:
            conn.close() #Se ejecuta SIEMPRE, previniendo Database Locked