from database import ConexionDBT
from services.economia_service import EconomiaService
from services.farmacia_service import FarmaciaService
from dao.divisa_dao import DivisaDAO
from dao.medicamento_dao import MedicamentoDAO
from models.divisa import Divisa
from screens.farmacia_screen import mostrar_detalle_medicamento
import time

def certificar_flujo_completo():
    print("=" * 65)
    print("TEST DE INTEGRACIÓN: API EXTERNA -> OBJETO POO -> SQLITE LOCAL")
    print("=" * 65)

    # 1. Consumo y Deserialización desde la red
    print("\n[PASO 1] Consultando cotización del dólar desde el servicio web...")
    conexion = ConexionDBT()
    dolar_remoto = EconomiaService(DivisaDAO(conexion))._consultar_indicador("usd")
    assert dolar_remoto is not None, "Error: No se pudo obtener el dólar desde la API externa."
    assert isinstance(dolar_remoto, Divisa), "El servicio debió retornar una instancia de Divisa."
    print(f" -> Éxito: Objeto deserializado correctamente: {dolar_remoto.nombre} = ${dolar_remoto.valor} CLP")

    # 2. Persistencia en SQLite local
    print("\n[PASO 2] Guardando objeto Divisa en la base de datos local...")
    dao = DivisaDAO(conexion)
    guardado = dao.actualizar(dolar_remoto)
    assert guardado is True, "Error: No se pudo persistir la divisa en la base de datos."
    print(" -> Éxito: Divisa persistida en la tabla local DIVISA.")

    # 3. Recuperación offline desde el DAO local
    print("\n[PASO 3] Recuperando registro desde SQLite para validar consistencia...")
    dolar_local = dao.obtener_por_codigo("usd")
    assert dolar_local is not None, "Error: La divisa no fue encontrada en la base de datos local."
    assert dolar_local.valor == dolar_remoto.valor, "Los valores recuperados no coinciden."
    print(f" -> Éxito: Registro local verificado: {dolar_local.nombre} = ${dolar_local.valor} CLP")

    # 4. Integración con Farmacia (Enriquecimiento automático en RAM y Detalle)
    print("\n[PASO 4] Registrando y recuperando medicamento con precio en USD...")
    medicamento_dao = MedicamentoDAO(conexion)
    economia_service = EconomiaService(dao)
    farmacia_service = FarmaciaService(medicamento_dao, consulta_service=None, economia_service=economia_service)

    nombre_med = f"Meloxicam Test {int(time.time())}"
    med_creado = farmacia_service.registrar_medicamento(nombre_med, precio=14200, stock=35)
    med_recuperado = farmacia_service.obtener_medicamento_por_id(med_creado.id_medicamento)

    assert med_recuperado.precio_usd is not None, "Error: El medicamento recuperado debió tener precio_usd calculado."
    print(f" -> Éxito: Medicamento hidratado y enriquecido con precio USD: ${med_recuperado.precio_usd:,.2f}")

    print("\nVisualización del detalle de producto generado:")
    mostrar_detalle_medicamento(med_recuperado, farmacia_service)

    print("\n" + "=" * 65)
    print("FLUJO COMPLETO CERTIFICADO CON ÉXITO")
    print("=" * 65)

if __name__ == "__main__":
    certificar_flujo_completo()