"""
Modelo SQLAlchemy para Usuarios del Sistema.
Gestiona la autenticación y autorización de usuarios.
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, CheckConstraint
from sqlalchemy.sql import func
from app.db import Base


class Usuario(Base):
    """
    Modelo de usuario para el sistema contable.
    
    Atributos:
        id_usuario: Identificador único del usuario
        username: Nombre de usuario único para login
        email: Correo electrónico único
        password_hash: Contraseña hasheada con bcrypt
        nombre_completo: Nombre completo del usuario
        rol: Rol del usuario (Administrador, Contador, Usuario)
        estado: Estado del usuario (ACTIVO, INACTIVO, BLOQUEADO)
        fecha_creacion: Fecha de registro del usuario
        fecha_actualizacion: Última actualización de datos
        ultimo_acceso: Último inicio de sesión exitoso
        intentos_fallidos: Contador de intentos de login fallidos
        bloqueado_hasta: Timestamp hasta cuándo está bloqueado
        debe_cambiar_password: Indica si debe cambiar contraseña en próximo login
    """
    __tablename__ = "usuarios"
    
    # Identificación
    id_usuario = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    
    # Información personal
    nombre_completo = Column(String(100))
    
    # Control de acceso
    rol = Column(
        String(20),
        nullable=False,
        default='Usuario'
    )
    
    estado = Column(
        String(20),
        nullable=False,
        default='ACTIVO'
    )
    
    # Auditoría y seguridad
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())
    fecha_actualizacion = Column(DateTime(timezone=True), onupdate=func.now())
    ultimo_acceso = Column(DateTime(timezone=True))
    intentos_fallidos = Column(Integer, default=0)
    bloqueado_hasta = Column(DateTime(timezone=True))
    debe_cambiar_password = Column(Boolean, default=False)
    
    # Restricciones
    __table_args__ = (
        CheckConstraint(
            rol.in_(['Administrador', 'Contador', 'Usuario']),
            name='check_rol_valido'
        ),
        CheckConstraint(
            estado.in_(['ACTIVO', 'INACTIVO', 'BLOQUEADO']),
            name='check_estado_valido'
        ),
    )
    
    def __repr__(self):
        return f"<Usuario(id={self.id_usuario}, username='{self.username}', rol='{self.rol}')>"
