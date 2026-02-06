"""
Módulo Streamlit para gestión del Catálogo de Cuentas.
Permite CRUD completo con jerarquía de cuentas.
"""
import streamlit as st
import requests
import pandas as pd
from typing import Dict, Any, List

def render_page(backend_url: str):
    """Renderizar página del catálogo de cuentas"""
    
    st.header("📚 Catálogo de Cuentas")
    st.markdown("Gestión completa del plan contable con jerarquía de cuentas")
    
    # Tabs para organizar funcionalidades
    tab1, tab2, tab3 = st.tabs(["📋 Ver Cuentas", "➕ Nueva Cuenta", "🔧 Gestionar"])
    
    with tab1:
        mostrar_catalogo(backend_url)
    
    with tab2:
        crear_cuenta(backend_url)
    
    with tab3:
        gestionar_cuentas(backend_url)

def mostrar_catalogo(backend_url: str):
    """Mostrar catálogo de cuentas con filtros"""
    
    st.subheader("Catálogo de Cuentas")
    
    # Filtros en un expander para mejor organización
    with st.expander("🔍 Filtros de Búsqueda", expanded=True):
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            filtro_tipo = st.selectbox(
                "Tipo de Cuenta:",
                ["Todos", "Activo", "Pasivo", "Capital", "Ingreso", "Egreso"],
                key="filtro_tipo_catalogo"
            )
        
        with col2:
            filtro_estado = st.selectbox(
                "Estado:",
                ["Todos", "ACTIVA", "INACTIVA"],
                key="filtro_estado_catalogo"
            )
        
        with col3:
            filtro_movimientos = st.selectbox(
                "Acepta Movimientos:",
                ["Todos", "Sí", "No"],
                key="filtro_movimientos_catalogo"
            )
        
        with col4:
            filtro_nivel = st.selectbox(
                "Nivel:",
                ["Todos", "1", "2", "3", "4", "5"],
                key="filtro_nivel_catalogo"
            )
        
        buscar_codigo = st.text_input(
            "🔎 Buscar por código o nombre:", 
            placeholder="Ej: 1101 o Caja",
            key="buscar_codigo_catalogo"
        )
        
        # Botón para aplicar filtros (opcional, ya que Streamlit refresca automáticamente)
        st.caption("Los filtros se aplican automáticamente")
    
    try:
        # Construir parámetros de consulta
        params = {}
        
        if filtro_tipo != "Todos":
            params["tipo_cuenta"] = filtro_tipo
        
        if filtro_estado != "Todos":
            params["estado"] = filtro_estado
        
        if filtro_movimientos == "Sí":
            params["acepta_movimientos"] = True
        elif filtro_movimientos == "No":
            params["acepta_movimientos"] = False
        
        if filtro_nivel != "Todos":
            params["nivel"] = int(filtro_nivel)
        
        if buscar_codigo:
            params["codigo_like"] = buscar_codigo
        
        # Realizar petición al backend
        response = requests.get(f"{backend_url}/api/catalogo-cuentas", params=params)
        
        if response.status_code == 200:
            cuentas = response.json()
            
            if cuentas:
                # Configuración de paginación
                total_cuentas = len(cuentas)
                
                col_info, col_items = st.columns([3, 1])
                with col_info:
                    st.info(f"📊 **Total de cuentas:** {total_cuentas}")
                with col_items:
                    items_per_page = st.selectbox(
                        "Cuentas por página:",
                        options=[20, 50, 100, 200],
                        index=0,  # 20 por defecto
                        key="items_per_page_catalogo"
                    )
                
                total_pages = (total_cuentas + items_per_page - 1) // items_per_page
                
                # Inicializar página actual
                if 'current_page_catalogo' not in st.session_state:
                    st.session_state.current_page_catalogo = 1
                
                # Ajustar página si está fuera de rango
                if st.session_state.current_page_catalogo > total_pages:
                    st.session_state.current_page_catalogo = total_pages
                
                # Calcular índices
                start_idx = (st.session_state.current_page_catalogo - 1) * items_per_page
                end_idx = min(start_idx + items_per_page, total_cuentas)
                
                # Obtener cuentas de la página actual
                cuentas_pagina = cuentas[start_idx:end_idx]
                
                # Crear DataFrame para mejor visualización
                df_cuentas = pd.DataFrame(cuentas_pagina)
                
                # Organizar columnas
                columnas_mostrar = [
                    'codigo_cuenta', 'nombre_cuenta', 'tipo_cuenta', 
                    'acepta_movimientos', 'estado', 'nivel_cuenta', 'cuenta_padre'
                ]
                
                df_display = df_cuentas[columnas_mostrar].copy()
                
                # Crear una columna de jerarquía visual
                df_display['jerarquia'] = df_display.apply(lambda row: 
                    '  ' * (row['nivel_cuenta'] - 1) + '└─ ' + row['nombre_cuenta'] 
                    if row['nivel_cuenta'] > 1 else row['nombre_cuenta'], axis=1)
                
                # Encontrar nombres de cuentas padre
                def get_padre_nombre(cuenta_padre_id):
                    if cuenta_padre_id is None:
                        return "---"
                    padre = df_cuentas[df_cuentas['id_cuenta'] == cuenta_padre_id]
                    return padre['nombre_cuenta'].iloc[0] if len(padre) > 0 else "---"
                
                df_display['padre_nombre'] = df_display['cuenta_padre'].apply(get_padre_nombre)
                
                # Reorganizar columnas para mostrar
                df_final = df_display[['codigo_cuenta', 'jerarquia', 'tipo_cuenta', 'padre_nombre', 'acepta_movimientos', 'estado', 'nivel_cuenta']].copy()
                df_final.columns = [
                    'Código', 'Nombre (Jerarquía)', 'Tipo', 'Cuenta Padre', 'Acepta Mov.', 'Estado', 'Nivel'
                ]
                
                # Mostrar tabla con formato
                st.dataframe(
                    df_final,
                    width="stretch",
                    hide_index=True
                )
                
                # Mostrar rango
                st.caption(f"Mostrando cuentas {start_idx + 1} - {end_idx} de {total_cuentas}")
                
                # Controles de paginación
                if total_pages > 1:
                    st.markdown("---")
                    col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])
                    
                    with col1:
                        if st.button("⏮️ Primera", key="first_catalogo", use_container_width=True, disabled=st.session_state.current_page_catalogo == 1):
                            st.session_state.current_page_catalogo = 1
                            st.rerun()
                    
                    with col2:
                        if st.button("◀️ Anterior", key="prev_catalogo", use_container_width=True, disabled=st.session_state.current_page_catalogo == 1):
                            st.session_state.current_page_catalogo -= 1
                            st.rerun()
                    
                    with col3:
                        st.markdown(f"<div style='text-align: center; padding: 8px;'><strong>Página {st.session_state.current_page_catalogo} de {total_pages}</strong></div>", unsafe_allow_html=True)
                    
                    with col4:
                        if st.button("▶️ Siguiente", key="next_catalogo", use_container_width=True, disabled=st.session_state.current_page_catalogo == total_pages):
                            st.session_state.current_page_catalogo += 1
                            st.rerun()
                    
                    with col5:
                        if st.button("⏭️ Última", key="last_catalogo", use_container_width=True, disabled=st.session_state.current_page_catalogo == total_pages):
                            st.session_state.current_page_catalogo = total_pages
                            st.rerun()
                
                st.markdown("---")
                
                # Métricas (usando todas las cuentas, no solo la página)
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Cuentas", total_cuentas)
                
                with col2:
                    activas = len([c for c in cuentas if c['estado'] == 'ACTIVA'])
                    st.metric("Cuentas Activas", activas)
                
                with col3:
                    con_movimientos = len([c for c in cuentas if c['acepta_movimientos']])
                    st.metric("Acepta Movimientos", con_movimientos)
                
                with col4:
                    nivel_max = max([c['nivel_cuenta'] or 0 for c in cuentas])
                    st.metric("Nivel Máximo", nivel_max)
                
            else:
                st.info("No se encontraron cuentas con los filtros aplicados")
                
        else:
            st.error(f"Error al obtener cuentas: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        st.error(f"Error de conexión con el backend: {e}")

def crear_cuenta(backend_url: str):
    """Formulario para crear nueva cuenta"""
    
    st.subheader("Crear Nueva Cuenta")
    
    # Formulario de creación
    with st.form("form_nueva_cuenta", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            codigo_cuenta = st.text_input(
                "Código de Cuenta*", 
                placeholder="Ej: 1101001",
                help="Código único que identifica la cuenta"
            )
            
            nombre_cuenta = st.text_input(
                "Nombre de Cuenta*",
                placeholder="Ej: Caja General",
                help="Nombre descriptivo de la cuenta"
            )
            
            tipo_cuenta = st.selectbox(
                "Tipo de Cuenta*",
                ["Activo", "Pasivo", "Capital", "Ingreso", "Egreso"]
            )
        
        with col2:
            # Obtener cuentas padre disponibles
            try:
                response_padre = requests.get(f"{backend_url}/api/catalogo-cuentas")
                cuentas_padre = response_padre.json() if response_padre.status_code == 200 else []
                
                # Mostrar todas las cuentas como opciones de padre
                # En un sistema contable real, cualquier cuenta puede ser padre de otra
                opciones_padre = ["Sin cuenta padre"] + [
                    f"{c['codigo_cuenta']} - {c['nombre_cuenta']} ({'Grupo' if not c['acepta_movimientos'] else 'Detalle'})" 
                    for c in cuentas_padre 
                ]
            except:
                opciones_padre = ["Sin cuenta padre"]
            
            cuenta_padre = st.selectbox(
                "Cuenta Padre", 
                opciones_padre,
                help="Selecciona la cuenta padre para crear una jerarquía. Las cuentas de grupo son más apropiadas como padres."
            )
            
            acepta_movimientos = st.checkbox(
                "Acepta Movimientos", 
                value=True,
                help="Si la cuenta puede tener asientos contables directos"
            )
            
            estado = st.selectbox(
                "Estado",
                ["ACTIVA", "INACTIVA"],
                index=0
            )
        
        descripcion = st.text_area(
            "Descripción",
            placeholder="Descripción opcional de la cuenta...",
            height=100
        )
        
        submit_button = st.form_submit_button("💾 Crear Cuenta", width="stretch")
        
        if submit_button:
            if codigo_cuenta and nombre_cuenta:
                # Preparar datos
                cuenta_padre_id = None
                if cuenta_padre != "Sin cuenta padre":
                    # Extraer el código de cuenta del formato "CODIGO - NOMBRE (Tipo)"
                    codigo_padre = cuenta_padre.split(" - ")[0]
                    cuenta_padre_obj = next((c for c in cuentas_padre if c['codigo_cuenta'] == codigo_padre), None)
                    if cuenta_padre_obj:
                        cuenta_padre_id = cuenta_padre_obj['id_cuenta']
                
                datos_cuenta = {
                    "codigo_cuenta": codigo_cuenta,
                    "nombre_cuenta": nombre_cuenta,
                    "tipo_cuenta": tipo_cuenta,
                    "cuenta_padre": cuenta_padre_id,
                    "acepta_movimientos": acepta_movimientos,
                    "estado": estado,
                    "descripcion": descripcion if descripcion else None
                }
                
                try:
                    response = requests.post(
                        f"{backend_url}/api/catalogo-cuentas",
                        json=datos_cuenta
                    )
                    
                    if response.status_code in [200, 201]:
                        st.success("✅ Cuenta creada exitosamente")
                        st.rerun()
                    else:
                        error_detail = response.json().get('detail', 'Error desconocido')
                        st.error(f"❌ Error al crear cuenta: {error_detail}")
                        
                except requests.exceptions.RequestException as e:
                    st.error(f"❌ Error de conexión: {e}")
            else:
                st.warning("⚠️ Por favor completa los campos obligatorios")

def gestionar_cuentas(backend_url: str):
    """Gestionar cuentas existentes"""
    
    st.subheader("Gestionar Cuentas Existentes")
    
    try:
        # Obtener todas las cuentas
        response = requests.get(f"{backend_url}/api/catalogo-cuentas")
        
        if response.status_code == 200:
            cuentas = response.json()
            
            if cuentas:
                # Selector de cuenta
                opciones_cuentas = [
                    f"{c['codigo_cuenta']} - {c['nombre_cuenta']}" 
                    for c in cuentas
                ]
                
                cuenta_seleccionada = st.selectbox(
                    "Seleccionar cuenta para editar:",
                    opciones_cuentas
                )
                
                if cuenta_seleccionada:
                    # Encontrar la cuenta seleccionada
                    codigo_seleccionado = cuenta_seleccionada.split(" - ")[0]
                    cuenta_obj = next((c for c in cuentas if c['codigo_cuenta'] == codigo_seleccionado), None)
                    
                    if cuenta_obj:
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            editar_cuenta(backend_url, cuenta_obj, cuentas)
                        
                        with col2:
                            mostrar_detalles_cuenta(cuenta_obj)
            else:
                st.info("No hay cuentas para gestionar")
                
        else:
            st.error(f"Error al obtener cuentas: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        st.error(f"Error de conexión: {e}")

def editar_cuenta(backend_url: str, cuenta: Dict[str, Any], todas_las_cuentas: List[Dict]):
    """Formulario para editar cuenta"""
    
    st.write("**Editar Cuenta**")
    
    with st.form("form_editar_cuenta"):
        nuevo_nombre = st.text_input(
            "Nombre de Cuenta",
            value=cuenta['nombre_cuenta']
        )
        
        nuevo_estado = st.selectbox(
            "Estado",
            ["ACTIVA", "INACTIVA"],
            index=0 if cuenta['estado'] == 'ACTIVA' else 1
        )
        
        nueva_descripcion = st.text_area(
            "Descripción",
            value=cuenta.get('descripcion', '') or ''
        )
        
        submit_editar = st.form_submit_button("🔄 Actualizar Cuenta")
        
        if submit_editar:
            datos_actualizacion = {
                "nombre_cuenta": nuevo_nombre,
                "estado": nuevo_estado,
                "descripcion": nueva_descripcion if nueva_descripcion else None
            }
            
            try:
                response = requests.put(
                    f"{backend_url}/api/catalogo-cuentas/{cuenta['id_cuenta']}",
                    json=datos_actualizacion
                )
                
                if response.status_code == 200:
                    st.success("✅ Cuenta actualizada exitosamente")
                    st.rerun()
                else:
                    error_detail = response.json().get('detail', 'Error desconocido')
                    st.error(f"❌ Error al actualizar: {error_detail}")
                    
            except requests.exceptions.RequestException as e:
                st.error(f"❌ Error de conexión: {e}")

def mostrar_detalles_cuenta(cuenta: Dict[str, Any]):
    """Mostrar detalles de la cuenta seleccionada"""
    
    st.write("**Detalles de la Cuenta**")
    
    # Información en formato de métricas y texto
    st.metric("Código", cuenta['codigo_cuenta'])
    st.metric("Tipo", cuenta['tipo_cuenta'])
    
    if cuenta.get('nivel_cuenta'):
        st.metric("Nivel Jerárquico", cuenta['nivel_cuenta'])
    
    # Estados como badges
    col1, col2 = st.columns(2)
    
    with col1:
        if cuenta['estado'] == 'ACTIVA':
            st.success("🟢 ACTIVA")
        else:
            st.error("🔴 INACTIVA")
    
    with col2:
        if cuenta['acepta_movimientos']:
            st.info("📝 Acepta Movimientos")
        else:
            st.warning("🚫 Solo Agrupadora")
    
    # Descripción si existe
    if cuenta.get('descripcion'):
        st.write("**Descripción:**")
        st.write(cuenta['descripción'])
