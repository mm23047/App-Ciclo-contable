"""
Modelo SQLAlchemy para Catálogo de Cuentas.
Define la estructura de la tabla de catálogo de cuentas con campos extendidos.
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db import Base

class CatalogoCuentas(Base):
    __tablename__ = "catalogo_cuentas"
    
    id_cuenta = Column(Integer, primary_key=True, autoincrement=True)
    codigo_cuenta = Column(String(20), unique=True, nullable=False, index=True)
    nombre_cuenta = Column(String(100), nullable=False)
    tipo_cuenta = Column(String(50), nullable=False)  # Activo, Pasivo, Capital, Ingreso, Egreso
    nivel_cuenta = Column(Integer, default=1)  # Para jerarquía de cuentas
    cuenta_padre = Column(Integer, ForeignKey("catalogo_cuentas.id_cuenta"))
    acepta_movimientos = Column(Boolean, default=True)  # FALSE para cuentas de agrupación
    fecha_creacion = Column(DateTime, default=func.current_timestamp())
    estado = Column(String(10), default='ACTIVA')  # ACTIVA, INACTIVA
    
    # Relaciones
    cuentas_hijas = relationship("CatalogoCuentas", remote_side=[cuenta_padre])
    manual = relationship("ManualCuentas", back_populates="cuenta", uselist=False)
    
    def __repr__(self):
        return f"<CatalogoCuentas(codigo='{self.codigo_cuenta}', nombre='{self.nombre_cuenta}', tipo='{self.tipo_cuenta}')>"