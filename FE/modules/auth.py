"""
Módulo de autenticación para el sistema contable.
Gestiona el inicio de sesión y control de acceso.
"""
import streamlit as st
import requests
import hashlib
import time
from typing import Optional, Dict, Any


def hash_password(password: str) -> str:
    """Generar hash de contraseña"""
    return hashlib.sha256(password.encode()).hexdigest()


def get_auth_header() -> Dict[str, str]:
    """
    Obtener header de autenticación con token JWT.
    
    Returns:
        Dict con el header Authorization para requests
    """
    token = st.session_state.get('access_token')
    token_type = st.session_state.get('token_type', 'bearer')
    
    if token:
        return {"Authorization": f"{token_type.capitalize()} {token}"}
    return {}


def check_authentication() -> bool:
    """Verificar si el usuario está autenticado"""
    return st.session_state.get('authenticated', False)


def get_current_user() -> Optional[Dict[str, Any]]:
    """Obtener información del usuario actual"""
    return st.session_state.get('user', None)


def login_user(username: str, user_data: Dict[str, Any]):
    """Marcar usuario como autenticado"""
    st.session_state['authenticated'] = True
    st.session_state['user'] = user_data
    st.session_state['username'] = username


def logout_user():
    """Cerrar sesión del usuario"""
    st.session_state['authenticated'] = False
    st.session_state['user'] = None
    st.session_state['username'] = None
    st.session_state['access_token'] = None
    st.session_state['token_type'] = None


def authenticate_user(backend_url: str, username: str, password: str) -> bool:
    """
    Autenticar usuario contra el backend API.
    
    Args:
        backend_url: URL base del backend (ej: http://localhost:8000)
        username: Nombre de usuario o email
        password: Contraseña en texto plano
        
    Returns:
        True si la autenticación es exitosa, False en caso contrario
    """
    
    # Limpiar espacios en blanco
    username = username.strip()
    password = password.strip()
    
    try:
        # Llamar al endpoint de login del backend
        response = requests.post(
            f"{backend_url}/api/auth/login",
            json={
                "username": username,
                "password": password
            },
            timeout=10
        )
        
        # Si la autenticación es exitosa
        if response.status_code == 200:
            data = response.json()
            
            # Verificar que la respuesta tenga los datos esperados
            if data.get("success") and data.get("data"):
                token_data = data["data"]
                user_data = token_data.get("user", {})
                
                # Guardar token JWT en session_state
                st.session_state['access_token'] = token_data.get("access_token")
                st.session_state['token_type'] = token_data.get("token_type", "bearer")
                
                # Mapear rol del backend al formato del frontend
                role_mapping = {
                    "Administrador": "admin",
                    "Contador": "contador",
                    "Usuario": "user"
                }
                
                # Guardar información del usuario
                user_info = {
                    "id": user_data.get("id_usuario"),
                    "username": user_data.get("username"),
                    "name": user_data.get("nombre_completo"),
                    "role": role_mapping.get(user_data.get("rol"), "user"),
                    "email": user_data.get("email")
                }
                
                login_user(username, user_info)
                return True
            else:
                st.error(f"❌ {data.get('message', 'Error en la respuesta del servidor')}")
                return False
        
        # Si la autenticación falla
        elif response.status_code == 401:
            data = response.json()
            st.error(f"❌ {data.get('message', 'Credenciales incorrectas')}")
            return False
        
        # Si el usuario está bloqueado
        elif response.status_code == 403:
            data = response.json()
            st.error(f"🚫 {data.get('message', 'Usuario bloqueado')}")
            return False
        
        # Otros errores
        else:
            st.error(f"❌ Error del servidor: {response.status_code}")
            return False
    
    except requests.exceptions.Timeout:
        st.error("⏱️ Tiempo de espera agotado. Verifique su conexión.")
        return False
    
    except requests.exceptions.ConnectionError:
        st.error("🔌 No se pudo conectar al servidor. Verifique que el backend esté ejecutándose.")
        # Fallback a autenticación local para desarrollo
        st.warning("⚠️ Usando autenticación local de respaldo...")
        return authenticate_user_local(username, password)
    
    except Exception as e:
        st.error(f"❌ Error inesperado: {str(e)}")
        return False


def register_user(backend_url: str, username: str, email: str, password: str, nombre_completo: str) -> bool:
    """
    Registrar un nuevo usuario en el sistema.
    
    Args:
        backend_url: URL base del backend
        username: Nombre de usuario
        email: Email del usuario
        password: Contraseña
        nombre_completo: Nombre completo
        
    Returns:
        True si el registro es exitoso, False en caso contrario
    """
    try:
        # Llamar al endpoint de signup del backend
        response = requests.post(
            f"{backend_url}/api/auth/signup",
            json={
                "username": username,
                "email": email,
                "password": password,
                "nombre_completo": nombre_completo,
                "rol": "Usuario"  # Por defecto
            },
            timeout=10
        )
        
        # Si el registro es exitoso
        if response.status_code == 201:
            data = response.json()
            
            if data.get("success") and data.get("data"):
                token_data = data["data"]
                user_data = token_data.get("user", {})
                
                # Guardar token JWT en session_state
                st.session_state['access_token'] = token_data.get("access_token")
                st.session_state['token_type'] = token_data.get("token_type", "bearer")
                
                # Mapear rol del backend al formato del frontend
                role_mapping = {
                    "Administrador": "admin",
                    "Contador": "contador",
                    "Usuario": "user"
                }
                
                # Guardar información del usuario
                user_info = {
                    "id": user_data.get("id_usuario"),
                    "username": user_data.get("username"),
                    "name": user_data.get("nombre_completo"),
                    "role": role_mapping.get(user_data.get("rol"), "user"),
                    "email": user_data.get("email")
                }
                
                login_user(username, user_info)
                return True
            else:
                st.error(f"❌ {data.get('message', 'Error en el registro')}")
                return False
        
        # Si hay error en el registro
        elif response.status_code == 400:
            data = response.json()
            error_msg = data.get('message', data.get('detail', 'Error en el registro'))
            if 'username' in error_msg.lower() and 'registrado' in error_msg.lower():
                st.error("❌ El nombre de usuario ya está en uso")
            elif 'email' in error_msg.lower() and 'registrado' in error_msg.lower():
                st.error("❌ El email ya está registrado")
            else:
                st.error(f"❌ {error_msg}")
            return False
        
        else:
            st.error(f"❌ Error del servidor: {response.status_code}")
            return False
    
    except requests.exceptions.Timeout:
        st.error("⏱️ Tiempo de espera agotado. Verifique su conexión.")
        return False
    
    except requests.exceptions.ConnectionError:
        st.error("🔌 No se pudo conectar al servidor. Verifique que el backend esté ejecutándose.")
        return False
    
    except Exception as e:
        st.error(f"❌ Error inesperado: {str(e)}")
        return False


def authenticate_user_local(username: str, password: str) -> bool:
    """
    Autenticación local de respaldo (solo para desarrollo).
    Se usa cuando el backend no está disponible.
    """
    
    # Usuarios de demostración local (SOLO PARA DESARROLLO)
    demo_users = {
        "admin": {
            "password": "admin123",
            "name": "Administrador",
            "role": "admin",
            "email": "admin@contable.com"
        },
        "contador": {
            "password": "contador123",
            "name": "Contador General",
            "role": "contador",
            "email": "contador@contable.com"
        },
        "usuario": {
            "password": "usuario123",
            "name": "Usuario",
            "role": "user",
            "email": "usuario@contable.com"
        }
    }
    
    # Verificar credenciales localmente
    if username in demo_users:
        user_data = demo_users[username]
        if user_data["password"] == password:
            user_info = {
                "username": username,
                "name": user_data["name"],
                "role": user_data["role"],
                "email": user_data["email"]
            }
            login_user(username, user_info)
            return True
    
    return False


def render_login_page(backend_url: str):
    """Renderizar página de inicio de sesión"""
    
    # CSS personalizado para la página de login
    st.markdown("""
    <style>
        .main {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        .login-container {
            max-width: 450px;
            margin: 0 auto;
            padding: 40px;
            background: white;
            border-radius: 20px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            margin-top: 50px;
        }
        .login-header {
            text-align: center;
            margin-bottom: 30px;
        }
        .login-title {
            color: #2c3e50;
            font-size: 32px;
            font-weight: bold;
            margin-bottom: 10px;
        }
        .login-subtitle {
            color: #7f8c8d;
            font-size: 16px;
        }
        .stButton > button {
            width: 100%;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px;
            font-size: 16px;
            font-weight: bold;
            border-radius: 10px;
            margin-top: 10px;
        }
        .stButton > button:hover {
            background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }
        .stButton button[kind="secondary"] {
            background: white !important;
            color: #667eea !important;
            border: 2px solid #667eea !important;
            font-size: 14px !important;
            padding: 8px 16px !important;
        }
        .stButton button[kind="secondary"]:hover {
            background: #f0f2ff !important;
            border-color: #764ba2 !important;
            color: #764ba2 !important;
        }
        .demo-credentials {
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 10px;
            margin-top: 20px;
            border-left: 4px solid #667eea;
        }
        .demo-credentials h4 {
            color: #2c3e50;
            margin-bottom: 10px;
            font-size: 14px;
        }
        .demo-credentials p {
            margin: 5px 0;
            color: #34495e;
            font-size: 13px;
        }
        .feature-list {
            margin-top: 30px;
            padding: 20px;
            background-color: #f8f9fa;
            border-radius: 10px;
        }
        .feature-item {
            display: flex;
            align-items: center;
            margin: 10px 0;
            color: #2c3e50;
        }
        .feature-icon {
            margin-right: 10px;
            font-size: 20px;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Contenedor principal
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    
    # Header
    st.markdown("""
    <div class="login-header">
        <div style="font-size: 60px; margin-bottom: 20px;">📊</div>
        <div class="login-title">Sistema Contable</div>
        <div class="login-subtitle">Gestión Integral de Contabilidad</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Inicializar estado para mostrar/ocultar formulario de registro
    if 'mostrar_registro' not in st.session_state:
        st.session_state['mostrar_registro'] = False
    
    # Mostrar formulario según el estado
    if not st.session_state['mostrar_registro']:
        # FORMULARIO DE LOGIN (por defecto)
        with st.form("login_form", clear_on_submit=False):
            username = st.text_input(
                "👤 Usuario",
                placeholder="Ingrese su usuario",
                key="login_username"
            )
            
            password = st.text_input(
                "🔒 Contraseña",
                type="password",
                placeholder="Ingrese su contraseña",
                key="login_password"
            )
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                remember_me = st.checkbox("Recordarme", value=False)
            
            with col2:
                st.markdown("")  # Espaciado
            
            submit = st.form_submit_button("🚀 Iniciar Sesión")
            
            if submit:
                if username and password:
                    # Intentar autenticación
                    if authenticate_user(backend_url, username, password):
                        st.success("✅ Inicio de sesión exitoso!")
                        st.rerun()
                    else:
                        st.error("❌ Usuario o contraseña incorrectos")
                else:
                    st.warning("⚠️ Por favor complete todos los campos")
        
        # Enlace para mostrar formulario de registro
        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("📝 ¿No tienes cuenta? Crear una nueva", use_container_width=True, type="secondary"):
                st.session_state['mostrar_registro'] = True
                st.rerun()
    
    else:
        # FORMULARIO DE REGISTRO
        st.markdown("""
        <div style="text-align: center; margin-bottom: 20px;">
            <h3 style="color: #2c3e50;">📝 Crear Nueva Cuenta</h3>
            <p style="color: #7f8c8d; font-size: 14px;">Completa el formulario para registrarte</p>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("register_form", clear_on_submit=False):
            nombre_completo = st.text_input(
                "👤 Nombre Completo",
                placeholder="Ej: Juan Pérez",
                key="reg_nombre"
            )
            
            username_reg = st.text_input(
                "🆔 Usuario",
                placeholder="Nombre de usuario único (mínimo 3 caracteres)",
                key="reg_username"
            )
            
            email = st.text_input(
                "📧 Email",
                placeholder="ejemplo@correo.com",
                key="reg_email"
            )
            
            password_reg = st.text_input(
                "🔒 Contraseña",
                type="password",
                placeholder="Mínimo 8 caracteres (letras y números)",
                key="reg_password"
            )
            
            password_confirm = st.text_input(
                "🔒 Confirmar Contraseña",
                type="password",
                placeholder="Repita su contraseña",
                key="reg_password_confirm"
            )
            
            col1, col2 = st.columns(2)
            with col1:
                submit_register = st.form_submit_button("✨ Crear Cuenta", use_container_width=True)
            with col2:
                cancel_register = st.form_submit_button("↩️ Volver al Login", use_container_width=True)
            
            if cancel_register:
                st.session_state['mostrar_registro'] = False
                st.rerun()
            
            if submit_register:
                # Validaciones
                if not all([nombre_completo, username_reg, email, password_reg, password_confirm]):
                    st.error("⚠️ Por favor complete todos los campos")
                elif len(username_reg) < 3:
                    st.error("⚠️ El usuario debe tener al menos 3 caracteres")
                elif len(password_reg) < 8:
                    st.error("⚠️ La contraseña debe tener al menos 8 caracteres")
                elif not any(c.isdigit() for c in password_reg) or not any(c.isalpha() for c in password_reg):
                    st.error("⚠️ La contraseña debe contener letras y números")
                elif password_reg != password_confirm:
                    st.error("⚠️ Las contraseñas no coinciden")
                elif '@' not in email or '.' not in email.split('@')[-1]:
                    st.error("⚠️ Email no válido")
                else:
                    # Intentar registro
                    if register_user(backend_url, username_reg, email, password_reg, nombre_completo):
                        st.success("✅ ¡Cuenta creada exitosamente! Redirigiendo...")
                        st.session_state['mostrar_registro'] = False
                        time.sleep(1)
                        st.rerun()
    
    # Credenciales de demostración
    st.markdown("""
    <div class="demo-credentials">
        <h4>🔑 Credenciales de Demostración</h4>
        <p><strong>Admin:</strong> admin / admin123</p>
        <p><strong>Contador:</strong> contador / contador123</p>
        <p><strong>Usuario:</strong> usuario / usuario123</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Características del sistema
    st.markdown("""
    <div class="feature-list">
        <h4 style="color: #2c3e50; margin-bottom: 15px;">✨ Características Principales</h4>
        <div class="feature-item">
            <span class="feature-icon">📋</span>
            <span>Gestión completa de catálogo de cuentas</span>
        </div>
        <div class="feature-item">
            <span class="feature-icon">💰</span>
            <span>Registro de transacciones y asientos</span>
        </div>
        <div class="feature-item">
            <span class="feature-icon">📊</span>
            <span>Reportes financieros en tiempo real</span>
        </div>
        <div class="feature-item">
            <span class="feature-icon">🧾</span>
            <span>Sistema de facturación digital</span>
        </div>
        <div class="feature-item">
            <span class="feature-icon">📈</span>
            <span>Estados financieros automáticos</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Footer
    st.markdown("""
    <div style="text-align: center; margin-top: 30px; color: white; font-size: 14px;">
        <p>© 2025 Sistema Contable Integral | Todos los derechos reservados</p>
    </div>
    """, unsafe_allow_html=True)


def render_user_profile():
    """Renderizar información del usuario en el sidebar"""
    
    user = get_current_user()
    
    if user:
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 👤 Usuario Activo")
        
        # Información del usuario con estilo
        st.sidebar.markdown(f"""
        <div style="background-color: #f0f2f6; padding: 15px; border-radius: 10px; margin-bottom: 10px;">
            <p style="margin: 0; font-weight: bold; color: #2c3e50;">{user['name']}</p>
            <p style="margin: 5px 0 0 0; font-size: 12px; color: #7f8c8d;">@{user['username']}</p>
            <p style="margin: 5px 0 0 0; font-size: 12px; color: #7f8c8d;">📧 {user['email']}</p>
            <p style="margin: 5px 0 0 0; font-size: 11px;">
                <span style="background-color: #667eea; color: white; padding: 2px 8px; border-radius: 5px;">
                    {user['role'].upper()}
                </span>
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Botón de cerrar sesión
        if st.sidebar.button("🚪 Cerrar Sesión", use_container_width=True):
            logout_user()
            st.rerun()


def check_user_permission(required_role: str) -> bool:
    """
    Verificar si el usuario tiene los permisos necesarios.
    Jerarquía: admin > contador > user
    """
    
    user = get_current_user()
    
    if not user:
        return False
    
    role_hierarchy = {
        "admin": 3,
        "contador": 2,
        "user": 1
    }
    
    user_level = role_hierarchy.get(user.get('role', 'user'), 0)
    required_level = role_hierarchy.get(required_role, 0)
    
    return user_level >= required_level
