"""
Rutas FastAPI para Facturación Digital.
Endpoints para gestión completa de facturación e integración contable.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
from app.db import get_db
from app.schemas.facturacion import (
    ClienteCreate, ClienteUpdate, ClienteRead,
    ProductoCreate, ProductoUpdate, ProductoRead,
    FacturaCreate, FacturaRead, DetalleFacturaCreate
)
from app.services.facturacion_service import (
    crear_cliente, crear_producto, crear_factura_completa, obtener_facturas_cliente,
    obtener_reporte_ventas_periodo, anular_factura, obtener_cuentas_por_cobrar
)
from app.models.facturacion import Cliente, Producto, Factura

router = APIRouter(
    prefix="/api/facturacion",
    tags=["Facturación"]
)

# Rutas para Clientes
@router.post("/clientes", response_model=ClienteRead)
def crear_nuevo_cliente(
    cliente: ClienteCreate,
    db: Session = Depends(get_db)
):
    """Crear un nuevo cliente"""
    return crear_cliente(db, cliente, "API_USER")

@router.get("/clientes", response_model=List[ClienteRead])
def listar_clientes(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    estado: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Listar clientes con paginación"""
    query = db.query(Cliente)
    if estado:
        query = query.filter(Cliente.estado_cliente == estado)
    return query.offset(skip).limit(limit).all()

@router.get("/clientes/{cliente_id}", response_model=ClienteRead)
def obtener_cliente(
    cliente_id: int,
    db: Session = Depends(get_db)
):
    """Obtener cliente específico por ID"""
    cliente = db.query(Cliente).filter(Cliente.id_cliente == cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return cliente

# Rutas para Productos
@router.post("/productos", response_model=ProductoRead)
def crear_nuevo_producto(
    producto: ProductoCreate,
    db: Session = Depends(get_db)
):
    """Crear un nuevo producto/servicio"""
    return crear_producto(db, producto, "API_USER")

@router.get("/productos", response_model=List[ProductoRead])
def listar_productos(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    tipo: Optional[str] = Query(None),
    estado: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Listar productos con paginación"""
    query = db.query(Producto)
    if tipo:
        query = query.filter(Producto.tipo_producto == tipo)
    if estado:
        query = query.filter(Producto.estado_producto == estado)
    return query.offset(skip).limit(limit).all()

# Rutas para Facturas
@router.post("/facturas", response_model=FacturaRead)
def crear_nueva_factura(
    factura: FacturaCreate,
    detalles: List[DetalleFacturaCreate],
    generar_contabilidad: bool = Query(True),
    db: Session = Depends(get_db)
):
    """Crear nueva factura con detalles"""
    return crear_factura_completa(db, factura, detalles, "API_USER", generar_contabilidad)

@router.get("/facturas/cliente/{cliente_id}", response_model=List[FacturaRead])
def obtener_facturas_por_cliente(
    cliente_id: int,
    estado: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Obtener facturas de un cliente específico"""
    return obtener_facturas_cliente(db, cliente_id, estado, limit, offset)

@router.get("/facturas/{factura_id}", response_model=FacturaRead)
def obtener_factura(
    factura_id: int,
    db: Session = Depends(get_db)
):
    """Obtener factura específica por ID"""
    factura = db.query(Factura).filter(Factura.id_factura == factura_id).first()
    if not factura:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    return factura

@router.post("/facturas/{factura_id}/anular")
def anular_factura_endpoint(
    factura_id: int,
    motivo: str,
    db: Session = Depends(get_db)
):
    """Anular una factura"""
    factura_anulada = anular_factura(db, factura_id, motivo, "API_USER")
    return {
        "message": "Factura anulada exitosamente",
        "factura_id": factura_anulada.id_factura,
        "nuevo_estado": factura_anulada.estado_factura
    }

# Rutas para Reportes
@router.get("/reportes/ventas")
def reporte_ventas(
    fecha_inicio: date,
    fecha_fin: date,
    cliente_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """Generar reporte de ventas por período"""
    return obtener_reporte_ventas_periodo(db, fecha_inicio, fecha_fin, cliente_id)

@router.get("/reportes/cuentas-por-cobrar")
def reporte_cuentas_por_cobrar(
    fecha_corte: Optional[date] = Query(None),
    db: Session = Depends(get_db)
):
    """Obtener reporte de cuentas por cobrar"""
    return obtener_cuentas_por_cobrar(db, fecha_corte)