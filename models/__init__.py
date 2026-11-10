import sys
from pathlib import Path

_models_dir = str(Path(__file__).resolve().parent)
if _models_dir not in sys.path:
    sys.path.insert(0, _models_dir)

# Mapear los módulos para que `from models.X import ...` y `from X import ...` apunten al mismo módulo exacto
for mod_name in [
    'especialidad', 'especie', 'persona', 'propietario', 'veterinario',
    'medicamento', 'mascota', 'detalle_consulta', 'receta_medica', 'consulta',
    'clima'
]:
    mod = __import__(mod_name)
    sys.modules[f'models.{mod_name}'] = mod

from especialidad import Especialidad
from especie import Especie
from persona import Persona
from propietario import Propietario
from veterinario import Veterinario
from medicamento import Medicamento
from mascota import Mascota
from detalle_consulta import DetalleConsulta
from receta_medica import RecetaMedica
from consulta import Consulta, EstadosConsulta
from clima import Clima

__all__ = [
    'Especialidad',
    'Especie',
    'Persona',
    'Propietario',
    'Veterinario',
    'Medicamento',
    'Mascota',
    'DetalleConsulta',
    'RecetaMedica',
    'Consulta',
    'EstadosConsulta',
    'Clima'
]
