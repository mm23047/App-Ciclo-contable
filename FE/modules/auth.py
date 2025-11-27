"""
Módulo de autenticación para el sistema contable.
Gestiona el inicio de sesión y control de acceso.
"""
import streamlit as st
import requests
import hashlib
from typing import Optional, Dict, Any


def hash_password(password: str) -> str:
    """Generar hash de contraseña"""
    return hashlib.sha256(password.encode()).hexdigest()


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
    
    # Formulario de login
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
                    st.balloons()
                    st.rerun()
                else:
                    st.error("❌ Usuario o contraseña incorrectos")
            else:
                st.warning("⚠️ Por favor complete todos los campos")
    
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


def authenticate_user(backend_url: str, username: str, password: str) -> bool:
    """
    Autenticar usuario contra el backend.
    Por ahora usa autenticación local, pero puede extenderse al backend.
    """
    
    # Usuarios de demostración (temporal - debería venir del backend)
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
    
    # Verificar credenciales
    if username in demo_users:
        user_data = demo_users[username]
        if user_data["password"] == password:
            # Guardar información del usuario (sin la contraseña)
            user_info = {
                "username": username,
                "name": user_data["name"],
                "role": user_data["role"],
                "email": user_data["email"]
            }
            login_user(username, user_info)
            return True
    
    return False


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
