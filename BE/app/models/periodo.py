"""
Modelo SQLAlchemy para Períodos Contables.
Define la estructura de la tabla de períodos contables con descripción.
"""
from sqlalchemy import Column, Integer, String, Date
from sqlalchemy.orm import relationship
from app.db import Base

class PeriodoContable(Base):
    __tablename__ = "periodos_contables"
    
    id_periodo = Column(Integer, primary_key=True, autoincrement=True)
    fecha_inicio = Column(Date, nullable=False)
    fecha_fin = Column(Date, nullable=False)
    tipo_periodo = Column(String(20), nullable=False)  # MENSUAL, TRIMESTRAL, SEMESTRAL, ANUAL
    estado = Column(String(10), nullable=False, default='ABIERTO')  # ABIERTO, CERRADO
    descripcion = Column(String(100))  # Ej: "Ejercicio Fiscal 2024"
    
    # Relaciones
    transacciones = relationship("Transaccion", back_populates="periodo")
    balanza_comprobacion = relationship("BalanzaComprobacion", back_populates="periodo")
    balance_inicial = relationship("BalanceInicial", back_populates="periodo")
    libro_mayor = relationship("LibroMayor", back_populates="periodo")
    partidas_ajuste = relationship("PartidaAjuste", back_populates="periodo")
    
    # NOTA: Restricciones CHECK implementadas en la base de datos:
    # CHECK (tipo_periodo IN ('MENSUAL','TRIMESTRAL','SEMESTRAL','ANUAL'))
    # CHECK (fecha_fin > fecha_inicio)
    
    def __repr__(self):
        return f"<PeriodoContable(id={self.id_periodo}, tipo='{self.tipo_periodo}', estado='{self.estado}')>"