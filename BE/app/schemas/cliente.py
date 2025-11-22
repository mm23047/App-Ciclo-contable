"""
Esquemas Pydantic para Cliente.
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from decimal import Decimal


class ClienteBase(BaseModel):
    """Schema base para Cliente"""
    codigo_cliente: str = Field(..., max_length=20, description="Código único del cliente")
    nombre: str = Field(..., max_length=200, description="Nombre o razón social")
    apellidos: Optional[str] = Field(None, max_length=200, description="Apellidos (persona natural)")
    nombre_comercial: Optional[str] = Field(None, max_length=200, description="Nombre comercial")
    tipo_cliente: str = Field(..., description="Tipo de cliente: Empresa o Persona Natural")
    
    # Identificación
    nit: Optional[str] = Field(None, max_length=20, description="NIT o cédula")
    dui: Optional[str] = Field(None, max_length=10, description="DUI")
    numero_registro_fiscal: Optional[str] = Field(None, max_length=30, description="Número de registro fiscal")
    
    # Información de contacto
    direccion: Optional[str] = None
    municipio: Optional[str] = Field(None, max_length=100)
    departamento: Optional[str] = Field(None, max_length=100)
    codigo_postal: Optional[str] = Field(None, max_length=10)
    telefono_principal: Optional[str] = Field(None, max_length=20, alias="telefono")
    telefono_secundario: Optional[str] = Field(None, max_length=20, alias="celular")
    email: Optional[str] = Field(None, max_length=100)
    sitio_web: Optional[str] = Field(None, max_length=200)
    
    # Información comercial
    categoria_cliente: Optional[str] = Field(None, max_length=50, description="Categoría del cliente")
    limite_credito: Optional[Decimal] = Field(default=Decimal("0.00"), description="Límite de crédito")
    dias_credito: Optional[int] = Field(default=0, description="Días de crédito")
    descuento_habitual: Optional[Decimal] = Field(default=Decimal("0.00"), alias="descuento_comercial", description="Descuento habitual")
    
    # Información adicional
    observaciones: Optional[str] = None
    activo: Optional[bool] = Field(default=True, description="Cliente activo")
    
    class Config:
        populate_by_name = True


class ClienteCreate(ClienteBase):
    """Schema para crear Cliente"""
    usuario_creacion: str = Field(default="sistema", max_length=50)


class ClienteUpdate(BaseModel):
    """Schema para actualizar Cliente"""
    nombre: Optional[str] = Field(None, max_length=200)
    apellidos: Optional[str] = Field(None, max_length=200)
    nombre_comercial: Optional[str] = Field(None, max_length=200)
    tipo_cliente: Optional[str] = None
    
    # Identificación
    nit: Optional[str] = Field(None, max_length=20)
    
    # Contacto
    direccion: Optional[str] = None
    municipio: Optional[str] = Field(None, max_length=100)
    telefono_principal: Optional[str] = Field(None, max_length=20, alias="telefono")
    telefono_secundario: Optional[str] = Field(None, max_length=20, alias="celular")
    email: Optional[str] = Field(None, max_length=100)
    
    # Comercial
    categoria_cliente: Optional[str] = Field(None, max_length=50)
    limite_credito: Optional[Decimal] = None
    dias_credito: Optional[int] = None
    descuento_habitual: Optional[Decimal] = Field(None, alias="descuento_comercial")
    
    # Control
    estado_cliente: Optional[str] = None
    activo: Optional[bool] = None
    observaciones: Optional[str] = None
    
    class Config:
        populate_by_name = True


class ClienteResponse(ClienteBase):
    """Schema de respuesta para Cliente"""
    id_cliente: int
    estado_cliente: str
    fecha_creacion: datetime
    fecha_actualizacion: Optional[datetime] = None
    
    class Config:
        from_attributes = True
        populate_by_name = True
