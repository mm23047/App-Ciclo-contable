"""
Esquemas Pydantic para Balanza de Comprobación.
Define la estructura de datos para requests y responses.
"""
from pydantic import BaseModel, validator
from typing import Optional
from decimal import Decimal
from datetime import date, datetime

class BalanzaComprobacionBase(BaseModel):
    id_periodo: int
    fecha_generacion: date
    id_cuenta: int
    saldo_inicial: Optional[Decimal] = Decimal("0.00")
    total_debe: Optional[Decimal] = Decimal("0.00")
    total_haber: Optional[Decimal] = Decimal("0.00")
    saldo_final: Decimal
    naturaleza_saldo: Optional[str] = None
    usuario_generacion: Optional[str] = None

class BalanzaComprobacionCreate(BalanzaComprobacionBase):
    """Esquema para crear balanza de comprobación"""
    pass

class BalanzaComprobacionUpdate(BaseModel):
    """Esquema para actualizar balanza de comprobación"""
    saldo_inicial: Optional[Decimal] = None
    total_debe: Optional[Decimal] = None
    total_haber: Optional[Decimal] = None
    saldo_final: Optional[Decimal] = None
    naturaleza_saldo: Optional[str] = None
    usuario_generacion: Optional[str] = None

class BalanzaComprobacionRead(BalanzaComprobacionBase):
    """Esquema para leer balanza de comprobación"""
    id_balanza: int
    fecha_creacion: datetime
    
    # Relaciones expandidas
    nombre_cuenta: Optional[str] = None
    codigo_cuenta: Optional[str] = None
    tipo_cuenta: Optional[str] = None

    class Config:
        from_attributes = True

class BalanzaComprobacionResumen(BaseModel):
    """Esquema para resumen de balanza de comprobación"""
    total_activo: Decimal = Decimal("0.00")
    total_pasivo: Decimal = Decimal("0.00")
    total_patrimonio: Decimal = Decimal("0.00")
    total_ingresos: Decimal = Decimal("0.00")
    total_gastos: Decimal = Decimal("0.00")
    total_debe: Decimal = Decimal("0.00")
    total_haber: Decimal = Decimal("0.00")
    diferencia: Decimal = Decimal("0.00")
    balanceado: bool = True
    
    class Config:
        from_attributes = True