"""
Esquemas Pydantic para Balance Inicial.
Define las estructuras de datos para requests y responses del API.
"""
from pydantic import BaseModel, Field, validator
from typing import Optional
from decimal import Decimal
from datetime import date
from enum import Enum

class EstadoBalance(str, Enum):
    ACTIVO = "ACTIVO"
    INACTIVO = "INACTIVO"
    PROCESADO = "PROCESADO"

class BalanceInicialBase(BaseModel):
    """Schema base para Balance Inicial"""
    id_cuenta: int = Field(..., description="ID de la cuenta contable")
    id_periodo: int = Field(..., description="ID del período contable")
    saldo_inicial: Decimal = Field(..., description="Saldo inicial de la cuenta", decimal_places=2)
    naturaleza_saldo: str = Field(..., pattern="^(DEUDOR|ACREEDOR)$", description="Naturaleza del saldo")
    observaciones: Optional[str] = Field(None, max_length=500, description="Observaciones adicionales")

    @validator('saldo_inicial')
    def validar_saldo_inicial(cls, v):
        if v is None:
            raise ValueError('El saldo inicial es requerido')
        return v

class BalanceInicialCreate(BalanceInicialBase):
    """Schema para crear un nuevo balance inicial"""
    
    @validator('observaciones')
    def validar_observaciones(cls, v):
        if v and len(v.strip()) == 0:
            return None
        return v

class BalanceInicialUpdate(BaseModel):
    """Schema para actualizar un balance inicial existente"""
    saldo_inicial: Optional[Decimal] = Field(None, description="Nuevo saldo inicial", decimal_places=2)
    observaciones: Optional[str] = Field(None, max_length=500, description="Observaciones actualizadas")
    estado_balance: Optional[EstadoBalance] = Field(None, description="Estado del balance")

    @validator('saldo_inicial')
    def validar_saldo_inicial(cls, v):
        if v is not None and v < 0:
            # Permitir negativos para ciertos casos especiales, validar en servicio según tipo de cuenta
            pass
        return v

class BalanceInicialResponse(BalanceInicialBase):
    """Schema para respuesta de balance inicial"""
    id_balance: int = Field(..., description="ID único del balance")
    estado_balance: EstadoBalance = Field(..., description="Estado del balance")
    fecha_creacion: date = Field(..., description="Fecha de creación")
    usuario_creacion: str = Field(..., description="Usuario que creó el balance")
    fecha_modificacion: Optional[date] = Field(None, description="Fecha de última modificación")
    usuario_modificacion: Optional[str] = Field(None, description="Usuario que modificó el balance")
    
    # Datos de la cuenta relacionada
    codigo_cuenta: Optional[str] = Field(None, description="Código de la cuenta")
    nombre_cuenta: Optional[str] = Field(None, description="Nombre de la cuenta")
    tipo_cuenta: Optional[str] = Field(None, description="Tipo de cuenta")

    class Config:
        from_attributes = True
        json_encoders = {
            Decimal: lambda v: float(v) if v else 0.0
        }

class BalanceInicialDetallado(BalanceInicialResponse):
    """Schema para balance inicial con información completa de la cuenta"""
    cuenta: Optional[dict] = Field(None, description="Información completa de la cuenta")
    periodo: Optional[dict] = Field(None, description="Información del período")

class ResumenBalancesPeriodo(BaseModel):
    """Schema para resumen de balances iniciales por período"""
    periodo_id: int = Field(..., description="ID del período")
    resumen_por_tipo: dict = Field(..., description="Resumen agrupado por tipo de cuenta")
    total_general: dict = Field(..., description="Totales generales")
    
    class Config:
        json_encoders = {
            Decimal: lambda v: float(v) if v else 0.0
        }

class BalanceInicialBulkCreate(BaseModel):
    """Schema para crear múltiples balances iniciales"""
    periodo_id: int = Field(..., description="ID del período contable")
    balances: list[BalanceInicialCreate] = Field(..., description="Lista de balances a crear")
    
    @validator('balances')
    def validar_balances_no_vacio(cls, v):
        if not v or len(v) == 0:
            raise ValueError('Debe proporcionar al menos un balance inicial')
        return v

class GenerarBalanceRequest(BaseModel):
    """Schema para solicitud de generación de balances desde período anterior"""
    periodo_actual_id: int = Field(..., description="ID del período para el cual generar balances")
    periodo_anterior_id: int = Field(..., description="ID del período base para los saldos")
    incluir_solo_cuentas_balance: bool = Field(True, description="Solo incluir cuentas de balance (Activo, Pasivo, Capital)")
    
    @validator('periodo_actual_id', 'periodo_anterior_id')
    def validar_periodos_diferentes(cls, v, values):
        if 'periodo_anterior_id' in values and v == values['periodo_anterior_id']:
            raise ValueError('El período actual debe ser diferente al período anterior')
        return v

class ValidacionCuadreRequest(BaseModel):
    """Schema para validar cuadre de balances iniciales"""
    periodo_id: int = Field(..., description="ID del período a validar")
    incluir_detalle_cuentas: bool = Field(False, description="Incluir detalle de cuentas en la respuesta")

class ValidacionCuadreResponse(BaseModel):
    """Schema para respuesta de validación de cuadre"""
    periodo_id: int = Field(..., description="ID del período validado")
    esta_cuadrado: bool = Field(..., description="Indica si los balances están cuadrados")
    diferencia_total: Decimal = Field(..., description="Diferencia entre debe y haber")
    total_debe: Decimal = Field(..., description="Total naturaleza deudora")
    total_haber: Decimal = Field(..., description="Total naturaleza acreedora")
    cantidad_cuentas: int = Field(..., description="Cantidad de cuentas con balance inicial")
    errores: list[str] = Field(default_factory=list, description="Lista de errores encontrados")
    advertencias: list[str] = Field(default_factory=list, description="Lista de advertencias")
    detalle_cuentas: Optional[list[dict]] = Field(None, description="Detalle por cuenta si se solicita")
    
    class Config:
        json_encoders = {
            Decimal: lambda v: float(v) if v else 0.0
        }

class BalanceInicialFiltros(BaseModel):
    """Schema para filtros en consultas de balances iniciales"""
    periodo_id: Optional[int] = Field(None, description="Filtrar por período")
    tipo_cuenta: Optional[str] = Field(None, description="Filtrar por tipo de cuenta")
    estado_balance: Optional[EstadoBalance] = Field(None, description="Filtrar por estado")
    codigo_cuenta_like: Optional[str] = Field(None, description="Filtrar por código de cuenta (parcial)")
    saldo_minimo: Optional[Decimal] = Field(None, description="Saldo mínimo")
    saldo_maximo: Optional[Decimal] = Field(None, description="Saldo máximo")
    usuario_creacion: Optional[str] = Field(None, description="Filtrar por usuario que creó")
    fecha_desde: Optional[date] = Field(None, description="Fecha de creación desde")
    fecha_hasta: Optional[date] = Field(None, description="Fecha de creación hasta")

class AnalisisBalancesPeriodo(BaseModel):
    """Schema para análisis de balances de un período"""
    periodo_id: int = Field(..., description="ID del período analizado")
    fecha_analisis: date = Field(..., description="Fecha del análisis")
    estadisticas: dict = Field(..., description="Estadísticas generales")
    distribucion_por_tipo: dict = Field(..., description="Distribución por tipo de cuenta")
    cuentas_sin_balance: list[dict] = Field(default_factory=list, description="Cuentas sin balance inicial")
    balances_negativos: list[dict] = Field(default_factory=list, description="Balances con saldo negativo")
    recomendaciones: list[str] = Field(default_factory=list, description="Recomendaciones de mejora")
    
    class Config:
        json_encoders = {
            Decimal: lambda v: float(v) if v else 0.0
        }