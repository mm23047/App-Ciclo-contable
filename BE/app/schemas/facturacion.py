"""
Esquemas Pydantic para Facturación.
Define la validación de datos y serialización para requests y responses de la API.
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal

# Esquemas para Cliente
class ClienteBase(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=200, description="Nombre del cliente")
    apellidos: Optional[str] = Field(None, max_length=200, description="Apellidos del cliente")
    nombre_comercial: Optional[str] = Field(None, max_length=200, description="Nombre comercial")
    tipo_cliente: str = Field(..., pattern="^(PERSONA_NATURAL|PERSONA_JURIDICA)$", description="Tipo de cliente")
    nit: Optional[str] = Field(None, max_length=20, description="NIT del cliente")
    dui: Optional[str] = Field(None, max_length=10, description="DUI del cliente")
    telefono_principal: Optional[str] = Field(None, max_length=20, description="Teléfono principal")
    email: Optional[str] = Field(None, max_length=100, description="Email del cliente")
    direccion: Optional[str] = Field(None, description="Dirección del cliente")
    categoria_cliente: Optional[str] = Field(None, pattern="^(MAYORISTA|MINORISTA|DISTRIBUIDOR|CORPORATIVO|GOBIERNO)$")
    limite_credito: Decimal = Field(default=Decimal("0.00"), ge=0, description="Límite de crédito")
    dias_credito: int = Field(default=0, ge=0, description="Días de crédito")
    estado_cliente: str = Field(default="ACTIVO", pattern="^(ACTIVO|INACTIVO|BLOQUEADO)$")
    usuario_creacion: str = Field(..., min_length=1, max_length=50, description="Usuario que crea el cliente")

class ClienteCreate(ClienteBase):
    codigo_cliente: Optional[str] = Field(None, max_length=20, description="Código único del cliente")

class ClienteUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=1, max_length=200)
    apellidos: Optional[str] = Field(None, max_length=200)
    telefono_principal: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=100)
    direccion: Optional[str] = None
    limite_credito: Optional[Decimal] = Field(None, ge=0)
    dias_credito: Optional[int] = Field(None, ge=0)
    estado_cliente: Optional[str] = Field(None, pattern="^(ACTIVO|INACTIVO|BLOQUEADO)$")

class ClienteRead(ClienteBase):
    id_cliente: int
    codigo_cliente: Optional[str]
    fecha_creacion: datetime
    
    class Config:
        from_attributes = True

# Esquemas para Producto
class ProductoBase(BaseModel):
    codigo_producto: str = Field(..., max_length=50, description="Código único del producto")
    nombre: str = Field(..., min_length=1, max_length=200, description="Nombre del producto")
    descripcion: Optional[str] = Field(None, description="Descripción del producto")
    tipo_producto: str = Field(..., pattern="^(PRODUCTO|SERVICIO|COMBO)$", description="Tipo de producto")
    precio_venta: Decimal = Field(..., gt=0, description="Precio de venta")
    precio_compra: Decimal = Field(default=Decimal("0.00"), ge=0, description="Precio de compra")
    aplica_iva: bool = Field(default=True, description="Si aplica IVA")
    porcentaje_iva: Decimal = Field(default=Decimal("13.00"), ge=0, le=100, description="Porcentaje de IVA")
    estado_producto: str = Field(default="ACTIVO", pattern="^(ACTIVO|INACTIVO|DESCONTINUADO)$")

class ProductoCreate(ProductoBase):
    categoria_producto: Optional[str] = Field(None, max_length=50)
    maneja_inventario: bool = Field(default=False, description="Si maneja inventario")
    stock_actual: Decimal = Field(default=Decimal("0.00"), ge=0, description="Stock actual")

class ProductoUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=1, max_length=200)
    descripcion: Optional[str] = None
    precio_venta: Optional[Decimal] = Field(None, gt=0)
    precio_compra: Optional[Decimal] = Field(None, ge=0)
    aplica_iva: Optional[bool] = None
    porcentaje_iva: Optional[Decimal] = Field(None, ge=0, le=100)
    estado_producto: Optional[str] = Field(None, pattern="^(ACTIVO|INACTIVO|DESCONTINUADO)$")

class ProductoRead(ProductoBase):
    id_producto: int
    categoria_producto: Optional[str]
    stock_actual: Optional[Decimal]
    fecha_creacion: datetime
    
    class Config:
        from_attributes = True

# Esquemas para Detalle de Factura
class DetalleFacturaBase(BaseModel):
    numero_linea: int = Field(..., ge=1, description="Número de línea en la factura")
    id_producto: Optional[int] = Field(None, description="ID del producto (opcional si es descripción personalizada)")
    descripcion_personalizada: Optional[str] = Field(None, max_length=300, description="Descripción personalizada")
    cantidad: Decimal = Field(..., gt=0, description="Cantidad del producto/servicio")
    precio_unitario: Decimal = Field(..., ge=0, description="Precio unitario")
    descuento_linea: Decimal = Field(default=Decimal("0.00"), ge=0, description="Descuento en la línea")

    @validator('precio_unitario')
    def validate_precio(cls, v):
        if v < 0:
            raise ValueError('El precio unitario debe ser mayor o igual a 0')
        return v

class DetalleFacturaCreate(DetalleFacturaBase):
    pass

class DetalleFacturaRead(DetalleFacturaBase):
    id_detalle: int
    id_factura: int
    subtotal_linea: Decimal
    impuesto_linea: Decimal
    total_linea: Decimal
    
    class Config:
        from_attributes = True

# Esquemas para Factura
class FacturaBase(BaseModel):
    numero_factura: str = Field(..., max_length=30, description="Número único de la factura")
    serie_factura: str = Field(default="A", max_length=10, description="Serie de la factura")
    fecha_emision: date = Field(..., description="Fecha de emisión")
    fecha_vencimiento: Optional[date] = Field(None, description="Fecha de vencimiento")
    id_cliente: int = Field(..., description="ID del cliente")
    metodo_pago: Optional[str] = Field(None, max_length=30, description="Método de pago")
    condiciones_pago: Optional[str] = Field(None, max_length=100, description="Condiciones de pago")
    observaciones: Optional[str] = Field(None, description="Observaciones")
    usuario_creacion: str = Field(..., min_length=1, max_length=50, description="Usuario que crea la factura")

class FacturaCreate(BaseModel):
    numero_factura: str = Field(..., max_length=30)
    serie_factura: str = Field(default="A", max_length=10)
    fecha_emision: date
    fecha_vencimiento: Optional[date] = None
    id_cliente: int
    metodo_pago: Optional[str] = Field(None, max_length=30)
    observaciones: Optional[str] = None
    usuario_creacion: str = Field(..., min_length=1, max_length=50)
    detalles: List[DetalleFacturaCreate] = Field(..., min_items=1, description="Detalles de la factura")

class FacturaUpdate(BaseModel):
    fecha_vencimiento: Optional[date] = None
    metodo_pago: Optional[str] = Field(None, max_length=30)
    condiciones_pago: Optional[str] = Field(None, max_length=100)
    observaciones: Optional[str] = None
    estado_factura: Optional[str] = Field(None, pattern="^(EMITIDA|PAGADA|ANULADA|VENCIDA)$")

class FacturaRead(FacturaBase):
    id_factura: int
    subtotal: Decimal
    descuento_general: Decimal
    subtotal_descuento: Decimal
    impuesto_iva: Decimal
    otros_impuestos: Decimal
    total: Decimal
    estado_factura: str
    fecha_creacion: datetime
    detalles: List[DetalleFacturaRead] = []
    
    class Config:
        from_attributes = True