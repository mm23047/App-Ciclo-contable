"""
Esquemas Pydantic para Partidas de Ajuste.
Define la validación de datos y serialización para requests y responses de la API.
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal

class AsientoAjusteBase(BaseModel):
    id_cuenta: int = Field(..., description="ID de la cuenta asociada")
    descripcion_detalle: Optional[str] = Field(None, description="Descripción detallada del asiento")
    debe: Decimal = Field(default=Decimal("0.00"), ge=0, description="Monto del débito")
    haber: Decimal = Field(default=Decimal("0.00"), ge=0, description="Monto del crédito")
    
    @validator('haber')
    def validate_debe_haber(cls, v, values):
        """Asegurar que exactamente uno de debe o haber sea mayor que 0"""
        debe = values.get('debe', Decimal("0.00"))
        if (debe > 0 and v > 0) or (debe == 0 and v == 0):
            raise ValueError('Exactamente uno de debe o haber debe ser mayor que 0')
        return v

class AsientoAjusteCreate(AsientoAjusteBase):
    pass

class AsientoAjusteRead(AsientoAjusteBase):
    id_asiento_ajuste: int
    id_partida_ajuste: int
    
    class Config:
        from_attributes = True

class PartidaAjusteBase(BaseModel):
    numero_partida: str = Field(..., max_length=20, description="Número único de la partida")
    fecha_ajuste: date = Field(..., description="Fecha del ajuste")
    descripcion: str = Field(..., min_length=1, description="Descripción del ajuste")
    tipo_ajuste: str = Field(..., pattern="^(DEPRECIACION|PROVISION|DEVENGO|DIFERIDO|RECLASIFICACION|CORRECCION_ERROR|AJUSTE_INVENTARIO|AJUSTE_CAMBIO|OTROS)$")
    motivo_ajuste: Optional[str] = Field(None, description="Motivo detallado del ajuste")
    id_periodo: int = Field(..., description="ID del período contable")
    usuario_creacion: str = Field(..., min_length=1, max_length=50, description="Usuario que crea el ajuste")
    estado: str = Field(default="ACTIVO", pattern="^(ACTIVO|ANULADO)$")
    usuario_aprobacion: Optional[str] = Field(None, max_length=50)

class PartidaAjusteCreate(BaseModel):
    numero_partida: str = Field(..., max_length=20)
    fecha_ajuste: date
    descripcion: str = Field(..., min_length=1)
    tipo_ajuste: str = Field(..., pattern="^(DEPRECIACION|PROVISION|DEVENGO|DIFERIDO|RECLASIFICACION|CORRECCION_ERROR|AJUSTE_INVENTARIO|AJUSTE_CAMBIO|OTROS)$")
    motivo_ajuste: Optional[str] = None
    id_periodo: int
    usuario_creacion: str = Field(..., min_length=1, max_length=50)
    asientos_ajuste: List[AsientoAjusteCreate] = Field(default=[], description="Lista de asientos de ajuste")

class PartidaAjusteUpdate(BaseModel):
    descripcion: Optional[str] = Field(None, min_length=1)
    motivo_ajuste: Optional[str] = None
    estado: Optional[str] = Field(None, pattern="^(ACTIVO|ANULADO)$")
    usuario_aprobacion: Optional[str] = Field(None, max_length=50)
    fecha_aprobacion: Optional[datetime] = None

class PartidaAjusteRead(PartidaAjusteBase):
    id_partida_ajuste: int
    fecha_creacion: datetime
    fecha_aprobacion: Optional[datetime]
    asientos_ajuste: List[AsientoAjusteRead] = []
    
    class Config:
        from_attributes = True