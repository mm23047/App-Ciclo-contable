"""
Módulo Streamlit para el Libro Mayor.
Muestra movimientos mayorizados por cuenta con saldos acumulados.
"""
import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, Any, List
from datetime import datetime, date

def render_page(backend_url: str):
    """Renderizar página del libro mayor"""
    
    st.header("📊 Libro Mayor")
    st.markdown("Consulta de movimientos mayorizados por cuenta contable")
    
    # Tabs para organizar funcionalidades
    tab1, tab2, tab3 = st.tabs(["📋 Consultar Mayor", "📈 Análisis Gráfico", "📊 Resumen de Cuentas"])
    
    with tab1:
        consultar_mayor(backend_url)
    
    with tab2:
        analisis_grafico(backend_url)
    
    with tab3:
        resumen_cuentas(backend_url)

def consultar_mayor(backend_url: str):
    """Consultar movimientos del libro mayor"""
    
    st.subheader("Consulta de Libro Mayor")
    
    # Filtros
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Obtener cuentas disponibles
        try:
            response_cuentas = requests.get(f"{backend_url}/api/catalogo-cuentas")
            cuentas = response_cuentas.json() if response_cuentas.status_code == 200 else []
            
            opciones_cuentas = ["Todas las cuentas"] + [
                f"{c['codigo_cuenta']} - {c['nombre_cuenta']}" 
                for c in cuentas if c['acepta_movimientos']
            ]
            
            cuenta_seleccionada = st.selectbox("Cuenta:", opciones_cuentas)
            
        except:
            cuenta_seleccionada = "Todas las cuentas"
    
    with col2:
        # Obtener períodos disponibles
        try:
            response_periodos = requests.get(f"{backend_url}/api/periodos")
            periodos = response_periodos.json() if response_periodos.status_code == 200 else []
            
            opciones_periodos = [
                f"{p['descripcion']} ({p['fecha_inicio']} - {p['fecha_fin']})"
                for p in periodos
            ]
            
            if opciones_periodos:
                periodo_seleccionado = st.selectbox("Período:", opciones_periodos)
            else:
                periodo_seleccionado = None
                st.warning("No hay períodos configurados")
            
        except:
            periodo_seleccionado = None
    
    with col3:
        incluir_saldo_inicial = st.checkbox("Incluir saldo inicial", value=True)
        
        mostrar_solo_con_movimientos = st.checkbox("Solo cuentas con movimientos", value=True)
    
    if st.button("📊 Generar Consulta", width="stretch"):
        if periodo_seleccionado:
            # Extraer ID del período
            nombre_periodo = periodo_seleccionado.split(" (")[0]
            periodo_obj = next((p for p in periodos if p['descripcion'] == nombre_periodo), None)
            
            if periodo_obj:
                id_periodo = periodo_obj['id_periodo']
                
                # Obtener ID de cuenta si se seleccionó una específica
                id_cuenta = None
                if cuenta_seleccionada != "Todas las cuentas":
                    codigo_cuenta = cuenta_seleccionada.split(" - ")[0]
                    cuenta_obj = next((c for c in cuentas if c['codigo_cuenta'] == codigo_cuenta), None)
                    if cuenta_obj:
                        id_cuenta = cuenta_obj['id_cuenta']
                
                obtener_movimientos_mayor(
                    backend_url, id_periodo, id_cuenta, 
                    incluir_saldo_inicial, mostrar_solo_con_movimientos
                )
        else:
            st.warning("⚠️ Selecciona un período válido")

def obtener_movimientos_mayor(
    backend_url: str, 
    id_periodo: int, 
    id_cuenta: int = None, 
    incluir_saldo_inicial: bool = True,
    solo_con_movimientos: bool = True
):
    """Obtener y mostrar movimientos del libro mayor"""
    
    try:
        # Construir parámetros de consulta
        if id_cuenta:
            # Consulta para una cuenta específica
            url = f"{backend_url}/api/libro-mayor/cuenta/{id_cuenta}/periodo/{id_periodo}"
        else:
            # Consulta para todas las cuentas
            url = f"{backend_url}/api/libro-mayor/periodo/{id_periodo}"
        
        params = {
            "incluir_saldo_inicial": incluir_saldo_inicial,
            "solo_con_movimientos": solo_con_movimientos
        }
        
        with st.spinner("Consultando libro mayor..."):
            response = requests.get(url, params=params)
        
        if response.status_code == 200:
            datos_mayor = response.json()
            
            if isinstance(datos_mayor, list):
                # Múltiples cuentas
                mostrar_mayor_multiple_cuentas(datos_mayor)
            else:
                # Una cuenta específica
                mostrar_mayor_cuenta_especifica(datos_mayor)
                
        else:
            st.error(f"Error al consultar libro mayor: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        st.error(f"Error de conexión: {e}")

def mostrar_mayor_cuenta_especifica(datos_cuenta: Dict[str, Any]):
    """Mostrar libro mayor para una cuenta específica"""
    
    # Información de la cuenta
    st.markdown("### 📊 Información de la Cuenta")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Código", datos_cuenta.get('codigo_cuenta', 'N/A'))
    
    with col2:
        st.metric("Tipo", datos_cuenta.get('tipo_cuenta', 'N/A'))
    
    with col3:
        saldo_inicial = datos_cuenta.get('saldo_inicial', 0)
        st.metric("Saldo Inicial", f"${saldo_inicial:,.2f}")
    
    with col4:
        saldo_final = datos_cuenta.get('saldo_final', 0)
        delta = saldo_final - saldo_inicial
        st.metric("Saldo Final", f"${saldo_final:,.2f}", delta=f"${delta:,.2f}")
    
    # Movimientos
    movimientos = datos_cuenta.get('movimientos', [])
    
    if movimientos:
        st.markdown("### 📝 Movimientos")
        
        # Crear DataFrame
        df_movimientos = pd.DataFrame(movimientos)
        
        # Formatear columnas
        df_display = df_movimientos.copy()
        df_display['fecha_movimiento'] = pd.to_datetime(df_display['fecha_movimiento']).dt.strftime('%d/%m/%Y')
        df_display['debe'] = df_display['debe'].apply(lambda x: f"${x:,.2f}" if x > 0 else "-")
        df_display['haber'] = df_display['haber'].apply(lambda x: f"${x:,.2f}" if x > 0 else "-")
        df_display['saldo_acumulado'] = df_display['saldo_acumulado'].apply(lambda x: f"${x:,.2f}")
        
        # Renombrar columnas
        df_display.columns = ['Fecha', 'Descripción', 'Referencia', 'Debe', 'Haber', 'Saldo Acumulado']
        
        st.dataframe(
            df_display,
            width="stretch",
            hide_index=True
        )
        
        # Gráfico de evolución del saldo
        if len(movimientos) > 1:
            st.markdown("### 📈 Evolución del Saldo")
            
            fig = px.line(
                df_movimientos,
                x='fecha_movimiento',
                y='saldo_acumulado',
                title='Evolución del Saldo de la Cuenta',
                markers=True
            )
            
            fig.update_layout(
                xaxis_title="Fecha",
                yaxis_title="Saldo ($)",
                hovermode='x unified'
            )
            
            st.plotly_chart(fig, width="stretch")
        
        # Resumen estadístico
        st.markdown("### 📊 Resumen Estadístico")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_debe = sum(m['debe'] for m in movimientos)
            st.metric("Total Debe", f"${total_debe:,.2f}")
        
        with col2:
            total_haber = sum(m['haber'] for m in movimientos)
            st.metric("Total Haber", f"${total_haber:,.2f}")
        
        with col3:
            st.metric("Cantidad Movimientos", len(movimientos))
        
        with col4:
            promedio_movimiento = (total_debe + total_haber) / len(movimientos) / 2
            st.metric("Promedio Movimiento", f"${promedio_movimiento:,.2f}")
    
    else:
        st.info("No hay movimientos registrados para esta cuenta en el período seleccionado")

def mostrar_mayor_multiple_cuentas(datos_cuentas: List[Dict[str, Any]]):
    """Mostrar resumen del libro mayor para múltiples cuentas"""
    
    if not datos_cuentas:
        st.info("No se encontraron cuentas con movimientos en el período seleccionado")
        return
    
    st.markdown("### 📊 Resumen por Cuentas")
    
    # Crear DataFrame para resumen
    resumen_data = []
    for cuenta in datos_cuentas:
        movimientos = cuenta.get('movimientos', [])
        total_debe = sum(m['debe'] for m in movimientos)
        total_haber = sum(m['haber'] for m in movimientos)
        
        resumen_data.append({
            'Código': cuenta.get('codigo_cuenta', 'N/A'),
            'Nombre': cuenta.get('nombre_cuenta', 'N/A'),
            'Tipo': cuenta.get('tipo_cuenta', 'N/A'),
            'Saldo Inicial': cuenta.get('saldo_inicial', 0),
            'Total Debe': total_debe,
            'Total Haber': total_haber,
            'Saldo Final': cuenta.get('saldo_final', 0),
            'Movimientos': len(movimientos)
        })
    
    df_resumen = pd.DataFrame(resumen_data)
    
    # Formatear columnas monetarias
    for col in ['Saldo Inicial', 'Total Debe', 'Total Haber', 'Saldo Final']:
        df_resumen[f'{col} (Formato)'] = df_resumen[col].apply(lambda x: f"${x:,.2f}")
    
    # Mostrar tabla
    columnas_mostrar = ['Código', 'Nombre', 'Tipo', 'Saldo Inicial (Formato)', 
                       'Total Debe (Formato)', 'Total Haber (Formato)', 
                       'Saldo Final (Formato)', 'Movimientos']
    
    st.dataframe(
        df_resumen[columnas_mostrar],
        width="stretch",
        hide_index=True
    )
    
    # Métricas generales
    st.markdown("### 📊 Totales Generales")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Cuentas con Movimientos", len(datos_cuentas))
    
    with col2:
        total_debe_general = df_resumen['Total Debe'].sum()
        st.metric("Total Debe General", f"${total_debe_general:,.2f}")
    
    with col3:
        total_haber_general = df_resumen['Total Haber'].sum()
        st.metric("Total Haber General", f"${total_haber_general:,.2f}")
    
    with col4:
        total_movimientos = df_resumen['Movimientos'].sum()
        st.metric("Total Movimientos", total_movimientos)

def analisis_grafico(backend_url: str):
    """Análisis gráfico del libro mayor"""
    
    st.subheader("📈 Análisis Gráfico del Libro Mayor")
    
    # Selector de período
    try:
        response_periodos = requests.get(f"{backend_url}/api/periodos")
        periodos = response_periodos.json() if response_periodos.status_code == 200 else []
        
        if periodos:
            opciones_periodos = [
                f"{p['descripcion']} ({p['fecha_inicio']} - {p['fecha_fin']})"
                for p in periodos
            ]
            
            periodo_seleccionado = st.selectbox("Seleccionar período:", opciones_periodos, key="grafico_periodo")
            
            if st.button("📊 Generar Análisis Gráfico"):
                nombre_periodo = periodo_seleccionado.split(" (")[0]
                periodo_obj = next((p for p in periodos if p['descripcion'] == nombre_periodo), None)
                
                if periodo_obj:
                    generar_graficos_mayor(backend_url, periodo_obj['id_periodo'])
        else:
            st.warning("No hay períodos configurados")
            
    except:
        st.error("Error al cargar períodos")

def generar_graficos_mayor(backend_url: str, id_periodo: int):
    """Generar gráficos de análisis del libro mayor"""
    
    try:
        # Obtener datos del análisis de cuentas
        url = f"{backend_url}/balanza-comprobacion/analisis/{id_periodo}"
        response = requests.get(url)
        
        if response.status_code == 200:
            datos_analisis = response.json()
            
            if datos_analisis:
                df_analisis = pd.DataFrame(datos_analisis)
                
                # Gráfico de distribución por tipo de cuenta
                fig_tipo = px.pie(
                    df_analisis,
                    names='tipo_cuenta',
                    values='cantidad_movimientos',
                    title='Distribución de Movimientos por Tipo de Cuenta'
                )
                st.plotly_chart(fig_tipo, width="stretch")
                
                # Gráfico de barras de saldos finales
                df_top_saldos = df_analisis.nlargest(10, 'saldo_final')
                
                fig_saldos = px.bar(
                    df_top_saldos,
                    x='codigo_cuenta',
                    y='saldo_final',
                    title='Top 10 Cuentas por Saldo Final',
                    hover_data=['nombre_cuenta']
                )
                
                fig_saldos.update_layout(
                    xaxis_title="Código de Cuenta",
                    yaxis_title="Saldo Final ($)"
                )
                
                st.plotly_chart(fig_saldos, width="stretch")
                
                # Gráfico de actividad de cuentas
                fig_actividad = px.scatter(
                    df_analisis,
                    x='cantidad_movimientos',
                    y='saldo_final',
                    hover_data=['codigo_cuenta', 'nombre_cuenta'],
                    title='Actividad vs Saldo Final',
                    color='tipo_cuenta'
                )
                
                fig_actividad.update_layout(
                    xaxis_title="Cantidad de Movimientos",
                    yaxis_title="Saldo Final ($)"
                )
                
                st.plotly_chart(fig_actividad, width="stretch")
                
            else:
                st.info("No hay datos de análisis disponibles para este período")
                
        else:
            st.error(f"Error al obtener datos de análisis: {response.status_code}")
            
    except Exception as e:
        st.error(f"Error al generar gráficos: {e}")

def resumen_cuentas(backend_url: str):
    """Resumen estadístico de cuentas"""
    
    st.subheader("📊 Resumen Estadístico de Cuentas")
    
    # Selector de período
    try:
        response_periodos = requests.get(f"{backend_url}/api/periodos")
        periodos = response_periodos.json() if response_periodos.status_code == 200 else []
        
        if periodos:
            opciones_periodos = [
                f"{p['descripcion']} ({p['fecha_inicio']} - {p['fecha_fin']})"
                for p in periodos
            ]
            
            periodo_seleccionado = st.selectbox("Seleccionar período:", opciones_periodos, key="resumen_periodo")
            
            col1, col2 = st.columns(2)
            
            with col1:
                tipo_filtro = st.selectbox(
                    "Filtrar por tipo:",
                    ["Todos", "Activo", "Pasivo", "Capital", "Ingreso", "Egreso"]
                )
            
            with col2:
                ordenar_por = st.selectbox(
                    "Ordenar por:",
                    ["Saldo Final", "Cantidad Movimientos", "Código", "Nombre"]
                )
            
            if st.button("📋 Generar Resumen"):
                nombre_periodo = periodo_seleccionado.split(" (")[0]
                periodo_obj = next((p for p in periodos if p['descripcion'] == nombre_periodo), None)
                
                if periodo_obj:
                    generar_resumen_estadistico(
                        backend_url, 
                        periodo_obj['id_periodo'], 
                        tipo_filtro if tipo_filtro != "Todos" else None,
                        ordenar_por
                    )
        else:
            st.warning("No hay períodos configurados")
            
    except:
        st.error("Error al cargar períodos")

def generar_resumen_estadistico(
    backend_url: str, 
    id_periodo: int, 
    tipo_filtro: str = None,
    ordenar_por: str = "Saldo Final"
):
    """Generar resumen estadístico detallado"""
    
    try:
        url = f"{backend_url}/api/balanza-comprobacion/analisis/{id_periodo}"
        params = {}
        if tipo_filtro:
            params["tipo_cuenta"] = tipo_filtro
            
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            datos = response.json()
            
            if datos:
                df = pd.DataFrame(datos)
                
                # Aplicar ordenamiento
                if ordenar_por == "Saldo Final":
                    df = df.sort_values('saldo_final', ascending=False)
                elif ordenar_por == "Cantidad Movimientos":
                    df = df.sort_values('cantidad_movimientos', ascending=False)
                elif ordenar_por == "Código":
                    df = df.sort_values('codigo_cuenta')
                elif ordenar_por == "Nombre":
                    df = df.sort_values('nombre_cuenta')
                
                # Mostrar estadísticas generales
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Cuentas", len(df))
                
                with col2:
                    total_movimientos = df['cantidad_movimientos'].sum()
                    st.metric("Total Movimientos", total_movimientos)
                
                with col3:
                    promedio_saldo = df['saldo_final'].mean()
                    st.metric("Promedio Saldo", f"${promedio_saldo:,.2f}")
                
                with col4:
                    cuentas_activas = len(df[df['cantidad_movimientos'] > 0])
                    st.metric("Cuentas con Actividad", cuentas_activas)
                
                # Tabla detallada
                st.markdown("### 📋 Detalle de Cuentas")
                
                # Formatear para visualización
                df_display = df.copy()
                df_display['saldo_inicial'] = df_display['saldo_inicial'].apply(lambda x: f"${x:,.2f}")
                df_display['total_debe'] = df_display['total_debe'].apply(lambda x: f"${x:,.2f}")
                df_display['total_haber'] = df_display['total_haber'].apply(lambda x: f"${x:,.2f}")
                df_display['saldo_final'] = df_display['saldo_final'].apply(lambda x: f"${x:,.2f}")
                
                columnas_mostrar = [
                    'codigo_cuenta', 'nombre_cuenta', 'tipo_cuenta', 
                    'saldo_inicial', 'total_debe', 'total_haber', 
                    'saldo_final', 'cantidad_movimientos'
                ]
                
                df_display.columns = [
                    'Código', 'Nombre', 'Tipo', 'Saldo Inicial', 
                    'Total Debe', 'Total Haber', 'Saldo Final', 'Movimientos'
                ]
                
                st.dataframe(
                    df_display[['Código', 'Nombre', 'Tipo', 'Saldo Inicial', 
                              'Total Debe', 'Total Haber', 'Saldo Final', 'Movimientos']],
                    width="stretch",
                    hide_index=True
                )
                
            else:
                st.info("No hay datos disponibles para el período seleccionado")
                
        else:
            st.error(f"Error al obtener datos: {response.status_code}")
            
    except Exception as e:
        st.error(f"Error al generar resumen: {e}")
