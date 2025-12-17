"""
Esquemas Pydantic para Transacciones.
Define la validación de datos y serialización para requests y responses de la API.
"""
from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime

# Categorías válidas para transacciones
CATEGORIAS_VALIDAS = [
    "VENTA", "COMPRA", "NÓMINA", "SERVICIOS", "IMPUESTOS", 
    "INVERSIÓN", "PRÉSTAMO", "ACTIVOS", "GASTOS ADMINISTRATIVOS", 
    "GASTOS OPERATIVOS", "OTROS"
]

class TransaccionBase(BaseModel):
    fecha_transaccion: datetime = Field(..., description="Fecha y hora de la transacción")
    descripcion: str = Field(..., min_length=1, max_length=500, description="Descripción de la transacción")
    tipo: str = Field(..., pattern="^(INGRESO|EGRESO)$", description="Tipo de transacción")
    categoria: str = Field(default="VENTA", description="Categoría de la transacción")
    moneda: str = Field(default="USD", min_length=3, max_length=3, description="Código de moneda")
    usuario_creacion: str = Field(..., min_length=1, max_length=50, description="Usuario que creó la transacción")
    id_periodo: int = Field(..., gt=0, description="ID del período contable asociado (requerido)")
    numero_referencia: Optional[str] = Field(None, max_length=30, description="Número de referencia externo")
    observaciones: Optional[str] = Field(None, max_length=1000, description="Observaciones adicionales")
    
    @validator('categoria')
    def validate_categoria(cls, v):
        if v and v not in CATEGORIAS_VALIDAS:
            raise ValueError(f"Categoría debe ser una de: {', '.join(CATEGORIAS_VALIDAS)}")
        return v
    
    @validator('moneda')
    def validate_moneda(cls, v):
        if v:
            return v.upper()
        return v

class TransaccionCreate(TransaccionBase):
    pass

class TransaccionUpdate(BaseModel):
    fecha_transaccion: Optional[datetime] = None
    descripcion: Optional[str] = Field(None, min_length=1, max_length=500)
    tipo: Optional[str] = Field(None, pattern="^(INGRESO|EGRESO)$")
    categoria: Optional[str] = None
    moneda: Optional[str] = Field(None, min_length=3, max_length=3)
    usuario_creacion: Optional[str] = Field(None, min_length=1, max_length=50)
    id_periodo: Optional[int] = Field(None, gt=0)
    numero_referencia: Optional[str] = Field(None, max_length=30)
    observaciones: Optional[str] = Field(None, max_length=1000)
    
    @validator('categoria')
    def validate_categoria(cls, v):
        if v and v not in CATEGORIAS_VALIDAS:
            raise ValueError(f"Categoría debe ser una de: {', '.join(CATEGORIAS_VALIDAS)}")
        return v
    
    @validator('moneda')
    def validate_moneda(cls, v):
        if v:
            return v.upper()
        return v

class TransaccionRead(TransaccionBase):
    id_transaccion: int
    fecha_creacion: datetime
    
    class Config:
        from_attributes = True