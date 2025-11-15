"""
Módulo Streamlit para Partidas de Ajuste.
Manejo de ajustes contables de fin de período.
"""
import streamlit as st
import requests
import pandas as pd
from datetime import datetime, date
from typing import Dict, Any, List

def render_page(backend_url: str):
    """Renderizar página de partidas de ajuste"""
    
    st.header("⚖️ Partidas de Ajuste")
    st.markdown("Gestión de ajustes contables de fin de período")
    
    # Tabs para organizar funcionalidades
    tab1, tab2, tab3 = st.tabs(["📝 Crear Ajuste", "📋 Consultar Ajustes", "📊 Reportes"])
    
    with tab1:
        crear_partida_ajuste(backend_url)
    
    with tab2:
        consultar_partidas_ajuste(backend_url)
    
    with tab3:
        reportes_ajustes(backend_url)

def crear_partida_ajuste(backend_url: str):
    """Crear nueva partida de ajuste"""
    
    st.subheader("📝 Crear Nueva Partida de Ajuste")
    
    # Obtener períodos disponibles
    try:
        response_periodos = requests.get(f"{backend_url}/api/periodos")
        periodos = response_periodos.json() if response_periodos.status_code == 200 else []
    except:
        periodos = []
    
    if not periodos:
        st.warning("⚠️ No hay períodos configurados. Configura un período primero.")
        return
    
    with st.form("form_crear_ajuste", clear_on_submit=False):
        col1, col2 = st.columns(2)
        
        with col1:
            # Selección de período
            opciones_periodos = [
                f"{p['nombre_periodo']} ({p['fecha_inicio']} - {p['fecha_fin']})"
                for p in periodos
            ]
            periodo_seleccionado = st.selectbox("Período contable:", opciones_periodos)
            
            # Fecha del ajuste
            fecha_ajuste = st.date_input(
                "Fecha del ajuste:",
                value=datetime.now().date(),
                help="Fecha de registro del ajuste"
            )
            
            # Tipo de ajuste
            tipos_ajuste = [
                "Depreciación de activos fijos",
                "Provision para cuentas incobrables", 
                "Ajuste de inventarios",
                "Gastos anticipados",
                "Ingresos diferidos",
                "Provision para impuestos",
                "Provision para prestaciones laborales",
                "Ajuste de devengos",
                "Corrección de errores",
                "Otro"
            ]
            tipo_ajuste = st.selectbox("Tipo de ajuste:", tipos_ajuste)
            
            if tipo_ajuste == "Otro":
                tipo_personalizado = st.text_input("Especificar tipo de ajuste:")
                tipo_ajuste_final = tipo_personalizado if tipo_personalizado else tipo_ajuste
            else:
                tipo_ajuste_final = tipo_ajuste
        
        with col2:
            # Descripción del ajuste
            descripcion = st.text_area(
                "Descripción del ajuste:",
                height=100,
                help="Descripción detallada del motivo y naturaleza del ajuste"
            )
            
            # Referencia
            referencia = st.text_input(
                "Referencia (opcional):",
                help="Número de documento o referencia externa"
            )
            
            # Observaciones
            observaciones = st.text_area(
                "Observaciones (opcional):",
                height=80,
                help="Observaciones adicionales sobre el ajuste"
            )
        
        st.markdown("### 📊 Movimientos del Ajuste")
        st.markdown("Agrega los movimientos que componen esta partida de ajuste:")
        
        # Gestión de movimientos
        if 'movimientos_ajuste' not in st.session_state:
            st.session_state.movimientos_ajuste = []
        
        # Formulario para agregar movimiento
        with st.expander("➕ Agregar Movimiento", expanded=True):
            col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
            
            with col1:
                # Obtener cuentas que aceptan movimientos
                try:
                    response_cuentas = requests.get(f"{backend_url}/api/catalogo-cuentas")
                    cuentas = response_cuentas.json() if response_cuentas.status_code == 200 else []
                    cuentas_disponibles = [
                        c for c in cuentas if c['acepta_movimientos']
                    ]
                except:
                    cuentas_disponibles = []
                
                opciones_cuentas = [
                    f"{c['codigo_cuenta']} - {c['nombre_cuenta']}"
                    for c in cuentas_disponibles
                ]
                
                if opciones_cuentas:
                    cuenta_mov = st.selectbox("Cuenta:", opciones_cuentas, key="cuenta_movimiento")
                else:
                    st.warning("No hay cuentas disponibles")
                    cuenta_mov = None
            
            with col2:
                descripcion_mov = st.text_input("Descripción del movimiento:", key="desc_movimiento")
            
            with col3:
                debe = st.number_input("Debe:", min_value=0.0, step=0.01, key="debe_mov")
            
            with col4:
                haber = st.number_input("Haber:", min_value=0.0, step=0.01, key="haber_mov")
            
            if st.button("➕ Agregar Movimiento"):
                if cuenta_mov and descripcion_mov and (debe > 0 or haber > 0):
                    if debe > 0 and haber > 0:
                        st.error("Un movimiento no puede tener valores en debe y haber al mismo tiempo")
                    else:
                        codigo_cuenta = cuenta_mov.split(" - ")[0]
                        cuenta_obj = next((c for c in cuentas_disponibles if c['codigo_cuenta'] == codigo_cuenta), None)
                        
                        nuevo_movimiento = {
                            'id_cuenta': cuenta_obj['id_cuenta'],
                            'codigo_cuenta': codigo_cuenta,
                            'nombre_cuenta': cuenta_obj['nombre_cuenta'],
                            'descripcion': descripcion_mov,
                            'debe': debe,
                            'haber': haber
                        }
                        
                        st.session_state.movimientos_ajuste.append(nuevo_movimiento)
                        st.rerun()
                else:
                    st.error("Complete todos los campos requeridos")
        
        # Mostrar movimientos agregados
        if st.session_state.movimientos_ajuste:
            st.markdown("#### Movimientos agregados:")
            
            for i, mov in enumerate(st.session_state.movimientos_ajuste):
                col1, col2, col3, col4, col5 = st.columns([2, 3, 1, 1, 1])
                
                with col1:
                    st.text(mov['codigo_cuenta'])
                
                with col2:
                    st.text(mov['nombre_cuenta'])
                
                with col3:
                    st.text(f"${mov['debe']:,.2f}" if mov['debe'] > 0 else "-")
                
                with col4:
                    st.text(f"${mov['haber']:,.2f}" if mov['haber'] > 0 else "-")
                
                with col5:
                    if st.button("🗑️", key=f"eliminar_{i}", help="Eliminar movimiento"):
                        st.session_state.movimientos_ajuste.pop(i)
                        st.rerun()
            
            # Validar balance
            total_debe = sum(m['debe'] for m in st.session_state.movimientos_ajuste)
            total_haber = sum(m['haber'] for m in st.session_state.movimientos_ajuste)
            diferencia = total_debe - total_haber
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Debe", f"${total_debe:,.2f}")
            with col2:
                st.metric("Total Haber", f"${total_haber:,.2f}")
            with col3:
                st.metric(
                    "Diferencia", 
                    f"${abs(diferencia):,.2f}",
                    delta=f"{'Debe' if diferencia > 0 else 'Haber' if diferencia < 0 else 'Balanceado'}"
                )
            
            if abs(diferencia) > 0.01:
                st.warning("⚠️ Los movimientos no están balanceados. Debe = Haber")
        
        # Botón para guardar
        submitted = st.form_submit_button(
            "💾 Crear Partida de Ajuste", 
            use_container_width=True,
            type="primary"
        )
        
        if submitted:
            if not st.session_state.movimientos_ajuste:
                st.error("❌ Debe agregar al menos un movimiento")
            elif abs(sum(m['debe'] for m in st.session_state.movimientos_ajuste) - 
                    sum(m['haber'] for m in st.session_state.movimientos_ajuste)) > 0.01:
                st.error("❌ Los movimientos deben estar balanceados (Debe = Haber)")
            elif not descripcion:
                st.error("❌ La descripción es requerida")
            else:
                crear_ajuste_backend(
                    backend_url, 
                    periodo_seleccionado, 
                    periodos,
                    fecha_ajuste,
                    tipo_ajuste_final,
                    descripcion,
                    referencia,
                    observaciones,
                    st.session_state.movimientos_ajuste
                )

def crear_ajuste_backend(
    backend_url: str, 
    periodo_seleccionado: str,
    periodos: List[Dict],
    fecha_ajuste: date,
    tipo_ajuste: str,
    descripcion: str,
    referencia: str,
    observaciones: str,
    movimientos: List[Dict]
):
    """Enviar partida de ajuste al backend"""
    
    try:
        # Obtener ID del período
        nombre_periodo = periodo_seleccionado.split(" (")[0]
        periodo_obj = next((p for p in periodos if p['nombre_periodo'] == nombre_periodo), None)
        
        if not periodo_obj:
            st.error("❌ Error al identificar el período")
            return
        
        # Preparar datos
        datos_ajuste = {
            "id_periodo": periodo_obj['id_periodo'],
            "fecha_ajuste": fecha_ajuste.isoformat(),
            "tipo_ajuste": tipo_ajuste,
            "descripcion": descripcion,
            "referencia": referencia if referencia else None,
            "observaciones": observaciones if observaciones else None,
            "movimientos": [
                {
                    "id_cuenta": mov['id_cuenta'],
                    "descripcion": mov['descripcion'],
                    "debe": mov['debe'],
                    "haber": mov['haber']
                }
                for mov in movimientos
            ]
        }
        
        # Enviar al backend
        with st.spinner("Creando partida de ajuste..."):
            response = requests.post(
                f"{backend_url}/api/partidas-ajuste",
                json=datos_ajuste
            )
        
        if response.status_code == 201:
            st.success("✅ Partida de ajuste creada exitosamente!")
            st.session_state.movimientos_ajuste = []  # Limpiar movimientos
            st.balloons()
            
            # Mostrar información del ajuste creado
            ajuste_creado = response.json()
            st.info(f"📄 Ajuste creado con ID: {ajuste_creado.get('id_ajuste', 'N/A')}")
            
        else:
            error_detail = response.json().get('detail', 'Error desconocido')
            st.error(f"❌ Error al crear partida de ajuste: {error_detail}")
            
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Error de conexión: {e}")
    except Exception as e:
        st.error(f"❌ Error inesperado: {e}")

def consultar_partidas_ajuste(backend_url: str):
    """Consultar partidas de ajuste existentes"""
    
    st.subheader("📋 Consultar Partidas de Ajuste")
    
    # Filtros
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Obtener períodos
        try:
            response_periodos = requests.get(f"{backend_url}/api/periodos")
            periodos = response_periodos.json() if response_periodos.status_code == 200 else []
            
            opciones_periodos = ["Todos los períodos"] + [
                f"{p['nombre_periodo']} ({p['fecha_inicio']} - {p['fecha_fin']})"
                for p in periodos
            ]
            
            periodo_filtro = st.selectbox("Período:", opciones_periodos)
            
        except:
            periodo_filtro = "Todos los períodos"
            periodos = []
    
    with col2:
        # Filtro por tipo de ajuste
        tipos_ajuste = [
            "Todos los tipos",
            "Depreciación de activos fijos",
            "Provision para cuentas incobrables",
            "Ajuste de inventarios",
            "Gastos anticipados",
            "Ingresos diferidos",
            "Provision para impuestos",
            "Provision para prestaciones laborales",
            "Ajuste de devengos",
            "Corrección de errores",
            "Otro"
        ]
        tipo_filtro = st.selectbox("Tipo de ajuste:", tipos_ajuste)
    
    with col3:
        # Filtro por fecha
        fecha_desde = st.date_input("Desde:", value=None, help="Fecha opcional para filtrar")
        fecha_hasta = st.date_input("Hasta:", value=None, help="Fecha opcional para filtrar")
    
    if st.button("🔍 Buscar Partidas de Ajuste", use_container_width=True):
        obtener_partidas_ajuste(
            backend_url, 
            periodo_filtro,
            periodos,
            tipo_filtro,
            fecha_desde,
            fecha_hasta
        )

def obtener_partidas_ajuste(
    backend_url: str,
    periodo_filtro: str,
    periodos: List[Dict],
    tipo_filtro: str,
    fecha_desde: date = None,
    fecha_hasta: date = None
):
    """Obtener y mostrar partidas de ajuste"""
    
    try:
        # Construir parámetros de consulta
        params = {}
        
        if periodo_filtro != "Todos los períodos":
            nombre_periodo = periodo_filtro.split(" (")[0]
            periodo_obj = next((p for p in periodos if p['nombre_periodo'] == nombre_periodo), None)
            if periodo_obj:
                params["id_periodo"] = periodo_obj['id_periodo']
        
        if tipo_filtro != "Todos los tipos":
            params["tipo_ajuste"] = tipo_filtro
        
        if fecha_desde:
            params["fecha_desde"] = fecha_desde.isoformat()
        
        if fecha_hasta:
            params["fecha_hasta"] = fecha_hasta.isoformat()
        
        # Realizar consulta
        with st.spinner("Consultando partidas de ajuste..."):
            response = requests.get(f"{backend_url}/api/partidas-ajuste", params=params)
        
        if response.status_code == 200:
            partidas = response.json()
            
            if partidas:
                mostrar_partidas_ajuste(partidas)
            else:
                st.info("📭 No se encontraron partidas de ajuste con los filtros aplicados")
                
        else:
            st.error(f"Error al consultar partidas: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        st.error(f"Error de conexión: {e}")

def mostrar_partidas_ajuste(partidas: List[Dict[str, Any]]):
    """Mostrar lista de partidas de ajuste"""
    
    st.markdown(f"### 📋 Partidas de Ajuste Encontradas ({len(partidas)})")
    
    for i, partida in enumerate(partidas):
        with st.expander(
            f"🔍 ID: {partida['id_ajuste']} - {partida['tipo_ajuste']} - "
            f"{partida['fecha_ajuste']} - ${partida.get('total_debe', 0):,.2f}",
            expanded=False
        ):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**📋 Información General:**")
                st.text(f"ID: {partida['id_ajuste']}")
                st.text(f"Fecha: {partida['fecha_ajuste']}")
                st.text(f"Tipo: {partida['tipo_ajuste']}")
                st.text(f"Período: {partida.get('nombre_periodo', 'N/A')}")
                
                if partida.get('referencia'):
                    st.text(f"Referencia: {partida['referencia']}")
            
            with col2:
                st.markdown("**💰 Totales:**")
                st.text(f"Total Debe: ${partida.get('total_debe', 0):,.2f}")
                st.text(f"Total Haber: ${partida.get('total_haber', 0):,.2f}")
                st.text(f"Estado: {partida.get('estado', 'N/A')}")
                
                if partida.get('fecha_creacion'):
                    st.text(f"Creado: {partida['fecha_creacion']}")
            
            # Descripción
            if partida.get('descripcion'):
                st.markdown("**📝 Descripción:**")
                st.text(partida['descripcion'])
            
            # Observaciones
            if partida.get('observaciones'):
                st.markdown("**📄 Observaciones:**")
                st.text(partida['observaciones'])
            
            # Movimientos
            if 'movimientos' in partida and partida['movimientos']:
                st.markdown("**📊 Movimientos:**")
                
                df_movimientos = pd.DataFrame(partida['movimientos'])
                df_display = df_movimientos.copy()
                
                # Formatear columnas
                df_display['debe'] = df_display['debe'].apply(lambda x: f"${x:,.2f}" if x > 0 else "-")
                df_display['haber'] = df_display['haber'].apply(lambda x: f"${x:,.2f}" if x > 0 else "-")
                
                # Seleccionar y renombrar columnas
                columnas_mostrar = ['codigo_cuenta', 'nombre_cuenta', 'descripcion', 'debe', 'haber']
                df_display = df_display[columnas_mostrar]
                df_display.columns = ['Código', 'Cuenta', 'Descripción', 'Debe', 'Haber']
                
                st.dataframe(df_display, use_container_width=True, hide_index=True)

def reportes_ajustes(backend_url: str):
    """Generar reportes de partidas de ajuste"""
    
    st.subheader("📊 Reportes de Partidas de Ajuste")
    
    # Selector de tipo de reporte
    tipo_reporte = st.selectbox(
        "Tipo de reporte:",
        [
            "Resumen por período",
            "Análisis por tipo de ajuste", 
            "Evolución temporal",
            "Detalle completo"
        ]
    )
    
    # Filtros comunes
    col1, col2 = st.columns(2)
    
    with col1:
        try:
            response_periodos = requests.get(f"{backend_url}/api/periodos")
            periodos = response_periodos.json() if response_periodos.status_code == 200 else []
            
            if periodos:
                opciones_periodos = ["Todos los períodos"] + [
                    f"{p['nombre_periodo']} ({p['fecha_inicio']} - {p['fecha_fin']})"
                    for p in periodos
                ]
                periodo_reporte = st.selectbox("Período:", opciones_periodos, key="reporte_periodo")
            else:
                periodo_reporte = "Todos los períodos"
                periodos = []
        except:
            periodo_reporte = "Todos los períodos"
            periodos = []
    
    with col2:
        fecha_corte = st.date_input(
            "Fecha de corte:",
            value=datetime.now().date(),
            help="Incluir ajustes hasta esta fecha"
        )
    
    if st.button("📊 Generar Reporte", use_container_width=True):
        generar_reporte_especifico(
            backend_url,
            tipo_reporte,
            periodo_reporte,
            periodos,
            fecha_corte
        )

def generar_reporte_especifico(
    backend_url: str,
    tipo_reporte: str,
    periodo_reporte: str,
    periodos: List[Dict],
    fecha_corte: date
):
    """Generar reporte específico según el tipo seleccionado"""
    
    try:
        # Obtener datos base
        params = {"fecha_hasta": fecha_corte.isoformat()}
        
        if periodo_reporte != "Todos los períodos":
            nombre_periodo = periodo_reporte.split(" (")[0]
            periodo_obj = next((p for p in periodos if p['nombre_periodo'] == nombre_periodo), None)
            if periodo_obj:
                params["id_periodo"] = periodo_obj['id_periodo']
        
        response = requests.get(f"{backend_url}/api/partidas-ajuste/reporte", params=params)
        
        if response.status_code == 200:
            datos_reporte = response.json()
            
            if tipo_reporte == "Resumen por período":
                mostrar_resumen_por_periodo(datos_reporte)
            elif tipo_reporte == "Análisis por tipo de ajuste":
                mostrar_analisis_por_tipo(datos_reporte)
            elif tipo_reporte == "Evolución temporal":
                mostrar_evolucion_temporal(datos_reporte)
            elif tipo_reporte == "Detalle completo":
                mostrar_detalle_completo(datos_reporte)
                
        else:
            st.error(f"Error al generar reporte: {response.status_code}")
            
    except Exception as e:
        st.error(f"Error al generar reporte: {e}")

def mostrar_resumen_por_periodo(datos: Dict[str, Any]):
    """Mostrar resumen de ajustes por período"""
    
    st.markdown("### 📊 Resumen por Período")
    
    if 'resumen_periodos' in datos:
        resumen = datos['resumen_periodos']
        
        # Métricas generales
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Períodos", len(resumen))
        
        with col2:
            total_ajustes = sum(p['cantidad_ajustes'] for p in resumen)
            st.metric("Total Ajustes", total_ajustes)
        
        with col3:
            total_debe = sum(p['total_debe'] for p in resumen)
            st.metric("Total Debe", f"${total_debe:,.2f}")
        
        with col4:
            promedio_por_periodo = total_debe / len(resumen) if resumen else 0
            st.metric("Promedio por Período", f"${promedio_por_periodo:,.2f}")
        
        # Tabla de resumen
        if resumen:
            df_resumen = pd.DataFrame(resumen)
            df_resumen['total_debe'] = df_resumen['total_debe'].apply(lambda x: f"${x:,.2f}")
            df_resumen['total_haber'] = df_resumen['total_haber'].apply(lambda x: f"${x:,.2f}")
            
            df_resumen.columns = ['Período', 'Cantidad Ajustes', 'Total Debe', 'Total Haber']
            
            st.dataframe(df_resumen, use_container_width=True, hide_index=True)

def mostrar_analisis_por_tipo(datos: Dict[str, Any]):
    """Mostrar análisis por tipo de ajuste"""
    
    st.markdown("### 📊 Análisis por Tipo de Ajuste")
    
    if 'resumen_tipos' in datos:
        tipos = datos['resumen_tipos']
        
        if tipos:
            df_tipos = pd.DataFrame(tipos)
            
            # Gráfico de distribución
            import plotly.express as px
            
            fig = px.pie(
                df_tipos,
                names='tipo_ajuste',
                values='cantidad_ajustes',
                title='Distribución de Ajustes por Tipo'
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Tabla detallada
            df_display = df_tipos.copy()
            df_display['total_debe'] = df_display['total_debe'].apply(lambda x: f"${x:,.2f}")
            df_display.columns = ['Tipo de Ajuste', 'Cantidad', 'Total Debe']
            
            st.dataframe(df_display, use_container_width=True, hide_index=True)

def mostrar_evolucion_temporal(datos: Dict[str, Any]):
    """Mostrar evolución temporal de ajustes"""
    
    st.markdown("### 📊 Evolución Temporal")
    
    if 'evolucion_temporal' in datos:
        evolucion = datos['evolucion_temporal']
        
        if evolucion:
            import plotly.graph_objects as go
            
            df_evolucion = pd.DataFrame(evolucion)
            
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=df_evolucion['fecha'],
                y=df_evolucion['cantidad_ajustes'],
                mode='lines+markers',
                name='Cantidad de Ajustes',
                yaxis='y'
            ))
            
            fig.add_trace(go.Scatter(
                x=df_evolucion['fecha'],
                y=df_evolucion['total_debe'],
                mode='lines+markers',
                name='Total Debe ($)',
                yaxis='y2'
            ))
            
            fig.update_layout(
                title='Evolución Temporal de Ajustes',
                xaxis_title='Fecha',
                yaxis=dict(title='Cantidad de Ajustes', side='left'),
                yaxis2=dict(title='Total Debe ($)', side='right', overlaying='y'),
                hovermode='x unified'
            )
            
            st.plotly_chart(fig, use_container_width=True)

def mostrar_detalle_completo(datos: Dict[str, Any]):
    """Mostrar detalle completo de ajustes"""
    
    st.markdown("### 📊 Detalle Completo")
    
    if 'detalle_completo' in datos:
        detalle = datos['detalle_completo']
        
        if detalle:
            # Convertir a DataFrame
            registros = []
            for ajuste in detalle:
                for mov in ajuste.get('movimientos', []):
                    registros.append({
                        'ID Ajuste': ajuste['id_ajuste'],
                        'Fecha': ajuste['fecha_ajuste'],
                        'Tipo': ajuste['tipo_ajuste'],
                        'Período': ajuste.get('nombre_periodo', 'N/A'),
                        'Cuenta': f"{mov['codigo_cuenta']} - {mov['nombre_cuenta']}",
                        'Descripción': mov['descripcion'],
                        'Debe': mov['debe'],
                        'Haber': mov['haber']
                    })
            
            if registros:
                df_detalle = pd.DataFrame(registros)
                
                # Formatear columnas monetarias
                df_detalle['Debe'] = df_detalle['Debe'].apply(lambda x: f"${x:,.2f}" if x > 0 else "-")
                df_detalle['Haber'] = df_detalle['Haber'].apply(lambda x: f"${x:,.2f}" if x > 0 else "-")
                
                st.dataframe(df_detalle, use_container_width=True, hide_index=True)
                
                # Opción de descarga
                csv = df_detalle.to_csv(index=False)
                st.download_button(
                    label="📥 Descargar CSV",
                    data=csv,
                    file_name=f"partidas_ajuste_detalle_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )