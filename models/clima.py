from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Clima:
    localidad: str
    region: str
    pais: str
    temperatura_c: float
    sensacion_termica_c: float
    condicion: str
    humedad_pct: int
    precipitacion_mm: float
    observado_en: datetime
