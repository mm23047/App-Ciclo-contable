"""
Modelos SQLAlchemy para Estados Financieros.
Define estructuras para configuración y histórico de estados financieros.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Date, Numeric, Boolean, LargeBinary, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB
from app.db import Base

class ConfiguracionEstadosFinancieros(Base):
    __tablename__ = "configuracion_estados_financieros"
    
    id_config = Column(Integer, primary_key=True, autoincrement=True)
    nombre_empresa = Column(String(200), nullable=False)
    nit_empresa = Column(String(20))
    direccion_empresa = Column(Text)
    telefono_empresa = Column(String(25))
    email_empresa = Column(String(100))
    sitio_web_empresa = Column(String(200))
    moneda_reporte = Column(String(10), default='USD')
    logo_empresa = Column(LargeBinary)  # Para almacenar logo en base64
    fecha_creacion = Column(DateTime, default=func.current_timestamp())
    activa = Column(Boolean, default=True)
    
    def __repr__(self):
        return f"<ConfiguracionEstadosFinancieros(id={self.id_config}, empresa='{self.nombre_empresa}')>"


class EstadosFinancierosHistorico(Base):
    __tablename__ = "estados_financieros_historico"
    
    id_estado = Column(Integer, primary_key=True, autoincrement=True)
    id_periodo = Column(Integer, ForeignKey("periodos_contables.id_periodo"), nullable=False)
    tipo_estado = Column(String(50), nullable=False)  # BALANCE_GENERAL, ESTADO_PERDIDAS_GANANCIAS, ESTADO_FLUJO_EFECTIVO
    fecha_generacion = Column(Date, nullable=False)
    contenido_json = Column(JSONB)  # Para almacenar el estado financiero en formato JSON
    total_activos = Column(Numeric(15, 2))
    total_pasivos = Column(Numeric(15, 2))
    patrimonio = Column(Numeric(15, 2))
    utilidad_perdida = Column(Numeric(15, 2))
    usuario_generacion = Column(String(50), nullable=False)
    fecha_creacion = Column(DateTime, default=func.current_timestamp())
    observaciones = Column(Text)
    
    # Relaciones
    periodo = relationship("PeriodoContable")
    
    def __repr__(self):
        return f"<EstadosFinancierosHistorico(id={self.id_estado}, tipo='{self.tipo_estado}', periodo_id={self.id_periodo})>"