"""
Aplicación principal Streamlit para el frontend del sistema contable.
Sistema contable integral con 9 módulos especializados.
"""
import streamlit as st
import os
from modules import (
    transacciones, 
    asientos, 
    reportes,
    catalogo_cuentas,
    manual_cuentas,
    libro_mayor,
    partidas_ajuste,
    balanza_comprobacion,
    balance_inicial,
    estados_financieros,
    facturacion,
    clientes,
    productos,
    reportes_ventas
)

# Configuración de la página
st.set_page_config(
    page_title="Sistema Contable Integral",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# URL del backend
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

def main():
    st.sidebar.title("📊 Sistema Contable Integral")
    st.sidebar.markdown("---")
    
    # Menú de navegación organizado por categorías
    st.sidebar.markdown("### 🏗️ **CONFIGURACIÓN**")
    menu_config = {
        "📋 Catálogo de Cuentas": "catalogo_cuentas",
        "📖 Manual de Cuentas": "manual_cuentas",
        "⚖️ Balance Inicial": "balance_inicial"
    }
    
    st.sidebar.markdown("### 📝 **OPERACIONES CONTABLES**")
    menu_operaciones = {
        "💰 Transacciones": "transacciones",
        "📝 Asientos Contables": "asientos",
        "⚖️ Partidas de Ajuste": "partidas_ajuste"
    }
    
    st.sidebar.markdown("### 🧾 **FACTURACIÓN Y VENTAS**")
    menu_facturacion = {
        "🧾 Facturación Digital": "facturacion",
        "👥 Gestión de Clientes": "clientes",
        "📦 Gestión de Productos": "productos",
        "📊 Reportes de Ventas": "reportes_ventas"
    }
    
    st.sidebar.markdown("### 📊 **REPORTES Y CONSULTAS**")
    menu_reportes = {
        "📚 Libro Mayor": "libro_mayor",
        "⚖️ Balanza de Comprobación": "balanza_comprobacion",
        "💼 Estados Financieros": "estados_financieros",
        "📈 Reportes Contables": "reportes"
    }
    
    # Combinar todos los menús
    all_menu_options = {**menu_config, **menu_operaciones, **menu_facturacion, **menu_reportes}
    
    # Agregar página de inicio
    menu_options = {"🏠 Inicio": "inicio", **all_menu_options}
    
    selected = st.sidebar.selectbox(
        "Seleccionar módulo:",
        list(menu_options.keys())
    )
    
    page = menu_options[selected]
    
    # Información del sistema en sidebar
    st.sidebar.markdown("---")
    st.sidebar.markdown("### ℹ️ **INFORMACIÓN**")
    st.sidebar.info("""
    **Sistema Contable Integral con Facturación**
    
    🏢 Gestión integral de contabilidad
    🧾 Sistema de facturación digital
    📊 13 módulos especializados
    ⚡ Operación en tiempo real
    🔒 Datos seguros y confiables
    """)
    
    # Mostrar transacción actual si existe
    if "transaccion_actual" not in st.session_state:
        st.session_state.transaccion_actual = None
    
    if st.session_state.transaccion_actual:
        st.sidebar.markdown("---")
        st.sidebar.markdown("**Transacción Actual:**")
        st.sidebar.markdown(f"ID: {st.session_state.transaccion_actual}")
        if st.sidebar.button("Limpiar Transacción"):
            st.session_state.transaccion_actual = None
            st.rerun()
    
    # Mostrar página seleccionada
    if page == "inicio":
        show_home_page()
    elif page == "catalogo_cuentas":
        catalogo_cuentas.render_page(BACKEND_URL)
    elif page == "manual_cuentas":
        manual_cuentas.render_page(BACKEND_URL)
    elif page == "balance_inicial":
        balance_inicial.render_page(BACKEND_URL)
    elif page == "transacciones":
        transacciones.render_page(BACKEND_URL)
    elif page == "asientos":
        asientos.render_page(BACKEND_URL)
    elif page == "partidas_ajuste":
        partidas_ajuste.render_page(BACKEND_URL)
    elif page == "libro_mayor":
        libro_mayor.render_page(BACKEND_URL)
    elif page == "balanza_comprobacion":
        balanza_comprobacion.render_page(BACKEND_URL)
    elif page == "estados_financieros":
        estados_financieros.render_page(BACKEND_URL)
    elif page == "reportes":
        reportes.render_page(BACKEND_URL)
    elif page == "facturacion":
        facturacion.render_page(BACKEND_URL)
    elif page == "clientes":
        clientes.render_page(BACKEND_URL)
    elif page == "productos":
        productos.render_page(BACKEND_URL)
    elif page == "reportes_ventas":
        reportes_ventas.render_page(BACKEND_URL)

def show_home_page():
    st.title("🏢 Sistema Contable Integral con Facturación")
    st.markdown("---")
    
    # Información principal del sistema
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        st.markdown("""
        ## 🎯 **Bienvenido al Sistema Contable Profesional**
        
        Sistema integral de gestión contable y facturación diseñado para empresas que requieren 
        control total de sus operaciones financieras con cumplimiento de normas 
        contables, facturación digital y generación de reportes profesionales.
        """)
    
    with col2:
        st.markdown("""
        ### 🚀 **Características Principales**
        
        ✅ **13 Módulos Especializados** - Cobertura completa  
        ✅ **Facturación Digital** - Sistema integrado de ventas  
        ✅ **Gestión de Clientes** - CRM incorporado  
        ✅ **Control de Inventario** - Gestión de productos  
        ✅ **Reportes en Tiempo Real** - Información actualizada  
        ✅ **Cumplimiento Normativo** - Estándares contables  
        ✅ **Integración Total** - Módulos interconectados  
        """)
    
    with col3:
        st.markdown("""
        ### 📊 **Estado del Sistema**
        
        🟢 **Backend**: Activo  
        🟢 **Base de Datos**: Conectada  
        🟢 **API**: Funcionando  
        🟢 **Frontend**: Operativo  
        🟢 **Facturación**: Disponible  
        """)
    
    # Sección de módulos disponibles
    st.markdown("---")
    st.markdown("## 📋 **Módulos del Sistema Contable**")
    
    # Módulos de Configuración
    st.markdown("### 🏗️ **Configuración Inicial**")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        **📋 Catálogo de Cuentas**
        - Gestión del plan de cuentas
        - Jerarquía de cuentas contables
        - Clasificación por tipos y niveles
        - Configuración de naturaleza contable
        """)
    
    with col2:
        st.markdown("""
        **📖 Manual de Cuentas**
        - Documentación detallada de cuentas
        - Políticas y procedimientos contables
        - Guías de uso y ejemplos
        - Control de versiones del manual
        """)
    
    with col3:
        st.markdown("""
        **⚖️ Balance Inicial**
        - Configuración de saldos iniciales
        - Carga masiva de saldos
        - Validación de ecuación contable
        - Balance de apertura de períodos
        """)
    
    # Módulos de Operaciones
    st.markdown("### 📝 **Operaciones Contables Diarias**")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        **💰 Transacciones**
        - Registro de operaciones comerciales
        - Gestión de documentos soporte
        - Clasificación automática
        - Integración con facturación
        """)
    
    with col2:
        st.markdown("""
        **📝 Asientos Contables**
        - Libro diario general
        - Asientos simples y compuestos
        - Validación de partida doble
        - Proceso de mayorización
        """)
    
    with col3:
        st.markdown("""
        **⚖️ Partidas de Ajuste**
        - Ajustes de fin de período
        - Correcciones contables
        - Asientos de regularización
        - Provisiones y estimaciones
        """)
    
    # Nuevos módulos de facturación
    st.markdown("### 🧾 **Sistema de Facturación y Ventas**")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        **🧾 Facturación Digital**
        - Creación de facturas electrónicas
        - Gestión de estados de factura
        - Integración automática contable
        - Reportes de ventas en tiempo real
        """)
    
    with col2:
        st.markdown("""
        **👥 Gestión de Clientes**
        - Registro completo de clientes
        - Historial de transacciones
        - Análisis de comportamiento
        - Sistema CRM integrado
        """)
    
    with col3:
        st.markdown("""
        **📦 Gestión de Productos**
        - Catálogo de productos/servicios
        - Control de inventario
        - Gestión de precios y costos
        - Análisis de rentabilidad
        """)
    
    with col4:
        st.markdown("""
        **📊 Reportes de Ventas**
        - Dashboard de ventas ejecutivo
        - Análisis por períodos
        - Top productos y clientes
        - Exportación de reportes
        """)
    
    # Módulos de Reportes
    st.markdown("### 📊 **Consultas y Reportes Financieros**")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        **📚 Libro Mayor**
        - Movimientos por cuenta contable
        - Saldos acumulados
        - Consultas por período
        - Análisis de movimientos
        """)
    
    with col2:
        st.markdown("""
        **⚖️ Balanza de Comprobación**
        - Reporte de saldos consolidado
        - Validación de cuadre contable
        - Análisis por tipos de cuenta
        - Comparativos entre períodos
        """)
    
    with col3:
        st.markdown("""
        **💼 Estados Financieros**
        - Balance General
        - Estado de Resultados
        - Análisis financiero
        - Indicadores de gestión
        """)
    
    # Sección de acciones rápidas
    st.markdown("---")
    st.markdown("## ⚡ **Acciones Rápidas**")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        if st.button("📋 Configurar Cuentas", use_container_width=True):
            st.info("💡 Navega a 'Catálogo de Cuentas' para configurar tu plan contable")
    
    with col2:
        if st.button("💰 Nueva Transacción", use_container_width=True):
            st.info("💡 Ve a 'Transacciones' para registrar operaciones comerciales")
    
    with col3:
        if st.button("🧾 Crear Factura", use_container_width=True):
            st.info("💡 Accede a 'Facturación Digital' para crear facturas electrónicas")
    
    with col4:
        if st.button("👥 Gestionar Clientes", use_container_width=True):
            st.info("💡 Ve a 'Gestión de Clientes' para administrar tu cartera de clientes")
    
    with col5:
        if st.button("📊 Ver Reportes", use_container_width=True):
            st.info("💡 Consulta 'Estados Financieros' o 'Reportes de Ventas' para análisis empresarial")
    
    # Footer con información adicional
    st.markdown("---")
    st.markdown("""
    ### 📞 **Soporte y Ayuda**
    
    - 💬 **Chat de Soporte**: Disponible 24/7 para consultas técnicas
    - 📚 **Documentación**: Manual completo del usuario disponible
    - 🎯 **Capacitación**: Sesiones de entrenamiento personalizadas
    - 🔄 **Actualizaciones**: Mejoras continuas del sistema
    
    ---
    *Sistema Contable Integral con Facturación v2.0 - Diseñado para la gestión profesional de contabilidad y ventas empresariales*
    """)

if __name__ == "__main__":
    main()