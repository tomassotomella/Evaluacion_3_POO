# Auditoría SAST/AppSec del consumo HTTP

## 1. Alcance

La revisión estática se concentró en:

- `services/cliente_resiliente.py`
- `services/economia_service.py`
- `services/feriado_service.py`
- `services/servicio_clima.py`
- `config/configuracion.py`

El objetivo fue determinar qué controles deben probarse directamente en el cliente HTTP y cuáles dependen del uso que hacen de él los servicios.

## 2. Decisión sobre el alcance de las pruebas

No es suficiente probar únicamente `cliente_resiliente.py`. Se requieren dos niveles:

1. **Pruebas directas del cliente HTTP**
   - Timeout y límite de intentos.
   - Reintentos únicamente para errores transitorios.
   - Ausencia de reintentos para errores permanentes.
   - Traducción explícita de errores de transporte y HTTP.
   - Validación de TLS y de la URL configurada.

2. **Pruebas de los servicios consumidores**
   - Carga y validación de configuración.
   - Uso de claves de API sin exponerlas en mensajes o trazas.
   - Construcción de solicitudes y parámetros.
   - Parseo de respuestas externas.
   - Uso correcto de caché y contingencias.
   - Propagación de excepciones de dominio sin convertirlas en resultados silenciosos.

El cliente garantiza políticas de transporte; los servicios pueden introducir riesgos adicionales al construir URLs, procesar JSON, registrar errores o decidir cómo degradar ante una falla externa.

## 3. Resultado ejecutivo

La revisión especializada no identificó vulnerabilidades explotables en los cambios revisados. No se requiere un refactor de producción como resultado de esta auditoría y no se modificó la lógica productiva.

Los controles observados son coherentes con una implementación resiliente:

- Timeout configurable.
- Reintentos acotados y aplicados a fallas transitorias.
- No reintentar indiscriminadamente errores permanentes.
- Excepciones externas traducidas a errores de dominio explícitos.
- Configuración externa para URLs y claves, sin secretos reales en `.env.example`.
- Separación entre el cliente de transporte y los servicios que interpretan las respuestas.

Este resultado no reemplaza pruebas dinámicas. Las pruebas deben ejecutarse con transporte simulado y, cuando corresponda, con servicios consumidores aislados.

## 4. Tabla de hallazgos

| # | Severity | File | Lines | Vulnerability | Confidence |
|---|----------|------|-------|---------------|------------|
| — | — | — | — | No se identificaron vulnerabilidades explotables en el alcance revisado. | — |

## 5. Evaluación por categoría

### A01: Broken Access Control / SSRF — CWE-918

**Hallazgo y Riesgo:** No se confirmó una vulnerabilidad SSRF. Las URLs se obtienen de la configuración de la aplicación y no se observó que provengan directamente de una entrada de usuario en el flujo revisado.

**Severidad:** No aplica.

**Mapeo OWASP / CWE:** Sin hallazgo confirmado.

**Código Refactorizado:** No aplica. Como endurecimiento opcional para despliegues donde la configuración pueda ser modificada por terceros, se recomienda una allowlist de esquema y host antes de ejecutar la solicitud:

```python
from urllib.parse import urlparse

HOSTS_PERMITIDOS = {
    "api.boostr.cl",
    "api.exchangerate.host",
    "api.weatherapi.com",
}


def validar_url_externa(url: str) -> str:
    partes = urlparse(url)
    if partes.scheme != "https" or partes.hostname not in HOSTS_PERMITIDOS:
        raise ValueError("La URL externa no está permitida")
    return url
```

Este endurecimiento no fue aplicado porque las URLs actuales son configuración administrativa y no se demostró control externo sobre ellas.

### A02: Security Misconfiguration / DoS — CWE-400

**Hallazgo y Riesgo:** No se confirmó una condición de denegación de servicio causada por ausencia de timeout o reintentos ilimitados. El cliente usa timeout configurable y una política de reintentos acotada.

**Severidad:** No aplica.

**Mapeo OWASP / CWE:** Sin hallazgo confirmado.

**Código Refactorizado:** No aplica. Como medida adicional para endpoints fuera del control de la aplicación, puede incorporarse un límite de tamaño de respuesta antes de parsear JSON. Debe implementarse en el cliente común para que todos los consumidores compartan la misma política.

### A03: Software Supply Chain Failures

**Hallazgo y Riesgo:** No se confirmó una vulnerabilidad de cadena de suministro en el alcance revisado.

**Severidad:** No aplica.

**Mapeo OWASP / CWE:** Sin hallazgo confirmado.

**Código Refactorizado:** No aplica. La revisión de versiones, hashes y dependencias debe mantenerse como control separado del análisis funcional del cliente HTTP.

### A04: Cryptographic Failures / Secretos — CWE-259, CWE-798

**Hallazgo y Riesgo:** No se observó una clave real embebida en el código ni en `.env.example`. La configuración de la clave de WeatherAPI se realiza mediante el entorno.

**Severidad:** No aplica.

**Mapeo OWASP / CWE:** Sin hallazgo confirmado.

**Código Refactorizado:** No aplica. Las pruebas deben verificar que las excepciones, logs y respuestas no incluyan headers o valores de API key.

### A05: Injection

**Hallazgo y Riesgo:** No se confirmó una inyección en el consumo HTTP revisado. El análisis no mostró que datos externos se conviertan en código, consultas SQL o encabezados sin pasar por las capas correspondientes.

**Severidad:** No aplica.

**Mapeo OWASP / CWE:** Sin hallazgo confirmado.

**Código Refactorizado:** No aplica.

### A06: Insecure Design

**Hallazgo y Riesgo:** La separación del cliente HTTP, la configuración y los servicios consumidores evita concentrar transporte, parseo y reglas de dominio en una única clase. No se confirmó un diseño inseguro explotable.

**Severidad:** No aplica.

**Mapeo OWASP / CWE:** Sin hallazgo confirmado.

**Código Refactorizado:** No aplica.

### A07: Authentication Failures

**Hallazgo y Riesgo:** No se confirmó un fallo de autenticación en el alcance revisado. Las credenciales de servicios externos no se trataron como datos de usuario ni se encontraron hardcodeadas.

**Severidad:** No aplica.

**Mapeo OWASP / CWE:** Sin hallazgo confirmado.

**Código Refactorizado:** No aplica.

### A08: Software and Data Integrity Failures

**Hallazgo y Riesgo:** No se confirmó una alteración de integridad explotable. Los consumidores son responsables de validar y parsear las respuestas antes de utilizarlas, y las fallas de formato no se presentan como respuestas exitosas silenciosas.

**Severidad:** No aplica.

**Mapeo OWASP / CWE:** Sin hallazgo confirmado.

**Código Refactorizado:** No aplica.

### A09: Security Logging and Alerting Failures

**Hallazgo y Riesgo:** No se confirmó una fuga de secretos ni un registro que convierta la respuesta externa completa en información sensible. Las excepciones conservan información útil para diagnóstico sin requerir un fallback silencioso.

**Severidad:** No aplica.

**Mapeo OWASP / CWE:** Sin hallazgo confirmado.

**Código Refactorizado:** No aplica.

### A10: Mishandling of Exceptional Conditions — CWE-391, CWE-755

**Hallazgo y Riesgo:** No se confirmó un manejo inseguro de excepciones. El cliente distingue fallas transitorias de errores permanentes, limita los reintentos y traduce los errores a excepciones explícitas.

**Severidad:** No aplica.

**Mapeo OWASP / CWE:** Sin hallazgo confirmado.

**Código Refactorizado:** No aplica.

## 6. Casos mínimos recomendados

### Cliente HTTP

- Timeout agotado.
- Error de conexión.
- HTTP 429 y HTTP 5xx con cantidad máxima de intentos.
- HTTP 401, 403 y 404 sin reintento.
- URL con esquema no permitido.
- Error TLS.
- Respuesta inválida o excesivamente grande, si se incorpora el límite de tamaño.

### Economía, feriados y clima

- API caída con y sin caché disponible.
- JSON inválido o incompleto.
- Configuración ausente o inválida.
- Verificación de que una API key nunca aparezca en errores, logs o resultados.
- Confirmación de que cada servicio aplica su propia política de parseo, caché y contingencia sin duplicar la lógica de transporte.

## 7. Conclusión

La estrategia correcta es probar **el cliente HTTP y sus consumidores**, no elegir uno de los dos. El cliente debe demostrar que sus límites y traducción de errores son seguros; los servicios deben demostrar que no convierten una respuesta externa o una configuración insegura en una vulnerabilidad de aplicación.
