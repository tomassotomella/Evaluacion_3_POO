import requests
from requests.adapters import HTTPAdapter
from urllib3.util.ssl_ import create_urllib3_context

# Cifrados compatibles con servidores legacy o con configuraciones SSL estrictas
CIPHERS = 'DEFAULT:@SECLEVEL=1'

class SSLAdapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        context = create_urllib3_context(ciphers=CIPHERS)
        kwargs['ssl_context'] = context
        return super().init_poolmanager(*args, **kwargs)

class Divisa:
    def __init__(self, codigo: str, valor: float):
        self.codigo = codigo
        self.valor = valor

    @classmethod
    def desde_api(cls, url_endpoint: str = "https://mindicador.cl/api/dolar"):
        session = requests.Session()
        session.mount('https://', SSLAdapter())
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"
        }

        respuesta = session.get(url_endpoint, headers=headers, timeout=10)
        respuesta.raise_for_status()

        datos = respuesta.json()
        ultimo_valor = datos["serie"][0]["valor"]
        
        return cls(codigo=datos["codigo"], valor=ultimo_valor)

# Prueba de ejecución
dolar = Divisa.desde_api()
print(f"Éxito: {dolar.codigo.upper()} a ${dolar.valor} CLP")