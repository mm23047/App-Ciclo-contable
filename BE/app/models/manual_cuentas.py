"""
Modelo SQLAlchemy para Manual de Cuentas.
Define la estructura para la descripción detallada de cada cuenta.
"""
from sqlalchemy import Column, Integer, Text, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db import Base

class ManualCuentas(Base):
    __tablename__ = "manual_cuentas"
    
    id_manual = Column(Integer, primary_key=True, autoincrement=True)
    id_cuenta = Column(Integer, ForeignKey("catalogo_cuentas.id_cuenta", ondelete="CASCADE"), nullable=False, unique=True)
    descripcion_detallada = Column(Text, nullable=False)
    naturaleza_cuenta = Column(String(20), nullable=False)  # DEUDORA, ACREEDORA
    clasificacion = Column(String(50))  # Corriente, No Corriente, etc.
    instrucciones_uso = Column(Text)
    ejemplos_movimientos = Column(Text)
    cuentas_relacionadas = Column(Text)
    normativa_aplicable = Column(Text)  # Referencias a NIIF, normativa local, etc.
    fecha_creacion = Column(DateTime, default=func.current_timestamp())
    fecha_actualizacion = Column(DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp())
    usuario_actualizacion = Column(String(50))
    
    # Relaciones
    cuenta = relationship("CatalogoCuentas", back_populates="manual")
    
    def __repr__(self):
        return f"<ManualCuentas(id={self.id_manual}, cuenta_id={self.id_cuenta}, naturaleza='{self.naturaleza_cuenta}')>"