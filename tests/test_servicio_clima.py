import os
import sqlite3
import tempfile
import unittest
from datetime import date, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

from database.conexion import ConexionDBT
from dao.especie_dao import EspecieDAO
from dao.mascota_dao import MascotaDAO
from dao.propietario_dao import PropietarioDAO
from exceptions.exceptions import (
    ConfiguracionException,
    ConexionTimeoutException,
    ErrorRespuestaHttpException,
    ErrorWeatherAPIException,
    FormatoRespuestaInvalidoException,
    ServicioExternoException,
)
from models.clima import Clima
from models.especie import Especie
from models.mascota import Mascota
from models.propietario import Propietario
from screens.menu_screen import _obtener_texto_clima
from screens.propietario_screens import _mostrar_clima_y_alertas
from services.alerta_zoosanitaria_service import AlertaZoosanitariaService
from services.servicio_clima import ServicioClima


class RespuestaSimulada:
    def __init__(self, contenido):
        self.contenido = contenido

    def json(self):
        if isinstance(self.contenido, Exception):
            raise self.contenido
        return self.contenido


class ClienteSimulado:
    def __init__(self, respuesta=None, error=None):
        self.respuesta = respuesta
        self.error = error
        self.llamadas = []

    def ejecutar_get(self, url, parametros=None, cabeceras=None, *, servicio):
        self.llamadas.append((url, parametros, cabeceras, servicio))
        if self.error is not None:
            raise self.error
        return self.respuesta


def crear_payload(
    temperatura=21.4,
    sensacion=20.8,
    humedad=65,
    precipitacion=0.0,
):
    return {
        "location": {
            "name": "Los Ángeles",
            "region": "Biobío",
            "country": "Chile",
        },
        "current": {
            "temp_c": temperatura,
            "feelslike_c": sensacion,
            "condition": {"text": "Parcialmente nublado"},
            "humidity": humedad,
            "precip_mm": precipitacion,
            "last_updated": "2026-11-10 10:00",
        },
    }


def crear_clima(temperatura=21.4, precipitacion=0.0):
    return Clima(
        localidad="Los Ángeles",
        region="Biobío",
        pais="Chile",
        temperatura_c=temperatura,
        sensacion_termica_c=temperatura,
        condicion="Soleado",
        humedad_pct=60,
        precipitacion_mm=precipitacion,
        observado_en=datetime(2026, 11, 10, 10, 0),
    )


class ServicioClimaTests(unittest.TestCase):
    def setUp(self):
        self.directorio_env = tempfile.TemporaryDirectory()
        self.ruta_env = Path(self.directorio_env.name) / ".env"
        self.ruta_env.write_text(
            "WEATHER_API_KEY=clave-de-prueba\n",
            encoding="utf-8",
        )
        self.patcher_env = patch.object(ServicioClima, "ENV_PATH", self.ruta_env)
        self.patcher_env.start()

    def tearDown(self):
        self.patcher_env.stop()
        self.directorio_env.cleanup()

    def test_respuesta_valida_se_normaliza_y_usa_key_en_parametros(self):
        cliente = ClienteSimulado(RespuestaSimulada(crear_payload()))
        with patch.dict(
            os.environ,
            {"WEATHER_API_KEY": "clave-de-entorno-que-no-se-usa"},
        ):
            servicio = ServicioClima(cliente)

        clima = servicio.obtener_clima(" Los Ángeles, Chile ")

        self.assertEqual(clima.localidad, "Los Ángeles")
        self.assertEqual(clima.region, "Biobío")
        self.assertEqual(clima.temperatura_c, 21.4)
        self.assertEqual(clima.sensacion_termica_c, 20.8)
        self.assertEqual(clima.condicion, "Parcialmente nublado")
        self.assertEqual(clima.humedad_pct, 65)
        self.assertEqual(clima.precipitacion_mm, 0.0)
        self.assertEqual(cliente.llamadas[0][1], {
            "key": "clave-de-prueba",
            "q": "Los Ángeles, Chile",
            "lang": "es",
        })

    def test_api_key_ausente_lanza_error_de_configuracion(self):
        ruta_sin_clave = Path(self.directorio_env.name) / "sin_clave.env"
        ruta_sin_clave.write_text("", encoding="utf-8")
        with patch.object(ServicioClima, "ENV_PATH", ruta_sin_clave):
            servicio = ServicioClima(ClienteSimulado())

        with self.assertRaisesRegex(ConfiguracionException, "WEATHER_API_KEY"):
            servicio.obtener_clima()

    def test_http_401_se_traduce_sin_exponer_clave(self):
        servicio = ServicioClima(
            ClienteSimulado(error=ErrorRespuestaHttpException(
                "WeatherAPI",
                401,
                "clave-de-prueba",
            )),
        )

        with self.assertRaises(ErrorWeatherAPIException) as contexto:
            servicio.obtener_clima()

        self.assertEqual(contexto.exception.status_code, 401)
        self.assertNotIn("clave-de-prueba", str(contexto.exception))
        self.assertIsNone(contexto.exception.__context__)

    def test_http_404_se_traduce_como_localidad_no_encontrada(self):
        servicio = ServicioClima(
            ClienteSimulado(error=ErrorRespuestaHttpException("WeatherAPI", 404)),
        )

        with self.assertRaisesRegex(ErrorWeatherAPIException, "localidad"):
            servicio.obtener_clima()

    def test_timeout_conserva_excepcion_resiliente(self):
        error = ConexionTimeoutException("WeatherAPI", 10)
        servicio = ServicioClima(
            ClienteSimulado(error=error),
        )

        with self.assertRaises(ConexionTimeoutException):
            servicio.obtener_clima()

    def test_error_de_conexion_no_expone_datos_del_cliente(self):
        servicio = ServicioClima(
            ClienteSimulado(error=ServicioExternoException(
                "Servicio externo",
                "error para clave-de-prueba",
            )),
        )

        with self.assertRaises(ErrorWeatherAPIException) as contexto:
            servicio.obtener_clima()

        self.assertNotIn("clave-de-prueba", str(contexto.exception))
        self.assertIsNone(contexto.exception.__context__)

    def test_json_invalido_se_traduce(self):
        servicio = ServicioClima(
            ClienteSimulado(RespuestaSimulada(ValueError("JSON inválido"))),
        )

        with self.assertRaises(FormatoRespuestaInvalidoException):
            servicio.obtener_clima()

    def test_campos_obligatorios_ausentes_se_traducen(self):
        servicio = ServicioClima(
            ClienteSimulado(RespuestaSimulada({"location": {}})),
        )

        with self.assertRaises(FormatoRespuestaInvalidoException):
            servicio.obtener_clima()

    def test_error_especifico_en_json_de_weatherapi_se_traduce(self):
        servicio = ServicioClima(
            ClienteSimulado(
                RespuestaSimulada({
                    "error": {
                        "code": 1006,
                        "message": "No location found.",
                    }
                })
            )
        )

        with self.assertRaises(ErrorWeatherAPIException) as contexto:
            servicio.obtener_clima()

        self.assertEqual(contexto.exception.codigo_api, 1006)
        self.assertRegex(str(contexto.exception), "localidad")


class AlertasZoosanitariasTests(unittest.TestCase):
    def setUp(self):
        self.especie = Especie(15, "Perro", id_especie=1)
        self.propietario = Propietario(
            "12345678-5",
            "Ana Perez",
            "+56912345678",
        )
        self.servicio = AlertaZoosanitariaService()

    def crear_mascota(self, raza, edad_anios=2):
        return Mascota(
            nombre="Luna",
            fecha_nacimiento=date.today() - timedelta(days=edad_anios * 365),
            especie=self.especie,
            propietario=self.propietario,
            raza=raza,
        )

    def test_calor_sobre_28_alerta_perro_braquicefalo(self):
        alertas = self.servicio.evaluar(
            crear_clima(temperatura=28.1),
            self.crear_mascota("Pug"),
        )

        self.assertIn("golpe_de_calor", [alerta.tipo for alerta in alertas])

    def test_frio_bajo_8_alerta_paciente_geriatrico(self):
        alertas = self.servicio.evaluar(
            crear_clima(temperatura=7.9),
            self.crear_mascota("Mestizo", edad_anios=8),
        )

        self.assertIn(
            "frio_paciente_geriatrico",
            [alerta.tipo for alerta in alertas],
        )

    def test_precipitacion_de_10_mm_genera_alerta(self):
        alertas = self.servicio.evaluar(
            crear_clima(precipitacion=10),
            self.crear_mascota("Mestizo"),
        )

        self.assertIn(
            "precipitacion_intensa",
            [alerta.tipo for alerta in alertas],
        )


class IntegracionClimaTests(unittest.TestCase):
    def setUp(self):
        self.directorio_env = tempfile.TemporaryDirectory()
        self.ruta_env = Path(self.directorio_env.name) / ".env"
        self.ruta_env.write_text(
            "WEATHER_API_KEY=clave-de-prueba\n",
            encoding="utf-8",
        )
        self.patcher_env = patch.object(ServicioClima, "ENV_PATH", self.ruta_env)
        self.patcher_env.start()

    def tearDown(self):
        self.patcher_env.stop()
        self.directorio_env.cleanup()

    def test_menu_muestra_offline_si_weatherapi_falla(self):
        servicio = ServicioClima(
            ClienteSimulado(error=ServicioExternoException(
                "WeatherAPI",
                "sin conexión",
            )),
        )

        self.assertEqual(
            _obtener_texto_clima(servicio),
            "[CLIMA EN VIVO]: No disponible (Offline)",
        )

    def test_ficha_consulta_clima_una_vez_y_reutiliza_datos(self):
        propietario = Propietario(
            "12345678-5",
            "Ana Perez",
            "+56912345678",
            comuna="Los Ángeles",
        )
        mascota = Mascota(
            "Luna",
            date.today() - timedelta(days=365),
            Especie(15, "Perro", id_especie=1),
            propietario,
            raza="Pug",
        )

        class ServicioClimaContador:
            def __init__(self):
                self.consultas = 0

            def obtener_clima(self, comuna):
                self.consultas += 1
                self.comuna = comuna
                return crear_clima(temperatura=30)

        class ServicioMascotas:
            def listar_mascotas_por_propietario(self, rut):
                return [mascota, mascota]

        servicio_clima = ServicioClimaContador()
        with patch("builtins.print"):
            _mostrar_clima_y_alertas(
                propietario,
                servicio_clima,
                AlertaZoosanitariaService(),
                ServicioMascotas(),
            )

        self.assertEqual(servicio_clima.consultas, 1)
        self.assertEqual(servicio_clima.comuna, "Los Ángeles")

    def test_dao_persiste_comuna_y_raza(self):
        with tempfile.TemporaryDirectory() as directorio:
            ruta_db = os.path.join(directorio, "vetcare.db")
            conexion = ConexionDBT(ruta_db)
            propietario_dao = PropietarioDAO(conexion)
            especie_dao = EspecieDAO(conexion)
            mascota_dao = MascotaDAO(
                conexion,
                especie_dao,
                propietario_dao,
            )

            propietario = Propietario(
                "12345678-5",
                "Ana Perez",
                "+56912345678",
                comuna="Los Ángeles",
            )
            propietario_dao.insertar(propietario)
            especie = Especie(15, "Perro")
            especie_dao.insertar(especie)
            mascota = Mascota(
                "Luna",
                date.today() - timedelta(days=365),
                especie,
                propietario,
                raza="Pug",
            )
            mascota_dao.insertar(mascota)

            self.assertEqual(
                propietario_dao.obtener_por_rut(propietario.rut).comuna,
                "Los Ángeles",
            )
            self.assertEqual(mascota_dao.obtener_por_id(mascota.id_mascota).raza, "Pug")

    def test_dao_migra_columnas_en_una_base_existente(self):
        with tempfile.TemporaryDirectory() as directorio:
            ruta_db = os.path.join(directorio, "vetcare_antigua.db")
            conn = sqlite3.connect(ruta_db)
            try:
                conn.executescript(
                    """
                    CREATE TABLE PROPIETARIO (
                        id_propietario INTEGER PRIMARY KEY AUTOINCREMENT,
                        rut TEXT UNIQUE NOT NULL,
                        nombre_completo TEXT NOT NULL,
                        telefono TEXT NOT NULL
                    );
                    INSERT INTO PROPIETARIO
                    VALUES (1, '12345678-5', 'Ana Perez', '+56912345678');
                    CREATE TABLE ESPECIE (
                        id_especie INTEGER PRIMARY KEY AUTOINCREMENT,
                        nombre_especie TEXT UNIQUE NOT NULL,
                        esperanza_vida_max INTEGER NOT NULL
                    );
                    INSERT INTO ESPECIE VALUES (1, 'Perro', 15);
                    CREATE TABLE MASCOTA (
                        id_mascota INTEGER PRIMARY KEY AUTOINCREMENT,
                        nombre TEXT NOT NULL,
                        fecha_nacimiento TEXT NOT NULL,
                        id_especie INTEGER NOT NULL,
                        id_propietario INTEGER NOT NULL
                    );
                    INSERT INTO MASCOTA
                    VALUES (1, 'Luna', '2020-01-01', 1, 1);
                    """
                )
                conn.commit()
            finally:
                conn.close()

            conexion = ConexionDBT(ruta_db)
            propietario_dao = PropietarioDAO(conexion)
            especie_dao = EspecieDAO(conexion)
            mascota_dao = MascotaDAO(
                conexion,
                especie_dao,
                propietario_dao,
            )

            propietario = propietario_dao.obtener_por_id(1)
            mascota = mascota_dao.obtener_por_id(1)
            self.assertEqual(propietario.comuna, "Los Ángeles, Chile")
            self.assertEqual(mascota.raza, "Sin especificar")


if __name__ == "__main__":
    unittest.main()
