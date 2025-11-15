"""
Capa de servicios para Facturación Digital.
Maneja la lógica de negocio para facturación e integración contable automática.
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc
from fastapi import HTTPException, status
from app.models.facturacion import Cliente, Producto, Factura, DetalleFactura
from app.models.catalogo_cuentas import CatalogoCuentas
from app.models.transaccion import Transaccion
from app.models.asiento import Asiento
from app.models.periodo import PeriodoContable
from app.schemas.facturacion import (
    ClienteCreate, ClienteUpdate, ProductoCreate, ProductoUpdate,
    FacturaCreate, FacturaUpdate, DetalleFacturaCreate
)
from app.schemas.transaccion import TransaccionCreate
from app.schemas.asiento import AsientoCreate
from typing import Dict, List, Optional
from decimal import Decimal
from datetime import date, datetime

def crear_cliente(db: Session, cliente_data: ClienteCreate, usuario: str) -> Cliente:
    """Crear un nuevo cliente con validaciones"""
    
    # Verificar que no exista un cliente con el mismo NIT/DUI
    cliente_existente = db.query(Cliente).filter(
        Cliente.nit_dui == cliente_data.nit_dui,
        Cliente.estado_cliente == 'ACTIVO'
    ).first()
    
    if cliente_existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ya existe un cliente activo con NIT/DUI: {cliente_data.nit_dui}"
        )
    
    try:
        db_cliente = Cliente(
            **cliente_data.dict(),
            fecha_registro=date.today(),
            usuario_creacion=usuario,
            estado_cliente='ACTIVO'
        )
        db.add(db_cliente)
        db.commit()
        db.refresh(db_cliente)
        return db_cliente
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error al crear cliente: {str(e)}"
        )

def crear_producto(db: Session, producto_data: ProductoCreate, usuario: str) -> Producto:
    """Crear un nuevo producto/servicio con validaciones"""
    
    # Verificar que no exista un producto con el mismo código
    if producto_data.codigo_producto:
        producto_existente = db.query(Producto).filter(
            Producto.codigo_producto == producto_data.codigo_producto,
            Producto.estado_producto == 'ACTIVO'
        ).first()
        
        if producto_existente:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ya existe un producto activo con código: {producto_data.codigo_producto}"
            )
    
    try:
        db_producto = Producto(
            **producto_data.dict(),
            fecha_creacion=date.today(),
            usuario_creacion=usuario,
            estado_producto='ACTIVO'
        )
        db.add(db_producto)
        db.commit()
        db.refresh(db_producto)
        return db_producto
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error al crear producto: {str(e)}"
        )

def crear_factura_completa(
    db: Session, 
    factura_data: FacturaCreate, 
    detalles: List[DetalleFacturaCreate],
    usuario: str,
    generar_contabilidad: bool = True
) -> Factura:
    """
    Crear factura completa con detalles y opcionalmente generar asientos contables
    """
    
    # Validar que el cliente exista
    cliente = db.query(Cliente).filter(
        Cliente.id_cliente == factura_data.id_cliente,
        Cliente.estado_cliente == 'ACTIVO'
    ).first()
    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente no encontrado o inactivo"
        )
    
    # Validar que todos los productos existan
    productos_ids = [detalle.id_producto for detalle in detalles]
    productos = db.query(Producto).filter(
        Producto.id_producto.in_(productos_ids),
        Producto.estado_producto == 'ACTIVO'
    ).all()
    
    if len(productos) != len(productos_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uno o más productos no encontrados o inactivos"
        )
    
    productos_map = {p.id_producto: p for p in productos}
    
    try:
        # Generar número de factura automático
        ultimo_numero = db.query(func.max(Factura.numero_factura)).filter(
            func.extract('year', Factura.fecha_factura) == date.today().year
        ).scalar() or 0
        
        nuevo_numero = ultimo_numero + 1
        
        # Calcular totales
        subtotal = Decimal('0.00')
        total_iva = Decimal('0.00')
        
        # Validar y calcular detalles
        detalles_calculados = []
        for detalle in detalles:
            producto = productos_map[detalle.id_producto]
            
            precio_unitario = detalle.precio_unitario or producto.precio_venta
            cantidad = detalle.cantidad
            
            if cantidad <= 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Cantidad debe ser mayor a 0 para producto {producto.nombre_producto}"
                )
            
            subtotal_linea = precio_unitario * Decimal(str(cantidad))
            
            # Calcular IVA si aplica
            iva_linea = Decimal('0.00')
            if producto.aplica_iva and factura_data.aplica_iva:
                iva_linea = subtotal_linea * Decimal('0.13')  # IVA 13% El Salvador
            
            total_linea = subtotal_linea + iva_linea
            
            detalles_calculados.append({
                'detalle_data': detalle,
                'precio_unitario': precio_unitario,
                'subtotal_linea': subtotal_linea,
                'iva_linea': iva_linea,
                'total_linea': total_linea
            })
            
            subtotal += subtotal_linea
            total_iva += iva_linea
        
        total_factura = subtotal + total_iva
        
        # Crear factura
        db_factura = Factura(
            numero_factura=nuevo_numero,
            id_cliente=factura_data.id_cliente,
            fecha_factura=factura_data.fecha_factura or date.today(),
            fecha_vencimiento=factura_data.fecha_vencimiento,
            subtotal=float(subtotal),
            impuestos=float(total_iva),
            total=float(total_factura),
            estado_factura=factura_data.estado_factura or 'EMITIDA',
            aplica_iva=factura_data.aplica_iva,
            observaciones=factura_data.observaciones,
            metodo_pago=factura_data.metodo_pago,
            usuario_creacion=usuario,
            fecha_creacion=date.today()
        )
        
        db.add(db_factura)
        db.flush()  # Para obtener el ID
        
        # Crear detalles de factura
        for detalle_calc in detalles_calculados:
            db_detalle = DetalleFactura(
                id_factura=db_factura.id_factura,
                id_producto=detalle_calc['detalle_data'].id_producto,
                cantidad=detalle_calc['detalle_data'].cantidad,
                precio_unitario=float(detalle_calc['precio_unitario']),
                subtotal=float(detalle_calc['subtotal_linea']),
                impuestos=float(detalle_calc['iva_linea']),
                total_linea=float(detalle_calc['total_linea']),
                descripcion_personalizada=detalle_calc['detalle_data'].descripcion_personalizada
            )
            db.add(db_detalle)
        
        # Generar contabilidad automática si se solicita
        if generar_contabilidad:
            _generar_asientos_factura(db, db_factura, usuario)
        
        db.commit()
        db.refresh(db_factura)
        return db_factura
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error al crear factura: {str(e)}"
        )

def _generar_asientos_factura(db: Session, factura: Factura, usuario: str):
    """Generar asientos contables automáticos para una factura"""
    
    # Obtener período contable activo
    periodo = db.query(PeriodoContable).filter(
        PeriodoContable.estado_periodo == 'ACTIVO'
    ).first()
    
    if not periodo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No hay período contable activo para generar asientos"
        )
    
    # Obtener cuentas contables configuradas
    cuenta_clientes = db.query(CatalogoCuentas).filter(
        CatalogoCuentas.codigo_cuenta.like('1103%'),  # Cuentas por cobrar clientes
        CatalogoCuentas.estado_cuenta == 'ACTIVA'
    ).first()
    
    cuenta_ventas = db.query(CatalogoCuentas).filter(
        CatalogoCuentas.codigo_cuenta.like('4101%'),  # Ventas
        CatalogoCuentas.estado_cuenta == 'ACTIVA'
    ).first()
    
    cuenta_iva_debito = db.query(CatalogoCuentas).filter(
        CatalogoCuentas.codigo_cuenta.like('2104%'),  # IVA débito fiscal
        CatalogoCuentas.estado_cuenta == 'ACTIVA'
    ).first()
    
    if not cuenta_clientes or not cuenta_ventas:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Faltan configurar cuentas contables para facturación"
        )
    
    # Crear transacción principal
    descripcion_transaccion = f"Factura #{factura.numero_factura} - Cliente: {factura.cliente.nombre_cliente}"
    
    db_transaccion = Transaccion(
        id_periodo=periodo.id_periodo,
        fecha_transaccion=factura.fecha_factura,
        descripcion=descripcion_transaccion,
        referencia_externa=f"FAC-{factura.numero_factura}",
        categoria='VENTAS',
        estado_transaccion='CONFIRMADA',
        usuario_creacion=usuario,
        fecha_creacion=datetime.now()
    )
    
    db.add(db_transaccion)
    db.flush()
    
    # Asiento 1: Cargo a Cuentas por Cobrar (Debe)
    asiento_cliente = Asiento(
        id_transaccion=db_transaccion.id_transaccion,
        id_cuenta=cuenta_clientes.id_cuenta,
        debe=float(factura.total),
        haber=0.00,
        concepto=f"Factura #{factura.numero_factura}",
        referencia_documento=f"FAC-{factura.numero_factura}",
        usuario_creacion=usuario
    )
    db.add(asiento_cliente)
    
    # Asiento 2: Abono a Ventas (Haber)
    asiento_ventas = Asiento(
        id_transaccion=db_transaccion.id_transaccion,
        id_cuenta=cuenta_ventas.id_cuenta,
        debe=0.00,
        haber=float(factura.subtotal),
        concepto=f"Venta según factura #{factura.numero_factura}",
        referencia_documento=f"FAC-{factura.numero_factura}",
        usuario_creacion=usuario
    )
    db.add(asiento_ventas)
    
    # Asiento 3: Abono a IVA Débito Fiscal si aplica
    if factura.aplica_iva and factura.impuestos > 0 and cuenta_iva_debito:
        asiento_iva = Asiento(
            id_transaccion=db_transaccion.id_transaccion,
            id_cuenta=cuenta_iva_debito.id_cuenta,
            debe=0.00,
            haber=float(factura.impuestos),
            concepto=f"IVA débito fiscal factura #{factura.numero_factura}",
            referencia_documento=f"FAC-{factura.numero_factura}",
            usuario_creacion=usuario
        )
        db.add(asiento_iva)

def obtener_facturas_cliente(
    db: Session, 
    cliente_id: int, 
    estado: str = None,
    limit: int = 50, 
    offset: int = 0
) -> List[Factura]:
    """Obtener facturas de un cliente específico"""
    
    query = db.query(Factura).filter(Factura.id_cliente == cliente_id)
    
    if estado:
        query = query.filter(Factura.estado_factura == estado)
    
    return query.order_by(desc(Factura.fecha_factura)).limit(limit).offset(offset).all()

def obtener_reporte_ventas_periodo(
    db: Session,
    fecha_inicio: date,
    fecha_fin: date,
    cliente_id: int = None
) -> Dict:
    """Generar reporte de ventas por período"""
    
    query = db.query(Factura).filter(
        Factura.fecha_factura >= fecha_inicio,
        Factura.fecha_factura <= fecha_fin,
        Factura.estado_factura.in_(['EMITIDA', 'PAGADA'])
    )
    
    if cliente_id:
        query = query.filter(Factura.id_cliente == cliente_id)
    
    facturas = query.all()
    
    # Calcular totales
    total_ventas = sum(f.total for f in facturas)
    total_subtotal = sum(f.subtotal for f in facturas)
    total_impuestos = sum(f.impuestos or 0 for f in facturas)
    cantidad_facturas = len(facturas)
    
    # Agrupar por cliente
    ventas_por_cliente = {}
    for factura in facturas:
        cliente_key = f"{factura.cliente.nit_dui} - {factura.cliente.nombre_cliente}"
        if cliente_key not in ventas_por_cliente:
            ventas_por_cliente[cliente_key] = {
                'cantidad_facturas': 0,
                'total_ventas': 0,
                'subtotal': 0,
                'impuestos': 0
            }
        
        ventas_por_cliente[cliente_key]['cantidad_facturas'] += 1
        ventas_por_cliente[cliente_key]['total_ventas'] += factura.total
        ventas_por_cliente[cliente_key]['subtotal'] += factura.subtotal
        ventas_por_cliente[cliente_key]['impuestos'] += factura.impuestos or 0
    
    # Productos más vendidos
    query_productos = db.query(
        Producto.nombre_producto,
        func.sum(DetalleFactura.cantidad).label('cantidad_vendida'),
        func.sum(DetalleFactura.total_linea).label('total_vendido')
    ).join(
        DetalleFactura, Producto.id_producto == DetalleFactura.id_producto
    ).join(
        Factura, DetalleFactura.id_factura == Factura.id_factura
    ).filter(
        Factura.fecha_factura >= fecha_inicio,
        Factura.fecha_factura <= fecha_fin,
        Factura.estado_factura.in_(['EMITIDA', 'PAGADA'])
    ).group_by(
        Producto.id_producto, Producto.nombre_producto
    ).order_by(
        desc(func.sum(DetalleFactura.cantidad))
    ).limit(10).all()
    
    productos_top = [
        {
            'producto': p.nombre_producto,
            'cantidad_vendida': float(p.cantidad_vendida),
            'total_vendido': float(p.total_vendido)
        }
        for p in query_productos
    ]
    
    return {
        'periodo': {
            'fecha_inicio': fecha_inicio,
            'fecha_fin': fecha_fin
        },
        'resumen': {
            'cantidad_facturas': cantidad_facturas,
            'total_ventas': float(total_ventas),
            'subtotal': float(total_subtotal),
            'impuestos': float(total_impuestos),
            'promedio_por_factura': float(total_ventas / cantidad_facturas) if cantidad_facturas > 0 else 0
        },
        'ventas_por_cliente': ventas_por_cliente,
        'productos_mas_vendidos': productos_top
    }

def anular_factura(db: Session, factura_id: int, motivo: str, usuario: str) -> Factura:
    """Anular una factura y sus asientos contables"""
    
    factura = db.query(Factura).filter(Factura.id_factura == factura_id).first()
    if not factura:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Factura no encontrada"
        )
    
    if factura.estado_factura == 'ANULADA':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La factura ya está anulada"
        )
    
    try:
        # Cambiar estado de factura
        factura.estado_factura = 'ANULADA'
        factura.observaciones = f"{factura.observaciones or ''}\nANULADA: {motivo}".strip()
        factura.fecha_modificacion = date.today()
        factura.usuario_modificacion = usuario
        
        # Buscar y anular asientos relacionados
        transacciones = db.query(Transaccion).filter(
            Transaccion.referencia_externa == f"FAC-{factura.numero_factura}"
        ).all()
        
        for transaccion in transacciones:
            transaccion.estado_transaccion = 'ANULADA'
            transaccion.observaciones = f"Anulada por anulación de factura #{factura.numero_factura}: {motivo}"
            transaccion.fecha_modificacion = datetime.now()
            transaccion.usuario_modificacion = usuario
        
        db.commit()
        db.refresh(factura)
        return factura
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error al anular factura: {str(e)}"
        )

def obtener_cuentas_por_cobrar(db: Session, fecha_corte: date = None) -> List[Dict]:
    """Obtener reporte de cuentas por cobrar pendientes"""
    
    if not fecha_corte:
        fecha_corte = date.today()
    
    facturas_pendientes = db.query(Factura).filter(
        Factura.estado_factura.in_(['EMITIDA', 'VENCIDA']),
        Factura.fecha_factura <= fecha_corte
    ).order_by(Factura.fecha_vencimiento).all()
    
    cuentas_por_cobrar = []
    total_pendiente = Decimal('0.00')
    
    for factura in facturas_pendientes:
        dias_vencimiento = 0
        if factura.fecha_vencimiento:
            dias_vencimiento = (fecha_corte - factura.fecha_vencimiento).days
        
        estado_cobranza = 'AL_DIA'
        if dias_vencimiento > 0:
            if dias_vencimiento <= 30:
                estado_cobranza = 'VENCIDA_30'
            elif dias_vencimiento <= 60:
                estado_cobranza = 'VENCIDA_60'
            elif dias_vencimiento <= 90:
                estado_cobranza = 'VENCIDA_90'
            else:
                estado_cobranza = 'VENCIDA_MAS_90'
        
        cuenta = {
            'id_factura': factura.id_factura,
            'numero_factura': factura.numero_factura,
            'cliente': {
                'id': factura.id_cliente,
                'nombre': factura.cliente.nombre_cliente,
                'nit_dui': factura.cliente.nit_dui
            },
            'fecha_factura': factura.fecha_factura,
            'fecha_vencimiento': factura.fecha_vencimiento,
            'total': float(factura.total),
            'dias_vencimiento': dias_vencimiento,
            'estado_cobranza': estado_cobranza
        }
        
        cuentas_por_cobrar.append(cuenta)
        total_pendiente += Decimal(str(factura.total))
    
    return {
        'fecha_corte': fecha_corte,
        'total_cuentas_por_cobrar': float(total_pendiente),
        'cantidad_facturas_pendientes': len(cuentas_por_cobrar),
        'detalle': cuentas_por_cobrar,
        'resumen_por_estado': _resumir_por_estado_cobranza(cuentas_por_cobrar)
    }

def _resumir_por_estado_cobranza(cuentas: List[Dict]) -> Dict:
    """Resumir cuentas por cobrar por estado de cobranza"""
    
    resumen = {
        'AL_DIA': {'cantidad': 0, 'total': 0},
        'VENCIDA_30': {'cantidad': 0, 'total': 0},
        'VENCIDA_60': {'cantidad': 0, 'total': 0},
        'VENCIDA_90': {'cantidad': 0, 'total': 0},
        'VENCIDA_MAS_90': {'cantidad': 0, 'total': 0}
    }
    
    for cuenta in cuentas:
        estado = cuenta['estado_cobranza']
        resumen[estado]['cantidad'] += 1
        resumen[estado]['total'] += cuenta['total']
    
    return resumen