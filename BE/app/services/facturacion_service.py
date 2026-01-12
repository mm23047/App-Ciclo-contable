"""
Capa de servicios para Facturación Digital.
Maneja la lógica de negocio para facturación e integración contable automática.
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from fastapi import HTTPException, status
from app.models.facturacion import Cliente, Producto, Factura, DetalleFactura, ConfiguracionFacturacion
from app.models.periodo import PeriodoContable
from app.schemas.facturacion import (
    ClienteCreate, ProductoCreate,
    FacturaCreate, DetalleFacturaCreate,
    ConfiguracionFacturacionCreate, ConfiguracionFacturacionUpdate
)
from typing import Dict, List
from decimal import Decimal
from datetime import date, datetime

def crear_cliente(db: Session, cliente_data: ClienteCreate, usuario: str) -> Cliente:
    """Crear un nuevo cliente con validaciones"""
    
    # Verificar que no exista un cliente con el mismo NIT o código
    if cliente_data.nit:
        cliente_existente = db.query(Cliente).filter(
            Cliente.nit == cliente_data.nit,
            Cliente.estado_cliente == 'ACTIVO'
        ).first()
        
        if cliente_existente:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ya existe un cliente activo con NIT: {cliente_data.nit}"
            )
    
    if cliente_data.codigo_cliente:
        codigo_existente = db.query(Cliente).filter(
            Cliente.codigo_cliente == cliente_data.codigo_cliente
        ).first()
        
        if codigo_existente:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ya existe un cliente con el código: {cliente_data.codigo_cliente}"
            )
    
    try:
        # Crear el cliente con los datos proporcionados
        cliente_dict = cliente_data.dict(exclude_unset=True)
        cliente_dict['usuario_creacion'] = usuario
        
        db_cliente = Cliente(**cliente_dict)
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
            fecha_creacion=date.today()
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
    usuario: str
) -> Factura:
    """
    Crear factura completa con detalles usando configuración fiscal
    """
    # Cargar configuración fiscal
    config = obtener_configuracion_facturacion(db)
    
    # Validar período contable
    periodo = db.query(PeriodoContable).filter(
        PeriodoContable.fecha_inicio <= factura_data.fecha_emision,
        PeriodoContable.fecha_fin >= factura_data.fecha_emision
    ).first()
    
    if periodo and periodo.estado == 'CERRADO':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No se puede crear factura en período cerrado ({periodo.tipo_periodo})"
        )
    
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
    
    # Validar que todos los productos con id_producto existan y filtrar None
    productos_ids = [detalle.id_producto for detalle in detalles if detalle.id_producto is not None]
    
    if productos_ids:  # Solo validar si hay productos con ID
        productos_ids_unicos = list(set(productos_ids))  # Obtener IDs únicos
        productos = db.query(Producto).filter(
            Producto.id_producto.in_(productos_ids_unicos),
            Producto.estado_producto == 'ACTIVO'
        ).all()
        
        if len(productos) != len(productos_ids_unicos):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uno o más productos no encontrados o inactivos"
            )
        
        productos_map = {p.id_producto: p for p in productos}
    else:
        productos_map = {}
    
    try:
        # Generar número de factura usando configuración
        if factura_data.numero_factura:
            numero_factura = factura_data.numero_factura
        else:
            # Usar prefijo y número actual de la configuración
            numero_factura = f"{config.prefijo_factura}-{str(config.numero_actual).zfill(4)}"
        
        # Calcular totales
        subtotal = Decimal('0.00')
        total_iva = Decimal('0.00')
        
        # Validar y calcular detalles
        detalles_calculados = []
        for detalle in detalles:
            # Validar que tenga producto o descripción personalizada
            if not detalle.id_producto and not detalle.descripcion_personalizada:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cada línea debe tener un producto o una descripción personalizada"
                )
            
            # Obtener datos del producto si existe
            if detalle.id_producto and detalle.id_producto in productos_map:
                producto = productos_map[detalle.id_producto]
                precio_unitario = detalle.precio_unitario if detalle.precio_unitario else producto.precio_venta
                aplica_iva = producto.aplica_iva
            else:
                # Producto personalizado, usar datos del detalle
                if not detalle.precio_unitario:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Precio unitario es requerido para descripciones personalizadas"
                    )
                precio_unitario = detalle.precio_unitario
                aplica_iva = True  # Por defecto aplica IVA a productos personalizados
            
            cantidad = detalle.cantidad
            
            if cantidad <= 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cantidad debe ser mayor a 0"
                )
            
            subtotal_linea = precio_unitario * Decimal(str(cantidad))
            
            # Calcular IVA si aplica usando configuración fiscal
            iva_linea = Decimal('0.00')
            if aplica_iva:
                # Usar porcentaje de IVA de la configuración
                iva_porcentaje = Decimal(str(config.iva_porcentaje)) / Decimal('100')
                iva_linea = subtotal_linea * iva_porcentaje
            
            total_linea = subtotal_linea + iva_linea
            
            detalles_calculados.append({
                'detalle_data': detalle,
                'precio_unitario': precio_unitario,
                'subtotal_linea': subtotal_linea,
                'iva_linea': iva_linea,
                'total_linea': total_linea,
                'aplica_iva': aplica_iva
            })
            
            subtotal += subtotal_linea
            total_iva += iva_linea
        
        # Calcular retenciones usando configuración fiscal
        retencion_fuente = Decimal('0.00')
        reteica = Decimal('0.00')
        
        if config.retefuente_porcentaje > 0:
            retencion_fuente = subtotal * (Decimal(str(config.retefuente_porcentaje)) / Decimal('100'))
        
        if config.reteica_porcentaje > 0:
            reteica = subtotal * (Decimal(str(config.reteica_porcentaje)) / Decimal('100'))
        
        # Calcular total general con retenciones
        total_factura = subtotal + total_iva - retencion_fuente - reteica
        
        # Crear factura
        db_factura = Factura(
            numero_factura=numero_factura,
            serie_factura=factura_data.serie_factura,
            id_cliente=factura_data.id_cliente,
            fecha_emision=factura_data.fecha_emision,
            fecha_vencimiento=factura_data.fecha_vencimiento,
            subtotal=float(subtotal),
            descuento_general=0.00,
            subtotal_descuento=float(subtotal),
            impuesto_iva=float(total_iva),
            otros_impuestos=0.00,
            retencion_fuente=float(retencion_fuente),
            reteica=float(reteica),
            total=float(total_factura),
            estado_factura='EMITIDA',
            observaciones=factura_data.observaciones,
            metodo_pago=factura_data.metodo_pago,
            usuario_creacion=factura_data.usuario_creacion
        )
        
        db.add(db_factura)
        db.flush()  # Para obtener el ID
        
        # Crear detalles de factura y actualizar stock
        for detalle_calc in detalles_calculados:
            db_detalle = DetalleFactura(
                id_factura=db_factura.id_factura,
                numero_linea=detalle_calc['detalle_data'].numero_linea,
                id_producto=detalle_calc['detalle_data'].id_producto,
                cantidad=detalle_calc['detalle_data'].cantidad,
                precio_unitario=float(detalle_calc['precio_unitario']),
                descuento_linea=float(detalle_calc['detalle_data'].descuento_linea),
                subtotal_linea=float(detalle_calc['subtotal_linea']),
                impuesto_linea=float(detalle_calc['iva_linea']),
                total_linea=float(detalle_calc['total_linea']),
                descripcion_personalizada=detalle_calc['detalle_data'].descripcion_personalizada
            )
            db.add(db_detalle)
            
            # Actualizar stock del producto si maneja inventario y tiene id_producto
            if detalle_calc['detalle_data'].id_producto and detalle_calc['detalle_data'].id_producto in productos_map:
                producto = productos_map[detalle_calc['detalle_data'].id_producto]
                if producto.maneja_inventario:
                    cantidad_vendida = Decimal(str(detalle_calc['detalle_data'].cantidad))
                    nuevo_stock = Decimal(str(producto.stock_actual)) - cantidad_vendida
                    
                    # Validar que no quede stock negativo
                    if nuevo_stock < 0:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Stock insuficiente para producto '{producto.nombre}'. Stock disponible: {producto.stock_actual}, cantidad solicitada: {cantidad_vendida}"
                        )
                    
                    producto.stock_actual = float(nuevo_stock)
        
        # Incrementar número actual de factura en la configuración
        if not factura_data.numero_factura:  # Solo si se generó automáticamente
            config.numero_actual += 1
        
        db.commit()
        db.refresh(db_factura)
        return db_factura
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error al crear factura: {str(e)}"
        )

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
    
    return query.order_by(desc(Factura.fecha_emision)).limit(limit).offset(offset).all()

def buscar_facturas(
    db: Session,
    estado: str = None,
    fecha_desde: date = None,
    fecha_hasta: date = None,
    numero_factura: str = None,
    codigo_cliente: str = None,
    limit: int = 100,
    offset: int = 0
) -> List[Factura]:
    """Buscar facturas con filtros opcionales"""
    
    query = db.query(Factura)
    
    if estado and estado != "Todas":
        # Mapear estados del frontend al backend
        estado_map = {
            "Pendiente": "EMITIDA",
            "Pagada": "PAGADA",
            "Vencida": "VENCIDA",
            "Anulada": "ANULADA"
        }
        estado_backend = estado_map.get(estado, estado.upper())
        query = query.filter(Factura.estado_factura == estado_backend)
    
    if fecha_desde:
        query = query.filter(Factura.fecha_emision >= fecha_desde)
    
    if fecha_hasta:
        query = query.filter(Factura.fecha_emision <= fecha_hasta)
    
    if numero_factura:
        query = query.filter(Factura.numero_factura.like(f"%{numero_factura}%"))
    
    if codigo_cliente:
        # Filtrar por código de cliente
        query = query.join(Cliente).filter(Cliente.codigo_cliente == codigo_cliente)
    
    return query.order_by(desc(Factura.fecha_emision)).limit(limit).offset(offset).all()

def obtener_reporte_ventas_periodo(
    db: Session,
    fecha_desde: date,
    fecha_hasta: date,
    cliente_id: int = None
) -> Dict:
    """Generar reporte de ventas por período"""
    
    query = db.query(Factura).filter(
        Factura.fecha_emision >= fecha_desde,
        Factura.fecha_emision <= fecha_hasta,
        Factura.estado_factura.in_(['EMITIDA', 'PAGADA'])
    )
    
    if cliente_id:
        query = query.filter(Factura.id_cliente == cliente_id)
    
    facturas = query.all()
    
    # Calcular totales
    total_ventas = sum(f.total for f in facturas)
    total_subtotal = sum(f.subtotal for f in facturas)
    total_impuestos = sum(f.impuesto_iva or 0 for f in facturas)
    cantidad_facturas = len(facturas)
    
    # Agrupar por cliente
    ventas_por_cliente = {}
    for factura in facturas:
        nit_cliente = factura.cliente.nit or factura.cliente.dui or "SIN-NIT"
        cliente_key = f"{nit_cliente} - {factura.cliente.nombre}"
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
        ventas_por_cliente[cliente_key]['impuestos'] += factura.impuesto_iva or 0
    
    # Productos más vendidos
    query_productos = db.query(
        Producto.nombre,
        func.sum(DetalleFactura.cantidad).label('cantidad_vendida'),
        func.sum(DetalleFactura.total_linea).label('total_vendido')
    ).join(
        DetalleFactura, Producto.id_producto == DetalleFactura.id_producto
    ).join(
        Factura, DetalleFactura.id_factura == Factura.id_factura
    ).filter(
        Factura.fecha_emision >= fecha_desde,
        Factura.fecha_emision <= fecha_hasta,
        Factura.estado_factura.in_(['EMITIDA', 'PAGADA'])
    ).group_by(
        Producto.id_producto, Producto.nombre
    ).order_by(
        desc(func.sum(DetalleFactura.cantidad))
    ).limit(10).all()
    
    productos_top = [
        {
            'producto': p.nombre,
            'cantidad_vendida': float(p.cantidad_vendida),
            'total_vendido': float(p.total_vendido)
        }
        for p in query_productos
    ]
    
    return {
        'periodo': {
            'fecha_desde': fecha_desde,
            'fecha_hasta': fecha_hasta
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

def marcar_factura_pagada(db: Session, factura_id: int, usuario: str) -> Factura:
    """Marcar factura como pagada"""
    
    factura = db.query(Factura).filter(Factura.id_factura == factura_id).first()
    if not factura:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Factura no encontrada"
        )
    
    if factura.estado_factura == 'ANULADA':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se puede marcar como pagada una factura anulada"
        )
    
    if factura.estado_factura == 'PAGADA':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La factura ya está marcada como pagada"
        )
    
    try:
        factura.estado_factura = 'PAGADA'
        db.commit()
        db.refresh(factura)
        return factura
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error al marcar factura como pagada: {str(e)}"
        )

def anular_factura(db: Session, factura_id: int, motivo: str, usuario: str) -> Factura:
    """Anular una factura, restaurar stock y sus asientos contables"""
    
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
        # Restaurar stock de los productos vendidos
        detalles = db.query(DetalleFactura).filter(
            DetalleFactura.id_factura == factura_id
        ).all()
        
        for detalle in detalles:
            producto = db.query(Producto).filter(
                Producto.id_producto == detalle.id_producto
            ).first()
            
            if producto and producto.maneja_inventario:
                # Devolver la cantidad al stock
                cantidad_devolver = Decimal(str(detalle.cantidad))
                producto.stock_actual = float(Decimal(str(producto.stock_actual)) + cantidad_devolver)
        
        # Cambiar estado de factura
        factura.estado_factura = 'ANULADA'
        factura.observaciones = f"{factura.observaciones or ''}\nANULADA: {motivo}".strip()
        factura.fecha_modificacion = date.today()
        factura.usuario_modificacion = usuario
        
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
        Factura.fecha_emision <= fecha_corte
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
                'nombre': factura.cliente.nombre,
                'nit': factura.cliente.nit or factura.cliente.dui
            },
            'fecha_factura': factura.fecha_emision,
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

def obtener_reporte_ventas_por_cliente(
    db: Session,
    fecha_desde: date,
    fecha_hasta: date
) -> Dict:
    """Generar reporte de ventas agrupado por cliente"""
    
    facturas = db.query(Factura).filter(
        Factura.fecha_emision >= fecha_desde,
        Factura.fecha_emision <= fecha_hasta,
        Factura.estado_factura.in_(['EMITIDA', 'PAGADA'])
    ).all()
    
    ventas_por_cliente = {}
    
    for factura in facturas:
        cliente_id = factura.id_cliente
        if cliente_id not in ventas_por_cliente:
            ventas_por_cliente[cliente_id] = {
                'id_cliente': cliente_id,
                'codigo_cliente': factura.cliente.codigo_cliente,
                'nombre': factura.cliente.nombre,
                'nit': factura.cliente.nit or factura.cliente.dui,
                'cantidad_facturas': 0,
                'total_ventas': 0,
                'subtotal': 0,
                'impuestos': 0
            }
        
        ventas_por_cliente[cliente_id]['cantidad_facturas'] += 1
        ventas_por_cliente[cliente_id]['total_ventas'] += float(factura.total)
        ventas_por_cliente[cliente_id]['subtotal'] += float(factura.subtotal)
        ventas_por_cliente[cliente_id]['impuestos'] += float(factura.impuesto_iva or 0)
    
    # Convertir a lista y ordenar por total de ventas
    lista_clientes = sorted(
        ventas_por_cliente.values(),
        key=lambda x: x['total_ventas'],
        reverse=True
    )
    
    total_general = sum(c['total_ventas'] for c in lista_clientes)
    
    return {
        'periodo': {
            'fecha_desde': fecha_desde,
            'fecha_hasta': fecha_hasta
        },
        'resumen': {
            'total_clientes': len(lista_clientes),
            'total_ventas': total_general,
            'promedio_por_cliente': total_general / len(lista_clientes) if lista_clientes else 0
        },
        'detalle_clientes': lista_clientes
    }

def obtener_reporte_ventas_por_producto(
    db: Session,
    fecha_desde: date,
    fecha_hasta: date
) -> Dict:
    """Generar reporte de ventas agrupado por producto"""
    
    query = db.query(
        Producto.id_producto,
        Producto.codigo_producto,
        Producto.nombre,
        Producto.precio_venta,
        func.sum(DetalleFactura.cantidad).label('cantidad_vendida'),
        func.sum(DetalleFactura.subtotal_linea).label('subtotal'),
        func.sum(DetalleFactura.impuesto_linea).label('impuestos'),
        func.sum(DetalleFactura.total_linea).label('total_vendido')
    ).join(
        DetalleFactura, Producto.id_producto == DetalleFactura.id_producto
    ).join(
        Factura, DetalleFactura.id_factura == Factura.id_factura
    ).filter(
        Factura.fecha_emision >= fecha_desde,
        Factura.fecha_emision <= fecha_hasta,
        Factura.estado_factura.in_(['EMITIDA', 'PAGADA'])
    ).group_by(
        Producto.id_producto,
        Producto.codigo_producto,
        Producto.nombre,
        Producto.precio_venta
    ).order_by(
        desc(func.sum(DetalleFactura.total_linea))
    ).all()
    
    productos = []
    total_general = 0
    cantidad_total = 0
    
    for p in query:
        total_vendido = float(p.total_vendido)
        cantidad = float(p.cantidad_vendida)
        
        productos.append({
            'id_producto': p.id_producto,
            'codigo_producto': p.codigo_producto,
            'nombre': p.nombre,
            'precio_venta': float(p.precio_venta),
            'cantidad_vendida': cantidad,
            'subtotal': float(p.subtotal),
            'impuestos': float(p.impuestos or 0),
            'total_vendido': total_vendido,
            'precio_promedio': total_vendido / cantidad if cantidad > 0 else 0
        })
        
        total_general += total_vendido
        cantidad_total += cantidad
    
    return {
        'periodo': {
            'fecha_desde': fecha_desde,
            'fecha_hasta': fecha_hasta
        },
        'resumen': {
            'total_productos': len(productos),
            'cantidad_total_vendida': cantidad_total,
            'total_ventas': total_general,
            'ticket_promedio': total_general / cantidad_total if cantidad_total > 0 else 0
        },
        'detalle_productos': productos
    }

def obtener_reporte_tendencias(
    db: Session,
    fecha_desde: date,
    fecha_hasta: date
) -> Dict:
    """Generar reporte de tendencias de ventas (diario, semanal, mensual)"""
    
    # Ventas por día
    query_diaria = db.query(
        Factura.fecha_emision,
        func.count(Factura.id_factura).label('cantidad_facturas'),
        func.sum(Factura.subtotal).label('subtotal'),
        func.sum(Factura.impuesto_iva).label('impuestos'),
        func.sum(Factura.total).label('total')
    ).filter(
        Factura.fecha_emision >= fecha_desde,
        Factura.fecha_emision <= fecha_hasta,
        Factura.estado_factura.in_(['EMITIDA', 'PAGADA'])
    ).group_by(
        Factura.fecha_emision
    ).order_by(
        Factura.fecha_emision
    ).all()
    
    ventas_diarias = []
    for v in query_diaria:
        ventas_diarias.append({
            'fecha': v.fecha_emision.isoformat(),
            'cantidad_facturas': v.cantidad_facturas,
            'subtotal': float(v.subtotal),
            'impuestos': float(v.impuestos or 0),
            'total': float(v.total)
        })
    
    # Calcular tendencia
    total_ventas = sum(v['total'] for v in ventas_diarias)
    total_facturas = sum(v['cantidad_facturas'] for v in ventas_diarias)
    dias_con_ventas = len(ventas_diarias)
    
    # Mejor día y peor día
    mejor_dia = max(ventas_diarias, key=lambda x: x['total']) if ventas_diarias else None
    peor_dia = min(ventas_diarias, key=lambda x: x['total']) if ventas_diarias else None
    
    return {
        'periodo': {
            'fecha_desde': fecha_desde,
            'fecha_hasta': fecha_hasta
        },
        'resumen': {
            'total_ventas': total_ventas,
            'total_facturas': total_facturas,
            'dias_con_ventas': dias_con_ventas,
            'promedio_diario': total_ventas / dias_con_ventas if dias_con_ventas > 0 else 0,
            'promedio_por_factura': total_ventas / total_facturas if total_facturas > 0 else 0
        },
        'mejor_dia': mejor_dia,
        'peor_dia': peor_dia,
        'ventas_diarias': ventas_diarias
    }

def obtener_configuracion_facturacion(db: Session) -> ConfiguracionFacturacion:
    """Obtener configuración activa de facturación con lock pesimista"""
    
    config = db.query(ConfiguracionFacturacion).filter(
        ConfiguracionFacturacion.activo == True
    ).with_for_update().first()
    
    if not config:
        # Si no existe configuración, crear una por defecto
        config = ConfiguracionFacturacion(
            empresa_nit="000000000-0",
            empresa_nombre="Empresa sin configurar",
            empresa_direccion="Dirección sin configurar",
            empresa_telefono="0000-0000",
            empresa_email="sin-email@empresa.com",
            empresa_web="",
            iva_porcentaje=Decimal('13.00'),
            retefuente_porcentaje=Decimal('0.00'),
            reteica_porcentaje=Decimal('0.00'),
            prefijo_factura='FV',
            numero_inicial=1,
            numero_actual=1,
            activo=True,
            usuario_actualizacion='SISTEMA'
        )
        db.add(config)
        db.commit()
        db.refresh(config)
    
    return config

def crear_configuracion_facturacion(
    db: Session,
    config_data: ConfiguracionFacturacionCreate
) -> ConfiguracionFacturacion:
    """Crear nueva configuración de facturación"""
    
    # Verificar si ya existe una configuración activa
    config_existente = db.query(ConfiguracionFacturacion).filter(
        ConfiguracionFacturacion.activo == True
    ).first()
    
    if config_existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe una configuración activa. Use actualizar en su lugar."
        )
    
    try:
        config_dict = config_data.dict()
        db_config = ConfiguracionFacturacion(**config_dict, activo=True)
        
        db.add(db_config)
        db.commit()
        db.refresh(db_config)
        
        return db_config
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error al crear configuración: {str(e)}"
        )

def actualizar_configuracion_facturacion(
    db: Session,
    config_data: ConfiguracionFacturacionUpdate
) -> ConfiguracionFacturacion:
    """Actualizar configuración activa de facturación"""
    
    config = db.query(ConfiguracionFacturacion).filter(
        ConfiguracionFacturacion.activo == True
    ).first()
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No existe configuración activa"
        )
    
    try:
        # Actualizar solo los campos proporcionados
        update_data = config_data.dict(exclude_unset=True)
        
        for field, value in update_data.items():
            if hasattr(config, field) and value is not None:
                setattr(config, field, value)
        
        config.fecha_actualizacion = datetime.now()
        
        db.commit()
        db.refresh(config)
        
        return config
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error al actualizar configuración: {str(e)}"
        )