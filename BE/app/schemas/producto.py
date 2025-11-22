"""
Schemas de Producto para validación de datos.
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
from decimal import Decimal

class ProductoBase(BaseModel):
    """Schema base para Producto"""
    codigo_producto: str = Field(..., max_length=50)
    nombre: str = Field(..., max_length=200)
    descripcion: Optional[str] = None
    tipo_producto: str = Field(default="PRODUCTO", max_length=30)
    categoria_producto: Optional[str] = Field(None, max_length=50)
    
    # Precios
    precio_venta: Decimal = Field(..., ge=0)
    precio_compra: Optional[Decimal] = Field(default=0.0, ge=0)
    margen_utilidad: Optional[Decimal] = Field(default=0.0, ge=0)
    
    # Inventario
    maneja_inventario: bool = Field(default=False)
    stock_actual: Optional[Decimal] = Field(default=0.0, ge=0)
    stock_minimo: Optional[Decimal] = Field(default=0.0, ge=0)
    stock_maximo: Optional[Decimal] = Field(default=0.0, ge=0)
    unidad_medida: str = Field(default="UNIDAD", max_length=20)
    
    # Impuestos
    aplica_iva: bool = Field(default=True)
    porcentaje_iva: Optional[Decimal] = Field(default=13.0, ge=0, le=100)
    codigo_impuesto: Optional[str] = Field(None, max_length=10)
    
    # Contabilidad
    cuenta_contable_ventas: Optional[int] = None
    cuenta_contable_inventario: Optional[int] = None
    cuenta_contable_costo: Optional[int] = None
    
    # Estado
    estado_producto: str = Field(default="ACTIVO", max_length=20)

    @field_validator('tipo_producto')
    @classmethod
    def validar_tipo(cls, v):
        if v not in ['PRODUCTO', 'SERVICIO', 'COMBO']:
            raise ValueError('Tipo debe ser "PRODUCTO", "SERVICIO" o "COMBO"')
        return v

    @field_validator('estado_producto')
    @classmethod
    def validar_estado(cls, v):
        if v not in ['ACTIVO', 'INACTIVO', 'DESCONTINUADO']:
            raise ValueError('Estado debe ser "ACTIVO", "INACTIVO" o "DESCONTINUADO"')
        return v

class ProductoCreate(ProductoBase):
    """Schema para crear Producto"""
    pass

class ProductoUpdate(BaseModel):
    """Schema para actualizar Producto"""
    codigo_producto: Optional[str] = Field(None, max_length=50)
    nombre: Optional[str] = Field(None, max_length=200)
    descripcion: Optional[str] = None
    tipo_producto: Optional[str] = Field(None, max_length=30)
    categoria_producto: Optional[str] = Field(None, max_length=50)
    
    # Precios
    precio_venta: Optional[Decimal] = Field(None, ge=0)
    precio_compra: Optional[Decimal] = Field(None, ge=0)
    margen_utilidad: Optional[Decimal] = Field(None, ge=0)
    
    # Inventario
    maneja_inventario: Optional[bool] = None
    stock_actual: Optional[Decimal] = Field(None, ge=0)
    stock_minimo: Optional[Decimal] = Field(None, ge=0)
    stock_maximo: Optional[Decimal] = Field(None, ge=0)
    unidad_medida: Optional[str] = Field(None, max_length=20)
    
    # Impuestos
    aplica_iva: Optional[bool] = None
    porcentaje_iva: Optional[Decimal] = Field(None, ge=0, le=100)
    codigo_impuesto: Optional[str] = Field(None, max_length=10)
    
    # Contabilidad
    cuenta_contable_ventas: Optional[int] = None
    cuenta_contable_inventario: Optional[int] = None
    cuenta_contable_costo: Optional[int] = None
    
    # Estado
    estado_producto: Optional[str] = Field(None, max_length=20)

class ProductoResponse(ProductoBase):
    """Schema de respuesta de Producto"""
    id_producto: int
    fecha_creacion: datetime
    fecha_actualizacion: Optional[datetime] = None

    class Config:
        from_attributes = True
