"""
Módulo Streamlit para la Balanza de Comprobación.
Reporte de saldos de todas las cuentas en un período determinado.
"""
import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
from typing import Dict, Any, List

def render_page(backend_url: str):
    """Renderizar página de balanza de comprobación"""
    
    st.header("⚖️ Balanza de Comprobación")
    st.markdown("Reporte consolidado de saldos de todas las cuentas contables")
    
    # Tabs para organizar funcionalidades
    tab1, tab2 = st.tabs(["📊 Generar Balanza", "📈 Análisis Gráfico"])
    
    with tab1:
        generar_balanza(backend_url)
    
    with tab2:
        analisis_grafico_balanza(backend_url)

def generar_balanza(backend_url: str):
    """Generar balanza de comprobación"""
    
    st.subheader("📊 Generar Balanza de Comprobación")
    
    # Selección de parámetros
    col1, col2 = st.columns(2)
    
    with col1:
        # Obtener períodos disponibles
        try:
            response_periodos = requests.get(f"{backend_url}/api/periodos")
            periodos = response_periodos.json() if response_periodos.status_code == 200 else []
            
            if periodos:
                opciones_periodos = [
                    f"{p['descripcion']} ({p['fecha_inicio']} - {p['fecha_fin']})"
                    for p in periodos
                ]
                periodo_seleccionado = st.selectbox("Período contable:", opciones_periodos)
            else:
                st.warning("No hay períodos configurados")
                return
                
        except:
            st.error("Error al cargar períodos")
            return
        
        # Fecha de corte
        fecha_corte = st.date_input(
            "Fecha de corte:",
            value=datetime.now().date(),
            help="Fecha hasta la cual considerar los movimientos"
        )
    
    with col2:
        # Opciones de configuración
        incluir_saldo_inicial = st.checkbox(
            "Incluir saldo inicial",
            value=True,
            help="Incluir los saldos iniciales de las cuentas"
        )
        
        solo_cuentas_con_movimientos = st.checkbox(
            "Solo cuentas con movimientos",
            value=False,
            help="Mostrar únicamente cuentas que tienen movimientos"
        )
        
        incluir_cuentas_cero = st.checkbox(
            "Incluir cuentas con saldo cero",
            value=True,
            help="Mostrar cuentas que tienen saldo cero"
        )
        
        formato_detallado = st.checkbox(
            "Formato detallado",
            value=True,
            help="Mostrar información adicional de las cuentas"
        )
    
    # Filtros adicionales
    with st.expander("🔍 Filtros Adicionales", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            tipos_cuenta = ["Todos", "Activo", "Pasivo", "Capital", "Ingreso", "Egreso"]
            tipo_filtro = st.selectbox("Filtrar por tipo de cuenta:", tipos_cuenta)
            
            nivel_filtro = st.selectbox(
                "Filtrar por nivel:",
                ["Todos los niveles", "Nivel 1", "Nivel 2", "Nivel 3", "Nivel 4", "Nivel 5"]
            )
        
        with col2:
            # Filtro por rango de códigos
            codigo_desde = st.text_input("Código desde (opcional):", help="Ej: 1000")
            codigo_hasta = st.text_input("Código hasta (opcional):", help="Ej: 9999")
            
            # Filtro por texto
            filtro_nombre = st.text_input("Buscar en nombres:", help="Texto a buscar en nombres de cuentas")
    
    if st.button("📊 Generar Balanza de Comprobación", width="stretch", type="primary"):
        # Extraer ID del período
        nombre_periodo = periodo_seleccionado.split(" (")[0]
        periodo_obj = next((p for p in periodos if p['descripcion'] == nombre_periodo), None)
        
        if periodo_obj:
            obtener_balanza_comprobacion(
                backend_url,
                periodo_obj['id_periodo'],
                fecha_corte,
                incluir_saldo_inicial,
                solo_cuentas_con_movimientos,
                incluir_cuentas_cero,
                formato_detallado,
                tipo_filtro,
                nivel_filtro,
                codigo_desde,
                codigo_hasta,
                filtro_nombre
            )

def obtener_balanza_comprobacion(
    backend_url: str,
    id_periodo: int,
    fecha_corte: date,
    incluir_saldo_inicial: bool,
    solo_cuentas_con_movimientos: bool,
    incluir_cuentas_cero: bool,
    formato_detallado: bool,
    tipo_filtro: str,
    nivel_filtro: str,
    codigo_desde: str,
    codigo_hasta: str,
    filtro_nombre: str
):
    """Obtener y mostrar balanza de comprobación"""
    
    try:
        # Construir parámetros
        params = {
            "fecha_corte": fecha_corte.isoformat(),
            "incluir_saldo_inicial": incluir_saldo_inicial,
            "solo_con_movimientos": solo_cuentas_con_movimientos,
            "incluir_saldo_cero": incluir_cuentas_cero,
            "formato_detallado": formato_detallado
        }
        
        if tipo_filtro != "Todos":
            params["tipo_cuenta"] = tipo_filtro
        
        if nivel_filtro != "Todos los niveles":
            nivel = int(nivel_filtro.split(" ")[1])
            params["nivel"] = nivel
        
        if codigo_desde:
            params["codigo_desde"] = codigo_desde
        
        if codigo_hasta:
            params["codigo_hasta"] = codigo_hasta
        
        if filtro_nombre:
            params["filtro_nombre"] = filtro_nombre
        
        # Realizar consulta - primero intentar obtener análisis de cuentas
        with st.spinner("Generando balanza de comprobación..."):
            # Usar endpoint de análisis de cuentas que retorna datos similares
            response = requests.get(
                f"{backend_url}/api/balanza-comprobacion/analisis/{id_periodo}",
                params={"tipo_cuenta": params.get("tipo_cuenta") if tipo_filtro != "Todos" else None}
            )
        
        if response.status_code == 200:
            datos_analisis = response.json()
            # Adaptar datos para mostrar como balanza
            # El endpoint puede devolver una lista directamente o un dict con 'cuentas'
            if isinstance(datos_analisis, list):
                cuentas = datos_analisis
            elif isinstance(datos_analisis, dict):
                cuentas = datos_analisis.get('cuentas', [])
            else:
                cuentas = []
            
            datos_balanza = {
                'descripcion': f'Período {id_periodo}',
                'fecha_corte': fecha_corte.isoformat(),
                'cuentas': cuentas
            }
            mostrar_balanza_comprobacion(datos_balanza, formato_detallado)
        elif response.status_code == 404:
            st.error("❌ Error al generar balanza: 404")
            st.info("💡 El endpoint de balanza no está disponible. Verifica la configuración del backend.")
        else:
            st.error(f"Error al generar balanza: {response.status_code}")
            
    except Exception as e:
        st.error(f"Error al obtener balanza: {e}")

def mostrar_balanza_comprobacion(datos_balanza: Dict[str, Any], formato_detallado: bool):
    """Mostrar los resultados de la balanza de comprobación"""
    
    # Información del período
    st.markdown("### 📊 Información del Reporte")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Período", datos_balanza.get('descripcion', 'N/A'))
    
    with col2:
        fecha_generacion = datetime.now().strftime('%d/%m/%Y %H:%M')
        st.metric("Fecha de Generación", fecha_generacion)
    
    with col3:
        total_cuentas = len(datos_balanza.get('cuentas', []))
        st.metric("Total Cuentas", total_cuentas)
    
    with col4:
        fecha_corte = datos_balanza.get('fecha_corte', 'N/A')
        st.metric("Fecha de Corte", fecha_corte)
    
    # Cuentas de la balanza
    cuentas = datos_balanza.get('cuentas', [])
    
    if cuentas:
        # Crear DataFrame
        df_cuentas = pd.DataFrame(cuentas)
        
        
        # Convertir columnas numéricas a float para evitar errores con Decimal
        for col in ['saldo_inicial', 'total_debe', 'total_haber', 'saldo_final']:
            if col in df_cuentas.columns:
                df_cuentas[col] = df_cuentas[col].apply(lambda x: float(x) if x is not None else 0.0)
        
        # Calcular totales
        total_debe = float(df_cuentas['total_debe'].sum())
        total_haber = float(df_cuentas['total_haber'].sum())
        total_saldo_deudor = float(df_cuentas[df_cuentas['saldo_final'] > 0]['saldo_final'].sum())
        total_saldo_acreedor = float(abs(df_cuentas[df_cuentas['saldo_final'] < 0]['saldo_final'].sum()))
        
        # Mostrar totales de control
        st.markdown("### 📊 Totales de Control")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Debe", f"${total_debe:,.2f}")
        
        with col2:
            st.metric("Total Haber", f"${total_haber:,.2f}")
        
        with col3:
            st.metric("Saldos Deudores", f"${total_saldo_deudor:,.2f}")
        
        with col4:
            st.metric("Saldos Acreedores", f"${total_saldo_acreedor:,.2f}")
        
        # Validación de balance
        diferencia_debe_haber = abs(total_debe - total_haber)
        diferencia_saldos = abs(total_saldo_deudor - total_saldo_acreedor)
        
        if diferencia_debe_haber > 0.01 or diferencia_saldos > 0.01:
            st.error("⚠️ ADVERTENCIA: La balanza no está cuadrada. Revisa las cifras.")
            col1, col2 = st.columns(2)
            with col1:
                st.error(f"Diferencia Debe-Haber: ${diferencia_debe_haber:,.2f}")
            with col2:
                st.error(f"Diferencia Saldos: ${diferencia_saldos:,.2f}")
        else:
            st.success("✅ La balanza está correctamente balanceada")
        
        # Tabla de cuentas
        st.markdown("### 📋 Detalle de Cuentas")
        
        # Preparar DataFrame para mostrar
        df_display = df_cuentas.copy()
        
        # Formatear columnas monetarias
        for col in ['saldo_inicial', 'total_debe', 'total_haber', 'saldo_final']:
            if col in df_display.columns:
                df_display[f'{col}_fmt'] = df_display[col].apply(
                    lambda x: f"${float(x):,.2f}" if x != 0 else "-"
                )
        
        # Determinar naturaleza del saldo
        df_display['naturaleza_saldo'] = df_display['saldo_final'].apply(
            lambda x: "Deudor" if x > 0 else "Acreedor" if x < 0 else "Cero"
        )
        
        # Valor absoluto para saldos acreedores
        df_display['saldo_deudor'] = df_display['saldo_final'].apply(
            lambda x: f"${float(x):,.2f}" if float(x) > 0 else "-"
        )
        df_display['saldo_acreedor'] = df_display['saldo_final'].apply(
            lambda x: f"${abs(float(x)):,.2f}" if float(x) < 0 else "-"
        )
        
        if formato_detallado:
            # Formato detallado con todas las columnas
            columnas_mostrar = [
                'codigo_cuenta', 'nombre_cuenta', 'tipo_cuenta', 
                'saldo_inicial_fmt', 'total_debe_fmt', 'total_haber_fmt',
                'saldo_deudor', 'saldo_acreedor', 'naturaleza_saldo'
            ]
            nombres_columnas = [
                'Código', 'Nombre de la Cuenta', 'Tipo', 
                'Saldo Inicial', 'Debe', 'Haber',
                'Saldo Deudor', 'Saldo Acreedor', 'Naturaleza'
            ]
        else:
            # Formato simplificado
            columnas_mostrar = [
                'codigo_cuenta', 'nombre_cuenta', 'saldo_deudor', 'saldo_acreedor'
            ]
            nombres_columnas = ['Código', 'Nombre de la Cuenta', 'Saldo Deudor', 'Saldo Acreedor']
        
        # Renombrar columnas
        df_final = df_display[columnas_mostrar].copy()
        df_final.columns = nombres_columnas
        
        # Mostrar tabla
        st.dataframe(
            df_final,
            width="stretch",
            hide_index=True,
            column_config={
                "Código": st.column_config.TextColumn(width="small"),
                "Nombre de la Cuenta": st.column_config.TextColumn(width="large"),
            }
        )
        
        # Filtros para análisis rápido
        st.markdown("### 🔍 Análisis Rápido")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Top 10 Saldos Deudores:**")
            top_deudores = df_cuentas[df_cuentas['saldo_final'] > 0].nlargest(10, 'saldo_final')
            if not top_deudores.empty:
                for _, cuenta in top_deudores.iterrows():
                    st.text(f"{cuenta['codigo_cuenta']}: ${float(cuenta['saldo_final']):,.2f}")
            else:
                st.info("No hay saldos deudores")
        
        with col2:
            st.markdown("**Top 10 Saldos Acreedores:**")
            top_acreedores = df_cuentas[df_cuentas['saldo_final'] < 0].nsmallest(10, 'saldo_final')
            if not top_acreedores.empty:
                for _, cuenta in top_acreedores.iterrows():
                    st.text(f"{cuenta['codigo_cuenta']}: ${abs(float(cuenta['saldo_final'])):,.2f}")
            else:
                st.info("No hay saldos acreedores")
        
        # Opción de descarga
        st.markdown("### 📥 Descargar Reporte")
        
        # Crear Excel con formato adecuado
        from io import BytesIO
        import openpyxl
        from openpyxl.styles import Font, Alignment
        
        # Crear archivo Excel
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_final.to_excel(writer, index=False, sheet_name='Balanza de Comprobación')
            
            # Obtener la hoja y aplicar formato
            workbook = writer.book
            worksheet = writer.sheets['Balanza de Comprobación']
            
            # Aplicar formato a encabezados
            for cell in worksheet[1]:
                cell.font = Font(bold=True)
                cell.alignment = Alignment(horizontal='center')
            
            # Ajustar ancho de columnas
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width
        
        excel_data = output.getvalue()
        
        st.download_button(
            label="📊 Descargar Excel",
            data=excel_data,
            file_name=f"balanza_comprobacion_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    
    else:
        st.info("📭 No se encontraron cuentas para mostrar con los filtros aplicados")

def analisis_grafico_balanza(backend_url: str):
    """Análisis gráfico de la balanza de comprobación"""
    
    st.subheader("📈 Análisis Gráfico de la Balanza")
    
    # Selección de período
    try:
        response_periodos = requests.get(f"{backend_url}/api/periodos")
        periodos = response_periodos.json() if response_periodos.status_code == 200 else []
        
        if periodos:
            opciones_periodos = [
                f"{p['descripcion']} ({p['fecha_inicio']} - {p['fecha_fin']})"
                for p in periodos
            ]
            periodo_grafico = st.selectbox("Seleccionar período:", opciones_periodos, key="grafico_balanza")
            
            if st.button("📊 Generar Gráficos"):
                nombre_periodo = periodo_grafico.split(" (")[0]
                periodo_obj = next((p for p in periodos if p['descripcion'] == nombre_periodo), None)
                
                if periodo_obj:
                    generar_graficos_balanza(backend_url, periodo_obj['id_periodo'])
        else:
            st.warning("No hay períodos configurados")
            
    except:
        st.error("Error al cargar períodos")

def generar_graficos_balanza(backend_url: str, id_periodo: int):
    """Generar gráficos de análisis de la balanza"""
    
    try:
        # Obtener datos de la balanza usando endpoint de análisis
        response = requests.get(f"{backend_url}/api/balanza-comprobacion/analisis/{id_periodo}")
        
        if response.status_code == 200:
            datos_analisis = response.json()
            # El endpoint puede devolver una lista directamente o un dict con 'cuentas'
            if isinstance(datos_analisis, list):
                cuentas = datos_analisis
            elif isinstance(datos_analisis, dict):
                cuentas = datos_analisis.get('cuentas', [])
            else:
                cuentas = []
            
            if cuentas:
                df = pd.DataFrame(cuentas)
                
                # Convertir columnas numéricas a float
                for col in ['saldo_inicial', 'total_debe', 'total_haber', 'saldo_final']:
                    if col in df.columns:
                        df[col] = df[col].apply(lambda x: float(x) if x is not None else 0.0)
                
                # Gráfico 1: Distribución por tipo de cuenta (Pie chart)
                st.markdown("#### 📊 Distribución por Tipo de Cuenta")
                
                resumen_tipos = df.groupby('tipo_cuenta').agg({
                    'saldo_final': lambda x: x.apply(abs).sum(),
                    'codigo_cuenta': 'count'
                }).reset_index()
                resumen_tipos.columns = ['tipo_cuenta', 'total_saldo', 'cantidad_cuentas']
                
                fig_pie = px.pie(
                    resumen_tipos,
                    values='total_saldo',
                    names='tipo_cuenta',
                    title='Distribución de Saldos por Tipo de Cuenta'
                )
                st.plotly_chart(fig_pie, width="stretch")
                
            else:
                st.info("No hay datos para generar gráficos")
        else:
            st.error(f"Error al obtener datos: {response.status_code}")
            
    except Exception as e:
        st.error(f"Error al generar gráficos: {e}")

def comparativo_periodos(backend_url: str):
    """Comparativo entre períodos"""
    
    st.subheader("📋 Comparativo entre Períodos")
    
    # Selección de períodos para comparar
    try:
        response_periodos = requests.get(f"{backend_url}/api/periodos")
        periodos = response_periodos.json() if response_periodos.status_code == 200 else []
        
        if len(periodos) < 2:
            st.warning("Se necesitan al menos 2 períodos configurados para realizar comparaciones")
            return
        
        opciones_periodos = [
            f"{p['descripcion']} ({p['fecha_inicio']} - {p['fecha_fin']})"
            for p in periodos
        ]
        
        col1, col2 = st.columns(2)
        
        with col1:
            periodo1 = st.selectbox("Período base:", opciones_periodos, key="periodo1")
        
        with col2:
            periodo2 = st.selectbox("Período comparación:", opciones_periodos, key="periodo2")
        
        # Opciones de comparación
        col1, col2 = st.columns(2)
        
        with col1:
            tipo_comparacion = st.selectbox(
                "Tipo de comparación:",
                ["Solo cuentas comunes", "Todas las cuentas", "Solo diferencias"]
            )
        
        with col2:
            umbral_diferencia = st.number_input(
                "Umbral de diferencia ($):",
                min_value=0.01,
                value=100.00,
                step=10.00,
                help="Mostrar solo diferencias mayores a este monto"
            )
        
        if st.button("📊 Generar Comparativo", width="stretch"):
            if periodo1 != periodo2:
                generar_comparativo_periodos(
                    backend_url, 
                    periodo1, 
                    periodo2, 
                    periodos,
                    tipo_comparacion,
                    umbral_diferencia
                )
            else:
                st.error("Selecciona períodos diferentes para comparar")
                
    except:
        st.error("Error al cargar períodos")

def generar_comparativo_periodos(
    backend_url: str,
    periodo1: str,
    periodo2: str,
    periodos: List[Dict],
    tipo_comparacion: str,
    umbral_diferencia: float
):
    """Generar comparativo entre períodos"""
    
    try:
        # Obtener IDs de períodos
        nombre_periodo1 = periodo1.split(" (")[0]
        nombre_periodo2 = periodo2.split(" (")[0]
        
        periodo_obj1 = next((p for p in periodos if p['descripcion'] == nombre_periodo1), None)
        periodo_obj2 = next((p for p in periodos if p['descripcion'] == nombre_periodo2), None)
        
        if not periodo_obj1 or not periodo_obj2:
            st.error("Error al identificar los períodos")
            return
        
        # Obtener datos de ambos períodos usando endpoint de análisis
        with st.spinner("Obteniendo datos de los períodos..."):
            response1 = requests.get(f"{backend_url}/api/balanza-comprobacion/analisis/{periodo_obj1['id_periodo']}")
            response2 = requests.get(f"{backend_url}/api/balanza-comprobacion/analisis/{periodo_obj2['id_periodo']}")
        
        if response1.status_code == 200 and response2.status_code == 200:
            datos1 = response1.json()
            datos2 = response2.json()
            
            # Manejar tanto listas como diccionarios
            if isinstance(datos1, list):
                cuentas1_list = datos1
            elif isinstance(datos1, dict):
                cuentas1_list = datos1.get('cuentas', [])
            else:
                cuentas1_list = []
            
            if isinstance(datos2, list):
                cuentas2_list = datos2
            elif isinstance(datos2, dict):
                cuentas2_list = datos2.get('cuentas', [])
            else:
                cuentas2_list = []
            
            cuentas1 = {c['codigo_cuenta']: c for c in cuentas1_list}
            cuentas2 = {c['codigo_cuenta']: c for c in cuentas2_list}
            
            mostrar_comparativo(
                cuentas1, cuentas2, 
                nombre_periodo1, nombre_periodo2,
                tipo_comparacion, umbral_diferencia
            )
            
        else:
            st.error("Error al obtener datos de los períodos")
            
    except Exception as e:
        st.error(f"Error al generar comparativo: {e}")

def mostrar_comparativo(
    cuentas1: Dict[str, Any],
    cuentas2: Dict[str, Any],
    nombre_periodo1: str,
    nombre_periodo2: str,
    tipo_comparacion: str,
    umbral_diferencia: float
):
    """Mostrar el comparativo entre períodos"""
    
    st.markdown(f"### 📊 Comparativo: {nombre_periodo1} vs {nombre_periodo2}")
    
    # Preparar datos para comparación
    todos_codigos = set(cuentas1.keys()) | set(cuentas2.keys())
    comparativo_data = []
    
    for codigo in todos_codigos:
        cuenta1 = cuentas1.get(codigo, {})
        cuenta2 = cuentas2.get(codigo, {})
        
        nombre_cuenta = cuenta1.get('nombre_cuenta') or cuenta2.get('nombre_cuenta', 'N/A')
        saldo1 = float(cuenta1.get('saldo_final', 0)) if cuenta1.get('saldo_final') is not None else 0.0
        saldo2 = float(cuenta2.get('saldo_final', 0)) if cuenta2.get('saldo_final') is not None else 0.0
        diferencia = saldo2 - saldo1
        
        # Aplicar filtros según tipo de comparación
        if tipo_comparacion == "Solo cuentas comunes" and (not cuenta1 or not cuenta2):
            continue
        elif tipo_comparacion == "Solo diferencias" and abs(diferencia) < umbral_diferencia:
            continue
        
        # Calcular porcentaje de variación
        porcentaje_variacion = 0
        if saldo1 != 0:
            porcentaje_variacion = (diferencia / abs(saldo1)) * 100
        
        comparativo_data.append({
            'codigo_cuenta': codigo,
            'nombre_cuenta': nombre_cuenta,
            'saldo_periodo1': saldo1,
            'saldo_periodo2': saldo2,
            'diferencia': diferencia,
            'porcentaje_variacion': porcentaje_variacion,
            'tiene_en_periodo1': codigo in cuentas1,
            'tiene_en_periodo2': codigo in cuentas2
        })
    
    if comparativo_data:
        df_comparativo = pd.DataFrame(comparativo_data)
        
        # Métricas resumen
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Cuentas Comparadas", len(df_comparativo))
        
        with col2:
            diferencias_positivas = len(df_comparativo[df_comparativo['diferencia'] > 0])
            st.metric("Incrementos", diferencias_positivas)
        
        with col3:
            diferencias_negativas = len(df_comparativo[df_comparativo['diferencia'] < 0])
            st.metric("Decrementos", diferencias_negativas)
        
        with col4:
            total_variacion = df_comparativo['diferencia'].abs().sum()
            st.metric("Variación Total", f"${total_variacion:,.2f}")
        
        # Formatear DataFrame para mostrar
        df_display = df_comparativo.copy()
        
        # Formatear columnas monetarias
        df_display['saldo_periodo1_fmt'] = df_display['saldo_periodo1'].apply(lambda x: f"${float(x):,.2f}")
        df_display['saldo_periodo2_fmt'] = df_display['saldo_periodo2'].apply(lambda x: f"${float(x):,.2f}")
        df_display['diferencia_fmt'] = df_display['diferencia'].apply(
            lambda x: f"${float(x):,.2f}" if float(x) >= 0 else f"-${abs(float(x)):,.2f}"
        )
        df_display['porcentaje_fmt'] = df_display['porcentaje_variacion'].apply(
            lambda x: f"{x:+.1f}%" if abs(x) < 999 else "N/A"
        )
        
        # Añadir indicadores
        df_display['tendencia'] = df_display['diferencia'].apply(
            lambda x: "📈" if x > 0 else "📉" if x < 0 else "➡️"
        )
        
        # Tabla de comparativo
        columnas_mostrar = [
            'codigo_cuenta', 'nombre_cuenta', 'saldo_periodo1_fmt', 
            'saldo_periodo2_fmt', 'diferencia_fmt', 'porcentaje_fmt', 'tendencia'
        ]
        
        nombres_columnas = [
            'Código', 'Nombre Cuenta', f'Saldo {nombre_periodo1}', 
            f'Saldo {nombre_periodo2}', 'Diferencia', 'Variación %', 'Tendencia'
        ]
        
        df_final = df_display[columnas_mostrar].copy()
        df_final.columns = nombres_columnas
        
        st.dataframe(df_final, width="stretch", hide_index=True)
        
        # Gráficos de análisis
        st.markdown("### 📊 Análisis Gráfico del Comparativo")
        
        # Top variaciones
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**🔺 Top 10 Incrementos**")
            top_incrementos = df_comparativo[df_comparativo['diferencia'] > 0].nlargest(10, 'diferencia')
            
            if not top_incrementos.empty:
                fig_incrementos = px.bar(
                    top_incrementos,
                    x='diferencia',
                    y='codigo_cuenta',
                    orientation='h',
                    title='Top Incrementos',
                    hover_data=['nombre_cuenta', 'porcentaje_variacion']
                )
                st.plotly_chart(fig_incrementos, width="stretch")
            else:
                st.info("No hay incrementos significativos")
        
        with col2:
            st.markdown("**🔻 Top 10 Decrementos**")
            top_decrementos = df_comparativo[df_comparativo['diferencia'] < 0].nsmallest(10, 'diferencia')
            
            if not top_decrementos.empty:
                fig_decrementos = px.bar(
                    top_decrementos,
                    x='diferencia',
                    y='codigo_cuenta',
                    orientation='h',
                    title='Top Decrementos',
                    hover_data=['nombre_cuenta', 'porcentaje_variacion']
                )
                st.plotly_chart(fig_decrementos, width="stretch")
            else:
                st.info("No hay decrementos significativos")
        
        # Descarga de comparativo
        st.markdown("### 📥 Descargar Comparativo")
        csv = df_final.to_csv(index=False)
        st.download_button(
            label="📥 Descargar Comparativo CSV",
            data=csv,
            file_name=f"comparativo_{nombre_periodo1}_vs_{nombre_periodo2}_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
        
    else:
        st.info("📭 No se encontraron datos para comparar con los filtros aplicados")
