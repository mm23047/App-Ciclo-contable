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
    FacturaCreate, FacturaRead, DetalleFacturaCreate, FacturaCompleta,
    ConfiguracionFacturacionCreate, ConfiguracionFacturacionUpdate, ConfiguracionFacturacionRead
)
from app.services.facturacion_service import (
    crear_cliente, crear_producto, crear_factura_completa, obtener_facturas_cliente,
    obtener_reporte_ventas_periodo, anular_factura, obtener_cuentas_por_cobrar,
    obtener_reporte_ventas_por_cliente, obtener_reporte_ventas_por_producto,
    obtener_reporte_tendencias, obtener_configuracion_facturacion,
    crear_configuracion_facturacion, actualizar_configuracion_facturacion
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
@router.post("/facturas", response_model=FacturaRead, status_code=status.HTTP_201_CREATED)
def crear_nueva_factura(
    factura: FacturaCreate,
    db: Session = Depends(get_db)
):
    """Crear nueva factura con detalles"""
    return crear_factura_completa(db, factura, factura.detalles, "API_USER")

@router.get("/facturas", response_model=List[FacturaRead])
def listar_facturas(
    estado: Optional[str] = Query(None),
    fecha_desde: Optional[date] = Query(None),
    fecha_hasta: Optional[date] = Query(None),
    numero_factura: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Listar todas las facturas con filtros opcionales"""
    from app.services.facturacion_service import buscar_facturas
    return buscar_facturas(db, estado, fecha_desde, fecha_hasta, numero_factura, limit, offset)

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

@router.get("/facturas/{factura_id}/completa", response_model=FacturaCompleta)
def obtener_factura_completa(
    factura_id: int,
    db: Session = Depends(get_db)
):
    """Obtener factura con datos completos del cliente y productos"""
    from app.models.facturacion import DetalleFactura
    
    factura = db.query(Factura).filter(Factura.id_factura == factura_id).first()
    if not factura:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    
    # Obtener cliente
    cliente = db.query(Cliente).filter(Cliente.id_cliente == factura.id_cliente).first()
    
    # Obtener detalles con información de productos
    detalles_completos = []
    for detalle in factura.detalles:
        detalle_dict = {
            "id_detalle": detalle.id_detalle,
            "id_factura": detalle.id_factura,
            "numero_linea": detalle.numero_linea,
            "id_producto": detalle.id_producto,
            "descripcion_personalizada": detalle.descripcion_personalizada,
            "cantidad": detalle.cantidad,
            "precio_unitario": detalle.precio_unitario,
            "descuento_linea": detalle.descuento_linea,
            "subtotal_linea": detalle.subtotal_linea,
            "impuesto_linea": detalle.impuesto_linea,
            "total_linea": detalle.total_linea,
            "nombre_producto": None,
            "codigo_producto": None
        }
        
        # Agregar datos del producto si existe
        if detalle.id_producto:
            producto = db.query(Producto).filter(Producto.id_producto == detalle.id_producto).first()
            if producto:
                detalle_dict["nombre_producto"] = producto.nombre
                detalle_dict["codigo_producto"] = producto.codigo_producto
        
        detalles_completos.append(detalle_dict)
    
    # Construir respuesta completa
    factura_completa = {
        "id_factura": factura.id_factura,
        "numero_factura": factura.numero_factura,
        "serie_factura": factura.serie_factura,
        "fecha_emision": factura.fecha_emision,
        "fecha_vencimiento": factura.fecha_vencimiento,
        "id_cliente": factura.id_cliente,
        "metodo_pago": factura.metodo_pago,
        "condiciones_pago": factura.condiciones_pago,
        "observaciones": factura.observaciones,
        "usuario_creacion": factura.usuario_creacion,
        "subtotal": factura.subtotal,
        "descuento_general": factura.descuento_general,
        "subtotal_descuento": factura.subtotal_descuento,
        "impuesto_iva": factura.impuesto_iva,
        "otros_impuestos": factura.otros_impuestos,
        "retencion_fuente": factura.retencion_fuente,
        "reteica": factura.reteica,
        "total": factura.total,
        "estado": factura.estado_factura,
        "fecha_creacion": factura.fecha_creacion,
        "cliente": cliente,
        "detalles": detalles_completos
    }
    
    return factura_completa

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
    fecha_desde: date = Query(..., description="Fecha de inicio del período"),
    fecha_hasta: date = Query(..., description="Fecha de fin del período"),
    cliente_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """Generar reporte de ventas por período"""
    return obtener_reporte_ventas_periodo(db, fecha_desde, fecha_hasta, cliente_id)

@router.get("/reportes/cuentas-por-cobrar")
def reporte_cuentas_por_cobrar(
    fecha_corte: Optional[date] = Query(None),
    db: Session = Depends(get_db)
):
    """Obtener reporte de cuentas por cobrar"""
    return obtener_cuentas_por_cobrar(db, fecha_corte)

@router.get("/reportes/ventas-cliente")
def reporte_ventas_cliente(
    fecha_desde: date = Query(..., description="Fecha de inicio del período"),
    fecha_hasta: date = Query(..., description="Fecha de fin del período"),
    db: Session = Depends(get_db)
):
    """Generar reporte de ventas agrupado por cliente"""
    return obtener_reporte_ventas_por_cliente(db, fecha_desde, fecha_hasta)

@router.get("/reportes/ventas-producto")
def reporte_ventas_producto(
    fecha_desde: date = Query(..., description="Fecha de inicio del período"),
    fecha_hasta: date = Query(..., description="Fecha de fin del período"),
    db: Session = Depends(get_db)
):
    """Generar reporte de ventas agrupado por producto"""
    return obtener_reporte_ventas_por_producto(db, fecha_desde, fecha_hasta)

@router.get("/reportes/tendencias-ventas")
def reporte_tendencias_ventas(
    fecha_desde: date = Query(..., description="Fecha de inicio del período"),
    fecha_hasta: date = Query(..., description="Fecha de fin del período"),
    db: Session = Depends(get_db)
):
    """Generar reporte de tendencias de ventas"""
    return obtener_reporte_tendencias(db, fecha_desde, fecha_hasta)

# Rutas para Configuración
@router.get("/configuracion", response_model=ConfiguracionFacturacionRead)
def obtener_configuracion(db: Session = Depends(get_db)):
    """Obtener configuración activa de facturación"""
    return obtener_configuracion_facturacion(db)

@router.post("/configuracion", response_model=ConfiguracionFacturacionRead)
def crear_configuracion(
    config: ConfiguracionFacturacionCreate,
    db: Session = Depends(get_db)
):
    """Crear nueva configuración de facturación"""
    return crear_configuracion_facturacion(db, config)

@router.put("/configuracion", response_model=ConfiguracionFacturacionRead)
def actualizar_configuracion(
    config: ConfiguracionFacturacionUpdate,
    db: Session = Depends(get_db)
):
    """Actualizar configuración activa de facturación"""
    return actualizar_configuracion_facturacion(db, config)
    """Generar reporte de tendencias de ventas"""
    return obtener_reporte_tendencias(db, fecha_desde, fecha_hasta)