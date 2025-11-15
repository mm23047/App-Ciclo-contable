"""
Modelo SQLAlchemy para Balanza de Comprobación.
Define la estructura para snapshots de saldos por período.
"""
from sqlalchemy import Column, Integer, Date, Numeric, DateTime, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db import Base

class BalanzaComprobacion(Base):
    __tablename__ = "balanza_comprobacion"
    
    id_balanza = Column(Integer, primary_key=True, autoincrement=True)
    id_periodo = Column(Integer, ForeignKey("periodos_contables.id_periodo"), nullable=False)
    fecha_generacion = Column(Date, nullable=False)
    id_cuenta = Column(Integer, ForeignKey("catalogo_cuentas.id_cuenta"), nullable=False)
    saldo_inicial = Column(Numeric(15, 2), default=0.00)
    total_debe = Column(Numeric(15, 2), default=0.00)
    total_haber = Column(Numeric(15, 2), default=0.00)
    saldo_final = Column(Numeric(15, 2), nullable=False)
    naturaleza_saldo = Column(String(10))  # DEUDOR, ACREEDOR
    fecha_creacion = Column(DateTime, default=func.current_timestamp())
    usuario_generacion = Column(String(50))
    
    # Relaciones
    periodo = relationship("PeriodoContable", back_populates="balanza_comprobacion")
    cuenta = relationship("CatalogoCuentas")
    
    def __repr__(self):
        return f"<BalanzaComprobacion(id={self.id_balanza}, periodo_id={self.id_periodo}, cuenta_id={self.id_cuenta})>"
    
    # Índice único para evitar duplicados
    __table_args__ = (
        {'sqlite_autoincrement': True},
    )