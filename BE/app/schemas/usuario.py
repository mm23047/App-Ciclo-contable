"""
Esquemas Pydantic para Usuarios y Autenticación.
Define la validación de datos y serialización para la API.
"""
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime


class UsuarioBase(BaseModel):
    """Schema base para usuario"""
    username: str = Field(..., min_length=3, max_length=50, description="Nombre de usuario único")
    email: EmailStr = Field(..., description="Correo electrónico válido")
    nombre_completo: Optional[str] = Field(None, max_length=100, description="Nombre completo del usuario")
    rol: str = Field(default='Usuario', description="Rol del usuario en el sistema")
    
    @validator('rol')
    def validar_rol(cls, v):
        roles_validos = ['Administrador', 'Contador', 'Usuario']
        if v not in roles_validos:
            raise ValueError(f'Rol debe ser uno de: {", ".join(roles_validos)}')
        return v
    
    @validator('username')
    def validar_username(cls, v):
        if not v.replace('_', '').replace('.', '').isalnum():
            raise ValueError('Username solo puede contener letras, números, guiones bajos y puntos')
        return v.lower()


class UsuarioCreate(UsuarioBase):
    """Schema para crear un nuevo usuario"""
    password: str = Field(..., min_length=8, description="Contraseña (mínimo 8 caracteres)")
    
    @validator('password')
    def validar_password(cls, v):
        if len(v) < 8:
            raise ValueError('La contraseña debe tener al menos 8 caracteres')
        
        # Validar que tenga al menos una letra y un número
        tiene_letra = any(c.isalpha() for c in v)
        tiene_numero = any(c.isdigit() for c in v)
        
        if not (tiene_letra and tiene_numero):
            raise ValueError('La contraseña debe contener al menos una letra y un número')
        
        return v


class UsuarioUpdate(BaseModel):
    """Schema para actualizar usuario"""
    email: Optional[EmailStr] = None
    nombre_completo: Optional[str] = None
    rol: Optional[str] = None
    estado: Optional[str] = None
    debe_cambiar_password: Optional[bool] = None
    
    @validator('rol')
    def validar_rol(cls, v):
        if v is not None:
            roles_validos = ['Administrador', 'Contador', 'Usuario']
            if v not in roles_validos:
                raise ValueError(f'Rol debe ser uno de: {", ".join(roles_validos)}')
        return v
    
    @validator('estado')
    def validar_estado(cls, v):
        if v is not None:
            estados_validos = ['ACTIVO', 'INACTIVO', 'BLOQUEADO']
            if v not in estados_validos:
                raise ValueError(f'Estado debe ser uno de: {", ".join(estados_validos)}')
        return v


class UsuarioResponse(UsuarioBase):
    """Schema para respuesta de usuario (sin contraseña)"""
    id_usuario: int
    estado: str
    fecha_creacion: datetime
    fecha_actualizacion: Optional[datetime] = None
    ultimo_acceso: Optional[datetime] = None
    debe_cambiar_password: bool
    
    class Config:
        from_attributes = True


class UsuarioLogin(BaseModel):
    """Schema para login"""
    username: str = Field(..., description="Nombre de usuario o email")
    password: str = Field(..., description="Contraseña")


class CambiarPassword(BaseModel):
    """Schema para cambiar contraseña"""
    password_actual: str = Field(..., description="Contraseña actual")
    password_nueva: str = Field(..., min_length=8, description="Nueva contraseña")
    password_confirmacion: str = Field(..., description="Confirmar nueva contraseña")
    
    @validator('password_confirmacion')
    def passwords_coinciden(cls, v, values):
        if 'password_nueva' in values and v != values['password_nueva']:
            raise ValueError('Las contraseñas no coinciden')
        return v


class Token(BaseModel):
    """Schema para token JWT"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 86400  # 24 horas en segundos
    user: UsuarioResponse


class TokenData(BaseModel):
    """Schema para datos decodificados del token"""
    username: Optional[str] = None
    user_id: Optional[int] = None
    rol: Optional[str] = None
    exp: Optional[datetime] = None


class LoginResponse(BaseModel):
    """Schema para respuesta de login exitoso o error"""
    success: bool
    message: str
    data: Optional[Token] = None
    error: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Login exitoso",
                "token": {
                    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "token_type": "bearer",
                    "expires_in": 86400,
                    "user": {
                        "id_usuario": 1,
                        "username": "admin",
                        "email": "admin@sistema.com",
                        "nombre_completo": "Administrador del Sistema",
                        "rol": "Administrador",
                        "estado": "ACTIVO"
                    }
                }
            }
        }


class ErrorResponse(BaseModel):
    """Schema para respuestas de error"""
    success: bool = False
    message: str
    detail: Optional[str] = None
