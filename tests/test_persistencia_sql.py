from datetime import date, datetime, timedelta

from database import ConexionDBT
from dao import (
    EspecialidadDAO,
    EspecieDAO,
    MedicamentoDAO,
    PropietarioDAO,
    VeterinarioDAO,
    MascotaDAO,
    ConsultaDAO,
    RecetaMedicaDAO,
)
from models import (
    Especialidad,
    Especie,
    Medicamento,
    Propietario,
    Veterinario,
    Mascota,
    Consulta,
    DetalleConsulta,
    RecetaMedica,
)


def main():
    print("=" * 65)
    print("      PRUEBA DE PERSISTENCIA SQL - TODAS LAS ENTIDADES")
    print("=" * 65)

    especialidades = [
        Especialidad(
            "Cardiologia",
            "Atencion del sistema cardiovascular"
        ),
        Especialidad(
            "Dermatologia",
            "Atencion de enfermedades de la piel"
        ),
        Especialidad(
            "Traumatologia",
            "Atencion de lesiones musculoesqueleticas"
        ),
    ]
    especies = [
        Especie(15, "Perro"),
        Especie(20, "Gato"),
        Especie(12, "Conejo"),
    ]
    medicamentos = [
        Medicamento("Amoxicilina 250mg", 5500, 100),
        Medicamento("Ketoprofeno 10mg", 3200, 50),
        Medicamento("Meloxicam 5mg", 4500, 80),
    ]
    propietarios = [
        Propietario("12345678-5", "Ana Perez", "+56912345678"),
        Propietario("11223344-6", "Beatriz Soto", "+56923456789"),
        Propietario("99887766-7", "Diego Rojas", "+56934567890"),
    ]
    veterinarios = [
        Veterinario(
            "98765432-1",
            "Carlos Gonzalez",
            "+56987654321",
            especialidades[0]
        ),
        Veterinario(
            "87654321-2",
            "Elena Martinez",
            "+56976543210",
            especialidades[1]
        ),
        Veterinario(
            "76543210-3",
            "Felipe Torres",
            "+56965432109",
            especialidades[2]
        ),
    ]
    mascotas = [
        Mascota(
            "Firulais",
            date.today() - timedelta(days=365 * 3),
            especies[0],
            propietarios[0]
        ),
        Mascota(
            "Michi",
            date.today() - timedelta(days=365 * 5),
            especies[1],
            propietarios[1]
        ),
        Mascota(
            "Bunny",
            date.today() - timedelta(days=365 * 2),
            especies[2],
            propietarios[2]
        ),
    ]
    consultas = [
        Consulta(
            mascotas[0],
            datetime.now() + timedelta(days=30),
            motivo="Control general"
        ),
        Consulta(
            mascotas[1],
            datetime.now() + timedelta(days=31),
            motivo="Revision dermatologica"
        ),
        Consulta(
            mascotas[2],
            datetime.now() + timedelta(days=32),
            motivo="Control traumatologico"
        ),
    ]
    detalles = [
        DetalleConsulta(
            consultas[0],
            veterinarios[0],
            diagnostico="Paciente saludable",
            tratamiento="Mantener controles",
            observaciones="Sin observaciones"
        ),
        DetalleConsulta(
            consultas[1],
            veterinarios[1],
            diagnostico="Dermatitis leve",
            tratamiento="Aplicar crema topica",
            observaciones="Control en dos semanas"
        ),
        DetalleConsulta(
            consultas[2],
            veterinarios[2],
            diagnostico="Contusion leve",
            tratamiento="Reposo por cinco dias",
            observaciones="No presenta fracturas"
        ),
    ]
    recetas = [
        RecetaMedica(
            2,
            "Administrar cada 8 horas",
            medicamentos[0],
            detalles[0]
        ),
        RecetaMedica(
            1,
            "Administrar cada 12 horas",
            medicamentos[1],
            detalles[1]
        ),
        RecetaMedica(
            1,
            "Administrar una vez al dia",
            medicamentos[2],
            detalles[2]
        ),
    ]

    print("\n[1] Objetos creados en memoria RAM:")
    for indice, especialidad in enumerate(especialidades, start=1):
        print(
            f"    - Especialidad [{indice}]: "
            f"{especialidad.nombre_especialidad}"
        )
    for indice, especie in enumerate(especies, start=1):
        print(f"    - Especie [{indice}]: {especie.nombre_especie}")
    for indice, medicamento in enumerate(medicamentos, start=1):
        print(
            f"    - Medicamento [{indice}]: "
            f"{medicamento.nombre_comercial}"
        )
    for indice, propietario in enumerate(propietarios, start=1):
        print(
            f"    - Propietario [{indice}]: "
            f"{propietario.nombre_completo}"
        )
    for indice, veterinario in enumerate(veterinarios, start=1):
        print(
            f"    - Veterinario [{indice}]: "
            f"{veterinario.nombre_completo}"
        )
    for indice, mascota in enumerate(mascotas, start=1):
        print(f"    - Mascota [{indice}]: {mascota.nombre}")
    for indice, consulta in enumerate(consultas, start=1):
        print(f"    - Consulta [{indice}]: {consulta.motivo}")
    for indice, detalle in enumerate(detalles, start=1):
        print(f"    - Detalle [{indice}]: {detalle.diagnostico}")
    for indice, receta in enumerate(recetas, start=1):
        print(f"    - Receta [{indice}]: {receta.instrucciones}")

    conexion = ConexionDBT()

    dao_especialidad = EspecialidadDAO(conexion)
    dao_especie = EspecieDAO(conexion)
    dao_medicamento = MedicamentoDAO(conexion)
    dao_propietario = PropietarioDAO(conexion)
    dao_veterinario = VeterinarioDAO(conexion)
    dao_mascota = MascotaDAO(conexion)
    dao_consulta = ConsultaDAO(conexion)
    dao_receta = RecetaMedicaDAO(conexion)

    print("\n[2] Objetos DAO inicializados correctamente.")
    print(f"    - Conectados a: {conexion.ruta_db}")

    print("\n[3] Enviando los objetos a la base de datos...")
    try:
        for especialidad in especialidades:
            dao_especialidad.insertar(especialidad)
        for especie in especies:
            dao_especie.insertar(especie)
        for medicamento in medicamentos:
            dao_medicamento.insertar(medicamento)
        for propietario in propietarios:
            dao_propietario.insertar(propietario)
        for veterinario in veterinarios:
            dao_veterinario.insertar(veterinario)
        for mascota in mascotas:
            dao_mascota.insertar(mascota)
        for consulta in consultas:
            dao_consulta.insertar_consulta(consulta)
        for detalle in detalles:
            dao_consulta.insertar_detalle(detalle)
        for receta in recetas:
            dao_receta.insertar(receta)

        for especialidad in especialidades:
            assert especialidad.id_especialidad is not None
        for especie in especies:
            assert especie.id_especie is not None
        for medicamento in medicamentos:
            assert medicamento.id_medicamento is not None
        for propietario in propietarios:
            assert propietario.id_propietario is not None
        for veterinario in veterinarios:
            assert veterinario.id_veterinario is not None
        for mascota in mascotas:
            assert mascota.id_mascota is not None
        for consulta in consultas:
            assert consulta.id_consulta is not None
        for detalle in detalles:
            assert detalle.id_detalle is not None
        for receta in recetas:
            assert receta.id_receta is not None

        assert len(dao_especialidad.listar_todos()) == 3
        assert len(dao_especie.listar_todos()) == 3
        assert len(dao_medicamento.listar_todos()) == 3
        assert len(dao_propietario.listar_todos()) == 3
        assert len(dao_veterinario.listar_todos()) == 3
        assert len(dao_mascota.listar_todos()) == 3
        assert len(dao_consulta.listar_consultas()) == 3
        assert len(dao_consulta.listar_detalles()) == 3
        assert len(dao_receta.listar_todos()) == 3

        print("\n¡EXITO TOTAL!")
        print("Se guardaron 3 objetos por cada entidad.")

    except Exception as error:
        print("\nNo se pudieron insertar todos los registros.")
        print(f"  Mensaje de error: {error}")
        raise

    print("\n" + "=" * 65)


if __name__ == "__main__":
    main()
