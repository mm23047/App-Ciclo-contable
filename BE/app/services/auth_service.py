"""
Servicio de Autenticación para el Sistema Contable.
Maneja toda la lógica de autenticación, autorización y seguridad.
"""
from datetime import datetime, timedelta
from typing import Optional
import bcrypt
import jwt
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.usuario import Usuario
from app.schemas.usuario import UsuarioCreate, UsuarioLogin, Token, CambiarPassword

# Configuración de seguridad
SECRET_KEY = "sistema-contable-secret-key-2025-change-in-production"  # ⚠️ CAMBIAR EN PRODUCCIÓN
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24
MAX_INTENTOS_LOGIN = 5
TIEMPO_BLOQUEO_MINUTOS = 30


class AuthService:
    """
    Servicio de autenticación y seguridad.
    
    Provee métodos para:
    - Hash y verificación de contraseñas
    - Generación y validación de tokens JWT
    - Login y logout de usuarios
    - Registro de usuarios
    - Cambio de contraseñas
    - Gestión de bloqueos por intentos fallidos
    """
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hashear contraseña usando bcrypt.
        
        Args:
            password: Contraseña en texto plano
            
        Returns:
            Hash de la contraseña
        """
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Verificar contraseña contra su hash.
        
        Args:
            plain_password: Contraseña en texto plano
            hashed_password: Hash almacenado en BD
            
        Returns:
            True si la contraseña es correcta
        """
        try:
            return bcrypt.checkpw(
                plain_password.encode('utf-8'),
                hashed_password.encode('utf-8')
            )
        except Exception:
            return False
    
    @staticmethod
    def create_access_token(
        data: dict,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Crear token JWT para autenticación.
        
        Args:
            data: Datos a incluir en el token (user_id, username, rol)
            expires_delta: Tiempo de expiración personalizado
            
        Returns:
            Token JWT codificado
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),  # Issued at
            "type": "access"
        })
        
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def decode_token(token: str) -> dict:
        """
        Decodificar y validar token JWT.
        
        Args:
            token: Token JWT a decodificar
            
        Returns:
            Payload del token
            
        Raises:
            HTTPException: Si el token es inválido o expirado
        """
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expirado. Por favor inicie sesión nuevamente.",
                headers={"WWW-Authenticate": "Bearer"}
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido. Por favor inicie sesión nuevamente.",
                headers={"WWW-Authenticate": "Bearer"}
            )
    
    @staticmethod
    def registrar_usuario(db: Session, usuario_data: UsuarioCreate) -> Usuario:
        """
        Registrar un nuevo usuario en el sistema.
        
        Args:
            db: Sesión de base de datos
            usuario_data: Datos del nuevo usuario
            
        Returns:
            Usuario creado
            
        Raises:
            HTTPException: Si el username o email ya existen
        """
        # Verificar si el username ya existe
        usuario_existente = db.query(Usuario).filter(
            Usuario.username == usuario_data.username.lower()
        ).first()
        
        if usuario_existente:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El nombre de usuario '{usuario_data.username}' ya está registrado"
            )
        
        # Verificar si el email ya existe
        email_existente = db.query(Usuario).filter(
            Usuario.email == usuario_data.email.lower()
        ).first()
        
        if email_existente:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El correo electrónico '{usuario_data.email}' ya está registrado"
            )
        
        # Hashear contraseña
        hashed_password = AuthService.hash_password(usuario_data.password)
        
        # Crear nuevo usuario
        nuevo_usuario = Usuario(
            username=usuario_data.username.lower(),
            email=usuario_data.email.lower(),
            password_hash=hashed_password,
            nombre_completo=usuario_data.nombre_completo,
            rol=usuario_data.rol,
            estado='ACTIVO',
            intentos_fallidos=0
        )
        
        db.add(nuevo_usuario)
        db.commit()
        db.refresh(nuevo_usuario)
        
        return nuevo_usuario
    
    @staticmethod
    def login(db: Session, credentials: UsuarioLogin) -> Token:
        """
        Autenticar usuario y generar token.
        
        Args:
            db: Sesión de base de datos
            credentials: Credenciales de login (username/email y password)
            
        Returns:
            Token JWT y datos del usuario
            
        Raises:
            HTTPException: Si las credenciales son incorrectas o el usuario está bloqueado
        """
        # Buscar usuario por username o email
        username_lower = credentials.username.lower()
        usuario = db.query(Usuario).filter(
            (Usuario.username == username_lower) |
            (Usuario.email == username_lower)
        ).first()
        
        # Si no existe el usuario, retornar error genérico (seguridad)
        if not usuario:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario o contraseña incorrectos"
            )
        
        # Verificar si el usuario está bloqueado temporalmente
        if usuario.bloqueado_hasta and usuario.bloqueado_hasta > datetime.utcnow():
            tiempo_restante = (usuario.bloqueado_hasta - datetime.utcnow()).seconds // 60 + 1
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Usuario bloqueado temporalmente. Intente nuevamente en {tiempo_restante} minuto(s)"
            )
        
        # Verificar estado del usuario
        if usuario.estado == 'INACTIVO':
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Usuario inactivo. Contacte al administrador del sistema"
            )
        
        if usuario.estado == 'BLOQUEADO':
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Usuario bloqueado permanentemente. Contacte al administrador del sistema"
            )
        
        # Verificar contraseña
        if not AuthService.verify_password(credentials.password, usuario.password_hash):
            # Incrementar contador de intentos fallidos
            usuario.intentos_fallidos += 1
            
            # Si alcanza el máximo de intentos, bloquear temporalmente
            if usuario.intentos_fallidos >= MAX_INTENTOS_LOGIN:
                usuario.bloqueado_hasta = datetime.utcnow() + timedelta(
                    minutes=TIEMPO_BLOQUEO_MINUTOS
                )
                db.commit()
                
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Demasiados intentos fallidos. Usuario bloqueado por {TIEMPO_BLOQUEO_MINUTOS} minutos"
                )
            
            db.commit()
            
            intentos_restantes = MAX_INTENTOS_LOGIN - usuario.intentos_fallidos
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Usuario o contraseña incorrectos. Intentos restantes: {intentos_restantes}"
            )
        
        # Login exitoso - Resetear intentos fallidos y actualizar último acceso
        usuario.intentos_fallidos = 0
        usuario.bloqueado_hasta = None
        usuario.ultimo_acceso = datetime.utcnow()
        db.commit()
        db.refresh(usuario)
        
        # Generar token JWT
        access_token = AuthService.create_access_token(
            data={
                "user_id": usuario.id_usuario,
                "username": usuario.username,
                "rol": usuario.rol,
                "email": usuario.email
            }
        )
        
        # Retornar token y datos del usuario
        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_HOURS * 3600,  # En segundos
            user=usuario
        )
    
    @staticmethod
    def obtener_usuario_actual(db: Session, token: str) -> Usuario:
        """
        Obtener usuario a partir del token JWT.
        
        Args:
            db: Sesión de base de datos
            token: Token JWT
            
        Returns:
            Usuario autenticado
            
        Raises:
            HTTPException: Si el token es inválido o el usuario no existe
        """
        # Decodificar token
        payload = AuthService.decode_token(token)
        
        # Extraer username del payload
        username = payload.get("username")
        user_id = payload.get("user_id")
        
        if not username or not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido: datos de usuario incompletos"
            )
        
        # Buscar usuario en BD
        usuario = db.query(Usuario).filter(
            Usuario.id_usuario == user_id,
            Usuario.username == username
        ).first()
        
        if not usuario:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario no encontrado o token inválido"
            )
        
        # Verificar que el usuario siga activo
        if usuario.estado != 'ACTIVO':
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Usuario inactivo o bloqueado"
            )
        
        return usuario
    
    @staticmethod
    def cambiar_password(
        db: Session,
        usuario: Usuario,
        datos_password: CambiarPassword
    ) -> dict:
        """
        Cambiar contraseña de un usuario.
        
        Args:
            db: Sesión de base de datos
            usuario: Usuario actual
            datos_password: Datos de cambio de contraseña
            
        Returns:
            Mensaje de éxito
            
        Raises:
            HTTPException: Si la contraseña actual es incorrecta
        """
        # Verificar contraseña actual
        if not AuthService.verify_password(
            datos_password.password_actual,
            usuario.password_hash
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La contraseña actual es incorrecta"
            )
        
        # Verificar que la nueva contraseña sea diferente
        if datos_password.password_actual == datos_password.password_nueva:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La nueva contraseña debe ser diferente a la actual"
            )
        
        # Actualizar contraseña
        usuario.password_hash = AuthService.hash_password(datos_password.password_nueva)
        usuario.debe_cambiar_password = False
        usuario.fecha_actualizacion = datetime.utcnow()
        
        db.commit()
        
        return {
            "success": True,
            "message": "Contraseña actualizada exitosamente"
        }
    
    @staticmethod
    def inicializar_usuarios_demo(db: Session):
        """
        Crear usuarios de demostración si no existen.
        Útil para desarrollo y pruebas.
        """
        usuarios_demo = [
            {
                "username": "admin",
                "email": "admin@sistema.com",
                "password": "admin123",
                "nombre_completo": "Administrador del Sistema",
                "rol": "Administrador"
            },
            {
                "username": "contador",
                "email": "contador@sistema.com",
                "password": "contador123",
                "nombre_completo": "Contador General",
                "rol": "Contador"
            },
            {
                "username": "usuario",
                "email": "usuario@sistema.com",
                "password": "usuario123",
                "nombre_completo": "Usuario Estándar",
                "rol": "Usuario"
            }
        ]
        
        for user_data in usuarios_demo:
            # Verificar si ya existe
            existe = db.query(Usuario).filter(
                Usuario.username == user_data["username"]
            ).first()
            
            if not existe:
                usuario_create = UsuarioCreate(**user_data)
                AuthService.registrar_usuario(db, usuario_create)
                print(f"✅ Usuario demo creado: {user_data['username']}")
