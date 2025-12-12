"""
Router de Autenticación para el Sistema Contable.
Endpoints para login, registro, logout y gestión de usuarios.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from app.db import get_db
from app.models.usuario import Usuario
from app.schemas.usuario import (
    UsuarioCreate,
    UsuarioLogin,
    UsuarioResponse,
    Token,
    CambiarPassword,
    LoginResponse,
    ErrorResponse
)
from app.services.auth_service import AuthService

router = APIRouter(
    prefix="/api/auth",
    tags=["Autenticación"]
)


def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> Usuario:
    """
    Dependencia para obtener el usuario actual desde el token JWT.
    
    Args:
        authorization: Header Authorization con formato "Bearer {token}"
        db: Sesión de base de datos
        
    Returns:
        Usuario autenticado
        
    Raises:
        HTTPException: Si no hay token o es inválido
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No se proporcionó token de autenticación",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Extraer token del header "Bearer {token}"
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Esquema de autenticación inválido. Use 'Bearer {token}'",
                headers={"WWW-Authenticate": "Bearer"}
            )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Formato de token inválido. Use 'Bearer {token}'",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return AuthService.obtener_usuario_actual(db, token)


def require_role(*roles: str):
    """
    Dependencia para requerir roles específicos.
    
    Args:
        roles: Roles permitidos (Administrador, Contador, Usuario)
        
    Returns:
        Función de dependencia que valida el rol
    """
    def role_checker(current_user: Usuario = Depends(get_current_user)) -> Usuario:
        if current_user.rol not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acceso denegado. Se requiere rol: {', '.join(roles)}"
            )
        return current_user
    return role_checker


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="Iniciar sesión",
    description="Autenticar usuario con username/email y contraseña. Retorna token JWT.",
    responses={
        200: {"description": "Login exitoso"},
        401: {"model": ErrorResponse, "description": "Credenciales incorrectas"},
        403: {"model": ErrorResponse, "description": "Usuario bloqueado"}
    }
)
def login(
    credentials: UsuarioLogin,
    db: Session = Depends(get_db)
):
    """
    Endpoint de inicio de sesión.
    
    - **username**: Username o email del usuario
    - **password**: Contraseña en texto plano
    
    Retorna token JWT válido por 24 horas.
    """
    try:
        token_data = AuthService.login(db, credentials)
        
        return LoginResponse(
            success=True,
            message="Login exitoso",
            data=token_data
        )
    
    except HTTPException as e:
        return LoginResponse(
            success=False,
            message=e.detail,
            error=e.detail
        )


@router.post(
    "/register",
    response_model=UsuarioResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar nuevo usuario",
    description="Crear un nuevo usuario en el sistema. Solo administradores.",
    responses={
        201: {"description": "Usuario creado exitosamente"},
        400: {"model": ErrorResponse, "description": "Username o email ya existen"},
        403: {"description": "Solo administradores pueden registrar usuarios"}
    }
)
def register(
    usuario_data: UsuarioCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role("Administrador"))
):
    """
    Endpoint de registro de usuarios (solo administradores).
    
    - **username**: Nombre de usuario único (3-50 caracteres)
    - **email**: Email único válido
    - **password**: Contraseña segura (8+ caracteres, letra + número)
    - **nombre_completo**: Nombre completo del usuario
    - **rol**: Rol del usuario (Administrador, Contador, Usuario)
    """
    nuevo_usuario = AuthService.registrar_usuario(db, usuario_data)
    return nuevo_usuario


@router.post(
    "/signup",
    response_model=LoginResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Auto-registro de usuario",
    description="Permite a cualquier persona crear una cuenta. El rol será 'Usuario' por defecto.",
    responses={
        201: {"description": "Usuario creado y autenticado exitosamente"},
        400: {"model": ErrorResponse, "description": "Username o email ya existen"}
    }
)
def signup(
    usuario_data: UsuarioCreate,
    db: Session = Depends(get_db)
):
    """
    Endpoint de auto-registro público.
    
    - **username**: Nombre de usuario único (3-50 caracteres)
    - **email**: Email único válido
    - **password**: Contraseña segura (8+ caracteres, letra + número)
    - **nombre_completo**: Nombre completo del usuario
    
    El rol se asigna automáticamente como 'Usuario'.
    Retorna token JWT para iniciar sesión automáticamente.
    """
    # Forzar rol a 'Usuario' para auto-registro público
    usuario_data.rol = "Usuario"
    
    try:
        # Crear usuario
        nuevo_usuario = AuthService.registrar_usuario(db, usuario_data)
        
        # Generar token para auto-login
        access_token = AuthService.create_access_token(
            data={
                "user_id": nuevo_usuario.id_usuario,
                "username": nuevo_usuario.username,
                "rol": nuevo_usuario.rol,
                "email": nuevo_usuario.email
            }
        )
        
        # Actualizar último acceso
        nuevo_usuario.ultimo_acceso = datetime.utcnow()
        db.commit()
        db.refresh(nuevo_usuario)
        
        from app.schemas.usuario import Token
        token_data = Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=86400,
            user=nuevo_usuario
        )
        
        return LoginResponse(
            success=True,
            message="Cuenta creada exitosamente. Bienvenido!",
            data=token_data
        )
    
    except HTTPException as e:
        return LoginResponse(
            success=False,
            message=e.detail,
            error=e.detail
        )


@router.get(
    "/me",
    response_model=UsuarioResponse,
    summary="Obtener usuario actual",
    description="Obtener información del usuario autenticado.",
    responses={
        200: {"description": "Información del usuario"},
        401: {"model": ErrorResponse, "description": "Token inválido o expirado"}
    }
)
def get_me(current_user: Usuario = Depends(get_current_user)):
    """
    Endpoint para obtener datos del usuario actual.
    
    Requiere token JWT válido en el header Authorization.
    """
    return current_user


@router.post(
    "/logout",
    summary="Cerrar sesión",
    description="Cerrar sesión del usuario actual.",
    responses={
        200: {"description": "Sesión cerrada exitosamente"}
    }
)
def logout(current_user: Usuario = Depends(get_current_user)):
    """
    Endpoint de cierre de sesión.
    
    Nota: En JWT no hay logout del lado del servidor.
    El cliente debe eliminar el token.
    """
    return {
        "success": True,
        "message": f"Sesión cerrada para usuario '{current_user.username}'"
    }


@router.post(
    "/cambiar-password",
    summary="Cambiar contraseña",
    description="Cambiar la contraseña del usuario autenticado.",
    responses={
        200: {"description": "Contraseña actualizada exitosamente"},
        400: {"model": ErrorResponse, "description": "Contraseña actual incorrecta"},
        401: {"model": ErrorResponse, "description": "Token inválido o expirado"}
    }
)
def cambiar_password(
    datos_password: CambiarPassword,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Endpoint para cambiar contraseña.
    
    - **password_actual**: Contraseña actual del usuario
    - **password_nueva**: Nueva contraseña (8+ caracteres, letra + número)
    
    Requiere autenticación con token JWT.
    """
    resultado = AuthService.cambiar_password(db, current_user, datos_password)
    return resultado


@router.get(
    "/usuarios",
    response_model=list[UsuarioResponse],
    summary="Listar todos los usuarios",
    description="Obtener lista de todos los usuarios. Solo administradores.",
    responses={
        200: {"description": "Lista de usuarios"},
        403: {"description": "Solo administradores pueden ver la lista de usuarios"}
    }
)
def listar_usuarios(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role("Administrador"))
):
    """
    Endpoint para listar todos los usuarios (solo administradores).
    
    Retorna información de todos los usuarios registrados.
    """
    usuarios = db.query(Usuario).order_by(Usuario.fecha_creacion.desc()).all()
    return usuarios


@router.patch(
    "/usuarios/{id_usuario}/estado",
    response_model=UsuarioResponse,
    summary="Cambiar estado de usuario",
    description="Activar, desactivar o bloquear un usuario. Solo administradores.",
    responses={
        200: {"description": "Estado actualizado exitosamente"},
        403: {"description": "Solo administradores pueden cambiar el estado"},
        404: {"description": "Usuario no encontrado"}
    }
)
def cambiar_estado_usuario(
    id_usuario: int,
    nuevo_estado: str,  # ACTIVO, INACTIVO, BLOQUEADO
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role("Administrador"))
):
    """
    Endpoint para cambiar el estado de un usuario (solo administradores).
    
    - **id_usuario**: ID del usuario a modificar
    - **nuevo_estado**: Nuevo estado (ACTIVO, INACTIVO, BLOQUEADO)
    
    No se puede modificar el propio estado del administrador.
    """
    # Verificar que no se está modificando a sí mismo
    if id_usuario == current_user.id_usuario:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puede modificar su propio estado"
        )
    
    # Validar estado
    estados_validos = ["ACTIVO", "INACTIVO", "BLOQUEADO"]
    if nuevo_estado not in estados_validos:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Estado inválido. Use: {', '.join(estados_validos)}"
        )
    
    # Buscar usuario
    usuario = db.query(Usuario).filter(Usuario.id_usuario == id_usuario).first()
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Usuario con ID {id_usuario} no encontrado"
        )
    
    # Actualizar estado
    usuario.estado = nuevo_estado
    if nuevo_estado == "ACTIVO":
        usuario.intentos_fallidos = 0
        usuario.bloqueado_hasta = None
    
    db.commit()
    db.refresh(usuario)
    
    return usuario


@router.delete(
    "/usuarios/{id_usuario}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar usuario",
    description="Eliminar un usuario del sistema. Solo administradores.",
    responses={
        204: {"description": "Usuario eliminado exitosamente"},
        403: {"description": "Solo administradores pueden eliminar usuarios"},
        404: {"description": "Usuario no encontrado"}
    }
)
def eliminar_usuario(
    id_usuario: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role("Administrador"))
):
    """
    Endpoint para eliminar un usuario (solo administradores).
    
    - **id_usuario**: ID del usuario a eliminar
    
    No se puede eliminar el propio usuario del administrador.
    """
    # Verificar que no se está eliminando a sí mismo
    if id_usuario == current_user.id_usuario:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puede eliminar su propio usuario"
        )
    
    # Buscar usuario
    usuario = db.query(Usuario).filter(Usuario.id_usuario == id_usuario).first()
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Usuario con ID {id_usuario} no encontrado"
        )
    
    # Eliminar usuario
    db.delete(usuario)
    db.commit()
    
    return None


@router.post(
    "/inicializar-demo",
    summary="Inicializar usuarios de demostración",
    description="Crear usuarios demo para pruebas (admin, contador, usuario). Solo desarrollo.",
    responses={
        200: {"description": "Usuarios demo creados exitosamente"}
    }
)
def inicializar_usuarios_demo(db: Session = Depends(get_db)):
    """
    Endpoint para crear usuarios de demostración.
    
    Crea 3 usuarios:
    - admin / admin123 (Administrador)
    - contador / contador123 (Contador)
    - usuario / usuario123 (Usuario)
    
    ⚠️ Solo para desarrollo/pruebas. Desactivar en producción.
    """
    AuthService.inicializar_usuarios_demo(db)
    return {
        "success": True,
        "message": "Usuarios demo inicializados exitosamente",
        "usuarios": [
            {"username": "admin", "password": "admin123", "rol": "Administrador"},
            {"username": "contador", "password": "contador123", "rol": "Contador"},
            {"username": "usuario", "password": "usuario123", "rol": "Usuario"}
        ]
    }
