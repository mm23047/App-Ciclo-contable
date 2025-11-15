"""
Modelos SQLAlchemy para sistema de facturación.
Define estructuras para clientes, productos y facturas.
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, Numeric, DateTime, Date, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db import Base

class Cliente(Base):
    __tablename__ = "clientes"
    
    id_cliente = Column(Integer, primary_key=True, autoincrement=True)
    codigo_cliente = Column(String(20), unique=True)
    nombre = Column(String(200), nullable=False)
    apellidos = Column(String(200))
    nombre_comercial = Column(String(200))
    tipo_cliente = Column(String(20), nullable=False)  # PERSONA_NATURAL, PERSONA_JURIDICA
    
    # Identificación
    nit = Column(String(20))
    dui = Column(String(10))
    numero_registro_fiscal = Column(String(30))
    
    # Información de contacto
    direccion = Column(Text)
    municipio = Column(String(100))
    departamento = Column(String(100))
    codigo_postal = Column(String(10))
    telefono_principal = Column(String(20))
    telefono_secundario = Column(String(20))
    email = Column(String(100))
    sitio_web = Column(String(200))
    
    # Información comercial
    categoria_cliente = Column(String(50))  # MAYORISTA, MINORISTA, DISTRIBUIDOR, etc.
    limite_credito = Column(Numeric(15, 2), default=0.00)
    dias_credito = Column(Integer, default=0)
    descuento_habitual = Column(Numeric(5, 2), default=0.00)
    
    # Información contable
    cuenta_contable_ventas = Column(Integer, ForeignKey("catalogo_cuentas.id_cuenta"))
    cuenta_contable_cobros = Column(Integer, ForeignKey("catalogo_cuentas.id_cuenta"))
    
    # Control
    estado_cliente = Column(String(20), default='ACTIVO')  # ACTIVO, INACTIVO, BLOQUEADO
    observaciones = Column(Text)
    usuario_creacion = Column(String(50), nullable=False)
    fecha_creacion = Column(DateTime, default=func.current_timestamp())
    fecha_actualizacion = Column(DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp())
    
    # Relaciones
    facturas = relationship("Factura", back_populates="cliente")
    cuenta_ventas = relationship("CatalogoCuentas", foreign_keys=[cuenta_contable_ventas])
    cuenta_cobros = relationship("CatalogoCuentas", foreign_keys=[cuenta_contable_cobros])
    
    def __repr__(self):
        return f"<Cliente(id={self.id_cliente}, nombre='{self.nombre}', tipo='{self.tipo_cliente}')>"


class Producto(Base):
    __tablename__ = "productos"
    
    id_producto = Column(Integer, primary_key=True, autoincrement=True)
    codigo_producto = Column(String(50), unique=True, nullable=False)
    nombre = Column(String(200), nullable=False)
    descripcion = Column(Text)
    tipo_producto = Column(String(30), nullable=False)  # PRODUCTO, SERVICIO, COMBO
    categoria_producto = Column(String(50))
    
    # Precios
    precio_venta = Column(Numeric(15, 4), nullable=False)
    precio_compra = Column(Numeric(15, 4), default=0.00)
    margen_utilidad = Column(Numeric(5, 2), default=0.00)
    
    # Inventario (solo para productos físicos)
    maneja_inventario = Column(Boolean, default=False)
    stock_actual = Column(Numeric(10, 3), default=0.00)
    stock_minimo = Column(Numeric(10, 3), default=0.00)
    stock_maximo = Column(Numeric(10, 3), default=0.00)
    unidad_medida = Column(String(20), default='UNIDAD')
    
    # Impuestos
    aplica_iva = Column(Boolean, default=True)
    porcentaje_iva = Column(Numeric(5, 2), default=13.00)
    codigo_impuesto = Column(String(10))
    
    # Contabilidad
    cuenta_contable_ventas = Column(Integer, ForeignKey("catalogo_cuentas.id_cuenta"))
    cuenta_contable_inventario = Column(Integer, ForeignKey("catalogo_cuentas.id_cuenta"))
    cuenta_contable_costo = Column(Integer, ForeignKey("catalogo_cuentas.id_cuenta"))
    
    # Control
    estado_producto = Column(String(20), default='ACTIVO')  # ACTIVO, INACTIVO, DESCONTINUADO
    fecha_creacion = Column(DateTime, default=func.current_timestamp())
    fecha_actualizacion = Column(DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp())
    
    # Relaciones
    detalle_facturas = relationship("DetalleFactura", back_populates="producto")
    cuenta_ventas = relationship("CatalogoCuentas", foreign_keys=[cuenta_contable_ventas])
    cuenta_inventario = relationship("CatalogoCuentas", foreign_keys=[cuenta_contable_inventario])
    cuenta_costo = relationship("CatalogoCuentas", foreign_keys=[cuenta_contable_costo])
    
    def __repr__(self):
        return f"<Producto(id={self.id_producto}, codigo='{self.codigo_producto}', nombre='{self.nombre}')>"


class Factura(Base):
    __tablename__ = "facturas"
    
    id_factura = Column(Integer, primary_key=True, autoincrement=True)
    numero_factura = Column(String(30), unique=True, nullable=False)
    serie_factura = Column(String(10), default='A')
    
    # Fechas
    fecha_emision = Column(Date, nullable=False)
    fecha_vencimiento = Column(Date)
    
    # Cliente
    id_cliente = Column(Integer, ForeignKey("clientes.id_cliente"), nullable=False)
    
    # Totales
    subtotal = Column(Numeric(15, 2), nullable=False)
    descuento_general = Column(Numeric(15, 2), default=0.00)
    subtotal_descuento = Column(Numeric(15, 2), nullable=False)
    impuesto_iva = Column(Numeric(15, 2), nullable=False)
    otros_impuestos = Column(Numeric(15, 2), default=0.00)
    total = Column(Numeric(15, 2), nullable=False)
    
    # Estado y control
    estado_factura = Column(String(20), default='EMITIDA')  # EMITIDA, PAGADA, ANULADA, VENCIDA
    metodo_pago = Column(String(30))
    condiciones_pago = Column(String(100))
    observaciones = Column(Text)
    
    # Relaciones
    id_periodo = Column(Integer, ForeignKey("periodos_contables.id_periodo"))
    usuario_creacion = Column(String(50), nullable=False)
    fecha_creacion = Column(DateTime, default=func.current_timestamp())
    
    # Facturación electrónica
    uuid_factura = Column(String(100))  # Para facturación electrónica
    codigo_autorizacion = Column(String(50))
    fecha_autorizacion = Column(DateTime)
    
    # Relaciones
    cliente = relationship("Cliente", back_populates="facturas")
    periodo = relationship("PeriodoContable")
    detalles = relationship("DetalleFactura", back_populates="factura", cascade="all, delete-orphan")
    asientos_facturacion = relationship("AsientosFacturacion", back_populates="factura")
    
    def __repr__(self):
        return f"<Factura(id={self.id_factura}, numero='{self.numero_factura}', cliente_id={self.id_cliente})>"


class DetalleFactura(Base):
    __tablename__ = "detalle_factura"
    
    id_detalle = Column(Integer, primary_key=True, autoincrement=True)
    id_factura = Column(Integer, ForeignKey("facturas.id_factura", ondelete="CASCADE"), nullable=False)
    numero_linea = Column(Integer, nullable=False)
    
    # Producto
    id_producto = Column(Integer, ForeignKey("productos.id_producto"))
    descripcion_personalizada = Column(String(300))
    
    # Cantidades y precios
    cantidad = Column(Numeric(10, 3), nullable=False)
    precio_unitario = Column(Numeric(15, 4), nullable=False)
    descuento_linea = Column(Numeric(15, 2), default=0.00)
    subtotal_linea = Column(Numeric(15, 2), nullable=False)
    impuesto_linea = Column(Numeric(15, 2), default=0.00)
    total_linea = Column(Numeric(15, 2), nullable=False)
    
    # Relaciones
    factura = relationship("Factura", back_populates="detalles")
    producto = relationship("Producto", back_populates="detalle_facturas")
    
    def __repr__(self):
        return f"<DetalleFactura(id={self.id_detalle}, factura_id={self.id_factura}, producto_id={self.id_producto})>"


class ResumenVentasDiarias(Base):
    __tablename__ = "resumen_ventas_diarias"
    
    id_resumen = Column(Integer, primary_key=True, autoincrement=True)
    fecha_venta = Column(Date, nullable=False, unique=True)
    cantidad_facturas = Column(Integer, nullable=False, default=0)
    total_ventas_brutas = Column(Numeric(15, 2), nullable=False, default=0.00)
    total_descuentos = Column(Numeric(15, 2), default=0.00)
    total_impuestos = Column(Numeric(15, 2), nullable=False, default=0.00)
    total_ventas_netas = Column(Numeric(15, 2), nullable=False, default=0.00)
    facturas_anuladas = Column(Integer, default=0)
    fecha_generacion = Column(DateTime, default=func.current_timestamp())
    usuario_generacion = Column(String(50))
    
    def __repr__(self):
        return f"<ResumenVentasDiarias(fecha={self.fecha_venta}, total_ventas={self.total_ventas_netas})>"


class AsientosFacturacion(Base):
    __tablename__ = "asientos_facturacion"
    
    id_asiento_factura = Column(Integer, primary_key=True, autoincrement=True)
    id_factura = Column(Integer, ForeignKey("facturas.id_factura"), nullable=False)
    id_transaccion = Column(Integer, ForeignKey("transacciones.id_transaccion"), nullable=False)
    tipo_asiento = Column(String(30), nullable=False)  # VENTA, COBRO, ANULACION, DESCUENTO
    fecha_creacion = Column(DateTime, default=func.current_timestamp())
    
    # Relaciones
    factura = relationship("Factura", back_populates="asientos_facturacion")
    transaccion = relationship("Transaccion", back_populates="asientos_facturacion")
    
    def __repr__(self):
        return f"<AsientosFacturacion(id={self.id_asiento_factura}, factura_id={self.id_factura}, tipo='{self.tipo_asiento}')>"