"""
Esquemas Pydantic para Catálogo de Cuentas.
Define la validación de datos y serialización para requests y responses de la API.
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class CatalogoCuentaBase(BaseModel):
    codigo_cuenta: str = Field(..., min_length=1, max_length=20, description="Código único de cuenta")
    nombre_cuenta: str = Field(..., min_length=1, max_length=100, description="Nombre de la cuenta")
    tipo_cuenta: str = Field(..., pattern="^(Activo|Pasivo|Capital|Ingreso|Egreso)$", description="Tipo de cuenta")

class CatalogoCuentaCreate(CatalogoCuentaBase):
    nivel_cuenta: Optional[int] = Field(default=1, description="Nivel jerárquico de la cuenta")
    cuenta_padre: Optional[int] = Field(default=None, description="ID de cuenta padre")
    acepta_movimientos: Optional[bool] = Field(default=True, description="Si acepta movimientos contables")
    estado: Optional[str] = Field(default='ACTIVA', pattern="^(ACTIVA|INACTIVA)$", description="Estado de la cuenta")

class CatalogoCuentaUpdate(BaseModel):
    codigo_cuenta: Optional[str] = Field(None, min_length=1, max_length=20)
    nombre_cuenta: Optional[str] = Field(None, min_length=1, max_length=100)
    tipo_cuenta: Optional[str] = Field(None, pattern="^(Activo|Pasivo|Capital|Ingreso|Egreso)$")
    nivel_cuenta: Optional[int] = Field(None, description="Nivel jerárquico de la cuenta")
    cuenta_padre: Optional[int] = Field(None, description="ID de cuenta padre")
    acepta_movimientos: Optional[bool] = Field(None, description="Si acepta movimientos contables")
    estado: Optional[str] = Field(None, pattern="^(ACTIVA|INACTIVA)$", description="Estado de la cuenta")

class CatalogoCuentaRead(CatalogoCuentaBase):
    id_cuenta: int
    nivel_cuenta: int
    cuenta_padre: Optional[int]
    acepta_movimientos: bool
    estado: str = Field(description="Estado de la cuenta")
    fecha_creacion: datetime
    
    class Config:
        from_attributes = True