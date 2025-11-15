"""
Modelo SQLAlchemy para Transacciones.
Define la estructura de la tabla de transacciones con categorías y campos extendidos.
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db import Base

class Transaccion(Base):
    __tablename__ = "transacciones"
    
    id_transaccion = Column(Integer, primary_key=True, autoincrement=True)
    fecha_transaccion = Column(DateTime, nullable=False)
    descripcion = Column(Text, nullable=False)
    tipo = Column(String(10), nullable=False)  # INGRESO, EGRESO
    categoria = Column(String(50), default='VENTA', nullable=False)  # Categorías predefinidas
    moneda = Column(String(3), nullable=False, default='USD')
    fecha_creacion = Column(DateTime, nullable=False, default=func.current_timestamp())
    usuario_creacion = Column(String(50), nullable=False)
    id_periodo = Column(Integer, ForeignKey("periodos_contables.id_periodo"), nullable=False)
    numero_referencia = Column(String(30))  # Para referenciar documentos externos
    observaciones = Column(Text)
    
    # Relaciones
    periodo = relationship("PeriodoContable", back_populates="transacciones")
    asientos = relationship("Asiento", back_populates="transaccion", cascade="all, delete-orphan")
    asientos_facturacion = relationship("AsientosFacturacion", back_populates="transaccion")
    
    # TODO: Implementar restricciones CHECK en producción:
    # CHECK (tipo IN ('INGRESO','EGRESO'))
    # CHECK (categoria IN ('VENTA', 'SERVICIOS', 'CONSULTORIA', etc.))
    
    def __repr__(self):
        return f"<Transaccion(id={self.id_transaccion}, tipo='{self.tipo}', categoria='{self.categoria}', fecha='{self.fecha_transaccion}')>"