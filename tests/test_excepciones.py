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


def ejecutar_suite_pruebas():
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
    print("SUITE DE EXCEPCIONES — TODAS LAS ENTIDADES")
    print("=" * 65)

    print("\n[TEST 1] Verificando invariantes de los modelos...")
    try:
        Especialidad("", "Descripcion")
        assert False, "Fallo: Se acepto una especialidad sin nombre."
    except exceptions.EntradaInvalidaException as error:
        assert isinstance(error, exceptions.VetCareException)
        print(f" -> Especialidad protegida correctamente: {error}")

    try:
        Especie(201, "Gato")
        assert False, "Fallo: Se acepto una esperanza de vida superior a 200."
    except exceptions.ReglaNegocioError as error:
        assert isinstance(error, exceptions.VetCareException)
        print(f" -> Especie protegida correctamente: {error}")

    try:
        Medicamento("Medicamento invalido", 0, 10)
        assert False, "Fallo: Se acepto un precio igual a cero."
    except exceptions.EntradaInvalidaException as error:
        assert isinstance(error, exceptions.VetCareException)
        print(f" -> Medicamento protegido correctamente: {error}")

    try:
        Propietario("123", "Nombre Valido", "+56912345678")
        assert False, "Fallo: Se acepto un RUT invalido."
    except exceptions.RutInvalidoException as error:
        assert isinstance(error, exceptions.VetCareException)
        print(f" -> Propietario protegido correctamente: {error}")

    try:
        Veterinario(
            "123",
            "Nombre Valido",
            "+56912345678",
            especialidad
        )
        assert False, "Fallo: Se acepto un RUT de veterinario invalido."
    except exceptions.RutInvalidoException as error:
        assert isinstance(error, exceptions.VetCareException)
        print(f" -> Veterinario protegido correctamente: {error}")

    try:
        Mascota(
            "Mascota futura",
            date.today() + timedelta(days=1),
            especie,
            propietario
        )
        assert False, "Fallo: Se acepto una fecha de nacimiento futura."
    except exceptions.ReglaNegocioError as error:
        assert isinstance(error, exceptions.VetCareException)
        print(f" -> Mascota protegida correctamente: {error}")

    try:
        Consulta(
            mascota,
            datetime.now() - timedelta(days=1)
        )
        assert False, "Fallo: Se acepto una consulta en el pasado."
    except exceptions.ReglaNegocioError as error:
        assert isinstance(error, exceptions.VetCareException)
        print(f" -> Consulta protegida correctamente: {error}")

    try:
        DetalleConsulta(
            consulta,
            veterinario,
            diagnostico="x" * 101
        )
        assert False, "Fallo: Se acepto un diagnostico demasiado largo."
    except exceptions.EntradaInvalidaException as error:
        assert isinstance(error, exceptions.VetCareException)
        print(f" -> Detalle de consulta protegido correctamente: {error}")

    try:
        RecetaMedica(0, "Instrucciones", medicamento, detalle)
        assert False, "Fallo: Se acepto una receta con cantidad cero."
    except exceptions.EntradaInvalidaException as error:
        assert isinstance(error, exceptions.VetCareException)
        print(f" -> Receta medica protegida correctamente: {error}")

    print("\n[TEST 2] Verificando entidades duplicadas...")
    try:
        dao_especialidad.insertar(
            Especialidad("Cardiologia", "Especialidad duplicada")
        )
        assert False, "Fallo: Se acepto una especialidad duplicada."
    except exceptions.EntidadExistenteException as error:
        print(f" -> Especialidad duplicada rechazada: {error}")

    try:
        dao_especie.insertar(Especie(12, "Perro"))
        assert False, "Fallo: Se acepto una especie duplicada."
    except exceptions.EntidadExistenteException as error:
        print(f" -> Especie duplicada rechazada: {error}")

    try:
        dao_medicamento.insertar(
            Medicamento("Amoxicilina 250mg", 5500, 10)
        )
        assert False, "Fallo: Se acepto un medicamento duplicado."
    except exceptions.EntidadExistenteException as error:
        print(f" -> Medicamento duplicado rechazado: {error}")

    try:
        dao_propietario.insertar(
            Propietario("12345678-5", "Otro Nombre", "+56911111111")
        )
        assert False, "Fallo: Se acepto un propietario duplicado."
    except exceptions.EntidadExistenteException as error:
        print(f" -> Propietario duplicado rechazado: {error}")

    try:
        dao_veterinario.insertar(
            Veterinario(
                "98765432-1",
                "Otro Veterinario",
                "+56911111111",
                especialidad
            )
        )
        assert False, "Fallo: Se acepto un veterinario duplicado."
    except exceptions.EntidadExistenteException as error:
        print(f" -> Veterinario duplicado rechazado: {error}")

    print("\n[TEST 3] Verificando restricciones de integridad referencial...")
    try:
        dao_especialidad.eliminar(especialidad.id_especialidad)
        assert False, "Fallo: Se elimino una especialidad referenciada."
    except exceptions.ReferenciaIntegridadError as error:
        print(f" -> Especialidad protegida: {error}")

    try:
        dao_especie.eliminar(especie.id_especie)
        assert False, "Fallo: Se elimino una especie referenciada."
    except exceptions.ReferenciaIntegridadError as error:
        print(f" -> Especie protegida: {error}")

    try:
        dao_medicamento.eliminar(medicamento.id_medicamento)
        assert False, "Fallo: Se elimino un medicamento referenciado."
    except exceptions.ReferenciaIntegridadError as error:
        print(f" -> Medicamento protegido: {error}")

    try:
        dao_propietario.eliminar(propietario.id_propietario)
        assert False, "Fallo: Se elimino un propietario referenciado."
    except exceptions.ReferenciaIntegridadError as error:
        print(f" -> Propietario protegido: {error}")

    try:
        dao_veterinario.eliminar(veterinario.id_veterinario)
        assert False, "Fallo: Se elimino un veterinario referenciado."
    except exceptions.ReferenciaIntegridadError as error:
        print(f" -> Veterinario protegido: {error}")

    try:
        dao_mascota.eliminar(mascota.id_mascota)
        assert False, "Fallo: Se elimino una mascota referenciada."
    except exceptions.ReferenciaIntegridadError as error:
        print(f" -> Mascota protegida: {error}")

    try:
        dao_consulta.eliminar_consulta(consulta.id_consulta)
        assert False, "Fallo: Se elimino una consulta referenciada."
    except exceptions.ReferenciaIntegridadError as error:
        print(f" -> Consulta protegida: {error}")

    try:
        dao_consulta.eliminar_detalle(detalle.id_detalle)
        assert False, "Fallo: Se elimino un detalle referenciado."
    except exceptions.ReferenciaIntegridadError as error:
        print(f" -> Detalle de consulta protegido: {error}")

    try:
        dao_receta.eliminar(99999)
        assert False, "Fallo: No se rechazo una receta inexistente."
    except exceptions.EntidadNoEncontradaException as error:
        print(f" -> Receta inexistente rechazada: {error}")

    print("\n" + "=" * 65)
    print("[EXITO] TODAS LAS PRUEBAS DE EXCEPCIONES PASARON CON EXITO")
    print("=" * 65)


if __name__ == "__main__":
    ejecutar_suite_pruebas()
