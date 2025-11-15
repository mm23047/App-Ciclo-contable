"""
Esquemas Pydantic para Balance Inicial y Estados Financieros.
Define la validación de datos y serialización para requests y responses de la API.
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import date, datetime
from decimal import Decimal

# Esquemas para Balance Inicial
class BalanceInicialBase(BaseModel):
    id_periodo: int = Field(..., description="ID del período contable")
    id_cuenta: int = Field(..., description="ID de la cuenta")
    saldo_inicial: Decimal = Field(..., description="Saldo inicial de la cuenta")
    naturaleza_saldo: str = Field(..., pattern="^(DEUDOR|ACREEDOR)$", description="Naturaleza del saldo")
    fecha_registro: date = Field(..., description="Fecha de registro del saldo")
    usuario_creacion: str = Field(..., min_length=1, max_length=50, description="Usuario que crea el registro")
    observaciones: Optional[str] = Field(None, description="Observaciones adicionales")

class BalanceInicialCreate(BalanceInicialBase):
    pass

class BalanceInicialUpdate(BaseModel):
    saldo_inicial: Optional[Decimal] = None
    naturaleza_saldo: Optional[str] = Field(None, pattern="^(DEUDOR|ACREEDOR)$")
    observaciones: Optional[str] = None
    estado_balance: Optional[str] = Field(None, pattern="^(ACTIVO|MODIFICADO|ANULADO)$")

class BalanceInicialRead(BalanceInicialBase):
    id_balance_inicial: int
    estado_balance: str
    fecha_creacion: datetime
    
    class Config:
        from_attributes = True

# Esquemas para Configuración de Estados Financieros
class ConfiguracionEstadosBase(BaseModel):
    nombre_empresa: str = Field(..., min_length=1, max_length=200, description="Nombre de la empresa")
    nit_empresa: Optional[str] = Field(None, max_length=20, description="NIT de la empresa")
    direccion_empresa: Optional[str] = Field(None, description="Dirección de la empresa")
    telefono_empresa: Optional[str] = Field(None, max_length=25, description="Teléfono de la empresa")
    email_empresa: Optional[str] = Field(None, max_length=100, description="Email de la empresa")
    sitio_web_empresa: Optional[str] = Field(None, max_length=200, description="Sitio web de la empresa")
    moneda_reporte: str = Field(default="USD", max_length=10, description="Moneda para los reportes")

class ConfiguracionEstadosCreate(ConfiguracionEstadosBase):
    pass

class ConfiguracionEstadosUpdate(BaseModel):
    nombre_empresa: Optional[str] = Field(None, min_length=1, max_length=200)
    nit_empresa: Optional[str] = Field(None, max_length=20)
    direccion_empresa: Optional[str] = None
    telefono_empresa: Optional[str] = Field(None, max_length=25)
    email_empresa: Optional[str] = Field(None, max_length=100)
    sitio_web_empresa: Optional[str] = Field(None, max_length=200)
    moneda_reporte: Optional[str] = Field(None, max_length=10)

class ConfiguracionEstadosRead(ConfiguracionEstadosBase):
    id_config: int
    activa: bool
    fecha_creacion: datetime
    
    class Config:
        from_attributes = True

# Esquemas para Estados Financieros Históricos
class EstadosFinancierosHistoricoBase(BaseModel):
    id_periodo: int = Field(..., description="ID del período contable")
    tipo_estado: str = Field(..., pattern="^(BALANCE_GENERAL|ESTADO_PERDIDAS_GANANCIAS|ESTADO_FLUJO_EFECTIVO)$", 
                           description="Tipo de estado financiero")
    fecha_generacion: date = Field(..., description="Fecha de generación del estado")
    usuario_generacion: str = Field(..., min_length=1, max_length=50, description="Usuario que genera el estado")
    observaciones: Optional[str] = Field(None, description="Observaciones del estado financiero")

class EstadosFinancierosHistoricoCreate(EstadosFinancierosHistoricoBase):
    contenido_json: Optional[Dict[str, Any]] = Field(None, description="Contenido JSON del estado financiero")
    total_activos: Optional[Decimal] = Field(None, description="Total de activos")
    total_pasivos: Optional[Decimal] = Field(None, description="Total de pasivos")
    patrimonio: Optional[Decimal] = Field(None, description="Total patrimonio")
    utilidad_perdida: Optional[Decimal] = Field(None, description="Utilidad o pérdida")

class EstadosFinancierosHistoricoRead(EstadosFinancierosHistoricoBase):
    id_estado: int
    contenido_json: Optional[Dict[str, Any]]
    total_activos: Optional[Decimal]
    total_pasivos: Optional[Decimal]
    patrimonio: Optional[Decimal]
    utilidad_perdida: Optional[Decimal]
    fecha_creacion: datetime
    
    class Config:
        from_attributes = True

# Esquemas para Balanza de Comprobación
class BalanzaComprobacionBase(BaseModel):
    id_periodo: int = Field(..., description="ID del período contable")
    fecha_generacion: date = Field(..., description="Fecha de generación")
    id_cuenta: int = Field(..., description="ID de la cuenta")
    saldo_inicial: Decimal = Field(default=Decimal("0.00"), description="Saldo inicial")
    total_debe: Decimal = Field(default=Decimal("0.00"), description="Total débitos")
    total_haber: Decimal = Field(default=Decimal("0.00"), description="Total créditos")
    saldo_final: Decimal = Field(..., description="Saldo final")
    naturaleza_saldo: Optional[str] = Field(None, pattern="^(DEUDOR|ACREEDOR)$", description="Naturaleza del saldo")
    usuario_generacion: Optional[str] = Field(None, max_length=50, description="Usuario que genera la balanza")

class BalanzaComprobacionCreate(BalanzaComprobacionBase):
    pass

class BalanzaComprobacionRead(BalanzaComprobacionBase):
    id_balanza: int
    fecha_creacion: datetime
    
    class Config:
        from_attributes = True