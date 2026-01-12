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

def convertir_a_float_seguro(df: pd.DataFrame, columna: str) -> pd.DataFrame:
    """
    Convertir columna a float de manera segura, manejando strings con comas,
    decimales, y valores ya numéricos.
    """
    if columna not in df.columns:
        return df
    
    def safe_convert(valor):
        if pd.isna(valor):
            return 0.0
        if isinstance(valor, (int, float)):
            return float(valor)
        if isinstance(valor, str):
            # Remover comas y espacios
            valor_limpio = valor.replace(',', '').replace(' ', '').strip()
            try:
                return float(valor_limpio)
            except (ValueError, AttributeError):
                return 0.0
        return 0.0
    
    df[columna] = df[columna].apply(safe_convert)
    return df

def render_page(backend_url: str):
    """Renderizar página de reportes de ventas"""
    
    st.header("📊 Reportes de Ventas")
    st.markdown("Sistema completo de reportes y análisis de ventas para la toma de decisiones")
    
    # Tabs para organizar reportes
    tab1, tab2, tab3 = st.tabs([
        "📈 Dashboard General", 
        "🏆 Top Productos/Clientes",
        "📤 Exportar"
    ])
    
    with tab1:
        dashboard_general(backend_url)
    
    with tab2:
        top_productos_clientes(backend_url)
    
    with tab3:
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
        st.plotly_chart(fig_ventas, width="stretch")
    
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
            st.plotly_chart(fig_cat, width="stretch")
    
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
            st.plotly_chart(fig_metodos, width="stretch")

def generar_dashboard_simulado(backend_url: str, fecha_inicio: date, fecha_fin: date):
    """Generar dashboard con datos reales disponibles"""
    
    try:
        # Obtener facturas del período
        params = {
            "fecha_desde": fecha_inicio.isoformat(),
            "fecha_hasta": fecha_fin.isoformat()
        }
        
        response_facturas = requests.get(f"{backend_url}/api/facturacion/facturas", params=params)
        
        if response_facturas.status_code == 200:
            facturas = response_facturas.json()
            
            # Calcular métricas básicas y convertir a float
            total_facturas = len(facturas)
            # Convertir cada total a float de manera segura
            totales = []
            for f in facturas:
                total_valor = f.get('total', 0)
                if isinstance(total_valor, str):
                    # Limpiar el string y convertir
                    total_valor = total_valor.replace(',', '').strip()
                totales.append(float(total_valor) if total_valor else 0.0)
            
            ventas_totales = sum(totales)
            ticket_promedio = ventas_totales / total_facturas if total_facturas > 0 else 0.0
            
            # Clientes únicos
            clientes_unicos = len(set(f.get('id_cliente') for f in facturas if f.get('id_cliente')))
            
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
    
    # Convertir columna total a float para evitar concatenación de strings
    if 'total' in df_facturas.columns:
        df_facturas = convertir_a_float_seguro(df_facturas, 'total')
    
    # Gráfico de ventas por día
    if 'fecha_emision' in df_facturas.columns:
        st.markdown("### 📈 Ventas Diarias")
        
        df_facturas['fecha_emision'] = pd.to_datetime(df_facturas['fecha_emision'])
        ventas_diarias = df_facturas.groupby(df_facturas['fecha_emision'].dt.date)['total'].sum().reset_index()
        
        fig_diarias = px.bar(
            ventas_diarias,
            x='fecha_emision',
            y='total',
            title='Ventas por Día'
        )
        st.plotly_chart(fig_diarias, width="stretch")
    
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
        st.plotly_chart(fig_hist, width="stretch")
    
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
            st.plotly_chart(fig_estados, width="stretch")

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
            "fecha_desde": fecha_desde.isoformat(),
            "fecha_hasta": fecha_hasta.isoformat()
        }
        
        with st.spinner("Generando reporte..."):
            response = requests.get(f"{backend_url}/api/facturacion/facturas", params=params)
        
        if response.status_code == 200:
            facturas = response.json()
            
            if facturas:
                df_facturas = pd.DataFrame(facturas)
                
                # Convertir columna total a float para evitar concatenación de strings
                if 'total' in df_facturas.columns:
                    df_facturas = convertir_a_float_seguro(df_facturas, 'total')
                
                # Resumen del período
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Facturas", len(facturas))
                
                with col2:
                    ventas_total = float(df_facturas['total'].sum())
                    st.metric("Ventas Totales", f"${ventas_total:,.2f}")
                
                with col3:
                    ticket_promedio = float(df_facturas['total'].mean())
                    st.metric("Ticket Promedio", f"${ticket_promedio:,.2f}")
                
                with col4:
                    clientes_unicos = df_facturas['id_cliente'].nunique() if 'id_cliente' in df_facturas.columns else 0
                    st.metric("Clientes", clientes_unicos)
                
                # Tabla detallada
                st.markdown("#### 📋 Detalle de Facturas")
                
                # Preparar datos para mostrar
                df_display = df_facturas.copy()
                if 'fecha_emision' in df_display.columns:
                    df_display['fecha_emision'] = pd.to_datetime(df_display['fecha_emision']).dt.strftime('%Y-%m-%d')
                
                # Formatear total
                if 'total' in df_display.columns:
                    df_display['total_fmt'] = df_display['total'].apply(lambda x: f"${float(x):,.2f}")
                
                # Seleccionar columnas relevantes
                columnas_mostrar = ['numero_factura', 'fecha_emision', 'id_cliente', 'total_fmt', 'estado_factura']
                columnas_disponibles = [col for col in columnas_mostrar if col in df_display.columns or col == 'total_fmt']
                
                if columnas_disponibles:
                    df_tabla = df_display[columnas_disponibles].copy()
                    
                    # Renombrar columnas
                    nombres_cols = {
                        'numero_factura': 'Número',
                        'fecha_emision': 'Fecha',
                        'id_cliente': 'Cliente',
                        'total_fmt': 'Total',
                        'estado_factura': 'Estado'
                    }
                    
                    df_tabla.columns = [nombres_cols.get(col, col) for col in df_tabla.columns]
                    
                    st.dataframe(df_tabla, width="stretch", hide_index=True)
                
                # Gráfico de evolución
                if len(facturas) > 1:
                    st.markdown("#### 📈 Evolución de Ventas")
                    
                    df_facturas['fecha_emision'] = pd.to_datetime(df_facturas['fecha_emision'])
                    ventas_diarias = df_facturas.groupby(df_facturas['fecha_emision'].dt.date)['total'].sum().reset_index()
                    
                    fig_evolucion = px.line(
                        ventas_diarias,
                        x='fecha_emision',
                        y='total',
                        title='Evolución de Ventas en el Período',
                        markers=True
                    )
                    st.plotly_chart(fig_evolucion, width="stretch")
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
            "fecha_desde": fecha_desde.isoformat(),
            "fecha_hasta": fecha_hasta.isoformat()
        }
        
        with st.spinner("Generando reporte por clientes..."):
            response_facturas = requests.get(f"{backend_url}/api/facturacion/facturas", params=params)
            response_clientes = requests.get(f"{backend_url}/api/clientes")
        
        if response_facturas.status_code == 200 and response_clientes.status_code == 200:
            facturas = response_facturas.json()
            clientes = response_clientes.json()
            
            if facturas:
                # Crear diccionario de clientes para mapear nombres
                clientes_dict = {c['id_cliente']: c for c in clientes}
                
                # Analizar ventas por cliente
                df_facturas = pd.DataFrame(facturas)
                
                # Convertir columna total a float para evitar concatenación de strings
                if 'total' in df_facturas.columns:
                    df_facturas = convertir_a_float_seguro(df_facturas, 'total')
                
                if 'id_cliente' in df_facturas.columns:
                    ventas_cliente = df_facturas.groupby('id_cliente').agg({
                        'total': ['sum', 'count', 'mean'],
                        'fecha_emision': ['min', 'max']
                    }).round(2)
                    
                    # Aplanar columnas
                    ventas_cliente.columns = ['Total_Ventas', 'Num_Facturas', 'Ticket_Promedio', 'Primera_Compra', 'Ultima_Compra']
                    ventas_cliente = ventas_cliente.reset_index()
                    
                    # Agregar información del cliente
                    ventas_cliente['Nombre_Cliente'] = ventas_cliente['id_cliente'].apply(
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
                            st.metric("Mejor Cliente", f"${float(mejor_cliente['Total_Ventas']):,.2f}")
                    
                    with col3:
                        ticket_promedio_general = float(ventas_cliente['Ticket_Promedio'].mean())
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
                    
                    st.dataframe(df_tabla, width="stretch", hide_index=True)
                    
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
                        st.plotly_chart(fig_clientes, width="stretch")
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
    
    if st.button("🔍 Generar Comparativo", width="stretch"):
        generar_comparativo_periodos(backend_url, periodo1_inicio, periodo1_fin, periodo2_inicio, periodo2_fin)

def generar_comparativo_periodos(backend_url: str, p1_inicio: date, p1_fin: date, p2_inicio: date, p2_fin: date):
    """Generar comparativo entre dos períodos"""
    
    try:
        # Obtener datos de ambos períodos
        params1 = {"fecha_desde": p1_inicio.isoformat(), "fecha_hasta": p1_fin.isoformat()}
        params2 = {"fecha_desde": p2_inicio.isoformat(), "fecha_hasta": p2_fin.isoformat()}
        
        with st.spinner("Generando análisis comparativo..."):
            response1 = requests.get(f"{backend_url}/api/facturacion/facturas", params=params1)
            response2 = requests.get(f"{backend_url}/api/facturacion/facturas", params=params2)
        
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
    
    # Convertir columna total a float para evitar concatenación de strings
    if 'total' in df.columns:
        df = convertir_a_float_seguro(df, 'total')
    
    return {
        'total_facturas': len(facturas),
        'ventas_totales': float(df['total'].sum()),
        'ticket_promedio': float(df['total'].mean()),
        'clientes_unicos': df['id_cliente'].nunique() if 'id_cliente' in df.columns else 0
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
        var_ventas = float(metricas2['ventas_totales']) - float(metricas1['ventas_totales'])
        var_ticket = float(metricas2['ticket_promedio']) - float(metricas1['ticket_promedio'])
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
    
    st.plotly_chart(fig_comp, width="stretch")

def analisis_periodo_simple(backend_url: str, tipo_periodo: str):
    """Análisis detallado por período (Mensual, Trimestral, Anual)"""
    
    st.markdown(f"### 📅 Análisis {tipo_periodo}")
    
    # Configuración de rango según tipo de período
    if tipo_periodo == "Mensual":
        # Selector de mes y año
        col1, col2 = st.columns(2)
        with col1:
            año_seleccionado = st.selectbox("Año:", list(range(datetime.now().year, datetime.now().year - 5, -1)), key="mes_año")
        with col2:
            meses = {
                "Enero": 1, "Febrero": 2, "Marzo": 3, "Abril": 4,
                "Mayo": 5, "Junio": 6, "Julio": 7, "Agosto": 8,
                "Septiembre": 9, "Octubre": 10, "Noviembre": 11, "Diciembre": 12
            }
            mes_nombre = st.selectbox("Mes:", list(meses.keys()), index=datetime.now().month - 1, key="mes_nombre")
            mes_seleccionado = meses[mes_nombre]
        
        # Calcular primer y último día del mes
        primer_dia = date(año_seleccionado, mes_seleccionado, 1)
        if mes_seleccionado == 12:
            ultimo_dia = date(año_seleccionado + 1, 1, 1) - timedelta(days=1)
        else:
            ultimo_dia = date(año_seleccionado, mes_seleccionado + 1, 1) - timedelta(days=1)
        
        fecha_desde = primer_dia
        fecha_hasta = ultimo_dia
        titulo_periodo = f"{mes_nombre} {año_seleccionado}"
        
    elif tipo_periodo == "Trimestral":
        # Selector de trimestre y año
        col1, col2 = st.columns(2)
        with col1:
            año_seleccionado = st.selectbox("Año:", list(range(datetime.now().year, datetime.now().year - 5, -1)), key="trim_año")
        with col2:
            trimestre = st.selectbox("Trimestre:", ["Q1 (Ene-Mar)", "Q2 (Abr-Jun)", "Q3 (Jul-Sep)", "Q4 (Oct-Dic)"], key="trimestre")
        
        # Calcular fechas del trimestre
        trimestre_num = int(trimestre[1])
        mes_inicio = (trimestre_num - 1) * 3 + 1
        mes_fin = mes_inicio + 2
        
        fecha_desde = date(año_seleccionado, mes_inicio, 1)
        if mes_fin == 12:
            fecha_hasta = date(año_seleccionado, 12, 31)
        else:
            fecha_hasta = date(año_seleccionado, mes_fin + 1, 1) - timedelta(days=1)
        
        titulo_periodo = f"{trimestre} {año_seleccionado}"
        
    else:  # Anual
        año_seleccionado = st.selectbox("Año:", list(range(datetime.now().year, datetime.now().year - 10, -1)), key="año_anual")
        fecha_desde = date(año_seleccionado, 1, 1)
        fecha_hasta = date(año_seleccionado, 12, 31)
        titulo_periodo = f"Año {año_seleccionado}"
    
    # Botón para generar análisis
    if st.button(f"📊 Generar Análisis {tipo_periodo}", type="primary", width="stretch"):
        generar_analisis_detallado(backend_url, fecha_desde, fecha_hasta, tipo_periodo, titulo_periodo)


def generar_analisis_detallado(backend_url: str, fecha_desde: date, fecha_hasta: date, tipo_periodo: str, titulo_periodo: str):
    """Generar análisis detallado con gráficos y métricas"""
    
    try:
        params = {"fecha_desde": fecha_desde.isoformat(), "fecha_hasta": fecha_hasta.isoformat()}
        
        with st.spinner(f"Generando análisis para {titulo_periodo}..."):
            response = requests.get(f"{backend_url}/api/facturacion/facturas", params=params)
        
        if response.status_code == 200:
            facturas = response.json()
            
            if not facturas:
                st.warning(f"📭 No hay datos de ventas para {titulo_periodo}")
                return
            
            # Convertir a DataFrame
            df_facturas = pd.DataFrame(facturas)
            
            # Convertir columna total a float
            if 'total' in df_facturas.columns:
                df_facturas = convertir_a_float_seguro(df_facturas, 'total')
            
            # Convertir fecha_emision a datetime
            df_facturas['fecha_emision'] = pd.to_datetime(df_facturas['fecha_emision'])
            
            # Mostrar resumen del período
            st.success(f"📊 Análisis generado para: **{titulo_periodo}**")
            st.info(f"📅 Período: {fecha_desde.strftime('%d/%m/%Y')} - {fecha_hasta.strftime('%d/%m/%Y')}")
            
            # Métricas principales
            mostrar_metricas_principales_periodo(df_facturas)
            
            st.markdown("---")
            
            # Gráficos de evolución
            mostrar_graficos_evolucion(df_facturas, tipo_periodo, titulo_periodo)
            
            st.markdown("---")
            
            # Análisis por estado de facturas
            mostrar_analisis_estados(df_facturas)
            
            st.markdown("---")
            
            # Top clientes del período
            mostrar_top_clientes_periodo(df_facturas)
            
        else:
            st.error(f"Error al cargar datos: {response.status_code}")
            
    except Exception as e:
        st.error(f"Error al generar análisis: {e}")


def mostrar_metricas_principales_periodo(df: pd.DataFrame):
    """Mostrar métricas principales del período"""
    
    st.markdown("### 💰 Métricas Principales")
    
    total_ventas = df['total'].sum()
    total_facturas = len(df)
    ticket_promedio = df['total'].mean()
    clientes_unicos = df['id_cliente'].nunique() if 'id_cliente' in df.columns else 0
    
    # Facturas por estado
    facturas_pagadas = len(df[df['estado_factura'] == 'PAGADA']) if 'estado_factura' in df.columns else 0
    facturas_pendientes = len(df[df['estado_factura'] == 'EMITIDA']) if 'estado_factura' in df.columns else 0
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="💵 Ventas Totales",
            value=f"${total_ventas:,.2f}",
            help="Suma total de todas las facturas"
        )
    
    with col2:
        st.metric(
            label="🧾 Total Facturas",
            value=f"{total_facturas:,}",
            help="Número total de facturas emitidas"
        )
    
    with col3:
        st.metric(
            label="🎯 Ticket Promedio",
            value=f"${ticket_promedio:,.2f}",
            help="Promedio de venta por factura"
        )
    
    with col4:
        st.metric(
            label="👥 Clientes",
            value=f"{clientes_unicos:,}",
            help="Clientes únicos que compraron"
        )
    
    # Segunda fila de métricas
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="✅ Facturas Pagadas",
            value=f"{facturas_pagadas:,}",
            delta=f"{(facturas_pagadas/total_facturas*100):.1f}%" if total_facturas > 0 else "0%"
        )
    
    with col2:
        st.metric(
            label="⏳ Facturas Pendientes",
            value=f"{facturas_pendientes:,}",
            delta=f"{(facturas_pendientes/total_facturas*100):.1f}%" if total_facturas > 0 else "0%"
        )
    
    with col3:
        venta_maxima = df['total'].max()
        st.metric(
            label="📈 Venta Máxima",
            value=f"${venta_maxima:,.2f}"
        )
    
    with col4:
        venta_minima = df['total'].min()
        st.metric(
            label="📉 Venta Mínima",
            value=f"${venta_minima:,.2f}"
        )


def mostrar_graficos_evolucion(df: pd.DataFrame, tipo_periodo: str, titulo_periodo: str):
    """Mostrar gráficos de evolución temporal"""
    
    st.markdown("### 📈 Evolución de Ventas")
    
    # Agrupar por fecha según el tipo de período
    if tipo_periodo == "Mensual":
        # Agrupar por día
        df_agrupado = df.groupby(df['fecha_emision'].dt.date).agg({
            'total': 'sum',
            'id_factura': 'count'
        }).reset_index()
        df_agrupado.columns = ['fecha', 'ventas', 'cantidad_facturas']
        titulo_eje_x = "Día del Mes"
        
    elif tipo_periodo == "Trimestral":
        # Agrupar por semana
        df['semana'] = df['fecha_emision'].dt.isocalendar().week
        df_agrupado = df.groupby('semana').agg({
            'total': 'sum',
            'id_factura': 'count'
        }).reset_index()
        df_agrupado.columns = ['semana', 'ventas', 'cantidad_facturas']
        df_agrupado['fecha'] = df_agrupado['semana'].apply(lambda x: f"Semana {x}")
        titulo_eje_x = "Semana del Año"
        
    else:  # Anual
        # Agrupar por mes
        df['mes'] = df['fecha_emision'].dt.month
        df_agrupado = df.groupby('mes').agg({
            'total': 'sum',
            'id_factura': 'count'
        }).reset_index()
        meses_nombres = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
        df_agrupado['fecha'] = df_agrupado['mes'].apply(lambda x: meses_nombres[x-1])
        df_agrupado.columns = ['mes', 'ventas', 'cantidad_facturas', 'fecha']
        titulo_eje_x = "Mes"
    
    # Crear gráfico de línea de evolución de ventas
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=('Evolución de Ventas ($)', 'Cantidad de Facturas'),
        vertical_spacing=0.15,
        row_heights=[0.6, 0.4]
    )
    
    # Gráfico de ventas
    fig.add_trace(
        go.Scatter(
            x=df_agrupado['fecha'],
            y=df_agrupado['ventas'],
            mode='lines+markers',
            name='Ventas',
            line=dict(color='#3498db', width=3),
            marker=dict(size=8),
            fill='tonexty',
            fillcolor='rgba(52, 152, 219, 0.2)'
        ),
        row=1, col=1
    )
    
    # Gráfico de cantidad de facturas
    fig.add_trace(
        go.Bar(
            x=df_agrupado['fecha'],
            y=df_agrupado['cantidad_facturas'],
            name='Facturas',
            marker=dict(color='#2ecc71')
        ),
        row=2, col=1
    )
    
    fig.update_xaxes(title_text=titulo_eje_x, row=1, col=1)
    fig.update_xaxes(title_text=titulo_eje_x, row=2, col=1)
    fig.update_yaxes(title_text="Ventas ($)", row=1, col=1)
    fig.update_yaxes(title_text="Cantidad", row=2, col=1)
    
    fig.update_layout(
        height=600,
        showlegend=True,
        title_text=f"Análisis de Ventas - {titulo_periodo}",
        hovermode='x unified'
    )
    
    st.plotly_chart(fig, use_container_width=True)


def mostrar_analisis_estados(df: pd.DataFrame):
    """Mostrar análisis de facturas por estado"""
    
    st.markdown("### 📊 Análisis por Estado de Facturas")
    
    if 'estado_factura' not in df.columns:
        st.info("No hay información de estados disponible")
        return
    
    # Agrupar por estado
    df_estados = df.groupby('estado_factura').agg({
        'total': 'sum',
        'id_factura': 'count'
    }).reset_index()
    df_estados.columns = ['estado', 'monto_total', 'cantidad']
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Gráfico de pie para cantidad
        fig_cantidad = px.pie(
            df_estados,
            values='cantidad',
            names='estado',
            title='Distribución de Facturas por Estado',
            color_discrete_sequence=['#2ecc71', '#f39c12', '#e74c3c', '#95a5a6']
        )
        st.plotly_chart(fig_cantidad, use_container_width=True)
    
    with col2:
        # Gráfico de pie para montos
        fig_monto = px.pie(
            df_estados,
            values='monto_total',
            names='estado',
            title='Distribución de Montos por Estado ($)',
            color_discrete_sequence=['#3498db', '#9b59b6', '#e67e22', '#34495e']
        )
        st.plotly_chart(fig_monto, use_container_width=True)
    
    # Tabla resumen
    st.markdown("#### 📋 Resumen por Estado")
    
    df_estados['monto_formateado'] = df_estados['monto_total'].apply(lambda x: f"${x:,.2f}")
    df_estados['porcentaje_cantidad'] = (df_estados['cantidad'] / df_estados['cantidad'].sum() * 100).round(2)
    df_estados['porcentaje_monto'] = (df_estados['monto_total'] / df_estados['monto_total'].sum() * 100).round(2)
    
    st.dataframe(
        df_estados[['estado', 'cantidad', 'porcentaje_cantidad', 'monto_formateado', 'porcentaje_monto']],
        column_config={
            'estado': 'Estado',
            'cantidad': 'Cantidad',
            'porcentaje_cantidad': '% Cantidad',
            'monto_formateado': 'Monto Total',
            'porcentaje_monto': '% Monto'
        },
        hide_index=True,
        use_container_width=True
    )


def mostrar_top_clientes_periodo(df: pd.DataFrame):
    """Mostrar top clientes del período"""
    
    st.markdown("### 🏆 Top 10 Clientes del Período")
    
    if 'id_cliente' not in df.columns:
        st.info("No hay información de clientes disponible")
        return
    
    # Agrupar por cliente
    df_clientes = df.groupby('id_cliente').agg({
        'total': 'sum',
        'id_factura': 'count'
    }).reset_index()
    df_clientes.columns = ['cliente', 'ventas_total', 'num_compras']
    df_clientes = df_clientes.sort_values('ventas_total', ascending=False).head(10)
    
    # Gráfico de barras horizontales
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        y=df_clientes['cliente'].astype(str),
        x=df_clientes['ventas_total'],
        orientation='h',
        marker=dict(
            color=df_clientes['ventas_total'],
            colorscale='Viridis',
            showscale=True
        ),
        text=df_clientes['ventas_total'].apply(lambda x: f'${x:,.2f}'),
        textposition='auto',
    ))
    
    fig.update_layout(
        title='Top 10 Clientes por Ventas',
        xaxis_title='Ventas Totales ($)',
        yaxis_title='Cliente ID',
        height=400,
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Tabla detallada
    df_clientes['ticket_promedio'] = df_clientes['ventas_total'] / df_clientes['num_compras']
    df_clientes['ventas_formateadas'] = df_clientes['ventas_total'].apply(lambda x: f"${x:,.2f}")
    df_clientes['ticket_formateado'] = df_clientes['ticket_promedio'].apply(lambda x: f"${x:,.2f}")
    
    st.dataframe(
        df_clientes[['cliente', 'num_compras', 'ventas_formateadas', 'ticket_formateado']],
        column_config={
            'cliente': 'Cliente ID',
            'num_compras': '# Compras',
            'ventas_formateadas': 'Ventas Totales',
            'ticket_formateado': 'Ticket Promedio'
        },
        hide_index=True,
        use_container_width=True
    )

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
    if st.button("📥 Generar y Descargar Reporte", width="stretch", type="primary"):
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
                "fecha_desde": fecha_desde.isoformat(),
                "fecha_hasta": fecha_hasta.isoformat()
            }
            
            response = requests.get(f"{backend_url}/api/facturacion/facturas", params=params)
            
            if response.status_code == 200:
                facturas = response.json()
                
                if formato.startswith("Excel"):
                    generar_excel(facturas, tipo_reporte, fecha_desde, fecha_hasta)
                elif formato.startswith("CSV"):
                    generar_csv(facturas, tipo_reporte, fecha_desde, fecha_hasta)
                elif formato.startswith("PDF"):
                    generar_pdf(facturas, tipo_reporte, fecha_desde, fecha_hasta, incluir_graficos, incluir_resumen)
                
            else:
                st.error("Error al obtener datos para exportación")
                
    except Exception as e:
        st.error(f"Error al generar exportación: {e}")

def generar_excel(facturas: List[Dict], tipo_reporte: str, fecha_desde: date, fecha_hasta: date):
    """Generar archivo Excel"""
    
    if not facturas:
        st.warning("⚠️ No hay datos para exportar")
        return
    
    try:
        # Crear archivo Excel en memoria
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Hoja principal con datos
            df_facturas = pd.DataFrame(facturas)
            
            # Convertir columna total a float para evitar concatenación de strings
            if 'total' in df_facturas.columns:
                df_facturas = convertir_a_float_seguro(df_facturas, 'total')
            
            # Formatear fecha_emision si existe
            if 'fecha_emision' in df_facturas.columns:
                df_facturas['fecha_emision'] = pd.to_datetime(df_facturas['fecha_emision']).dt.strftime('%Y-%m-%d')
            
            # Seleccionar columnas principales para exportar
            columnas_exportar = ['numero_factura', 'fecha_emision', 'id_cliente', 'total', 'estado_factura']
            columnas_disponibles = [col for col in columnas_exportar if col in df_facturas.columns]
            
            if columnas_disponibles:
                df_export = df_facturas[columnas_disponibles].copy()
                df_export.to_excel(writer, sheet_name='Ventas Detalladas', index=False)
            else:
                df_facturas.to_excel(writer, sheet_name='Ventas Detalladas', index=False)
            
            # Hoja resumen
            total_ventas = float(df_facturas['total'].sum()) if 'total' in df_facturas.columns else 0
            ticket_promedio = float(df_facturas['total'].mean()) if 'total' in df_facturas.columns else 0
            
            resumen_data = {
                'Métrica': ['Total Facturas', 'Ventas Totales', 'Ticket Promedio', 'Período'],
                'Valor': [
                    len(facturas),
                    f"${total_ventas:,.2f}",
                    f"${ticket_promedio:,.2f}",
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
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary",
            use_container_width=True
        )
        
        st.success("✅ Archivo Excel generado exitosamente!")
        
    except Exception as e:
        st.error(f"❌ Error al generar archivo Excel: {e}")

def generar_csv(facturas: List[Dict], tipo_reporte: str, fecha_desde: date, fecha_hasta: date):
    """Generar archivo CSV"""
    
    if not facturas:
        st.warning("⚠️ No hay datos para exportar")
        return
    
    try:
        df_facturas = pd.DataFrame(facturas)
        
        # Convertir columna total a float
        if 'total' in df_facturas.columns:
            df_facturas = convertir_a_float_seguro(df_facturas, 'total')
        
        # Formatear fecha_emision si existe
        if 'fecha_emision' in df_facturas.columns:
            df_facturas['fecha_emision'] = pd.to_datetime(df_facturas['fecha_emision']).dt.strftime('%Y-%m-%d')
        
        csv_data = df_facturas.to_csv(index=False)
        
        # Botón de descarga
        st.download_button(
            label="📥 Descargar Reporte CSV",
            data=csv_data,
            file_name=f"reporte_ventas_{fecha_desde}_{fecha_hasta}.csv",
            mime="text/csv",
            type="primary",
            use_container_width=True
        )
        
        st.success("✅ Archivo CSV generado exitosamente!")
        
    except Exception as e:
        st.error(f"❌ Error al generar archivo CSV: {e}")


def generar_pdf(facturas: List[Dict], tipo_reporte: str, fecha_desde: date, fecha_hasta: date, incluir_graficos: bool, incluir_resumen: bool):
    """Generar archivo PDF con reportlab"""
    
    if not facturas:
        st.warning("⚠️ No hay datos para exportar")
        return
    
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
        from reportlab.platypus import Image as RLImage
        from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
        
        # Crear archivo PDF en memoria
        buffer = io.BytesIO()
        
        # Configurar documento
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=0.5*inch,
            leftMargin=0.5*inch,
            topMargin=0.75*inch,
            bottomMargin=0.5*inch
        )
        
        # Preparar contenido
        story = []
        styles = getSampleStyleSheet()
        
        # Estilos personalizados
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#34495e'),
            spaceAfter=12,
            alignment=TA_CENTER
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=12,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        )
        
        # Título del reporte
        story.append(Paragraph("📊 REPORTE DE VENTAS", title_style))
        story.append(Paragraph(f"{tipo_reporte}", subtitle_style))
        story.append(Paragraph(f"Período: {fecha_desde.strftime('%d/%m/%Y')} - {fecha_hasta.strftime('%d/%m/%Y')}", subtitle_style))
        story.append(Spacer(1, 0.3*inch))
        
        # Preparar datos
        df_facturas = pd.DataFrame(facturas)
        
        # Convertir columna total a float
        if 'total' in df_facturas.columns:
            df_facturas = convertir_a_float_seguro(df_facturas, 'total')
        
        # Resumen ejecutivo si está habilitado
        if incluir_resumen:
            story.append(Paragraph("📈 RESUMEN EJECUTIVO", heading_style))
            
            total_ventas = float(df_facturas['total'].sum()) if 'total' in df_facturas.columns else 0
            total_facturas = len(facturas)
            ticket_promedio = float(df_facturas['total'].mean()) if 'total' in df_facturas.columns else 0
            clientes_unicos = df_facturas['id_cliente'].nunique() if 'id_cliente' in df_facturas.columns else 0
            
            # Tabla de resumen
            resumen_data = [
                ['Métrica', 'Valor'],
                ['Total de Facturas', f'{total_facturas:,}'],
                ['Ventas Totales', f'${total_ventas:,.2f}'],
                ['Ticket Promedio', f'${ticket_promedio:,.2f}'],
                ['Clientes Únicos', f'{clientes_unicos:,}']
            ]
            
            resumen_table = Table(resumen_data, colWidths=[3*inch, 3*inch])
            resumen_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#ecf0f1')])
            ]))
            
            story.append(resumen_table)
            story.append(Spacer(1, 0.3*inch))
        
        # Detalle de ventas
        story.append(Paragraph("📋 DETALLE DE VENTAS", heading_style))
        
        # Preparar datos para la tabla
        tabla_data = [['#', 'Factura', 'Fecha', 'Cliente', 'Total', 'Estado']]
        
        for idx, factura in enumerate(facturas[:50], 1):  # Limitar a 50 primeras facturas
            numero = factura.get('numero_factura', 'N/A')
            fecha = factura.get('fecha_emision', '')[:10] if factura.get('fecha_emision') else 'N/A'
            cliente = str(factura.get('id_cliente', 'N/A'))
            total = float(factura.get('total', 0))
            estado = factura.get('estado_factura', 'N/A')
            
            tabla_data.append([
                str(idx),
                str(numero),
                fecha,
                cliente,
                f'${total:,.2f}',
                estado
            ])
        
        # Crear tabla de detalles
        detalle_table = Table(tabla_data, colWidths=[0.4*inch, 1.2*inch, 1*inch, 1*inch, 1.2*inch, 1.2*inch])
        detalle_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
            ('ALIGN', (4, 1), (4, -1), 'RIGHT'),
        ]))
        
        story.append(detalle_table)
        
        # Nota si hay más facturas
        if len(facturas) > 50:
            story.append(Spacer(1, 0.2*inch))
            nota = Paragraph(
                f"<i>Nota: Se muestran las primeras 50 facturas de un total de {len(facturas)}. "
                f"Para ver el detalle completo, use la exportación a Excel.</i>",
                styles['Italic']
            )
            story.append(nota)
        
        # Pie de página con fecha de generación
        story.append(Spacer(1, 0.5*inch))
        footer = Paragraph(
            f"<i>Reporte generado el {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</i>",
            ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, textColor=colors.grey, alignment=TA_CENTER)
        )
        story.append(footer)
        
        # Construir PDF
        doc.build(story)
        
        # Obtener datos del buffer
        buffer.seek(0)
        pdf_data = buffer.getvalue()
        
        # Botón de descarga
        st.download_button(
            label="📥 Descargar Reporte PDF",
            data=pdf_data,
            file_name=f"reporte_ventas_{fecha_desde}_{fecha_hasta}.pdf",
            mime="application/pdf",
            type="primary",
            use_container_width=True
        )
        
        st.success("✅ Archivo PDF generado exitosamente!")
        st.info(f"📊 Total de facturas en el reporte: {min(len(facturas), 50)} de {len(facturas)}")
        
    except ImportError as e:
        st.error("❌ Error: La librería reportlab no está instalada correctamente")
        st.info("💡 Contacte al administrador del sistema")
    except Exception as e:
        st.error(f"❌ Error al generar archivo PDF: {e}")

