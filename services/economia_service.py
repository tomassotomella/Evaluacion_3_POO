import requests
from datetime import date, datetime, timedelta
from dao.divisa_dao import DivisaDAO
from exceptions import exceptions
from utilities.ValidadorEntradas import ValidadorEntradas
from exceptions.exceptions import (
    ServicioExternoException,
    ConexionTimeoutException,
    ErrorRespuestaHttpException,
    FormatoRespuestaInvalidoException
)
from models.divisa import Divisa


class EconomiaService:
    SERVICIO_NOMBRE = "DolarAPI"
    URL_BASE = "https://cl.dolarapi.com/v1/cotizaciones"
    TIMEOUT = 10
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    def __init__(self, divisa_dao: DivisaDAO):
        self.divisa_dao = divisa_dao
        # Caché
        self._cache: dict[str, Divisa] = {}


    @classmethod
    def obtener_indicador(cls, tipo_indicador: str) -> Divisa:
        indicador_seguro = ValidadorEntradas.sanitizar_codigo_indicador(tipo_indicador)
        endpoint = f"{cls.URL_BASE}/{indicador_seguro}"

        try:
            respuesta = requests.get(endpoint, headers=cls.HEADERS, timeout=cls.TIMEOUT)

            if respuesta.status_code != 200:
                raise ErrorRespuestaHttpException(
                    servicio=cls.SERVICIO_NOMBRE,
                    status_code=respuesta.status_code,
                    detalle=respuesta.text[:200]
                )

            try:
                payload = respuesta.json()
            except ValueError as error_json:
                raise FormatoRespuestaInvalidoException(
                    servicio=cls.SERVICIO_NOMBRE,
                    motivo=f"La respuesta no es un JSON válido: {error_json}"
                ) from error_json

            if not isinstance(payload, dict):
                raise FormatoRespuestaInvalidoException(
                    servicio=cls.SERVICIO_NOMBRE,
                    motivo="El cuerpo de la respuesta no es un objeto JSON estructurado."
                )

            codigo = payload.get("moneda") 
            nombre = payload.get("nombre") 
            valor = payload.get("venta")
            fecha_raw = payload.get("fechaActualizacion")

            if valor is None:
                raise FormatoRespuestaInvalidoException(
                    servicio=cls.SERVICIO_NOMBRE,
                    motivo="No se encontró el valor de cotización ('venta') en la respuesta."
                )

            if not fecha_raw:
                raise FormatoRespuestaInvalidoException(
                    servicio=cls.SERVICIO_NOMBRE,
                    motivo="No se encontró la fecha de actualización en la respuesta."
                )

            fecha_actualizacion = datetime.fromisoformat(payload['fechaActualizacion']).date()

            return Divisa(
                codigo=codigo,
                nombre=nombre,
                valor=float(valor),
                fecha_actualizacion=fecha_actualizacion
            )

        except requests.exceptions.Timeout as error_timeout:
            raise ConexionTimeoutException(
                servicio=cls.SERVICIO_NOMBRE,
                timeout_segundos=cls.TIMEOUT
            ) from error_timeout

        except requests.exceptions.RequestException as error_red:
            raise ServicioExternoException(
                servicio=cls.SERVICIO_NOMBRE,
                mensaje=f"Fallo en la conexión de red: {error_red}"
            ) from error_red

        except (ValueError, TypeError) as error_datos:
            raise FormatoRespuestaInvalidoException(
                servicio=cls.SERVICIO_NOMBRE,
                motivo=f"Error al procesar los tipos de datos de la divisa: {error_datos}"
            ) from error_datos

    @staticmethod
    def _obtener_fecha_habil_esperada(fecha_referencia: date | None = None) -> date:
        """Calcula la fecha de cotización esperada según el calendario bursátil/bancario.
        
        Si la fecha de referencia cae en fin de semana (sábado o domingo), el mercado
        no publica cotizaciones y rige oficialmente el valor del último viernes hábil.
        """
        fecha = fecha_referencia or date.today()
        dia_semana = fecha.weekday()  # 0: Lunes ... 4: Viernes, 5: Sábado, 6: Domingo

        if dia_semana == 5:  # Sábado -> se espera la cotización del viernes anterior
            return fecha - timedelta(days=1)
        if dia_semana == 6:  # Domingo -> se espera la cotización del viernes anterior
            return fecha - timedelta(days=2)
        return fecha

    def obtener_dolar_actual(self, forzar_refresco: bool = False) -> Divisa:
        """Obtiene la cotización actual del dólar implementando una estrategia de caché multinivel
        (RAM -> SQLite -> API Externa) con soporte de contingencia degradada ante caídas de red.
        """
        return self.obtener_divisa_actual(codigo="usd", forzar_refresco=forzar_refresco)

    def obtener_divisa_actual(self, codigo: str = "usd", forzar_refresco: bool = False) -> Divisa:
        """Obtiene una divisa gestionando los tres niveles de almacenamiento:
        1. Nivel L1 (RAM): Retorno inmediato si ya fue cargada para la fecha hábil esperada.
        2. Nivel L2 (SQLite): Consulta local evitando peticiones externas si está vigente.
        3. Nivel L3 (API HTTP): Sincroniza desde el servicio remoto y persiste en BD y RAM.
        4. Modo Contingencia: Si la API falla, utiliza el registro previo guardado en SQLite.
        """
        codigo_limpio = codigo.strip().lower()
        codigo_normalizado = codigo_limpio
        hoy = date.today()
        fecha_esperada = self._obtener_fecha_habil_esperada(hoy)

        # 1. VERIFICAR MEMORIA RAM (Caché L1)
        if not forzar_refresco and codigo_normalizado in self._cache:
            divisa_ram = self._cache[codigo_normalizado]
            if divisa_ram.fecha_actualizacion >= fecha_esperada:
                return divisa_ram

        # 2. VERIFICAR SQLITE (Caché L2)
        divisa_historica: Divisa | None = None
        try:
            divisa_sqlite = self.divisa_dao.obtener_por_codigo(codigo_normalizado)
            if not forzar_refresco and divisa_sqlite.fecha_actualizacion >= fecha_esperada:
                self._cache[codigo_normalizado] = divisa_sqlite
                return divisa_sqlite
            # Respaldamos la divisa histórica en caso de que la API externa falle
            divisa_historica = divisa_sqlite
        except exceptions.EntidadNoEncontradaException:
            divisa_historica = None

        # 3. CONSUMIR SERVICIO EXTERNO (API HTTP)
        try:
            divisa_fresca = self.obtener_indicador(codigo_normalizado)
            self.divisa_dao.actualizar(divisa_fresca)
            self._cache[codigo_normalizado] = divisa_fresca #guardar en cache
            return divisa_fresca

        except ServicioExternoException as error_api:
            # 4. CONTINGENCIA / MODO DEGRADADO: Usar el valor histórico si existe
            if divisa_historica is not None:
                self._cache[codigo_normalizado] = divisa_historica
                return divisa_historica

            # 5. SIN CONEXIÓN Y SIN REGISTROS PREVIOS EN BD
            raise error_api

    def convertir_clp_a_usd(self, monto_clp: float) -> tuple[float, Divisa]:
        
        divisa_dolar = self.obtener_dolar_actual()
        monto_usd = divisa_dolar.convertir_desde_pesos(monto_clp)
        return monto_usd, divisa_dolar

    def limpiar_cache(self) -> None:
        self._cache.clear()
