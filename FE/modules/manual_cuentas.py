"""
Módulo Streamlit para gestión del Manual de Cuentas.
Permite crear y mantener descripciones detalladas para cada cuenta contable.
"""
import streamlit as st
import requests
import pandas as pd
from typing import Dict, Any, List
from datetime import datetime

def render_page(backend_url: str):
    """Renderizar página del manual de cuentas"""
    
    st.header("📖 Manual de Cuentas")
    st.markdown("Gestión de descripciones detalladas y guías de uso para cada cuenta contable")
    
    # Tabs para organizar funcionalidades
    tab1, tab2, tab3 = st.tabs(["📚 Ver Manual", "✍️ Crear/Editar", "🔍 Buscar"])
    
    with tab1:
        mostrar_manual(backend_url)
    
    with tab2:
        gestionar_manual(backend_url)
    
    with tab3:
        buscar_manual(backend_url)

def mostrar_manual(backend_url: str):
    """Mostrar manual de cuentas existente"""
    
    st.subheader("Manual de Cuentas Actual")
    
    # Filtros
    col1, col2 = st.columns(2)
    
    with col1:
        # Obtener períodos disponibles
        try:
            response_periodos = requests.get(f"{backend_url}/api/periodos")
            periodos = response_periodos.json() if response_periodos.status_code == 200 else []
            
            opciones_periodos = ["Todos los períodos"] + [
                f"{p['nombre_periodo']} ({p['fecha_inicio']} - {p['fecha_fin']})"
                for p in periodos
            ]
            
            periodo_filtro = st.selectbox("Filtrar por período:", opciones_periodos)
            
        except:
            periodo_filtro = "Todos los períodos"
    
    with col2:
        orden = st.selectbox(
            "Ordenar por:",
            ["Código de Cuenta", "Nombre de Cuenta", "Fecha Creación"]
        )
    
    try:
        # Obtener manuales del backend
        params = {}
        if periodo_filtro != "Todos los períodos":
            # Extraer ID del período seleccionado
            periodo_nombre = periodo_filtro.split(" (")[0]
            periodo_obj = next((p for p in periodos if p['nombre_periodo'] == periodo_nombre), None)
            if periodo_obj:
                params["id_periodo"] = periodo_obj['id_periodo']
        
        response = requests.get(f"{backend_url}/api/manual-cuentas")
        
        if response.status_code == 200:
            manuales = response.json()
            
            if manuales:
                # Mostrar manuales
                for manual in manuales:
                    with st.expander(f"📄 {manual.get('codigo_cuenta', 'N/A')} - {manual.get('nombre_cuenta', manual['descripcion_cuenta'][:50])}"):
                        mostrar_detalle_manual(manual, backend_url)
                
                # Resumen estadístico
                st.markdown("---")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Total de Manuales", len(manuales))
                
                with col2:
                    con_ejemplos = len([m for m in manuales if m.get('ejemplos_uso')])
                    st.metric("Con Ejemplos", con_ejemplos)
                
                with col3:
                    ultimos_30 = len([
                        m for m in manuales 
                        if m.get('fecha_creacion') and 
                        (datetime.now() - datetime.fromisoformat(m['fecha_creacion'].replace('Z', '+00:00'))).days <= 30
                    ])
                    st.metric("Creados últimos 30 días", ultimos_30)
                
            else:
                st.info("No se encontraron manuales de cuentas")
                
                # Sugerir crear el primer manual
                if st.button("📝 Crear el primer manual de cuenta"):
                    st.session_state.tab_activo = 1  # Cambiar a tab de crear
                    st.rerun()
                
        else:
            st.error(f"Error al obtener manuales: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        st.error(f"Error de conexión con el backend: {e}")

def mostrar_detalle_manual(manual: Dict[str, Any], backend_url: str):
    """Mostrar detalles de un manual específico"""
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Información principal
        st.markdown(f"**Descripción:** {manual.get('descripcion_cuenta', 'No disponible')}")
        
        if manual.get('naturaleza_cuenta'):
            color = "green" if manual['naturaleza_cuenta'] == 'DEUDORA' else "blue"
            st.markdown(f"**Naturaleza:** :{color}[{manual['naturaleza_cuenta']}]")
        
        if manual.get('instrucciones_uso'):
            st.markdown("**Instrucciones de Uso:**")
            st.write(manual['instrucciones_uso'])
        
        if manual.get('ejemplos_uso'):
            st.markdown("**Ejemplos de Uso:**")
            st.write(manual['ejemplos_uso'])
        
        if manual.get('normativa_aplicable'):
            st.markdown("**Normativa Aplicable:**")
            st.write(manual['normativa_aplicable'])
    
    with col2:
        # Información de metadatos
        st.markdown("**📊 Información del Manual**")
        
        if manual.get('fecha_creacion'):
            fecha_creacion = datetime.fromisoformat(manual['fecha_creacion'].replace('Z', '+00:00'))
            st.markdown(f"**Creado:** {fecha_creacion.strftime('%d/%m/%Y')}")
        
        if manual.get('usuario_creacion'):
            st.markdown(f"**Por:** {manual['usuario_creacion']}")
        
        if manual.get('version'):
            st.markdown(f"**Versión:** {manual['version']}")
        
        # Botón de edición
        if st.button(f"✏️ Editar", key=f"edit_{manual['id_manual']}"):
            st.session_state.manual_editar = manual
            st.session_state.tab_activo = 1
            st.rerun()

def gestionar_manual(backend_url: str):
    """Crear o editar manual de cuenta"""
    
    # Verificar si hay un manual para editar en session_state
    manual_editar = st.session_state.get('manual_editar', None)
    
    if manual_editar:
        st.subheader(f"✏️ Editar Manual - {manual_editar.get('codigo_cuenta', 'N/A')}")
        
        if st.button("⬅️ Cancelar Edición"):
            del st.session_state.manual_editar
            st.rerun()
    else:
        st.subheader("📝 Crear Nuevo Manual de Cuenta")
    
    # Obtener cuentas disponibles
    try:
        response_cuentas = requests.get(f"{backend_url}/api/catalogo-cuentas")
        cuentas = response_cuentas.json() if response_cuentas.status_code == 200 else []
        
        response_periodos = requests.get(f"{backend_url}/api/periodos")
        periodos = response_periodos.json() if response_periodos.status_code == 200 else []
        
    except:
        cuentas = []
        periodos = []
        st.error("Error al cargar datos del servidor")
        return
    
    # Formulario
    with st.form("form_manual_cuenta", clear_on_submit=not manual_editar):
        col1, col2 = st.columns(2)
        
        with col1:
            # Selector de cuenta
            if not manual_editar:
                opciones_cuentas = [
                    f"{c['codigo_cuenta']} - {c['nombre_cuenta']}" 
                    for c in cuentas if c['estado'] == 'ACTIVA'
                ]
                
                cuenta_seleccionada = st.selectbox(
                    "Cuenta*",
                    opciones_cuentas,
                    help="Seleccione la cuenta para crear su manual"
                )
            else:
                cuenta_seleccionada = f"{manual_editar.get('codigo_cuenta', 'N/A')} - {manual_editar.get('nombre_cuenta', 'N/A')}"
                st.text_input("Cuenta", value=cuenta_seleccionada, disabled=True)
            
            # Selector de período
            opciones_periodos = [
                f"{p['nombre_periodo']} ({p['fecha_inicio']} - {p['fecha_fin']})"
                for p in periodos
            ]
            
            if manual_editar and manual_editar.get('id_periodo'):
                periodo_actual = next((p for p in periodos if p['id_periodo'] == manual_editar['id_periodo']), None)
                if periodo_actual:
                    index_periodo = next(
                        (i for i, opt in enumerate(opciones_periodos) 
                         if opt.startswith(periodo_actual['nombre_periodo'])), 0
                    )
                else:
                    index_periodo = 0
            else:
                index_periodo = 0
            
            periodo_seleccionado = st.selectbox(
                "Período*",
                opciones_periodos,
                index=index_periodo,
                help="Período contable para este manual"
            )
            
            naturaleza_cuenta = st.selectbox(
                "Naturaleza de la Cuenta*",
                ["DEUDORA", "ACREEDORA"],
                index=0 if not manual_editar else (0 if manual_editar.get('naturaleza_cuenta') == 'DEUDORA' else 1),
                help="Naturaleza contable de la cuenta"
            )
        
        with col2:
            version = st.text_input(
                "Versión",
                value=manual_editar.get('version', '1.0') if manual_editar else '1.0',
                help="Versión del manual (ej: 1.0, 1.1, 2.0)"
            )
            
            activo = st.checkbox(
                "Activo",
                value=manual_editar.get('activo', True) if manual_editar else True,
                help="Si este manual está activo"
            )
        
        # Descripción principal
        descripcion_cuenta = st.text_area(
            "Descripción de la Cuenta*",
            value=manual_editar.get('descripcion_cuenta', '') if manual_editar else '',
            height=100,
            help="Descripción detallada del propósito y uso de la cuenta"
        )
        
        # Instrucciones de uso
        instrucciones_uso = st.text_area(
            "Instrucciones de Uso",
            value=manual_editar.get('instrucciones_uso', '') if manual_editar else '',
            height=120,
            help="Instrucciones específicas sobre cuándo y cómo usar esta cuenta"
        )
        
        # Ejemplos de uso
        ejemplos_uso = st.text_area(
            "Ejemplos de Uso",
            value=manual_editar.get('ejemplos_uso', '') if manual_editar else '',
            height=120,
            help="Ejemplos prácticos de transacciones que afectan esta cuenta"
        )
        
        # Normativa aplicable
        normativa_aplicable = st.text_area(
            "Normativa Aplicable",
            value=manual_editar.get('normativa_aplicable', '') if manual_editar else '',
            height=80,
            help="Referencias a NIIF, normativa local o políticas internas"
        )
        
        # Botón de envío
        texto_boton = "🔄 Actualizar Manual" if manual_editar else "💾 Crear Manual"
        submit_button = st.form_submit_button(texto_boton, use_container_width=True)
        
        if submit_button:
            if cuenta_seleccionada and periodo_seleccionado and descripcion_cuenta:
                # Obtener IDs de cuenta y período
                if not manual_editar:
                    codigo_cuenta = cuenta_seleccionada.split(" - ")[0]
                    cuenta_obj = next((c for c in cuentas if c['codigo_cuenta'] == codigo_cuenta), None)
                    id_cuenta = cuenta_obj['id_cuenta'] if cuenta_obj else None
                else:
                    id_cuenta = manual_editar['id_cuenta']
                
                nombre_periodo = periodo_seleccionado.split(" (")[0]
                periodo_obj = next((p for p in periodos if p['nombre_periodo'] == nombre_periodo), None)
                id_periodo = periodo_obj['id_periodo'] if periodo_obj else None
                
                if id_cuenta and id_periodo:
                    # Preparar datos
                    datos_manual = {
                        "id_cuenta": id_cuenta,
                        "id_periodo": id_periodo,
                        "descripcion_cuenta": descripcion_cuenta,
                        "naturaleza_cuenta": naturaleza_cuenta,
                        "instrucciones_uso": instrucciones_uso if instrucciones_uso else None,
                        "ejemplos_uso": ejemplos_uso if ejemplos_uso else None,
                        "normativa_aplicable": normativa_aplicable if normativa_aplicable else None,
                        "version": version,
                        "activo": activo
                    }
                    
                    try:
                        if manual_editar:
                            # Actualizar manual existente
                            response = requests.put(
                                f"{backend_url}/api/manual-cuentas/{manual_editar['id_manual']}",
                                json=datos_manual
                            )
                        else:
                            # Crear nuevo manual
                            response = requests.post(
                                f"{backend_url}/api/manual-cuentas",
                                json=datos_manual
                            )
                        
                        if response.status_code in [200, 201]:
                            accion = "actualizado" if manual_editar else "creado"
                            st.success(f"✅ Manual {accion} exitosamente")
                            
                            if manual_editar:
                                del st.session_state.manual_editar
                            
                            st.rerun()
                        else:
                            error_detail = response.json().get('detail', 'Error desconocido')
                            st.error(f"❌ Error al procesar manual: {error_detail}")
                            
                    except requests.exceptions.RequestException as e:
                        st.error(f"❌ Error de conexión: {e}")
                else:
                    st.error("❌ Error al obtener IDs de cuenta o período")
            else:
                st.warning("⚠️ Por favor completa los campos obligatorios")

def buscar_manual(backend_url: str):
    """Búsqueda avanzada en manuales"""
    
    st.subheader("🔍 Búsqueda Avanzada en Manuales")
    
    # Filtros de búsqueda
    col1, col2 = st.columns(2)
    
    with col1:
        texto_busqueda = st.text_input(
            "Buscar texto:",
            placeholder="Buscar en descripción, instrucciones, ejemplos...",
            help="Busca en todos los campos de texto del manual"
        )
        
        naturaleza_filtro = st.selectbox(
            "Naturaleza:",
            ["Todas", "DEUDORA", "ACREEDORA"]
        )
    
    with col2:
        solo_activos = st.checkbox("Solo manuales activos", value=True)
        
        solo_con_ejemplos = st.checkbox("Solo con ejemplos de uso", value=False)
    
    if st.button("🔍 Buscar", use_container_width=True):
        try:
            # Obtener todos los manuales y filtrar localmente
            response = requests.get(f"{backend_url}/api/manual-cuentas")
            
            if response.status_code == 200:
                manuales = response.json()
                
                # Aplicar filtros
                manuales_filtrados = manuales
                
                if texto_busqueda:
                    manuales_filtrados = [
                        m for m in manuales_filtrados
                        if any(texto_busqueda.lower() in str(m.get(campo, '')).lower() 
                               for campo in ['descripcion_cuenta', 'instrucciones_uso', 'ejemplos_uso', 'normativa_aplicable'])
                    ]
                
                if naturaleza_filtro != "Todas":
                    manuales_filtrados = [
                        m for m in manuales_filtrados
                        if m.get('naturaleza_cuenta') == naturaleza_filtro
                    ]
                
                if solo_activos:
                    manuales_filtrados = [
                        m for m in manuales_filtrados
                        if m.get('activo', True)
                    ]
                
                if solo_con_ejemplos:
                    manuales_filtrados = [
                        m for m in manuales_filtrados
                        if m.get('ejemplos_uso')
                    ]
                
                # Mostrar resultados
                if manuales_filtrados:
                    st.success(f"✅ Se encontraron {len(manuales_filtrados)} manuales")
                    
                    for manual in manuales_filtrados:
                        with st.expander(f"📄 {manual.get('codigo_cuenta', 'N/A')} - {manual.get('nombre_cuenta', manual['descripcion_cuenta'][:50])}"):
                            mostrar_detalle_manual(manual, backend_url)
                else:
                    st.warning("⚠️ No se encontraron manuales con los filtros aplicados")
                    
            else:
                st.error(f"Error al buscar: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            st.error(f"Error de conexión: {e}")