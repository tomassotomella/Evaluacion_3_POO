from __future__ import annotations
from typing import TYPE_CHECKING
from models.medicamento import Medicamento
from dao.medicamento_dao import MedicamentoDAO
from utilities.ValidadorEntradas import ValidadorEntradas
from exceptions import exceptions

if TYPE_CHECKING:
    from services.consulta_service import ConsultaService
    from services.economia_service import EconomiaService
    from models.receta_medica import RecetaMedica


class FarmaciaService:
    def __init__(
        self,
        medicamento_dao: MedicamentoDAO,
        consulta_service: ConsultaService,
        economia_service: EconomiaService
    ):
        self.medicamento_dao = medicamento_dao
        self.consulta_service = consulta_service
        self.economia_service = economia_service

    def _enriquecer_medicamento(self, medicamento: Medicamento | None) -> Medicamento | None:
        if medicamento is not None:
            try:
                dolar = self.economia_service.obtener_dolar_actual()
                medicamento.calcular_precio_usd(dolar)
            except exceptions.ServicioExternoException:
                pass
        return medicamento

    def _enriquecer_medicamentos(self, medicamentos: list[Medicamento]) -> list[Medicamento]:
        if medicamentos:
            try:
                dolar = self.economia_service.obtener_dolar_actual()
                for med in medicamentos:
                    med.calcular_precio_usd(dolar)
            except exceptions.ServicioExternoException:
                pass
        return medicamentos

    def registrar_medicamento(
        self,
        nombre_comercial: str,
        precio: int,
        stock: int
    ) -> Medicamento:
        medicamento = Medicamento(
            nombre_comercial=nombre_comercial,
            precio=precio,
            stock=stock
        )
        self.medicamento_dao.insertar(medicamento)
        return self._enriquecer_medicamento(medicamento)

    def obtener_medicamento_por_id(self, id_medicamento: int | str) -> Medicamento:
        id_valido = ValidadorEntradas.validar_id(id_medicamento, "Medicamento")
        return self._enriquecer_medicamento(self.medicamento_dao.obtener_por_id(id_valido))

    def buscar_medicamentos_por_nombre(self, nombre: str) -> list[Medicamento]:
        return self._enriquecer_medicamentos(self.medicamento_dao.buscar_por_nombre(nombre))

    def listar_medicamentos(self) -> list[Medicamento]:
        return self._enriquecer_medicamentos(self.medicamento_dao.listar_todos())

    def eliminar_medicamento(self, id_medicamento: int | str) -> None:
        id_valido = ValidadorEntradas.validar_id(id_medicamento, "Medicamento")
        self.medicamento_dao.eliminar(id_valido)

    # Gestion de Stock
    def reponer_stock(self, id_medicamento: int | str, cantidad: int) -> Medicamento:
        medicamento = self.obtener_medicamento_por_id(id_medicamento)
        medicamento.reponer_stock(cantidad)
        self.medicamento_dao.actualizar(medicamento)
        return medicamento

    def descontar_stock(self, id_medicamento: int | str, cantidad: int) -> Medicamento:
        medicamento = self.obtener_medicamento_por_id(id_medicamento)
        medicamento.descontar_stock(cantidad)
        self.medicamento_dao.actualizar(medicamento)
        return medicamento

    def listar_stock_critico(self) -> list[Medicamento]:
        return self._enriquecer_medicamentos(self.medicamento_dao.listar_stock_critico())

    #Gestion de venta

    def obtener_receta_para_despacho(self, id_receta: int | str) -> RecetaMedica:
        receta = self.consulta_service.obtener_receta_por_id(id_receta)
        self._enriquecer_medicamento(receta.medicamento)
        return receta

    def listar_recetas_para_despacho(self, id_detalle: int | str) -> list[RecetaMedica]:
        recetas = self.consulta_service.listar_recetas_por_detalle(id_detalle)
        for r in recetas:
            self._enriquecer_medicamento(r.medicamento)
        return recetas

    def despachar_receta(self, id_receta: int | str) -> int:
        receta = self.consulta_service.obtener_receta_por_id(id_receta)
        self.descontar_stock(receta.medicamento.id_medicamento, receta.cantidad)
        monto_total = receta.calcular_subtotal()
        return monto_total

    def despachar_recetas_seleccionadas(self, ids_recetas: list[int | str]) -> int:
        if not ids_recetas:
            raise exceptions.ReglaNegocioError("Debe proporcionar al menos un ID de receta para despachar.")

        recetas_a_despachar: list[RecetaMedica] = []
        for id_receta in ids_recetas:
            receta = self.consulta_service.obtener_receta_por_id(id_receta)
            recetas_a_despachar.append(receta)

        # Acumula el stock requerido por medicamento para validar recetas
        # duplicadas del mismo medicamento como una sola solicitud.
        stock_requerido: dict[int, int] = {}
        medicamentos_involucrados: dict[int, Medicamento] = {}
        for receta in recetas_a_despachar:
            medicamento = receta.medicamento
            if medicamento.id_medicamento is None:
                raise exceptions.ReglaNegocioError("La receta debe incluir un medicamento con ID.")
            id_medicamento = medicamento.id_medicamento
            stock_requerido[id_medicamento] = stock_requerido.get(id_medicamento, 0) + receta.cantidad
            medicamentos_involucrados.setdefault(id_medicamento, medicamento)

        monto_total = sum(receta.calcular_subtotal() for receta in recetas_a_despachar)

        # Bloque transaccional atómico: valida y descuenta todo el stock en una
        # sola transacción; ConexionDB ejecuta rollback() ante cualquier error.
        stock_final: dict[int, int] = {}
        with self.medicamento_dao.conexion_db.obtener_conexion() as conn:
            try:
                cursor = conn.cursor()
                for id_medicamento, cantidad_total in stock_requerido.items():
                    fila = cursor.execute(
                        "SELECT nombre_comercial, stock FROM MEDICAMENTO WHERE id_medicamento = ?;",
                        (id_medicamento,)
                    ).fetchone()
                    if fila is None:
                        raise exceptions.EntidadNoEncontradaException("Medicamento", id_medicamento)
                    nombre_comercial, stock_disponible = fila
                    if stock_disponible < cantidad_total:
                        raise exceptions.SinStockException(
                            nombre_comercial,
                            cantidad_total,
                            stock_disponible
                        )
                    cursor.execute(
                        "UPDATE MEDICAMENTO SET stock = stock - ? WHERE id_medicamento = ?;",
                        (cantidad_total, id_medicamento)
                    )
                    stock_final[id_medicamento] = stock_disponible - cantidad_total
            except Exception:
                conn.rollback()
                raise

        # Sincroniza los objetos en memoria con el stock ya descontado en la BD.
        for id_medicamento, medicamento in medicamentos_involucrados.items():
            medicamento.stock = stock_final[id_medicamento]

        return monto_total

    def despachar_todas_recetas_de_detalle(self, id_detalle: int | str) -> int:
        recetas = self.consulta_service.listar_recetas_por_detalle(id_detalle)

        if not recetas:
            raise exceptions.ReglaNegocioError('No puede despachar un detalle si no tiene recetas asociadas') 
        ids = []
        for receta in recetas:
            if receta.id_receta is not None:
                ids.append(receta.id_receta) 
        return self.despachar_recetas_seleccionadas(ids)