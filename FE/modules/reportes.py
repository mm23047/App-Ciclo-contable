"""
Módulo Streamlit para el Libro Diario.
Muestra todos los asientos contables con funcionalidad de exportación a Excel y HTML.
"""
import streamlit as st
import requests
import pandas as pd
from io import BytesIO
from typing import Optional, List, Dict, Any

def load_periods(backend_url: str):
    """Cargar períodos disponibles desde la API"""
    try:
        response = requests.get(f"{backend_url}/api/periodos/activos", timeout=10)
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"❌ Error al cargar períodos: {response.text}")
            return []
            
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Error de conexión al cargar períodos: {str(e)}")
        return []

def render_page(backend_url: str):
    """Renderizar la página de Libro Diario"""
    st.header("📋 Libro Diario")
    st.markdown("""Registro cronológico de todas las transacciones contables con sus asientos de débito y crédito.""")
    
    # Tabs para el Libro Diario
    tab1, tab2, tab3 = st.tabs(["📋 Consultar Diario", "📥 Descargar Libro Diario", "⚖️ Resumen por Período"])
    
    with tab1:
        show_libro_diario(backend_url)
    
    with tab2:
        show_export_libro_diario(backend_url)
    
    with tab3:
        show_balance_report(backend_url)

def show_libro_diario(backend_url: str):
    """Mostrar el Libro Diario (General Journal)"""
    st.subheader("📋 Consultar Libro Diario")
    st.markdown("Visualiza todos los asientos contables registrados cronológicamente.")
    
    # Cargar períodos disponibles
    periods = load_periods(backend_url)
    
    # Filters
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Selector de período mejorado
        if periods:
            # Agregar opción "Todos los períodos" al inicio
            period_options = {"Todos los períodos": None}
            for period in periods:
                display_text = f"{period['tipo_periodo']} - {period['fecha_inicio']} a {period['fecha_fin']}"
                period_options[display_text] = period['id_periodo']
            
            selected_period_display = st.selectbox(
                "📅 Filtrar por Período",
                options=list(period_options.keys()),
                help="Selecciona el período contable para filtrar los asientos"
            )
            selected_period_id = period_options[selected_period_display]
        else:
            st.warning("⚠️ No se pudieron cargar los períodos disponibles")
            selected_period_id = None
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        cargar_btn = st.button("🔍 Cargar", type="primary", use_container_width=True)
    
    # Display results outside the columns
    if cargar_btn:
        load_libro_diario(backend_url, selected_period_id)

def load_libro_diario(backend_url: str, periodo_id: Optional[int] = None):
    """Cargar y mostrar los datos del Libro Diario"""
    try:
        params = {}
        if periodo_id:
            params["periodo_id"] = periodo_id
        
        with st.spinner("📊 Cargando libro diario..."):
            response = requests.get(
                f"{backend_url}/api/reportes/libro-diario",
                params=params,
                timeout=10
            )
        
        if response.status_code == 200:
            data = response.json()
            
            if not data:
                st.info("📭 No hay datos para mostrar en el libro diario")
                return
            
            # Convert to DataFrame
            df = pd.DataFrame(data)
            
            # Format datetime column - handle ISO format from backend
            if 'fecha_transaccion' in df.columns:
                df['fecha_transaccion'] = pd.to_datetime(df['fecha_transaccion'], errors='coerce')
                df['fecha_transaccion'] = df['fecha_transaccion'].dt.strftime('%Y-%m-%d %H:%M')
            
            # Display summary metrics
            total_debe = df['debe'].sum()
            total_haber = df['haber'].sum()
            total_entries = len(df)
            diferencia = abs(total_debe - total_haber)
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("📊 Total Asientos", f"{total_entries:,}")
            with col2:
                st.metric("💰 Total Débitos", f"${total_debe:,.2f}")
            with col3:
                st.metric("💰 Total Créditos", f"${total_haber:,.2f}")
            with col4:
                st.metric("⚖️ Diferencia", f"${diferencia:,.2f}")
            
            # Balance validation
            if diferencia > 0.01:  # Allow for small floating point differences
                st.error("⚠️ ATENCIÓN: El libro diario no está balanceado. Revisa los asientos.")
            else:
                st.success("✅ El libro diario está correctamente balanceado.")
            
            # Display data table with better formatting
            st.markdown("---")
            st.markdown("### 📋 Detalle de Asientos")
            
            # Format columns for display
            df_display = df[['fecha_transaccion', 'descripcion', 'tipo_transaccion', 
                           'codigo_cuenta', 'nombre_cuenta', 'debe', 'haber']].copy()
            
            df_display.columns = ['Fecha', 'Descripción', 'Tipo', 'Código', 'Cuenta', 'Debe', 'Haber']
            
            # Format currency columns
            df_display['Debe'] = df_display['Debe'].apply(lambda x: f"${x:,.2f}" if x > 0 else "-")
            df_display['Haber'] = df_display['Haber'].apply(lambda x: f"${x:,.2f}" if x > 0 else "-")
            
            # Display in full width with increased height
            st.dataframe(
                df_display,
                use_container_width=True,
                height=600
            )
        
        else:
            st.error(f"❌ Error al cargar libro diario: {response.text}")
            
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Error de conexión: {str(e)}")

def show_export_libro_diario(backend_url: str):
    """Mostrar opciones de exportación del Libro Diario con formato Excel/HTML"""
    st.subheader("💾 Descargar Libro Diario")
    st.markdown("Exporta el libro diario completo en formato Excel o HTML.")
    
    # Cargar períodos disponibles
    periods = load_periods(backend_url)
    
    if not periods:
        st.error("❌ No se pudieron cargar los períodos disponibles")
        return
    
    # Selector de período
    col1, col2 = st.columns(2)
    
    with col1:
        period_options = {}
        for period in periods:
            descripcion = f"{period.get('tipo_periodo', 'Período')} - {period.get('fecha_inicio', '')} a {period.get('fecha_fin', '')}"
            period_options[descripcion] = period
        
        selected_period_name = st.selectbox(
            "📅 Seleccionar Período",
            options=list(period_options.keys()),
            help="Selecciona el período contable"
        )
        
        periodo = period_options[selected_period_name]
    
    with col2:
        formato = st.selectbox(
            "📄 Formato de Exportación",
            options=["Excel", "HTML"],
            help="Selecciona el formato de descarga"
        )
    
    # Botón de generación
    if st.button("📊 Generar Archivo", type="primary", use_container_width=True):
        if formato == "Excel":
            generar_excel_libro_diario(backend_url, periodo)
        else:
            generar_html_libro_diario(backend_url, periodo)


def generar_excel_libro_diario(backend_url: str, periodo: Dict[str, Any]):
    """Generar archivo Excel del libro diario"""
    
    try:
        # Obtener datos del libro diario
        params = {"periodo_id": periodo['id_periodo']}
        
        with st.spinner("📊 Generando archivo Excel..."):
            response = requests.get(
                f"{backend_url}/api/reportes/libro-diario",
                params=params,
                timeout=30
            )
        
        if response.status_code == 200:
            datos = response.json()
            
            if not datos:
                st.warning("📭 No hay movimientos para exportar en este período")
                return
            
            # Crear archivo Excel en memoria
            output = BytesIO()
            
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                # Convertir a DataFrame
                df = pd.DataFrame(datos)
                
                # Formatear columnas
                df['fecha_transaccion'] = pd.to_datetime(df['fecha_transaccion']).dt.strftime('%Y-%m-%d %H:%M')
                df['debe'] = df['debe'].astype(float)
                df['haber'] = df['haber'].astype(float)
                
                # Seleccionar y renombrar columnas
                df_export = df[['fecha_transaccion', 'descripcion', 'tipo_transaccion', 
                               'codigo_cuenta', 'nombre_cuenta', 'debe', 'haber']].copy()
                
                df_export.columns = ['Fecha', 'Descripción', 'Tipo', 'Código Cuenta', 
                                    'Nombre Cuenta', 'Debe', 'Haber']
                
                # Exportar a Excel
                df_export.to_excel(writer, sheet_name='Libro Diario', index=False)
                
                # Hoja de resumen
                resumen_data = {
                    'Métrica': ['Total Asientos', 'Total Debe', 'Total Haber', 'Diferencia'],
                    'Valor': [
                        len(df),
                        f"${df['debe'].sum():,.2f}",
                        f"${df['haber'].sum():,.2f}",
                        f"${abs(df['debe'].sum() - df['haber'].sum()):,.2f}"
                    ]
                }
                df_resumen = pd.DataFrame(resumen_data)
                df_resumen.to_excel(writer, sheet_name='Resumen', index=False)
            
            output.seek(0)
            
            # Botón de descarga
            nombre_archivo = f"libro_diario_{periodo['tipo_periodo']}_{periodo['fecha_inicio']}.xlsx"
            
            st.download_button(
                label="⬇️ Descargar Excel",
                data=output,
                file_name=nombre_archivo,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary",
                use_container_width=True
            )
            
            st.success(f"✅ Archivo Excel generado exitosamente")
            st.info(f"📊 Total de asientos exportados: {len(datos)}")
            
        else:
            st.error(f"❌ Error al obtener datos: {response.status_code}")
            
    except Exception as e:
        st.error(f"❌ Error al generar Excel: {str(e)}")


def generar_html_libro_diario(backend_url: str, periodo: Dict[str, Any]):
    """Generar archivo HTML del libro diario"""
    
    try:
        # Obtener datos del libro diario
        params = {"periodo_id": periodo['id_periodo']}
        
        with st.spinner("📄 Generando archivo HTML..."):
            response = requests.get(
                f"{backend_url}/api/reportes/libro-diario",
                params=params,
                timeout=30
            )
        
        if response.status_code == 200:
            datos = response.json()
            
            if not datos:
                st.warning("📭 No hay movimientos para exportar en este período")
                return
            
            # Calcular totales
            total_debe = sum(float(d.get('debe', 0)) for d in datos)
            total_haber = sum(float(d.get('haber', 0)) for d in datos)
            
            # Generar HTML
            html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Libro Diario - {periodo['tipo_periodo']}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .header {{ text-align: center; background: #2c3e50; color: white; padding: 20px; margin-bottom: 30px; border-radius: 5px; }}
        .resumen {{ background: white; padding: 20px; margin-bottom: 20px; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .metricas {{ display: flex; justify-content: space-around; margin: 15px 0; }}
        .metrica {{ text-align: center; padding: 10px; background: #f8f9fa; border-radius: 5px; flex: 1; margin: 0 5px; }}
        .metrica-valor {{ font-size: 24px; font-weight: bold; color: #2c3e50; }}
        .metrica-label {{ color: #7f8c8d; font-size: 12px; }}
        table {{ width: 100%; border-collapse: collapse; background: white; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        th {{ background: #34495e; color: white; padding: 12px; text-align: left; position: sticky; top: 0; }}
        td {{ padding: 10px; border-bottom: 1px solid #ddd; }}
        tr:hover {{ background: #f5f5f5; }}
        .numero {{ text-align: right; font-family: 'Courier New', monospace; }}
        .debe {{ color: #27ae60; font-weight: bold; }}
        .haber {{ color: #e74c3c; font-weight: bold; }}
        .totales {{ background: #ecf0f1; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📋 LIBRO DIARIO</h1>
        <h2>{periodo['tipo_periodo']}</h2>
        <p>{periodo['fecha_inicio']} → {periodo['fecha_fin']}</p>
    </div>
    
    <div class="resumen">
        <h3>📊 Resumen del Período</h3>
        <div class="metricas">
            <div class="metrica">
                <div class="metrica-label">Total Asientos</div>
                <div class="metrica-valor">{len(datos)}</div>
            </div>
            <div class="metrica">
                <div class="metrica-label">Total Debe</div>
                <div class="metrica-valor debe">${total_debe:,.2f}</div>
            </div>
            <div class="metrica">
                <div class="metrica-label">Total Haber</div>
                <div class="metrica-valor haber">${total_haber:,.2f}</div>
            </div>
            <div class="metrica">
                <div class="metrica-label">Balance</div>
                <div class="metrica-valor">{'✅ OK' if abs(total_debe - total_haber) < 0.01 else '⚠️ Desbalanceado'}</div>
            </div>
        </div>
    </div>
    
    <table>
        <thead>
            <tr>
                <th>Fecha</th>
                <th>Descripción</th>
                <th>Tipo</th>
                <th>Código</th>
                <th>Cuenta</th>
                <th class="numero">Debe</th>
                <th class="numero">Haber</th>
            </tr>
        </thead>
        <tbody>
"""
            
            # Agregar cada asiento
            for asiento in datos:
                fecha = asiento.get('fecha_transaccion', '')[:10]
                descripcion = asiento.get('descripcion', '')
                tipo = asiento.get('tipo_transaccion', '')
                codigo = asiento.get('codigo_cuenta', '')
                cuenta = asiento.get('nombre_cuenta', '')
                debe = float(asiento.get('debe', 0))
                haber = float(asiento.get('haber', 0))
                
                html_content += f"""
            <tr>
                <td>{fecha}</td>
                <td>{descripcion}</td>
                <td>{tipo}</td>
                <td>{codigo}</td>
                <td>{cuenta}</td>
                <td class="numero debe">{'$' + f'{debe:,.2f}' if debe > 0 else '-'}</td>
                <td class="numero haber">{'$' + f'{haber:,.2f}' if haber > 0 else '-'}</td>
            </tr>
"""
            
            # Fila de totales
            html_content += f"""
            <tr class="totales">
                <td colspan="5" style="text-align: right;">TOTALES:</td>
                <td class="numero debe">${total_debe:,.2f}</td>
                <td class="numero haber">${total_haber:,.2f}</td>
            </tr>
        </tbody>
    </table>
</body>
</html>
"""
            
            # Botón de descarga con codificación UTF-8
            nombre_archivo = f"libro_diario_{periodo['tipo_periodo']}_{periodo['fecha_inicio']}.html"
            
            st.download_button(
                label="⬇️ Descargar HTML",
                data=html_content.encode('utf-8'),
                file_name=nombre_archivo,
                mime="text/html; charset=utf-8",
                type="primary",
                use_container_width=True
            )
            
            st.success(f"✅ Archivo HTML generado exitosamente")
            st.info(f"📊 Total de asientos exportados: {len(datos)}")
            
        else:
            st.error(f"❌ Error al obtener datos: {response.status_code}")
            
    except Exception as e:
        st.error(f"❌ Error al generar HTML: {str(e)}")

def show_balance_report(backend_url: str):
    """Mostrar reporte de balance por período"""
    st.subheader("⚖️ Resumen de Balance por Período")
    st.markdown("Visualiza el resumen de saldos de todas las cuentas en un período específico.")
    
    # Cargar períodos disponibles
    periods = load_periods(backend_url)
    
    # Period selection
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Selector de período mejorado (requerido para balance)
        if periods:
            period_options = {}
            for period in periods:
                display_text = f"{period['tipo_periodo']} - {period['fecha_inicio']} a {period['fecha_fin']}"
                period_options[display_text] = period['id_periodo']
            
            selected_period_display = st.selectbox(
                "📅 Período para Balance",
                options=list(period_options.keys()),
                help="Selecciona el período contable para generar el balance (requerido)"
            )
            selected_period_id = period_options[selected_period_display]
        else:
            st.warning("⚠️ No se pudieron cargar los períodos disponibles")
            selected_period_id = None
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        generar_btn = st.button("📊 Generar", type="primary", use_container_width=True)
    
    # Display results outside the columns
    if generar_btn and selected_period_id:
        load_balance_report(backend_url, selected_period_id)

def load_balance_report(backend_url: str, periodo_id: int):
    """Cargar y mostrar reporte de balance"""
    try:
        response = requests.get(
            f"{backend_url}/api/reportes/balance",
            params={"periodo_id": periodo_id},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            cuentas = data.get("cuentas", [])
            totales = data.get("totales", {})
            
            if not cuentas:
                st.info(f"📭 No hay datos de balance para el período {periodo_id}")
                return
            
            # Display period info
            st.info(f"📅 Balance para Período ID: {periodo_id}")
            
            # Convert to DataFrame
            df = pd.DataFrame(cuentas)
            
            # Display balance by account type
            for tipo_cuenta in df['tipo_cuenta'].unique():
                st.markdown(f"### {tipo_cuenta}")
                tipo_df = df[df['tipo_cuenta'] == tipo_cuenta]
                
                # Filter out rows where all numeric columns are zero or empty
                tipo_df = tipo_df[
                    (tipo_df['total_debe'] != 0) | 
                    (tipo_df['total_haber'] != 0) | 
                    (tipo_df['saldo'] != 0)
                ]
                
                if not tipo_df.empty:
                    st.dataframe(
                        tipo_df[['codigo_cuenta', 'nombre_cuenta', 'total_debe', 'total_haber', 'saldo']],
                        use_container_width=True,
                        hide_index=True
                    )
                else:
                    st.info(f"No hay movimientos en {tipo_cuenta} para este período")
            
            # Display totals
            st.markdown("---")
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("💰 Total Débitos", f"${totales.get('total_debe', 0):,.2f}")
            
            with col2:
                st.metric("💰 Total Créditos", f"${totales.get('total_haber', 0):,.2f}")
            
            # Balance validation
            difference = totales.get('total_debe', 0) - totales.get('total_haber', 0)
            if abs(difference) > 0.01:
                st.error(f"⚠️ ATENCIÓN: Balance desbalanceado por ${difference:,.2f}")
            else:
                st.success("✅ Balance correctamente balanceado.")
        
        else:
            st.error(f"❌ Error al cargar balance: {response.text}")
            
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Error de conexión: {str(e)}")
