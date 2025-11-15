"""
Modelo SQLAlchemy para Configuración Contable por Categoría.
Define automatización de asientos contables según categoría.
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db import Base

class ConfiguracionContableCategoria(Base):
    __tablename__ = "configuracion_contable_categoria"
    
    id_config = Column(Integer, primary_key=True, autoincrement=True)
    categoria = Column(String(50), nullable=False)
    tipo_transaccion = Column(String(10), nullable=False)  # INGRESO, EGRESO
    
    # Cuentas por defecto según la categoría
    cuenta_debito_default = Column(Integer, ForeignKey("catalogo_cuentas.id_cuenta"))
    cuenta_credito_default = Column(Integer, ForeignKey("catalogo_cuentas.id_cuenta"))
    cuenta_iva_default = Column(Integer, ForeignKey("catalogo_cuentas.id_cuenta"))
    
    # Configuración adicional
    descripcion = Column(Text)
    activa = Column(Boolean, default=True)
    porcentaje_iva_default = Column(Numeric(5, 2), default=13.00)
    fecha_creacion = Column(DateTime, default=func.current_timestamp())
    
    # Relaciones
    cuenta_debito = relationship("CatalogoCuentas", foreign_keys=[cuenta_debito_default])
    cuenta_credito = relationship("CatalogoCuentas", foreign_keys=[cuenta_credito_default])
    cuenta_iva = relationship("CatalogoCuentas", foreign_keys=[cuenta_iva_default])
    
    def __repr__(self):
        return f"<ConfiguracionContableCategoria(id={self.id_config}, categoria='{self.categoria}', tipo='{self.tipo_transaccion}')>"
    
    # Índice único para evitar duplicados de categoría-tipo
    __table_args__ = (
        {'sqlite_autoincrement': True},
    )