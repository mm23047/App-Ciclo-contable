"""
Modelos SQLAlchemy para Partidas de Ajuste.
Define estructuras para ajustes contables y sus asientos.
"""
from sqlalchemy import Column, Integer, String, Date, Text, DateTime, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db import Base

class PartidaAjuste(Base):
    __tablename__ = "partidas_ajuste"
    
    id_partida_ajuste = Column(Integer, primary_key=True, autoincrement=True)
    numero_partida = Column(String(20), unique=True, nullable=False)
    fecha_ajuste = Column(Date, nullable=False)
    descripcion = Column(Text, nullable=False)
    tipo_ajuste = Column(String(50), nullable=False)  # DEPRECIACION, PROVISION, DEVENGO, etc.
    motivo_ajuste = Column(Text)
    id_periodo = Column(Integer, ForeignKey("periodos_contables.id_periodo"), nullable=False)
    usuario_creacion = Column(String(50), nullable=False)
    fecha_creacion = Column(DateTime, default=func.current_timestamp())
    estado = Column(String(20), default='ACTIVO')  # ACTIVO, ANULADO
    usuario_aprobacion = Column(String(50))
    fecha_aprobacion = Column(DateTime)
    
    # Relaciones
    periodo = relationship("PeriodoContable", back_populates="partidas_ajuste")
    asientos_ajuste = relationship("AsientoAjuste", back_populates="partida_ajuste", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<PartidaAjuste(id={self.id_partida_ajuste}, numero='{self.numero_partida}', tipo='{self.tipo_ajuste}')>"


class AsientoAjuste(Base):
    __tablename__ = "asientos_ajuste"
    
    id_asiento_ajuste = Column(Integer, primary_key=True, autoincrement=True)
    id_partida_ajuste = Column(Integer, ForeignKey("partidas_ajuste.id_partida_ajuste", ondelete="CASCADE"), nullable=False)
    id_cuenta = Column(Integer, ForeignKey("catalogo_cuentas.id_cuenta"), nullable=False)
    descripcion_detalle = Column(Text)
    debe = Column(Numeric(15, 2), default=0.00)
    haber = Column(Numeric(15, 2), default=0.00)
    
    # Relaciones
    partida_ajuste = relationship("PartidaAjuste", back_populates="asientos_ajuste")
    cuenta = relationship("CatalogoCuentas")
    
    def __repr__(self):
        return f"<AsientoAjuste(id={self.id_asiento_ajuste}, partida_id={self.id_partida_ajuste}, cuenta_id={self.id_cuenta})>"