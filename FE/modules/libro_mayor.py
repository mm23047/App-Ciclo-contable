"""
Módulo Streamlit para el Libro Mayor.
Muestra movimientos mayorizados por cuenta con saldos acumulados.
Incluye funcionalidad de exportación a Excel y HTML.
"""
import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from typing import Dict, Any, List
from datetime import datetime
from io import BytesIO

def render_page(backend_url: str):
    """Renderizar página del libro mayor"""
    
    st.header("📚 Libro Mayor")
    st.markdown("Consulta de movimientos mayorizados por cuenta contable con saldos acumulados")
    
    # Tabs para organizar funcionalidades
    tab1, tab2, tab3 = st.tabs(["📋 Consultar Mayor", "📊 Resumen de Cuentas", "📥 Descargar Libro Mayor"])
    
    with tab1:
        consultar_mayor(backend_url)
    
    with tab2:
        resumen_cuentas(backend_url)
    
    with tab3:
        descargar_libro_mayor(backend_url)

def consultar_mayor(backend_url: str):
    """Consultar movimientos del libro mayor"""
    
    st.subheader("📋 Consulta de Libro Mayor")
    
    # Filtros
    col1, col2 = st.columns(2)
    
    with col1:
        # Obtener cuentas disponibles
        try:
            response_cuentas = requests.get(f"{backend_url}/api/catalogo-cuentas", timeout=10)
            cuentas = response_cuentas.json() if response_cuentas.status_code == 200 else []
            
            opciones_cuentas = ["Todas las cuentas"] + [
                f"{c['codigo_cuenta']} - {c['nombre_cuenta']}" 
                for c in cuentas if c.get('acepta_movimientos', True) and c.get('estado') == 'ACTIVA'
            ]
            
            cuenta_seleccionada = st.selectbox("🏦 Cuenta:", opciones_cuentas)
            
        except Exception as e:
            st.error(f"Error al cargar cuentas: {str(e)}")
            cuenta_seleccionada = "Todas las cuentas"
            cuentas = []
    
    with col2:
        # Obtener períodos disponibles
        try:
            response_periodos = requests.get(f"{backend_url}/api/periodos", timeout=10)
            periodos = response_periodos.json() if response_periodos.status_code == 200 else []
            
            opciones_periodos = [
                f"{p['descripcion']} ({p['fecha_inicio']} → {p['fecha_fin']})"
                for p in periodos
            ]
            
            if opciones_periodos:
                periodo_seleccionado = st.selectbox("📅 Período:", opciones_periodos)
            else:
                periodo_seleccionado = None
                st.warning("⚠️ No hay períodos configurados")
            
        except Exception as e:
            st.error(f"Error al cargar períodos: {str(e)}")
            periodo_seleccionado = None
            periodos = []
    
    if st.button("📊 Generar Consulta", type="primary", use_container_width=True):
        if periodo_seleccionado and periodos:
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
                
                obtener_movimientos_mayor(backend_url, id_periodo, id_cuenta)
        else:
            st.warning("⚠️ Selecciona un período válido")

def obtener_movimientos_mayor(backend_url: str, id_periodo: int, id_cuenta: int = None):
    """Obtener y mostrar movimientos del libro mayor"""
    
    try:
        # Construir URL
        if id_cuenta:
            url = f"{backend_url}/api/libro-mayor/cuenta/{id_cuenta}/periodo/{id_periodo}"
        else:
            url = f"{backend_url}/api/libro-mayor/periodo/{id_periodo}"
        
        with st.spinner("📖 Consultando libro mayor..."):
            response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            datos_mayor = response.json()
            
            if isinstance(datos_mayor, list):
                # Múltiples cuentas
                mostrar_mayor_multiple_cuentas(datos_mayor)
            else:
                # Una cuenta específica
                mostrar_mayor_cuenta_especifica(datos_mayor)
                
        elif response.status_code == 404:
            st.info("📭 No se encontraron movimientos para el período seleccionado")
        else:
            st.error(f"❌ Error al consultar libro mayor: {response.status_code}")
            
    except requests.exceptions.Timeout:
        st.error("❌ Tiempo de espera agotado. Intenta de nuevo.")
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Error de conexión: {str(e)}")
    except Exception as e:
        st.error(f"❌ Error inesperado: {str(e)}")

def mostrar_mayor_cuenta_especifica(datos_cuenta: Dict[str, Any]):
    """Mostrar libro mayor para una cuenta específica"""
    
    # Información de la cuenta
    st.markdown("### 📊 Información de la Cuenta")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📋 Código", datos_cuenta.get('codigo_cuenta', 'N/A'))
    
    with col2:
        st.metric("🏷️ Tipo", datos_cuenta.get('tipo_cuenta', 'N/A'))
    
    with col3:
        saldo_inicial = float(datos_cuenta.get('saldo_inicial', 0))
        st.metric("💰 Saldo Inicial", f"${saldo_inicial:,.2f}")
    
    with col4:
        saldo_final = float(datos_cuenta.get('saldo_final', 0))
        delta = saldo_final - saldo_inicial
        st.metric("🎯 Saldo Final", f"${saldo_final:,.2f}", delta=f"${delta:,.2f}")
    
    st.markdown(f"**Nombre:** {datos_cuenta.get('nombre_cuenta', 'N/A')}")
    
    # Movimientos
    movimientos = datos_cuenta.get('movimientos', [])
    
    if movimientos:
        st.markdown("---")
        st.markdown("### 📝 Movimientos Detallados")
        
        # Crear DataFrame
        df_movimientos = pd.DataFrame(movimientos)
        
        # Formatear columnas para visualización
        df_display = df_movimientos.copy()
        df_display['fecha_movimiento'] = pd.to_datetime(df_display['fecha_movimiento'], format='ISO8601').dt.strftime('%d/%m/%Y')
        df_display['debe'] = df_display['debe'].apply(lambda x: f"${float(x):,.2f}" if float(x) > 0 else "-")
        df_display['haber'] = df_display['haber'].apply(lambda x: f"${float(x):,.2f}" if float(x) > 0 else "-")
        df_display['saldo_acumulado'] = df_display['saldo_acumulado'].apply(lambda x: f"${float(x):,.2f}")
        
        # Renombrar y seleccionar columnas
        columnas_display = {
            'fecha_movimiento': 'Fecha',
            'descripcion': 'Descripción',
            'referencia': 'Referencia',
            'debe': 'Debe',
            'haber': 'Haber',
            'saldo_acumulado': 'Saldo'
        }
        df_display = df_display.rename(columns=columnas_display)
        
        st.dataframe(
            df_display[['Fecha', 'Descripción', 'Referencia', 'Debe', 'Haber', 'Saldo']],
            use_container_width=True,
            hide_index=True
        )
        
        # Gráfico de evolución del saldo
        if len(movimientos) > 1:
            st.markdown("---")
            st.markdown("### 📈 Evolución del Saldo")
            
            df_grafico = pd.DataFrame(movimientos)
            df_grafico['fecha_movimiento'] = pd.to_datetime(df_grafico['fecha_movimiento'], format='ISO8601')
            df_grafico['saldo_acumulado'] = df_grafico['saldo_acumulado'].astype(float)
            
            fig = px.line(
                df_grafico,
                x='fecha_movimiento',
                y='saldo_acumulado',
                title=f'Evolución del Saldo - {datos_cuenta.get("nombre_cuenta", "")}',
                markers=True,
                labels={'fecha_movimiento': 'Fecha', 'saldo_acumulado': 'Saldo ($)'}
            )
            
            fig.update_layout(hovermode='x unified', height=400)
            fig.update_traces(line_color='#1f77b4', marker=dict(size=8))
            
            st.plotly_chart(fig, use_container_width=True)
        
        # Resumen estadístico
        st.markdown("---")
        st.markdown("### 📊 Resumen Estadístico")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_debe = sum(float(m['debe']) for m in movimientos)
            st.metric("🟢 Total Debe", f"${total_debe:,.2f}")
        
        with col2:
            total_haber = sum(float(m['haber']) for m in movimientos)
            st.metric("🔴 Total Haber", f"${total_haber:,.2f}")
        
        with col3:
            st.metric("🔢 Cantidad Movimientos", len(movimientos))
        
        with col4:
            promedio_movimiento = (total_debe + total_haber) / len(movimientos) / 2 if len(movimientos) > 0 else 0
            st.metric("📊 Promedio Movimiento", f"${promedio_movimiento:,.2f}")
    
    else:
        st.info("📭 No hay movimientos registrados para esta cuenta en el período seleccionado")

def mostrar_mayor_multiple_cuentas(datos_cuentas: List[Dict[str, Any]]):
    """Mostrar resumen del libro mayor para múltiples cuentas"""
    
    if not datos_cuentas:
        st.info("📭 No se encontraron cuentas con movimientos en el período seleccionado")
        return
    
    st.markdown("### 📊 Resumen por Cuentas")
    
    # Crear DataFrame para resumen
    resumen_data = []
    for cuenta in datos_cuentas:
        movimientos = cuenta.get('movimientos', [])
        
        resumen_data.append({
            'Código': cuenta.get('codigo_cuenta', 'N/A'),
            'Nombre': cuenta.get('nombre_cuenta', 'N/A'),
            'Tipo': cuenta.get('tipo_cuenta', 'N/A'),
            'Saldo Inicial': float(cuenta.get('saldo_inicial', 0)),
            'Total Debe': float(cuenta.get('total_debe', 0)),
            'Total Haber': float(cuenta.get('total_haber', 0)),
            'Saldo Final': float(cuenta.get('saldo_final', 0)),
            'Movimientos': cuenta.get('cantidad_movimientos', len(movimientos))
        })
    
    df_resumen = pd.DataFrame(resumen_data)
    
    # Formatear para visualización
    df_display = df_resumen.copy()
    df_display['Saldo Inicial'] = df_display['Saldo Inicial'].apply(lambda x: f"${x:,.2f}")
    df_display['Total Debe'] = df_display['Total Debe'].apply(lambda x: f"${x:,.2f}")
    df_display['Total Haber'] = df_display['Total Haber'].apply(lambda x: f"${x:,.2f}")
    df_display['Saldo Final'] = df_display['Saldo Final'].apply(lambda x: f"${x:,.2f}")
    
    # Mostrar tabla
    st.dataframe(
        df_display,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Código": st.column_config.TextColumn("Código", width="small"),
            "Nombre": st.column_config.TextColumn("Nombre de Cuenta", width="large"),
            "Tipo": st.column_config.TextColumn("Tipo", width="small"),
            "Saldo Inicial": st.column_config.TextColumn("Saldo Inicial", width="medium"),
            "Total Debe": st.column_config.TextColumn("Total Debe", width="medium"),
            "Total Haber": st.column_config.TextColumn("Total Haber", width="medium"),
            "Saldo Final": st.column_config.TextColumn("Saldo Final", width="medium"),
            "Movimientos": st.column_config.NumberColumn("# Mov", width="small"),
        }
    )
    
    # Métricas generales
    st.markdown("---")
    st.markdown("### 📊 Totales Generales")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📝 Cuentas con Movimientos", len(datos_cuentas))
    
    with col2:
        total_debe_general = df_resumen['Total Debe'].sum()
        st.metric("🟢 Total Debe General", f"${total_debe_general:,.2f}")
    
    with col3:
        total_haber_general = df_resumen['Total Haber'].sum()
        st.metric("🔴 Total Haber General", f"${total_haber_general:,.2f}")
    
    with col4:
        total_movimientos = df_resumen['Movimientos'].sum()
        st.metric("🔢 Total Movimientos", int(total_movimientos))
    
    # Gráfico de distribución por tipo
    if len(datos_cuentas) > 0:
        st.markdown("---")
        st.markdown("### 📊 Distribución por Tipo de Cuenta")
        
        tipo_count = df_resumen.groupby('Tipo').agg({
            'Movimientos': 'sum',
            'Saldo Final': 'sum'
        }).reset_index()
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig_tipo = px.pie(
                tipo_count,
                values='Movimientos',
                names='Tipo',
                title='Movimientos por Tipo',
                hole=0.4
            )
            fig_tipo.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_tipo, use_container_width=True)
        
        with col2:
            fig_saldos = px.bar(
                tipo_count,
                x='Tipo',
                y='Saldo Final',
                title='Saldos Finales por Tipo',
                text='Saldo Final'
            )
            fig_saldos.update_traces(texttemplate='$%{text:,.0f}', textposition='outside')
            fig_saldos.update_layout(yaxis_title='Saldo Final ($)', xaxis_title='')
            st.plotly_chart(fig_saldos, use_container_width=True)

def resumen_cuentas(backend_url: str):
    """Resumen estadístico de cuentas"""
    
    st.subheader("📊 Resumen Estadístico de Cuentas")
    st.markdown("Vista consolidada del libro mayor con estadísticas y análisis")
    
    # Selector de período
    try:
        response_periodos = requests.get(f"{backend_url}/api/periodos", timeout=10)
        periodos = response_periodos.json() if response_periodos.status_code == 200 else []
        
        if periodos:
            opciones_periodos = [
                f"{p['descripcion']} ({p['fecha_inicio']} → {p['fecha_fin']})"
                for p in periodos
            ]
            
            periodo_seleccionado = st.selectbox("📅 Seleccionar período:", opciones_periodos, key="resumen_periodo")
            
            if st.button("📋 Generar Resumen Estadístico", type="primary", use_container_width=True):
                nombre_periodo = periodo_seleccionado.split(" (")[0]
                periodo_obj = next((p for p in periodos if p['descripcion'] == nombre_periodo), None)
                
                if periodo_obj:
                    generar_resumen_estadistico(backend_url, periodo_obj['id_periodo'])
        else:
            st.warning("⚠️ No hay períodos configurados")
            
    except Exception as e:
        st.error(f"❌ Error al cargar períodos: {str(e)}")

def generar_resumen_estadistico(backend_url: str, id_periodo: int):
    """Generar resumen estadístico detallado"""
    
    try:
        url = f"{backend_url}/api/libro-mayor/periodo/{id_periodo}"
            
        with st.spinner("📊 Generando resumen estadístico..."):
            response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            datos = response.json()
            
            if datos:
                mostrar_mayor_multiple_cuentas(datos)
            else:
                st.info("📭 No hay datos disponibles para el período seleccionado")
        else:
            st.error(f"❌ Error al obtener datos: {response.status_code}")
            
    except Exception as e:
        st.error(f"❌ Error al generar resumen: {str(e)}")

def descargar_libro_mayor(backend_url: str):
    """Funcionalidad para descargar el libro mayor completo"""
    
    st.subheader("📥 Descargar Libro Mayor")
    st.markdown("Exporta el libro mayor completo (solo cuentas mayores con movimientos) en formato Excel o HTML")
    
    # Selector de período
    try:
        response_periodos = requests.get(f"{backend_url}/api/periodos", timeout=10)
        periodos = response_periodos.json() if response_periodos.status_code == 200 else []
        
        if periodos:
            col1, col2 = st.columns(2)
            
            with col1:
                opciones_periodos = [
                    f"{p['descripcion']} ({p['fecha_inicio']} → {p['fecha_fin']})"
                    for p in periodos
                ]
                periodo_seleccionado = st.selectbox("📅 Período a exportar:", opciones_periodos, key="download_periodo")
            
            with col2:
                formato_descarga = st.selectbox(
                    "📄 Formato de descarga:",
                    ["Excel (.xlsx)", "HTML (.html)"],
                    key="formato_descarga"
                )
            
            st.markdown("---")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("📥 Descargar Libro Mayor", type="primary", use_container_width=True):
                    nombre_periodo = periodo_seleccionado.split(" (")[0]
                    periodo_obj = next((p for p in periodos if p['descripcion'] == nombre_periodo), None)
                    
                    if periodo_obj:
                        if "Excel" in formato_descarga:
                            generar_excel_libro_mayor(backend_url, periodo_obj)
                        else:
                            generar_html_libro_mayor(backend_url, periodo_obj)
            
            with col2:
                st.info("💡 **Nota:** El archivo incluirá solo las cuentas mayores (cuentas con movimientos en el período)")
                
        else:
            st.warning("⚠️ No hay períodos configurados")
            
    except Exception as e:
        st.error(f"❌ Error al cargar períodos: {str(e)}")

def generar_excel_libro_mayor(backend_url: str, periodo: Dict[str, Any]):
    """Generar archivo Excel del libro mayor"""
    
    try:
        url = f"{backend_url}/api/libro-mayor/periodo/{periodo['id_periodo']}"
        
        with st.spinner("📊 Generando archivo Excel..."):
            response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            datos_cuentas = response.json()
            
            if not datos_cuentas:
                st.warning("📭 No hay movimientos para exportar en este período")
                return
            
            # Crear archivo Excel en memoria
            output = BytesIO()
            
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                # Hoja de resumen
                resumen_data = []
                for cuenta in datos_cuentas:
                    resumen_data.append({
                        'Código': cuenta.get('codigo_cuenta'),
                        'Nombre de Cuenta': cuenta.get('nombre_cuenta'),
                        'Tipo': cuenta.get('tipo_cuenta'),
                        'Saldo Inicial': float(cuenta.get('saldo_inicial', 0)),
                        'Total Debe': float(cuenta.get('total_debe', 0)),
                        'Total Haber': float(cuenta.get('total_haber', 0)),
                        'Saldo Final': float(cuenta.get('saldo_final', 0)),
                        'Cantidad Movimientos': cuenta.get('cantidad_movimientos', 0)
                    })
                
                df_resumen = pd.DataFrame(resumen_data)
                df_resumen.to_excel(writer, sheet_name='Resumen', index=False)
                
                # Hoja por cada cuenta mayor
                for cuenta in datos_cuentas:
                    if cuenta.get('cantidad_movimientos', 0) > 0:
                        movimientos = cuenta.get('movimientos', [])
                        
                        if movimientos:
                            df_movimientos = pd.DataFrame(movimientos)
                            df_movimientos['debe'] = df_movimientos['debe'].astype(float)
                            df_movimientos['haber'] = df_movimientos['haber'].astype(float)
                            df_movimientos['saldo_acumulado'] = df_movimientos['saldo_acumulado'].astype(float)
                            
                            # Renombrar columnas
                            df_movimientos = df_movimientos.rename(columns={
                                'fecha_movimiento': 'Fecha',
                                'descripcion': 'Descripción',
                                'referencia': 'Referencia',
                                'debe': 'Debe',
                                'haber': 'Haber',
                                'saldo_acumulado': 'Saldo Acumulado'
                            })
                            
                            # Nombre de la hoja (limitado a 31 caracteres)
                            nombre_hoja = f"{cuenta.get('codigo_cuenta', 'CTA')}"[:31]
                            df_movimientos[['Fecha', 'Descripción', 'Referencia', 'Debe', 'Haber', 'Saldo Acumulado']].to_excel(
                                writer, 
                                sheet_name=nombre_hoja, 
                                index=False
                            )
            
            output.seek(0)
            
            # Botón de descarga
            nombre_archivo = f"libro_mayor_{periodo['descripcion'].replace(' ', '_')}.xlsx"
            
            st.download_button(
                label="⬇️ Descargar Excel",
                data=output,
                file_name=nombre_archivo,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary",
                use_container_width=True
            )
            
            st.success(f"✅ Archivo Excel generado exitosamente")
            st.info(f"📊 Total de cuentas mayores exportadas: {len(datos_cuentas)}")
            
        else:
            st.error(f"❌ Error al obtener datos: {response.status_code}")
            
    except Exception as e:
        st.error(f"❌ Error al generar Excel: {str(e)}")

def generar_html_libro_mayor(backend_url: str, periodo: Dict[str, Any]):
    """Generar archivo HTML del libro mayor"""
    
    try:
        url = f"{backend_url}/api/libro-mayor/periodo/{periodo['id_periodo']}"
        
        with st.spinner("📄 Generando archivo HTML..."):
            response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            datos_cuentas = response.json()
            
            if not datos_cuentas:
                st.warning("📭 No hay movimientos para exportar en este período")
                return
            
            # Generar HTML
            html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Libro Mayor - {periodo['descripcion']}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .header {{ text-align: center; background: #2c3e50; color: white; padding: 20px; margin-bottom: 30px; border-radius: 5px; }}
        .cuenta {{ background: white; margin-bottom: 30px; padding: 20px; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .cuenta-header {{ background: #3498db; color: white; padding: 10px; margin: -20px -20px 15px -20px; border-radius: 5px 5px 0 0; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
        th {{ background: #34495e; color: white; padding: 10px; text-align: left; }}
        td {{ padding: 8px; border-bottom: 1px solid #ddd; }}
        tr:hover {{ background: #f5f5f5; }}
        .numero {{ text-align: right; }}
        .resumen {{ display: flex; justify-content: space-around; margin: 15px 0; }}
        .metrica {{ text-align: center; padding: 10px; background: #f8f9fa; border-radius: 5px; flex: 1; margin: 0 5px; }}
        .metrica-valor {{ font-size: 24px; font-weight: bold; color: #2c3e50; }}
        .metrica-label {{ color: #7f8c8d; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📚 LIBRO MAYOR</h1>
        <h2>{periodo['descripcion']}</h2>
        <p>{periodo['fecha_inicio']} → {periodo['fecha_fin']}</p>
    </div>
"""
            
            # Agregar cada cuenta
            for cuenta in datos_cuentas:
                movimientos = cuenta.get('movimientos', [])
                
                if len(movimientos) > 0:
                    html_content += f"""
    <div class="cuenta">
        <div class="cuenta-header">
            <h3>{cuenta.get('codigo_cuenta')} - {cuenta.get('nombre_cuenta')}</h3>
        </div>
        <div class="resumen">
            <div class="metrica">
                <div class="metrica-label">Tipo</div>
                <div class="metrica-valor" style="font-size: 16px;">{cuenta.get('tipo_cuenta')}</div>
            </div>
            <div class="metrica">
                <div class="metrica-label">Saldo Inicial</div>
                <div class="metrica-valor">${float(cuenta.get('saldo_inicial', 0)):,.2f}</div>
            </div>
            <div class="metrica">
                <div class="metrica-label">Total Debe</div>
                <div class="metrica-valor">${float(cuenta.get('total_debe', 0)):,.2f}</div>
            </div>
            <div class="metrica">
                <div class="metrica-label">Total Haber</div>
                <div class="metrica-valor">${float(cuenta.get('total_haber', 0)):,.2f}</div>
            </div>
            <div class="metrica">
                <div class="metrica-label">Saldo Final</div>
                <div class="metrica-valor">${float(cuenta.get('saldo_final', 0)):,.2f}</div>
            </div>
        </div>
        <table>
            <thead>
                <tr>
                    <th>Fecha</th>
                    <th>Descripción</th>
                    <th>Referencia</th>
                    <th class="numero">Debe</th>
                    <th class="numero">Haber</th>
                    <th class="numero">Saldo</th>
                </tr>
            </thead>
            <tbody>
"""
                    
                    for mov in movimientos:
                        debe = float(mov.get('debe', 0))
                        haber = float(mov.get('haber', 0))
                        saldo = float(mov.get('saldo_acumulado', 0))
                        
                        html_content += f"""
                <tr>
                    <td>{mov.get('fecha_movimiento', '')}</td>
                    <td>{mov.get('descripcion', '')}</td>
                    <td>{mov.get('referencia', '')}</td>
                    <td class="numero">{'$' + f'{debe:,.2f}' if debe > 0 else '-'}</td>
                    <td class="numero">{'$' + f'{haber:,.2f}' if haber > 0 else '-'}</td>
                    <td class="numero">${saldo:,.2f}</td>
                </tr>
"""
                    
                    html_content += """
            </tbody>
        </table>
    </div>
"""
            
            html_content += "</body></html>"
            
            # Botón de descarga con codificación UTF-8
            nombre_archivo = f"libro_mayor_{periodo['descripcion'].replace(' ', '_')}.html"
            
            st.download_button(
                label="⬇️ Descargar HTML",
                data=html_content.encode('utf-8'),
                file_name=nombre_archivo,
                mime="text/html; charset=utf-8",
                type="primary",
                use_container_width=True
            )
            
            st.success(f"✅ Archivo HTML generado exitosamente")
            st.info(f"📊 Total de cuentas mayores exportadas: {len(datos_cuentas)}")
            
        else:
            st.error(f"❌ Error al obtener datos: {response.status_code}")
            
    except Exception as e:
        st.error(f"❌ Error al generar HTML: {str(e)}")
