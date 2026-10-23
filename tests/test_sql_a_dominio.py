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
from exceptions import exceptions
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
    conexion = ConexionDBT()
    dao_especialidad = EspecialidadDAO(conexion)
    dao_especie = EspecieDAO(conexion)
    dao_medicamento = MedicamentoDAO(conexion)
    dao_propietario = PropietarioDAO(conexion)
    dao_veterinario = VeterinarioDAO(conexion)
    dao_mascota = MascotaDAO(conexion)
    dao_consulta = ConsultaDAO(conexion)
    dao_receta = RecetaMedicaDAO(conexion)

    print("=== INICIO DE PRUEBAS DE SQL A DOMINIO ===")
    print("Los objetos se leeran desde la base existente.")

    try:
        especialidades = dao_especialidad.listar_todos()
        assert len(especialidades) >= 3, (
            "La base debe contener al menos 3 especialidades."
        )

        print("\n[1] Especialidades recuperadas:")
        for especialidad in especialidades[:3]:
            assert isinstance(especialidad, Especialidad)
            assert especialidad.id_especialidad is not None
            print(f"Tipo de objeto: {type(especialidad)}")
            print(
                f"Especialidad: {especialidad.nombre_especialidad} | "
                f"Descripcion: {especialidad.descripcion}"
            )

        especies = dao_especie.listar_todos()
        assert len(especies) >= 3, (
            "La base debe contener al menos 3 especies."
        )

        print("\n[2] Especies recuperadas:")
        for especie in especies[:3]:
            assert isinstance(especie, Especie)
            assert especie.id_especie is not None
            print(f"Tipo de objeto: {type(especie)}")
            print(
                f"Especie: {especie.nombre_especie} | "
                f"Esperanza de vida: {especie.esperanza_vida_max}"
            )

        medicamentos = dao_medicamento.listar_todos()
        assert len(medicamentos) >= 3, (
            "La base debe contener al menos 3 medicamentos."
        )

        print("\n[3] Medicamentos recuperados:")
        for medicamento in medicamentos[:3]:
            assert isinstance(medicamento, Medicamento)
            assert medicamento.id_medicamento is not None
            print(f"Tipo de objeto: {type(medicamento)}")
            print(
                f"Medicamento: {medicamento.nombre_comercial} | "
                f"Precio: ${medicamento.precio} | "
                f"Stock: {medicamento.stock}"
            )

        propietarios = dao_propietario.listar_todos()
        assert len(propietarios) >= 3, (
            "La base debe contener al menos 3 propietarios."
        )

        print("\n[4] Propietarios recuperados:")
        for propietario in propietarios[:3]:
            assert isinstance(propietario, Propietario)
            assert propietario.id_propietario is not None
            print(f"Tipo de objeto: {type(propietario)}")
            print(
                f"Propietario: {propietario.nombre_completo} | "
                f"RUT: {propietario.rut} | "
                f"Telefono: {propietario.telefono}"
            )

        veterinarios = dao_veterinario.listar_todos()
        assert len(veterinarios) >= 3, (
            "La base debe contener al menos 3 veterinarios."
        )

        print("\n[5] Veterinarios recuperados:")
        for veterinario in veterinarios[:3]:
            assert isinstance(veterinario, Veterinario)
            assert veterinario.id_veterinario is not None
            assert isinstance(veterinario.especialidad, Especialidad)
            print(f"Tipo de objeto: {type(veterinario)}")
            print(
                f"Veterinario: {veterinario.nombre_completo} | "
                f"RUT: {veterinario.rut} | "
                f"Especialidad: "
                f"{veterinario.especialidad.nombre_especialidad}"
            )

        mascotas = dao_mascota.listar_todos()
        assert len(mascotas) >= 3, (
            "La base debe contener al menos 3 mascotas."
        )

        print("\n[6] Mascotas recuperadas:")
        for mascota in mascotas[:3]:
            assert isinstance(mascota, Mascota)
            assert mascota.id_mascota is not None
            assert isinstance(mascota.especie, Especie)
            assert isinstance(mascota.propietario, Propietario)
            print(f"Tipo de objeto: {type(mascota)}")
            print(
                f"Mascota: {mascota.nombre} | "
                f"Especie: {mascota.especie.nombre_especie} | "
                f"Propietario: {mascota.propietario.nombre_completo}"
            )

        consultas = dao_consulta.listar_consultas()
        assert len(consultas) >= 3, (
            "La base debe contener al menos 3 consultas."
        )

        print("\n[7] Consultas recuperadas:")
        for consulta in consultas[:3]:
            assert isinstance(consulta, Consulta)
            assert consulta.id_consulta is not None
            assert isinstance(consulta.mascota, Mascota)
            assert consulta.detalle is not None
            assert isinstance(consulta.detalle, DetalleConsulta)
            print(f"Tipo de objeto: {type(consulta)}")
            print(
                f"Consulta: {consulta.motivo} | "
                f"Estado: {consulta.estado.value} | "
                f"Mascota: {consulta.mascota.nombre}"
            )

        detalles = dao_consulta.listar_detalles()
        assert len(detalles) >= 3, (
            "La base debe contener al menos 3 detalles de consulta."
        )

        print("\n[8] Detalles de consulta recuperados:")
        for detalle in detalles[:3]:
            assert isinstance(detalle, DetalleConsulta)
            assert detalle.id_detalle is not None
            assert isinstance(detalle.consulta, Consulta)
            assert isinstance(detalle.veterinario, Veterinario)
            print(f"Tipo de objeto: {type(detalle)}")
            print(
                f"Detalle medico: {detalle.diagnostico} | "
                f"Veterinario: {detalle.veterinario.nombre_completo}"
            )

        recetas = dao_receta.listar_todos()
        assert len(recetas) >= 3, (
            "La base debe contener al menos 3 recetas medicas."
        )

        print("\n[9] Recetas medicas recuperadas:")
        for receta in recetas[:3]:
            assert isinstance(receta, RecetaMedica)
            assert receta.id_receta is not None
            assert isinstance(receta.medicamento, Medicamento)
            assert isinstance(receta.detalle, DetalleConsulta)
            print(f"Tipo de objeto: {type(receta)}")
            print(
                f"Receta: {receta.instrucciones} | "
                f"Medicamento: {receta.medicamento.nombre_comercial}"
            )

    except Exception as error:
        print(f"[ERROR DE HIDRATACION]: {error}")
        raise

    try:
        dao_medicamento.obtener_por_id(99999)
        assert False, "Fallo: Se retorno un medicamento inexistente sin lanzar excepcion."
    except exceptions.EntidadNoEncontradaException as error:
        print(f"\nResultado ID inexistente (debe lanzar excepcion): {error}")

    print("\n==================================================")
    print("3 OBJETOS POR ENTIDAD FUERON HIDRATADOS CORRECTAMENTE")
    print("==================================================")


if __name__ == "__main__":
    main()
