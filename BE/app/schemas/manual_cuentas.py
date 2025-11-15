"""
Esquemas Pydantic para Manual de Cuentas.
Define la validación de datos y serialización para requests y responses de la API.
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class ManualCuentasBase(BaseModel):
    id_cuenta: int = Field(..., description="ID de la cuenta asociada")
    descripcion_detallada: str = Field(..., min_length=1, description="Descripción completa de la cuenta")
    naturaleza_cuenta: str = Field(..., pattern="^(DEUDORA|ACREEDORA)$", description="Naturaleza de la cuenta")
    clasificacion: Optional[str] = Field(None, description="Clasificación adicional (Corriente, No Corriente, etc.)")
    instrucciones_uso: Optional[str] = Field(None, description="Instrucciones para el uso de la cuenta")
    ejemplos_movimientos: Optional[str] = Field(None, description="Ejemplos de movimientos típicos")
    cuentas_relacionadas: Optional[str] = Field(None, description="Cuentas relacionadas")
    normativa_aplicable: Optional[str] = Field(None, description="Referencias normativas aplicables")
    usuario_actualizacion: Optional[str] = Field(None, max_length=50, description="Usuario que actualizó el registro")

class ManualCuentasCreate(ManualCuentasBase):
    pass

class ManualCuentasUpdate(BaseModel):
    descripcion_detallada: Optional[str] = Field(None, min_length=1)
    naturaleza_cuenta: Optional[str] = Field(None, pattern="^(DEUDORA|ACREEDORA)$")
    clasificacion: Optional[str] = None
    instrucciones_uso: Optional[str] = None
    ejemplos_movimientos: Optional[str] = None
    cuentas_relacionadas: Optional[str] = None
    normativa_aplicable: Optional[str] = None
    usuario_actualizacion: Optional[str] = Field(None, max_length=50)

class ManualCuentasRead(ManualCuentasBase):
    id_manual: int
    fecha_creacion: datetime
    fecha_actualizacion: datetime
    
    class Config:
        from_attributes = True