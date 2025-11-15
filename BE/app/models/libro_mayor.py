"""
Modelo SQLAlchemy para Libro Mayor.
Define la estructura para movimientos por cuenta con saldos.
"""
from sqlalchemy import Column, Integer, Date, Text, String, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db import Base

class LibroMayor(Base):
    __tablename__ = "libro_mayor"
    
    id_movimiento_mayor = Column(Integer, primary_key=True, autoincrement=True)
    id_cuenta = Column(Integer, ForeignKey("catalogo_cuentas.id_cuenta"), nullable=False)
    fecha_movimiento = Column(Date, nullable=False)
    descripcion = Column(Text, nullable=False)
    referencia = Column(String(50))  # Número de asiento o transacción
    debe = Column(Numeric(15, 2), default=0.00)
    haber = Column(Numeric(15, 2), default=0.00)
    saldo_anterior = Column(Numeric(15, 2), default=0.00)
    saldo_actual = Column(Numeric(15, 2), nullable=False)
    id_asiento = Column(Integer, ForeignKey("asientos.id_asiento"))
    id_periodo = Column(Integer, ForeignKey("periodos_contables.id_periodo"), nullable=False)
    fecha_creacion = Column(DateTime, default=func.current_timestamp())
    tipo_saldo = Column(String(10))  # DEUDOR, ACREEDOR
    
    # Relaciones
    cuenta = relationship("CatalogoCuentas")
    asiento = relationship("Asiento")
    periodo = relationship("PeriodoContable", back_populates="libro_mayor")
    
    def __repr__(self):
        return f"<LibroMayor(id={self.id_movimiento_mayor}, cuenta_id={self.id_cuenta}, saldo={self.saldo_actual})>"