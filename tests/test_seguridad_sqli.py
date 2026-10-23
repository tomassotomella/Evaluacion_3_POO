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


def verificar_seguridad_todas_las_entidades():
    conexion = ConexionDBT()
    dao_especialidad = EspecialidadDAO(conexion)
    dao_especie = EspecieDAO(conexion)
    dao_medicamento = MedicamentoDAO(conexion)
    dao_propietario = PropietarioDAO(conexion)
    dao_veterinario = VeterinarioDAO(conexion)
    dao_mascota = MascotaDAO(conexion)
    dao_consulta = ConsultaDAO(conexion)
    dao_receta = RecetaMedicaDAO(conexion)

    especialidad = Especialidad(
        "Cardiologia",
        "Atencion del sistema cardiovascular"
    )
    especie = Especie(15, "Perro")
    medicamento = Medicamento("Amoxicilina 250mg", 5500, 100)
    propietario = Propietario(
        "12345678-5",
        "Ana Perez",
        "+56912345678"
    )
    veterinario = Veterinario(
        "98765432-1",
        "Carlos Gonzalez",
        "+56987654321",
        especialidad
    )
    mascota = Mascota(
        "Firulais",
        date.today() - timedelta(days=365 * 3),
        especie,
        propietario
    )
    consulta = Consulta(
        mascota,
        datetime.now() + timedelta(days=30),
        motivo="Control general"
    )
    detalle = DetalleConsulta(
        consulta,
        veterinario,
        diagnostico="Paciente saludable",
        tratamiento="Mantener controles",
        observaciones="Sin observaciones"
    )
    receta = RecetaMedica(
        2,
        "Administrar cada 8 horas",
        medicamento,
        detalle
    )

    dao_especialidad.insertar(especialidad)
    dao_especie.insertar(especie)
    dao_medicamento.insertar(medicamento)
    dao_propietario.insertar(propietario)
    dao_veterinario.insertar(veterinario)
    dao_mascota.insertar(mascota)
    dao_consulta.insertar_consulta(consulta)
    dao_consulta.insertar_detalle(detalle)
    dao_receta.insertar(receta)

    print("=" * 65)
    print("AUDITORIA DE SEGURIDAD CONTRA SQL INJECTION (OWASP A03)")
    print("OBJETIVO DE PRUEBA: TODOS LOS DAO DEL SISTEMA")
    print("=" * 65)

    payload_bypass = "' OR '1'='1"

    print("\n[AUDITORIA 1] Probando EspecialidadDAO...")
    resultados_bypass = dao_especialidad.buscar_por_nombre(payload_bypass)
    assert resultados_bypass == [], (
        "VULNERABILIDAD: EspecialidadDAO altero la logica SQL."
    )
    resultados_legitimos = dao_especialidad.buscar_por_nombre("Cardio")
    assert len(resultados_legitimos) == 1
    print(" -> APROBADO: EspecialidadDAO usa busqueda parametrizada.")

    print("\n[AUDITORIA 2] Probando EspecieDAO...")
    resultados_bypass = dao_especie.buscar_por_nombre(payload_bypass)
    assert resultados_bypass == [], (
        "VULNERABILIDAD: EspecieDAO altero la logica SQL."
    )
    resultados_legitimos = dao_especie.buscar_por_nombre("Per")
    assert len(resultados_legitimos) == 1
    print(" -> APROBADO: EspecieDAO usa busqueda parametrizada.")

    print("\n[AUDITORIA 3] Probando MedicamentoDAO...")
    resultados_bypass = dao_medicamento.buscar_por_nombre(payload_bypass)
    assert resultados_bypass == [], (
        "VULNERABILIDAD: MedicamentoDAO altero la logica SQL."
    )
    resultados_legitimos = dao_medicamento.buscar_por_nombre("Amoxi")
    assert len(resultados_legitimos) == 1
    print(" -> APROBADO: MedicamentoDAO usa busqueda parametrizada.")

    print("\n[AUDITORIA 4] Probando PropietarioDAO...")
    resultados_bypass = dao_propietario.buscar_por_nombre(payload_bypass)
    assert resultados_bypass == [], (
        "VULNERABILIDAD: PropietarioDAO altero la logica SQL."
    )
    resultados_legitimos = dao_propietario.buscar_por_nombre("Ana")
    assert len(resultados_legitimos) == 1
    print(" -> APROBADO: PropietarioDAO usa busqueda parametrizada.")

    print("\n[AUDITORIA 5] Probando VeterinarioDAO...")
    resultados_bypass = dao_veterinario.buscar_por_nombre(payload_bypass)
    assert resultados_bypass == [], (
        "VULNERABILIDAD: VeterinarioDAO altero la logica SQL."
    )
    resultados_legitimos = dao_veterinario.buscar_por_nombre("Carlos")
    assert len(resultados_legitimos) == 1
    print(" -> APROBADO: VeterinarioDAO usa busqueda parametrizada.")

    print("\n[AUDITORIA 6] Probando MascotaDAO...")
    resultados_bypass = dao_mascota.buscar_por_nombre(payload_bypass)
    assert resultados_bypass == [], (
        "VULNERABILIDAD: MascotaDAO altero la logica SQL."
    )
    resultados_legitimos = dao_mascota.buscar_por_nombre("Firu")
    assert len(resultados_legitimos) == 1
    print(" -> APROBADO: MascotaDAO usa busqueda parametrizada.")

    print("\n[AUDITORIA 7] Probando ConsultaDAO...")
    resultados_bypass = dao_consulta.buscar_consultas_por_nombre_mascota(
        payload_bypass
    )
    assert resultados_bypass == [], (
        "VULNERABILIDAD: ConsultaDAO altero la logica SQL."
    )
    resultados_legitimos = dao_consulta.buscar_consultas_por_nombre_mascota(
        "Firu"
    )
    assert len(resultados_legitimos) == 1
    print(" -> APROBADO: ConsultaDAO usa busqueda parametrizada.")

    print("\n[AUDITORIA 8] Probando RecetaMedicaDAO...")
    resultados_bypass = dao_receta.buscar_por_nombre_medicamento(
        payload_bypass
    )
    assert resultados_bypass == [], (
        "VULNERABILIDAD: RecetaMedicaDAO altero la logica SQL."
    )
    resultados_legitimos = dao_receta.buscar_por_nombre_medicamento("Amoxi")
    assert len(resultados_legitimos) == 1
    print(" -> APROBADO: RecetaMedicaDAO usa busqueda parametrizada.")

    print("\n" + "=" * 65)
    print("TODOS LOS DAO FUERON CERTIFICADOS CONTRA SQL INJECTION")
    print("=" * 65)


if __name__ == "__main__":
    verificar_seguridad_todas_las_entidades()
