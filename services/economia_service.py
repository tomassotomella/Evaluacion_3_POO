import requests
from datetime import datetime
from exceptions import exceptions
from models.divisa import Divisa

class EconomicService:
    URL_BASE = "https://mindicador.cl/api"

@classmethod
def obtener_indicador(cls, tipo_indicador: str) -> Divisa | None:
    endpoint = f'{cls.URL_BASE}/{tipo_indicador.lower()}'
    try:
        respuesta = requests.get(endpoint, timeout=10)
        if respuesta.status_code != 200:
            raise exceptions.DominioException(respuesta)
        payload = respuesta.json()

        if 'serie' not in payload or len(payload['serie'] == 0):
            print('Estructura de datos incompleta')
            return None

        ultima_observacion = payload['serie'][0]

        return Divisa(
            codigo = payload.get('codigo', tipo_indicador),
            nombre = payload.get('nombre', 'Sin Nombre'),
            valor = ultima_observacion['valor'],
            fecha_actualizacion = datetime.fromisoformat(ultima_observacion['fecha']).date()
        )
    except requests.exceptions.Timeout:
        print("[ERROR DE CONEXIÓN] El servidor tardó más de 10 segundos en responder.")
        return None
    except requests.exceptions.RequestException as error_red:
        print(f"[ERROR DE CONEXIÓN] Fallo al consultar el servicio económico: {error_red}")
        return None    
    except (KeyError, ValueError, TypeError) as error_datos:
            print(f"[ERROR DE DESERIALIZACIÓN] Falla al parsear los datos recibidos: {error_datos}")
            return None