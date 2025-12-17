"""
Modelo SQLAlchemy para Balance Inicial.
Define la estructura para saldos de apertura por período.
"""
from sqlalchemy import Column, Integer, Date, Numeric, DateTime, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db import Base

class BalanceInicial(Base):
    __tablename__ = "balance_inicial"
    
    id_balance_inicial = Column(Integer, primary_key=True, autoincrement=True)
    id_periodo = Column(Integer, ForeignKey("periodos_contables.id_periodo"), nullable=False)
    id_cuenta = Column(Integer, ForeignKey("catalogo_cuentas.id_cuenta"), nullable=False)
    saldo_inicial = Column(Numeric(15, 2), nullable=False)
    naturaleza_saldo = Column(String(20), nullable=False)  # DEUDOR, ACREEDOR
    fecha_registro = Column(Date, nullable=False)
    usuario_creacion = Column(String(50), nullable=False)
    observaciones = Column(Text)
    fecha_creacion = Column(DateTime, default=func.current_timestamp())
    fecha_modificacion = Column(Date, nullable=True)
    usuario_modificacion = Column(String(50), nullable=True)
    estado_balance = Column(String(15), default='ACTIVO')  # ACTIVO, MODIFICADO, ANULADO
    
    # Relaciones
    periodo = relationship("PeriodoContable", back_populates="balance_inicial")
    cuenta = relationship("CatalogoCuentas")
    
    def __repr__(self):
        return f"<BalanceInicial(id={self.id_balance_inicial}, periodo_id={self.id_periodo}, cuenta_id={self.id_cuenta}, saldo={self.saldo_inicial})>"
    
    # Índice único para un solo balance inicial por período-cuenta
    __table_args__ = (
        {'sqlite_autoincrement': True},
    )