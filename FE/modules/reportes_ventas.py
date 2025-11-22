"""
Módulo Streamlit para Reportes de Ventas.
Sistema completo de reportes y análisis de ventas para el sistema de facturación.
"""
import streamlit as st
import requests
import pandas as pd
from datetime import datetime, date, timedelta
from typing import Dict, Any, List
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import io

def render_page(backend_url: str):
    """Renderizar página de reportes de ventas"""
    
    st.header("📊 Reportes de Ventas")
    st.markdown("Sistema completo de reportes y análisis de ventas para la toma de decisiones")
    
    # Tabs para organizar reportes
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 Dashboard General", 
        "📋 Reportes Detallados", 
        "🎯 Análisis por Periodo",
        "🏆 Top Productos/Clientes",
        "📤 Exportar"
    ])
    
    with tab1:
        dashboard_general(backend_url)
    
    with tab2:
        reportes_detallados(backend_url)
    
    with tab3:
        analisis_periodo(backend_url)
    
    with tab4:
        top_productos_clientes(backend_url)
    
    with tab5:
        exportar_reportes(backend_url)

def dashboard_general(backend_url: str):
    """Dashboard general de ventas"""
    
    st.subheader("📈 Dashboard General de Ventas")
    
    # Filtros de período
    col1, col2, col3 = st.columns(3)
    
    with col1:
        periodo_dashboard = st.selectbox(
            "Período:",
            ["Hoy", "Esta Semana", "Este Mes", "Últimos 30 días", "Este Año", "Personalizado"]
        )
    
    with col2:
        if periodo_dashboard == "Personalizado":
            fecha_inicio = st.date_input("Desde:", value=date.today() - timedelta(days=30), key="dashboard_fecha_inicio")
        else:
            fecha_inicio = calcular_fecha_inicio(periodo_dashboard)
    
    with col3:
        if periodo_dashboard == "Personalizado":
            fecha_fin = st.date_input("Hasta:", value=date.today(), key="dashboard_fecha_fin")
        else:
            fecha_fin = date.today()
    
    # Obtener datos del dashboard
    try:
        params = {
            "fecha_inicio": fecha_inicio.isoformat(),
            "fecha_fin": fecha_fin.isoformat()
        }
        
        with st.spinner("Cargando dashboard..."):
            response = requests.get(f"{backend_url}/api/reportes/dashboard", params=params)
        
        if response.status_code == 200:
            datos_dashboard = response.json()
            mostrar_metricas_principales(datos_dashboard)
            mostrar_graficos_dashboard(datos_dashboard)
        else:
            # Generar dashboard con datos simulados si no existe el endpoint
            generar_dashboard_simulado(backend_url, fecha_inicio, fecha_fin)
            
    except Exception as e:
        st.error(f"Error al cargar dashboard: {e}")
        generar_dashboard_simulado(backend_url, fecha_inicio, fecha_fin)

def calcular_fecha_inicio(periodo: str) -> date:
    """Calcular fecha de inicio según período seleccionado"""
    
    hoy = date.today()
    
    if periodo == "Hoy":
        return hoy
    elif periodo == "Esta Semana":
        return hoy - timedelta(days=hoy.weekday())
    elif periodo == "Este Mes":
        return hoy.replace(day=1)
    elif periodo == "Últimos 30 días":
        return hoy - timedelta(days=30)
    elif periodo == "Este Año":
        return hoy.replace(month=1, day=1)
    else:
        return hoy - timedelta(days=30)

def mostrar_metricas_principales(datos: Dict[str, Any]):
    """Mostrar métricas principales del dashboard"""
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            "💰 Ventas Totales",
            f"${datos.get('ventas_totales', 0):,.0f}",
            delta=f"{datos.get('variacion_ventas', 0):+.1f}%"
        )
    
    with col2:
        st.metric(
            "🧾 Facturas",
            datos.get('total_facturas', 0),
            delta=datos.get('variacion_facturas', 0)
        )
    
    with col3:
        st.metric(
            "👥 Clientes",
            datos.get('clientes_activos', 0),
            delta=datos.get('nuevos_clientes', 0)
        )
    
    with col4:
        st.metric(
            "📦 Productos Vendidos",
            datos.get('productos_vendidos', 0),
            delta=f"{datos.get('variacion_productos', 0):+.1f}%"
        )
    
    with col5:
        st.metric(
            "💵 Ticket Promedio",
            f"${datos.get('ticket_promedio', 0):,.2f}",
            delta=f"${datos.get('variacion_ticket', 0):+.2f}"
        )

def mostrar_graficos_dashboard(datos: Dict[str, Any]):
    """Mostrar gráficos del dashboard"""
    
    # Gráfico de ventas por período
    if 'ventas_periodo' in datos:
        st.markdown("### 📈 Evolución de Ventas")
        
        ventas_periodo = datos['ventas_periodo']
        df_ventas = pd.DataFrame(ventas_periodo)
        
        fig_ventas = px.line(
            df_ventas, 
            x='fecha', 
            y='ventas',
            title='Evolución de Ventas en el Período',
            markers=True
        )
        fig_ventas.update_layout(
            xaxis_title="Fecha",
            yaxis_title="Ventas ($)"
        )
        st.plotly_chart(fig_ventas, use_container_width=True)
    
    # Gráficos en dos columnas
    col1, col2 = st.columns(2)
    
    with col1:
        # Distribución de ventas por categoría
        if 'ventas_categoria' in datos:
            st.markdown("### 🏷️ Ventas por Categoría")
            
            categorias = datos['ventas_categoria']
            df_cat = pd.DataFrame(list(categorias.items()), columns=['Categoría', 'Ventas'])
            
            fig_cat = px.pie(
                df_cat, 
                values='Ventas', 
                names='Categoría',
                title='Distribución por Categoría'
            )
            st.plotly_chart(fig_cat, use_container_width=True)
    
    with col2:
        # Métodos de pago
        if 'metodos_pago' in datos:
            st.markdown("### 💳 Métodos de Pago")
            
            metodos = datos['metodos_pago']
            df_metodos = pd.DataFrame(list(metodos.items()), columns=['Método', 'Cantidad'])
            
            fig_metodos = px.bar(
                df_metodos,
                x='Método',
                y='Cantidad',
                title='Facturas por Método de Pago'
            )
            st.plotly_chart(fig_metodos, use_container_width=True)

def generar_dashboard_simulado(backend_url: str, fecha_inicio: date, fecha_fin: date):
    """Generar dashboard con datos reales disponibles"""
    
    try:
        # Obtener facturas del período
        params = {
            "fecha_inicio": fecha_inicio.isoformat(),
            "fecha_fin": fecha_fin.isoformat()
        }
        
        response_facturas = requests.get(f"{backend_url}/api/facturas", params=params)
        
        if response_facturas.status_code == 200:
            facturas = response_facturas.json()
            
            # Calcular métricas básicas
            total_facturas = len(facturas)
            ventas_totales = sum(f.get('total', 0) for f in facturas)
            ticket_promedio = ventas_totales / total_facturas if total_facturas > 0 else 0
            
            # Clientes únicos
            clientes_unicos = len(set(f.get('cliente_id') for f in facturas if f.get('cliente_id')))
            
            # Mostrar métricas
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("💰 Ventas Totales", f"${ventas_totales:,.0f}")
            
            with col2:
                st.metric("🧾 Total Facturas", total_facturas)
            
            with col3:
                st.metric("👥 Clientes", clientes_unicos)
            
            with col4:
                st.metric("💵 Ticket Promedio", f"${ticket_promedio:,.2f}")
            
            # Generar gráficos básicos
            if facturas:
                generar_graficos_basicos(facturas)
        else:
            st.info("📭 No hay datos de facturas disponibles para el período seleccionado")
            
    except Exception as e:
        st.error(f"Error al generar dashboard: {e}")

def generar_graficos_basicos(facturas: List[Dict]):
    """Generar gráficos básicos con datos de facturas"""
    
    df_facturas = pd.DataFrame(facturas)
    
    if df_facturas.empty:
        return
    
    # Gráfico de ventas por día
    if 'fecha_factura' in df_facturas.columns:
        st.markdown("### 📈 Ventas Diarias")
        
        df_facturas['fecha_factura'] = pd.to_datetime(df_facturas['fecha_factura'])
        ventas_diarias = df_facturas.groupby(df_facturas['fecha_factura'].dt.date)['total'].sum().reset_index()
        
        fig_diarias = px.bar(
            ventas_diarias,
            x='fecha_factura',
            y='total',
            title='Ventas por Día'
        )
        st.plotly_chart(fig_diarias, use_container_width=True)
    
    # Distribución de montos
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 💰 Distribución de Montos")
        
        fig_hist = px.histogram(
            df_facturas,
            x='total',
            nbins=20,
            title='Distribución de Montos de Facturas'
        )
        st.plotly_chart(fig_hist, use_container_width=True)
    
    with col2:
        # Estados de facturas si está disponible
        if 'estado' in df_facturas.columns:
            st.markdown("### 📊 Estados de Facturas")
            
            estados_count = df_facturas['estado'].value_counts()
            fig_estados = px.pie(
                values=estados_count.values,
                names=estados_count.index,
                title='Distribución por Estado'
            )
            st.plotly_chart(fig_estados, use_container_width=True)

def reportes_detallados(backend_url: str):
    """Reportes detallados de ventas"""
    
    st.subheader("📋 Reportes Detallados")
    
    # Selector de tipo de reporte
    tipo_reporte = st.selectbox(
        "Seleccione Tipo de Reporte:",
        [
            "Ventas por Período",
            "Ventas por Cliente",
            "Ventas por Producto", 
            "Comisiones de Vendedores",
            "Análisis de Rentabilidad",
            "Reporte de Devoluciones"
        ]
    )
    
    # Filtros comunes
    col1, col2 = st.columns(2)
    
    with col1:
        fecha_desde = st.date_input("Desde:", value=date.today() - timedelta(days=30))
    
    with col2:
        fecha_hasta = st.date_input("Hasta:", value=date.today())
    
    # Generar reporte según tipo
    if tipo_reporte == "Ventas por Período":
        generar_reporte_periodo(backend_url, fecha_desde, fecha_hasta)
    elif tipo_reporte == "Ventas por Cliente":
        generar_reporte_clientes(backend_url, fecha_desde, fecha_hasta)
    elif tipo_reporte == "Ventas por Producto":
        generar_reporte_productos(backend_url, fecha_desde, fecha_hasta)
    elif tipo_reporte == "Comisiones de Vendedores":
        generar_reporte_comisiones(backend_url, fecha_desde, fecha_hasta)
    elif tipo_reporte == "Análisis de Rentabilidad":
        generar_reporte_rentabilidad(backend_url, fecha_desde, fecha_hasta)
    elif tipo_reporte == "Reporte de Devoluciones":
        generar_reporte_devoluciones(backend_url, fecha_desde, fecha_hasta)

def generar_reporte_periodo(backend_url: str, fecha_desde: date, fecha_hasta: date):
    """Generar reporte de ventas por período"""
    
    st.markdown("### 📅 Reporte de Ventas por Período")
    
    try:
        params = {
            "fecha_inicio": fecha_desde.isoformat(),
            "fecha_fin": fecha_hasta.isoformat()
        }
        
        with st.spinner("Generando reporte..."):
            response = requests.get(f"{backend_url}/api/facturas", params=params)
        
        if response.status_code == 200:
            facturas = response.json()
            
            if facturas:
                df_facturas = pd.DataFrame(facturas)
                
                # Resumen del período
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Facturas", len(facturas))
                
                with col2:
                    ventas_total = df_facturas['total'].sum()
                    st.metric("Ventas Totales", f"${ventas_total:,.2f}")
                
                with col3:
                    ticket_promedio = df_facturas['total'].mean()
                    st.metric("Ticket Promedio", f"${ticket_promedio:,.2f}")
                
                with col4:
                    clientes_unicos = df_facturas['cliente_id'].nunique() if 'cliente_id' in df_facturas.columns else 0
                    st.metric("Clientes", clientes_unicos)
                
                # Tabla detallada
                st.markdown("#### 📋 Detalle de Facturas")
                
                # Preparar datos para mostrar
                df_display = df_facturas.copy()
                if 'fecha_factura' in df_display.columns:
                    df_display['fecha_factura'] = pd.to_datetime(df_display['fecha_factura']).dt.strftime('%Y-%m-%d')
                
                # Formatear total
                if 'total' in df_display.columns:
                    df_display['total_fmt'] = df_display['total'].apply(lambda x: f"${float(x):,.2f}")
                
                # Seleccionar columnas relevantes
                columnas_mostrar = ['numero_factura', 'fecha_factura', 'cliente_nombre', 'total_fmt', 'estado']
                columnas_disponibles = [col for col in columnas_mostrar if col in df_display.columns or col == 'total_fmt']
                
                if columnas_disponibles:
                    df_tabla = df_display[columnas_disponibles].copy()
                    
                    # Renombrar columnas
                    nombres_cols = {
                        'numero_factura': 'Número',
                        'fecha_factura': 'Fecha',
                        'cliente_nombre': 'Cliente',
                        'total_fmt': 'Total',
                        'estado': 'Estado'
                    }
                    
                    df_tabla.columns = [nombres_cols.get(col, col) for col in df_tabla.columns]
                    
                    st.dataframe(df_tabla, use_container_width=True, hide_index=True)
                
                # Gráfico de evolución
                if len(facturas) > 1:
                    st.markdown("#### 📈 Evolución de Ventas")
                    
                    df_facturas['fecha_factura'] = pd.to_datetime(df_facturas['fecha_factura'])
                    ventas_diarias = df_facturas.groupby(df_facturas['fecha_factura'].dt.date)['total'].sum().reset_index()
                    
                    fig_evolucion = px.line(
                        ventas_diarias,
                        x='fecha_factura',
                        y='total',
                        title='Evolución de Ventas en el Período',
                        markers=True
                    )
                    st.plotly_chart(fig_evolucion, use_container_width=True)
            else:
                st.info("📭 No se encontraron ventas en el período seleccionado")
        else:
            st.error("Error al cargar datos de ventas")
            
    except Exception as e:
        st.error(f"Error al generar reporte: {e}")

def generar_reporte_clientes(backend_url: str, fecha_desde: date, fecha_hasta: date):
    """Generar reporte de ventas por cliente"""
    
    st.markdown("### 👥 Reporte de Ventas por Cliente")
    
    try:
        # Obtener facturas del período
        params = {
            "fecha_inicio": fecha_desde.isoformat(),
            "fecha_fin": fecha_hasta.isoformat()
        }
        
        with st.spinner("Generando reporte por clientes..."):
            response_facturas = requests.get(f"{backend_url}/api/facturas", params=params)
            response_clientes = requests.get(f"{backend_url}/api/clientes")
        
        if response_facturas.status_code == 200 and response_clientes.status_code == 200:
            facturas = response_facturas.json()
            clientes = response_clientes.json()
            
            if facturas:
                # Crear diccionario de clientes para mapear nombres
                clientes_dict = {c['id_cliente']: c for c in clientes}
                
                # Analizar ventas por cliente
                df_facturas = pd.DataFrame(facturas)
                
                if 'cliente_id' in df_facturas.columns:
                    ventas_cliente = df_facturas.groupby('cliente_id').agg({
                        'total': ['sum', 'count', 'mean'],
                        'fecha_factura': ['min', 'max']
                    }).round(2)
                    
                    # Aplanar columnas
                    ventas_cliente.columns = ['Total_Ventas', 'Num_Facturas', 'Ticket_Promedio', 'Primera_Compra', 'Ultima_Compra']
                    ventas_cliente = ventas_cliente.reset_index()
                    
                    # Agregar información del cliente
                    ventas_cliente['Nombre_Cliente'] = ventas_cliente['cliente_id'].apply(
                        lambda x: clientes_dict.get(x, {}).get('nombre_completo', f'Cliente {x}')
                    )
                    
                    # Ordenar por ventas totales
                    ventas_cliente = ventas_cliente.sort_values('Total_Ventas', ascending=False)
                    
                    # Mostrar métricas
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Clientes con Compras", len(ventas_cliente))
                    
                    with col2:
                        mejor_cliente = ventas_cliente.iloc[0] if len(ventas_cliente) > 0 else None
                        if mejor_cliente is not None:
                            st.metric("Mejor Cliente", f"${mejor_cliente['Total_Ventas']:,.2f}")
                    
                    with col3:
                        ticket_promedio_general = ventas_cliente['Ticket_Promedio'].mean()
                        st.metric("Ticket Prom. General", f"${ticket_promedio_general:,.2f}")
                    
                    # Tabla de ventas por cliente
                    st.markdown("#### 📊 Ranking de Clientes")
                    
                    # Formatear para mostrar
                    df_display = ventas_cliente.copy()
                    df_display['Total_Ventas'] = df_display['Total_Ventas'].apply(lambda x: f"${float(x):,.2f}")
                    df_display['Ticket_Promedio'] = df_display['Ticket_Promedio'].apply(lambda x: f"${float(x):,.2f}")
                    
                    # Seleccionar columnas para mostrar
                    cols_mostrar = ['Nombre_Cliente', 'Total_Ventas', 'Num_Facturas', 'Ticket_Promedio', 'Primera_Compra', 'Ultima_Compra']
                    df_tabla = df_display[cols_mostrar].copy()
                    df_tabla.columns = ['Cliente', 'Total Ventas', 'Facturas', 'Ticket Prom.', 'Primera Compra', 'Última Compra']
                    
                    st.dataframe(df_tabla, use_container_width=True, hide_index=True)
                    
                    # Gráfico de top clientes
                    if len(ventas_cliente) > 0:
                        st.markdown("#### 🏆 Top 10 Clientes por Ventas")
                        
                        top_10_clientes = ventas_cliente.head(10)
                        
                        fig_clientes = px.bar(
                            top_10_clientes,
                            x='Total_Ventas',
                            y='Nombre_Cliente',
                            orientation='h',
                            title='Top 10 Clientes por Volumen de Ventas'
                        )
                        fig_clientes.update_layout(yaxis={'categoryorder': 'total ascending'})
                        st.plotly_chart(fig_clientes, use_container_width=True)
                else:
                    st.warning("⚠️ No se encontró información de clientes en las facturas")
            else:
                st.info("📭 No se encontraron ventas en el período seleccionado")
        else:
            st.error("Error al cargar datos de clientes y facturas")
            
    except Exception as e:
        st.error(f"Error al generar reporte de clientes: {e}")

def generar_reporte_productos(backend_url: str, fecha_desde: date, fecha_hasta: date):
    """Generar reporte de ventas por producto"""
    
    st.markdown("### 📦 Reporte de Ventas por Producto")
    st.info("💡 Este reporte requiere datos detallados de items de factura")
    
    # Placeholder para futuras implementaciones con detalles de factura
    st.markdown("""
    **Funcionalidades a implementar:**
    - Top productos más vendidos
    - Análisis de rentabilidad por producto
    - Productos con mayor rotación
    - Análisis de categorías de productos
    - Tendencias de venta por producto
    """)

def generar_reporte_comisiones(backend_url: str, fecha_desde: date, fecha_hasta: date):
    """Generar reporte de comisiones de vendedores"""
    
    st.markdown("### 💼 Reporte de Comisiones")
    st.info("💡 Este reporte requiere configuración de vendedores y comisiones")

def generar_reporte_rentabilidad(backend_url: str, fecha_desde: date, fecha_hasta: date):
    """Generar reporte de análisis de rentabilidad"""
    
    st.markdown("### 💹 Análisis de Rentabilidad")
    st.info("💡 Este reporte requiere datos de costos de productos")

def generar_reporte_devoluciones(backend_url: str, fecha_desde: date, fecha_hasta: date):
    """Generar reporte de devoluciones"""
    
    st.markdown("### 🔄 Reporte de Devoluciones")
    st.info("💡 Este reporte requiere funcionalidad de devoluciones implementada")

def analisis_periodo(backend_url: str):
    """Análisis comparativo por períodos"""
    
    st.subheader("🎯 Análisis Comparativo por Períodos")
    
    # Selector de tipo de análisis
    tipo_analisis = st.selectbox(
        "Tipo de Análisis:",
        ["Mensual", "Trimestral", "Anual", "Comparativo"]
    )
    
    if tipo_analisis == "Comparativo":
        analisis_comparativo(backend_url)
    else:
        analisis_periodo_simple(backend_url, tipo_analisis)

def analisis_comparativo(backend_url: str):
    """Análisis comparativo entre dos períodos"""
    
    st.markdown("### 📊 Análisis Comparativo")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Período 1:**")
        periodo1_inicio = st.date_input("Desde (P1):", value=date.today() - timedelta(days=60), key="comp_p1_inicio")
        periodo1_fin = st.date_input("Hasta (P1):", value=date.today() - timedelta(days=30), key="comp_p1_fin")
    
    with col2:
        st.markdown("**Período 2:**")
        periodo2_inicio = st.date_input("Desde (P2):", value=date.today() - timedelta(days=30), key="comp_p2_inicio")
        periodo2_fin = st.date_input("Hasta (P2):", value=date.today(), key="comp_p2_fin")
    
    if st.button("🔍 Generar Comparativo", use_container_width=True):
        generar_comparativo_periodos(backend_url, periodo1_inicio, periodo1_fin, periodo2_inicio, periodo2_fin)

def generar_comparativo_periodos(backend_url: str, p1_inicio: date, p1_fin: date, p2_inicio: date, p2_fin: date):
    """Generar comparativo entre dos períodos"""
    
    try:
        # Obtener datos de ambos períodos
        params1 = {"fecha_inicio": p1_inicio.isoformat(), "fecha_fin": p1_fin.isoformat()}
        params2 = {"fecha_inicio": p2_inicio.isoformat(), "fecha_fin": p2_fin.isoformat()}
        
        with st.spinner("Generando análisis comparativo..."):
            response1 = requests.get(f"{backend_url}/api/facturas", params=params1)
            response2 = requests.get(f"{backend_url}/api/facturas", params=params2)
        
        if response1.status_code == 200 and response2.status_code == 200:
            facturas1 = response1.json()
            facturas2 = response2.json()
            
            # Calcular métricas de ambos períodos
            metricas1 = calcular_metricas_periodo(facturas1)
            metricas2 = calcular_metricas_periodo(facturas2)
            
            # Mostrar comparativo
            mostrar_comparativo_metricas(metricas1, metricas2, p1_inicio, p1_fin, p2_inicio, p2_fin)
        else:
            st.error("Error al cargar datos para el comparativo")
            
    except Exception as e:
        st.error(f"Error al generar comparativo: {e}")

def calcular_metricas_periodo(facturas: List[Dict]) -> Dict[str, Any]:
    """Calcular métricas de un período"""
    
    if not facturas:
        return {
            'total_facturas': 0,
            'ventas_totales': 0,
            'ticket_promedio': 0,
            'clientes_unicos': 0
        }
    
    df = pd.DataFrame(facturas)
    
    return {
        'total_facturas': len(facturas),
        'ventas_totales': df['total'].sum(),
        'ticket_promedio': df['total'].mean(),
        'clientes_unicos': df['cliente_id'].nunique() if 'cliente_id' in df.columns else 0
    }

def mostrar_comparativo_metricas(metricas1: Dict, metricas2: Dict, p1_inicio: date, p1_fin: date, p2_inicio: date, p2_fin: date):
    """Mostrar comparativo de métricas entre períodos"""
    
    st.markdown("### 📊 Comparativo de Períodos")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"**Período 1: {p1_inicio} - {p1_fin}**")
        st.metric("Facturas", metricas1['total_facturas'])
        st.metric("Ventas Totales", f"${metricas1['ventas_totales']:,.2f}")
        st.metric("Ticket Promedio", f"${metricas1['ticket_promedio']:,.2f}")
        st.metric("Clientes", metricas1['clientes_unicos'])
    
    with col2:
        st.markdown(f"**Período 2: {p2_inicio} - {p2_fin}**")
        
        # Calcular variaciones
        var_facturas = metricas2['total_facturas'] - metricas1['total_facturas']
        var_ventas = metricas2['ventas_totales'] - metricas1['ventas_totales']
        var_ticket = metricas2['ticket_promedio'] - metricas1['ticket_promedio']
        var_clientes = metricas2['clientes_unicos'] - metricas1['clientes_unicos']
        
        st.metric("Facturas", metricas2['total_facturas'], delta=var_facturas)
        st.metric("Ventas Totales", f"${metricas2['ventas_totales']:,.2f}", 
                 delta=f"${var_ventas:,.2f}")
        st.metric("Ticket Promedio", f"${metricas2['ticket_promedio']:,.2f}", 
                 delta=f"${var_ticket:,.2f}")
        st.metric("Clientes", metricas2['clientes_unicos'], delta=var_clientes)
    
    # Gráfico comparativo
    st.markdown("### 📈 Comparativo Visual")
    
    categorias = ['Facturas', 'Ventas Totales', 'Ticket Promedio', 'Clientes']
    valores_p1 = [
        metricas1['total_facturas'],
        metricas1['ventas_totales'],
        metricas1['ticket_promedio'],
        metricas1['clientes_unicos']
    ]
    valores_p2 = [
        metricas2['total_facturas'],
        metricas2['ventas_totales'],
        metricas2['ticket_promedio'],
        metricas2['clientes_unicos']
    ]
    
    fig_comp = go.Figure(data=[
        go.Bar(name='Período 1', x=categorias, y=valores_p1),
        go.Bar(name='Período 2', x=categorias, y=valores_p2)
    ])
    
    fig_comp.update_layout(
        title='Comparativo entre Períodos',
        barmode='group',
        xaxis_title='Métricas',
        yaxis_title='Valores'
    )
    
    st.plotly_chart(fig_comp, use_container_width=True)

def analisis_periodo_simple(backend_url: str, tipo_periodo: str):
    """Análisis simple por período"""
    
    st.markdown(f"### 📅 Análisis {tipo_periodo}")
    st.info(f"💡 Análisis {tipo_periodo.lower()} implementado en futuras versiones")

def top_productos_clientes(backend_url: str):
    """Análisis de top productos y clientes"""
    
    st.subheader("🏆 Top Productos y Clientes")
    
    # Filtros de período
    col1, col2 = st.columns(2)
    
    with col1:
        fecha_desde = st.date_input("Desde:", value=date.today() - timedelta(days=30), key="top_fecha_desde")
    
    with col2:
        fecha_hasta = st.date_input("Hasta:", value=date.today(), key="top_fecha_hasta")
    
    # Tabs para diferentes análisis
    tab_clientes, tab_productos = st.tabs(["👥 Top Clientes", "📦 Top Productos"])
    
    with tab_clientes:
        generar_top_clientes(backend_url, fecha_desde, fecha_hasta)
    
    with tab_productos:
        generar_top_productos(backend_url, fecha_desde, fecha_hasta)

def generar_top_clientes(backend_url: str, fecha_desde: date, fecha_hasta: date):
    """Generar ranking de top clientes"""
    
    st.markdown("### 👥 Ranking de Mejores Clientes")
    
    # Usar la función ya implementada
    generar_reporte_clientes(backend_url, fecha_desde, fecha_hasta)

def generar_top_productos(backend_url: str, fecha_desde: date, fecha_hasta: date):
    """Generar ranking de top productos"""
    
    st.markdown("### 📦 Ranking de Productos Más Vendidos")
    st.info("💡 Este análisis requiere datos detallados de items de factura")

def exportar_reportes(backend_url: str):
    """Funcionalidad de exportación de reportes"""
    
    st.subheader("📤 Exportar Reportes")
    
    st.markdown("""
    ### 📋 Opciones de Exportación
    
    Seleccione el tipo de reporte que desea exportar:
    """)
    
    # Opciones de exportación
    tipo_exportacion = st.selectbox(
        "Tipo de Reporte:",
        [
            "Ventas por Período",
            "Ranking de Clientes",
            "Análisis de Productos",
            "Dashboard Completo",
            "Reporte Personalizado"
        ]
    )
    
    # Formato de exportación
    formato = st.selectbox(
        "Formato:",
        ["Excel (.xlsx)", "CSV (.csv)", "PDF (.pdf)"]
    )
    
    # Filtros de fecha
    col1, col2 = st.columns(2)
    
    with col1:
        fecha_desde = st.date_input("Desde:", value=date.today() - timedelta(days=30), key="export_fecha_desde")
    
    with col2:
        fecha_hasta = st.date_input("Hasta:", value=date.today(), key="export_fecha_hasta")
    
    # Opciones adicionales
    incluir_graficos = st.checkbox("Incluir Gráficos", value=True)
    incluir_resumen = st.checkbox("Incluir Resumen Ejecutivo", value=True)
    
    # Botón de exportación
    if st.button("📥 Generar y Descargar Reporte", use_container_width=True, type="primary"):
        generar_exportacion(
            backend_url, 
            tipo_exportacion, 
            formato, 
            fecha_desde, 
            fecha_hasta,
            incluir_graficos,
            incluir_resumen
        )

def generar_exportacion(backend_url: str, tipo_reporte: str, formato: str, fecha_desde: date, fecha_hasta: date, incluir_graficos: bool, incluir_resumen: bool):
    """Generar archivo de exportación"""
    
    try:
        with st.spinner(f"Generando reporte en formato {formato}..."):
            # Obtener datos
            params = {
                "fecha_inicio": fecha_desde.isoformat(),
                "fecha_fin": fecha_hasta.isoformat()
            }
            
            response = requests.get(f"{backend_url}/api/facturas", params=params)
            
            if response.status_code == 200:
                facturas = response.json()
                
                if formato.startswith("Excel"):
                    generar_excel(facturas, tipo_reporte, fecha_desde, fecha_hasta)
                elif formato.startswith("CSV"):
                    generar_csv(facturas, tipo_reporte, fecha_desde, fecha_hasta)
                elif formato.startswith("PDF"):
                    st.info("💡 Exportación PDF en desarrollo")
                
            else:
                st.error("Error al obtener datos para exportación")
                
    except Exception as e:
        st.error(f"Error al generar exportación: {e}")

def generar_excel(facturas: List[Dict], tipo_reporte: str, fecha_desde: date, fecha_hasta: date):
    """Generar archivo Excel"""
    
    if not facturas:
        st.warning("⚠️ No hay datos para exportar")
        return
    
    # Crear archivo Excel en memoria
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        # Hoja principal con datos
        df_facturas = pd.DataFrame(facturas)
        df_facturas.to_excel(writer, sheet_name='Ventas Detalladas', index=False)
        
        # Hoja resumen
        resumen_data = {
            'Métrica': ['Total Facturas', 'Ventas Totales', 'Ticket Promedio', 'Período'],
            'Valor': [
                len(facturas),
                f"${float(df_facturas['total'].sum()):,.2f}",
                f"${float(df_facturas['total'].mean()):,.2f}",
                f"{fecha_desde} a {fecha_hasta}"
            ]
        }
        
        df_resumen = pd.DataFrame(resumen_data)
        df_resumen.to_excel(writer, sheet_name='Resumen', index=False)
    
    output.seek(0)
    
    # Botón de descarga
    st.download_button(
        label="📥 Descargar Reporte Excel",
        data=output.getvalue(),
        file_name=f"reporte_ventas_{fecha_desde}_{fecha_hasta}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    
    st.success("✅ Archivo Excel generado exitosamente!")

def generar_csv(facturas: List[Dict], tipo_reporte: str, fecha_desde: date, fecha_hasta: date):
    """Generar archivo CSV"""
    
    if not facturas:
        st.warning("⚠️ No hay datos para exportar")
        return
    
    df_facturas = pd.DataFrame(facturas)
    csv_data = df_facturas.to_csv(index=False)
    
    # Botón de descarga
    st.download_button(
        label="📥 Descargar Reporte CSV",
        data=csv_data,
        file_name=f"reporte_ventas_{fecha_desde}_{fecha_hasta}.csv",
        mime="text/csv"
    )
    
    st.success("✅ Archivo CSV generado exitosamente!")