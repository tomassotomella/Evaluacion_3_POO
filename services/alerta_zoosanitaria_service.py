from __future__ import annotations

import unicodedata
from dataclasses import dataclass

from models.clima import Clima
from models.mascota import Mascota


@dataclass(frozen=True)
class AlertaZoosanitaria:
    tipo: str
    mensaje: str
    recomendacion: str


class AlertaZoosanitariaService:
    UMBRAL_TEMPERATURA_ALTA_C = 28
    UMBRAL_TEMPERATURA_BAJA_C = 8
    UMBRAL_PRECIPITACION_INTENSA_MM = 10
    EDAD_GERIATRICA_ANIOS = 7

    RAZAS_BRAQUICEFALAS = {
        "boston terrier",
        "boxer",
        "bulldog",
        "bulldog americano",
        "bulldog frances",
        "bulldog ingles",
        "carlino",
        "pequines",
        "pug",
        "shih tzu",
    }

    def evaluar(self, clima: Clima, mascota: Mascota) -> list[AlertaZoosanitaria]:
        alertas: list[AlertaZoosanitaria] = []
        especie = self._normalizar(mascota.especie.nombre_especie)
        raza = self._normalizar(mascota.raza)
        es_perro = especie in {"perro", "canino", "can"}
        es_braquicefalo = es_perro and raza in self.RAZAS_BRAQUICEFALAS

        if es_braquicefalo and clima.temperatura_c > self.UMBRAL_TEMPERATURA_ALTA_C:
            alertas.append(
                AlertaZoosanitaria(
                    tipo="golpe_de_calor",
                    mensaje=(
                        f"{mascota.nombre}: riesgo de golpe de calor "
                        "por temperatura sobre 28 °C en una raza braquicéfala."
                    ),
                    recomendacion=(
                        "Mantener agua y sombra disponibles, evitar ejercicio "
                        "en horas calurosas y vigilar signos de dificultad respiratoria."
                    ),
                )
            )

        if (
            clima.temperatura_c < self.UMBRAL_TEMPERATURA_BAJA_C
            and mascota.calcular_edad_anios() >= self.EDAD_GERIATRICA_ANIOS
        ):
            alertas.append(
                AlertaZoosanitaria(
                    tipo="frio_paciente_geriatrico",
                    mensaje=(
                        f"{mascota.nombre}: posible riesgo asociado al frío "
                        "en un paciente de 7 años o más."
                    ),
                    recomendacion=(
                        "Limitar la exposición al frío y consultar al equipo "
                        "veterinario si presenta temblores o decaimiento."
                    ),
                )
            )

        if clima.precipitacion_mm >= self.UMBRAL_PRECIPITACION_INTENSA_MM:
            alertas.append(
                AlertaZoosanitaria(
                    tipo="precipitacion_intensa",
                    mensaje=(
                        f"{mascota.nombre}: precipitación intensa "
                        "(umbral: 10 mm en el dato actual de WeatherAPI)."
                    ),
                    recomendacion=(
                        "Preferir paseos breves y evitar zonas inundadas o "
                        "con agua estancada."
                    ),
                )
            )

        return alertas

    @staticmethod
    def _normalizar(valor: str) -> str:
        descompuesto = unicodedata.normalize("NFKD", valor.casefold())
        return "".join(
            caracter
            for caracter in descompuesto
            if not unicodedata.combining(caracter)
        ).strip()
