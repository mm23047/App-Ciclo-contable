"""
Módulo Streamlit para Estados Financieros.
Generación de estados financieros principales: Balance General y Estado de Resultados.
"""
import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
from typing import Dict, Any, List

def render_page(backend_url: str):
    """Renderizar página de estados financieros"""
    
    st.header("📊 Estados Financieros")
    st.markdown("Generación de estados financieros principales para análisis empresarial")
    
    # Tabs para diferentes estados financieros
    tab1, tab2, tab3, tab4 = st.tabs(["💰 Balance General", "📈 Estado de Resultados", "📊 Análisis Comparativo", "📋 Reportes"])
    
    with tab1:
        balance_general(backend_url)
    
    with tab2:
        estado_resultados(backend_url)
    
    with tab3:
        analisis_comparativo(backend_url)
    
    with tab4:
        reportes_financieros(backend_url)

def balance_general(backend_url: str):
    """Generar Balance General"""
    
    st.subheader("💰 Balance General")
    st.markdown("Estado de situación financiera en un momento determinado")
    
    # Configuración del reporte
    col1, col2 = st.columns(2)
    
    with col1:
        # Selección de período
        try:
            response_periodos = requests.get(f"{backend_url}/api/periodos")
            periodos = response_periodos.json() if response_periodos.status_code == 200 else []
            
            if periodos:
                opciones_periodos = [
                    f"{p['descripcion']} ({p['fecha_inicio']} - {p['fecha_fin']})"
                    for p in periodos
                ]
                periodo_seleccionado = st.selectbox("Período:", opciones_periodos)
            else:
                st.warning("No hay períodos configurados")
                return
        except:
            st.error("Error al cargar períodos")
            return
        
        fecha_corte = st.date_input(
            "Fecha de corte:",
            value=datetime.now().date(),
            help="Fecha para el balance general"
        )
    
    with col2:
        # Opciones de formato
        formato_detallado = st.checkbox("Formato detallado", value=True)
        incluir_saldo_cero = st.checkbox("Incluir cuentas con saldo cero", value=False)
        mostrar_codigos = st.checkbox("Mostrar códigos de cuenta", value=True)
        comparativo_periodo_anterior = st.checkbox("Comparativo con período anterior", value=False)
    
    if st.button("📊 Generar Balance General", use_container_width=True, type="primary"):
        nombre_periodo = periodo_seleccionado.split(" (")[0]
        periodo_obj = next((p for p in periodos if p['descripcion'] == nombre_periodo), None)
        
        if periodo_obj:
            generar_balance_general(
                backend_url,
                periodo_obj['id_periodo'],
                fecha_corte,
                formato_detallado,
                incluir_saldo_cero,
                mostrar_codigos,
                comparativo_periodo_anterior
            )

def generar_balance_general(
    backend_url: str,
    id_periodo: int,
    fecha_corte: date,
    formato_detallado: bool,
    incluir_saldo_cero: bool,
    mostrar_codigos: bool,
    comparativo: bool
):
    """Generar y mostrar balance general"""
    
    try:
        params = {
            "fecha_corte": fecha_corte.isoformat(),
            "formato_detallado": formato_detallado,
            "incluir_saldo_cero": incluir_saldo_cero,
            "comparativo": comparativo
        }
        
        with st.spinner("Generando Balance General..."):
            response = requests.get(f"{backend_url}/api/estados-financieros/balance-general/{id_periodo}", params=params)
        
        if response.status_code == 200:
            balance_data = response.json()
            mostrar_balance_general(balance_data, mostrar_codigos, comparativo)
        else:
            st.error(f"Error al generar balance general: {response.status_code}")
            
    except Exception as e:
        st.error(f"Error al generar balance general: {e}")

def mostrar_balance_general(balance_data: Dict[str, Any], mostrar_codigos: bool, comparativo: bool):
    """Mostrar el balance general formateado"""
    
    # Encabezado del reporte
    st.markdown("### 💰 BALANCE GENERAL")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Período", balance_data.get('descripcion', 'N/A'))
    
    with col2:
        st.metric("Fecha de Corte", balance_data.get('fecha_corte', 'N/A'))
    
    with col3:
        fecha_generacion = datetime.now().strftime('%d/%m/%Y %H:%M')
        st.metric("Fecha de Generación", fecha_generacion)
    
    # ACTIVOS
    st.markdown("#### 📈 ACTIVOS")
    activos = balance_data.get('activos', {})
    
    # Activos Corrientes
    if 'activos_corrientes' in activos:
        with st.expander("💧 Activos Corrientes", expanded=True):
            mostrar_seccion_balance(activos['activos_corrientes'], mostrar_codigos, comparativo)
            
            total_corrientes = activos['activos_corrientes'].get('total', 0)
            st.markdown(f"**Total Activos Corrientes: ${total_corrientes:,.2f}**")
    
    # Activos No Corrientes
    if 'activos_no_corrientes' in activos:
        with st.expander("🏢 Activos No Corrientes", expanded=True):
            mostrar_seccion_balance(activos['activos_no_corrientes'], mostrar_codigos, comparativo)
            
            total_no_corrientes = activos['activos_no_corrientes'].get('total', 0)
            st.markdown(f"**Total Activos No Corrientes: ${total_no_corrientes:,.2f}**")
    
    total_activos = activos.get('total_activos', 0)
    st.markdown(f"### 💰 **TOTAL ACTIVOS: ${total_activos:,.2f}**")
    
    # PASIVOS Y PATRIMONIO
    st.markdown("#### 📉 PASIVOS Y PATRIMONIO")
    
    pasivos = balance_data.get('pasivos', {})
    patrimonio = balance_data.get('patrimonio', {})
    
    # Pasivos Corrientes
    if 'pasivos_corrientes' in pasivos:
        with st.expander("⚡ Pasivos Corrientes", expanded=True):
            mostrar_seccion_balance(pasivos['pasivos_corrientes'], mostrar_codigos, comparativo)
            
            total_pasivos_corrientes = pasivos['pasivos_corrientes'].get('total', 0)
            st.markdown(f"**Total Pasivos Corrientes: ${total_pasivos_corrientes:,.2f}**")
    
    # Pasivos No Corrientes
    if 'pasivos_no_corrientes' in pasivos:
        with st.expander("📅 Pasivos No Corrientes", expanded=True):
            mostrar_seccion_balance(pasivos['pasivos_no_corrientes'], mostrar_codigos, comparativo)
            
            total_pasivos_no_corrientes = pasivos['pasivos_no_corrientes'].get('total', 0)
            st.markdown(f"**Total Pasivos No Corrientes: ${total_pasivos_no_corrientes:,.2f}**")
    
    total_pasivos = pasivos.get('total_pasivos', 0)
    st.markdown(f"**Total Pasivos: ${total_pasivos:,.2f}**")
    
    # Patrimonio
    if patrimonio:
        with st.expander("🏦 Patrimonio", expanded=True):
            mostrar_seccion_balance(patrimonio, mostrar_codigos, comparativo)
    
    total_patrimonio = patrimonio.get('total', 0)
    st.markdown(f"**Total Patrimonio: ${total_patrimonio:,.2f}**")
    
    # Total Pasivos + Patrimonio
    total_pasivos_patrimonio = total_pasivos + total_patrimonio
    st.markdown(f"### 💼 **TOTAL PASIVOS + PATRIMONIO: ${total_pasivos_patrimonio:,.2f}**")
    
    # Validación de balance
    diferencia = total_activos - total_pasivos_patrimonio
    
    if abs(diferencia) < 0.01:
        st.success("✅ El Balance General está correctamente balanceado")
    else:
        st.error(f"❌ ADVERTENCIA: Diferencia de ${diferencia:,.2f} - El balance no cuadra")
    
    # Indicadores financieros básicos
    mostrar_indicadores_balance(total_activos, total_pasivos, total_patrimonio, balance_data)
    
    # Descargar reporte
    generar_descarga_balance(balance_data)

def mostrar_seccion_balance(seccion: Dict[str, Any], mostrar_codigos: bool, comparativo: bool):
    """Mostrar una sección del balance general"""
    
    if 'cuentas' in seccion:
        data = []
        
        for cuenta in seccion['cuentas']:
            fila = {}
            
            if mostrar_codigos:
                fila['Cuenta'] = f"{cuenta['codigo_cuenta']} - {cuenta['nombre_cuenta']}"
            else:
                fila['Cuenta'] = cuenta['nombre_cuenta']
            
            fila['Saldo'] = f"${cuenta['saldo']:,.2f}"
            
            if comparativo and 'saldo_anterior' in cuenta:
                fila['Saldo Anterior'] = f"${cuenta['saldo_anterior']:,.2f}"
                variacion = cuenta['saldo'] - cuenta['saldo_anterior']
                fila['Variación'] = f"${variacion:,.2f}"
                if cuenta['saldo_anterior'] != 0:
                    porcentaje = (variacion / abs(cuenta['saldo_anterior'])) * 100
                    fila['% Variación'] = f"{porcentaje:+.1f}%"
            
            data.append(fila)
        
        if data:
            df = pd.DataFrame(data)
            st.dataframe(df, use_container_width=True, hide_index=True)

def mostrar_indicadores_balance(total_activos: float, total_pasivos: float, total_patrimonio: float, balance_data: Dict):
    """Mostrar indicadores financieros básicos"""
    
    st.markdown("### 📊 Indicadores Financieros")
    
    col1, col2, col3, col4 = st.columns(4)
    
    # Ratio de liquidez (necesita activos y pasivos corrientes)
    activos_corrientes = balance_data.get('activos', {}).get('activos_corrientes', {}).get('total', 0)
    pasivos_corrientes = balance_data.get('pasivos', {}).get('pasivos_corrientes', {}).get('total', 0)
    
    with col1:
        if pasivos_corrientes > 0:
            ratio_liquidez = activos_corrientes / pasivos_corrientes
            st.metric("Ratio de Liquidez", f"{ratio_liquidez:.2f}")
        else:
            st.metric("Ratio de Liquidez", "N/A")
    
    with col2:
        if total_activos > 0:
            ratio_endeudamiento = (total_pasivos / total_activos) * 100
            st.metric("% Endeudamiento", f"{ratio_endeudamiento:.1f}%")
        else:
            st.metric("% Endeudamiento", "N/A")
    
    with col3:
        if total_activos > 0:
            ratio_patrimonio = (total_patrimonio / total_activos) * 100
            st.metric("% Patrimonio", f"{ratio_patrimonio:.1f}%")
        else:
            st.metric("% Patrimonio", "N/A")
    
    with col4:
        if total_patrimonio > 0:
            ratio_apalancamiento = total_pasivos / total_patrimonio
            st.metric("Apalancamiento", f"{ratio_apalancamiento:.2f}")
        else:
            st.metric("Apalancamiento", "N/A")

def generar_descarga_balance(balance_data: Dict[str, Any]):
    """Generar archivo para descarga del balance"""
    
    st.markdown("### 📥 Descargar Reporte")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Crear resumen para CSV
        resumen_data = []
        
        # Agregar activos
        activos = balance_data.get('activos', {})
        if 'activos_corrientes' in activos:
            for cuenta in activos['activos_corrientes'].get('cuentas', []):
                resumen_data.append({
                    'Tipo': 'Activo Corriente',
                    'Codigo': cuenta['codigo_cuenta'],
                    'Cuenta': cuenta['nombre_cuenta'],
                    'Saldo': cuenta['saldo']
                })
        
        # Similar para otros tipos...
        
        if resumen_data:
            df_resumen = pd.DataFrame(resumen_data)
            csv = df_resumen.to_csv(index=False)
            
            st.download_button(
                label="📥 Descargar CSV",
                data=csv,
                file_name=f"balance_general_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv"
            )
    
    with col2:
        # JSON completo
        import json
        json_data = json.dumps(balance_data, indent=2, ensure_ascii=False)
        
        st.download_button(
            label="📄 Descargar JSON",
            data=json_data,
            file_name=f"balance_general_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
            mime="application/json"
        )

def estado_resultados(backend_url: str):
    """Generar Estado de Resultados"""
    
    st.subheader("📈 Estado de Resultados")
    st.markdown("Estado de pérdidas y ganancias del período")
    
    # Configuración del reporte
    col1, col2 = st.columns(2)
    
    with col1:
        # Selección de período
        try:
            response_periodos = requests.get(f"{backend_url}/api/periodos")
            periodos = response_periodos.json() if response_periodos.status_code == 200 else []
            
            if periodos:
                opciones_periodos = [
                    f"{p['descripcion']} ({p['fecha_inicio']} - {p['fecha_fin']})"
                    for p in periodos
                ]
                periodo_seleccionado = st.selectbox("Período:", opciones_periodos, key="periodo_resultados")
            else:
                st.warning("No hay períodos configurados")
                return
        except:
            st.error("Error al cargar períodos")
            return
        
        fecha_desde = st.date_input("Desde:", help="Fecha inicial del período")
        fecha_hasta = st.date_input("Hasta:", value=datetime.now().date(), help="Fecha final del período")
    
    with col2:
        # Opciones de formato
        formato_detallado = st.checkbox("Formato detallado", value=True, key="detalle_resultados")
        agrupar_por_categoria = st.checkbox("Agrupar por categoría", value=True)
        incluir_cuentas_cero = st.checkbox("Incluir cuentas con movimiento cero", value=False, key="cero_resultados")
        mostrar_margenes = st.checkbox("Mostrar márgenes", value=True)
    
    if st.button("📊 Generar Estado de Resultados", use_container_width=True, type="primary"):
        nombre_periodo = periodo_seleccionado.split(" (")[0]
        periodo_obj = next((p for p in periodos if p['descripcion'] == nombre_periodo), None)
        
        if periodo_obj:
            generar_estado_resultados(
                backend_url,
                periodo_obj['id_periodo'],
                fecha_desde,
                fecha_hasta,
                formato_detallado,
                agrupar_por_categoria,
                incluir_cuentas_cero,
                mostrar_margenes
            )

def generar_estado_resultados(
    backend_url: str,
    id_periodo: int,
    fecha_desde: date,
    fecha_hasta: date,
    formato_detallado: bool,
    agrupar_por_categoria: bool,
    incluir_cuentas_cero: bool,
    mostrar_margenes: bool
):
    """Generar y mostrar estado de resultados"""
    
    try:
        params = {
            "fecha_desde": fecha_desde.isoformat(),
            "fecha_hasta": fecha_hasta.isoformat(),
            "formato_detallado": formato_detallado,
            "agrupar_por_categoria": agrupar_por_categoria,
            "incluir_cuentas_cero": incluir_cuentas_cero
        }
        
        with st.spinner("Generando Estado de Resultados..."):
            response = requests.get(f"{backend_url}/api/estados-financieros/estado-resultados/{id_periodo}", params=params)
        
        if response.status_code == 200:
            resultados_data = response.json()
            mostrar_estado_resultados(resultados_data, mostrar_margenes)
        else:
            st.error(f"Error al generar estado de resultados: {response.status_code}")
            
    except Exception as e:
        st.error(f"Error al generar estado de resultados: {e}")

def mostrar_estado_resultados(resultados_data: Dict[str, Any], mostrar_margenes: bool):
    """Mostrar el estado de resultados formateado"""
    
    # Encabezado del reporte
    st.markdown("### 📈 ESTADO DE RESULTADOS")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Período", resultados_data.get('descripcion', 'N/A'))
    
    with col2:
        fecha_desde = resultados_data.get('fecha_desde', 'N/A')
        fecha_hasta = resultados_data.get('fecha_hasta', 'N/A')
        st.metric("Rango de Fechas", f"{fecha_desde} - {fecha_hasta}")
    
    with col3:
        fecha_generacion = datetime.now().strftime('%d/%m/%Y %H:%M')
        st.metric("Fecha de Generación", fecha_generacion)
    
    # INGRESOS
    st.markdown("#### 💰 INGRESOS")
    ingresos = resultados_data.get('ingresos', {})
    
    with st.expander("📈 Ingresos Operacionales", expanded=True):
        if 'ingresos_operacionales' in ingresos:
            mostrar_seccion_resultados(ingresos['ingresos_operacionales'])
            total_ing_op = ingresos['ingresos_operacionales'].get('total', 0)
            st.markdown(f"**Total Ingresos Operacionales: ${total_ing_op:,.2f}**")
    
    if 'ingresos_no_operacionales' in ingresos:
        with st.expander("💡 Ingresos No Operacionales", expanded=False):
            mostrar_seccion_resultados(ingresos['ingresos_no_operacionales'])
            total_ing_no_op = ingresos['ingresos_no_operacionales'].get('total', 0)
            st.markdown(f"**Total Ingresos No Operacionales: ${total_ing_no_op:,.2f}**")
    
    total_ingresos = ingresos.get('total_ingresos', 0)
    st.markdown(f"### 💵 **TOTAL INGRESOS: ${total_ingresos:,.2f}**")
    
    # COSTOS Y GASTOS
    st.markdown("#### 📉 COSTOS Y GASTOS")
    
    costos = resultados_data.get('costos', {})
    gastos = resultados_data.get('gastos', {})
    
    # Costo de Ventas
    if costos:
        with st.expander("🏭 Costo de Ventas", expanded=True):
            mostrar_seccion_resultados(costos)
            total_costos = costos.get('total', 0)
            st.markdown(f"**Total Costo de Ventas: ${total_costos:,.2f}**")
        
        # Utilidad Bruta
        utilidad_bruta = total_ingresos - total_costos
        st.markdown(f"### 📊 **UTILIDAD BRUTA: ${utilidad_bruta:,.2f}**")
        
        if mostrar_margenes and total_ingresos > 0:
            margen_bruto = (utilidad_bruta / total_ingresos) * 100
            st.info(f"📊 Margen Bruto: {margen_bruto:.1f}%")
    
    # Gastos Operacionales
    if 'gastos_operacionales' in gastos:
        with st.expander("🏢 Gastos Operacionales", expanded=True):
            mostrar_seccion_resultados(gastos['gastos_operacionales'])
            total_gastos_op = gastos['gastos_operacionales'].get('total', 0)
            st.markdown(f"**Total Gastos Operacionales: ${total_gastos_op:,.2f}**")
    
    # Gastos No Operacionales
    if 'gastos_no_operacionales' in gastos:
        with st.expander("📋 Gastos No Operacionales", expanded=False):
            mostrar_seccion_resultados(gastos['gastos_no_operacionales'])
            total_gastos_no_op = gastos['gastos_no_operacionales'].get('total', 0)
            st.markdown(f"**Total Gastos No Operacionales: ${total_gastos_no_op:,.2f}**")
    
    total_gastos = gastos.get('total_gastos', 0)
    st.markdown(f"**Total Gastos: ${total_gastos:,.2f}**")
    
    # UTILIDAD NETA
    utilidad_neta = resultados_data.get('utilidad_neta', 0)
    
    if utilidad_neta >= 0:
        st.success(f"### 🎉 **UTILIDAD NETA: ${utilidad_neta:,.2f}**")
    else:
        st.error(f"### 😞 **PÉRDIDA NETA: ${abs(utilidad_neta):,.2f}**")
    
    # Márgenes de rentabilidad
    if mostrar_margenes:
        mostrar_margenes_rentabilidad(total_ingresos, utilidad_neta, resultados_data)
    
    # Gráfico de composición
    mostrar_grafico_resultados(resultados_data)
    
    # Descargar reporte
    generar_descarga_resultados(resultados_data)

def mostrar_seccion_resultados(seccion: Dict[str, Any]):
    """Mostrar una sección del estado de resultados"""
    
    if 'cuentas' in seccion:
        data = []
        
        for cuenta in seccion['cuentas']:
            data.append({
                'Cuenta': f"{cuenta['codigo_cuenta']} - {cuenta['nombre_cuenta']}",
                'Saldo': f"${cuenta['saldo']:,.2f}"
            })
        
        if data:
            df = pd.DataFrame(data)
            st.dataframe(df, use_container_width=True, hide_index=True)

def mostrar_margenes_rentabilidad(total_ingresos: float, utilidad_neta: float, resultados_data: Dict):
    """Mostrar márgenes de rentabilidad"""
    
    st.markdown("### 📊 Márgenes de Rentabilidad")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if total_ingresos > 0:
            margen_neto = (utilidad_neta / total_ingresos) * 100
            st.metric("Margen Neto", f"{margen_neto:.1f}%")
        else:
            st.metric("Margen Neto", "N/A")
    
    with col2:
        # Margen operacional (si hay datos de utilidad operacional)
        gastos_op = resultados_data.get('gastos', {}).get('gastos_operacionales', {}).get('total', 0)
        utilidad_operacional = total_ingresos - gastos_op
        
        if total_ingresos > 0:
            margen_operacional = (utilidad_operacional / total_ingresos) * 100
            st.metric("Margen Operacional", f"{margen_operacional:.1f}%")
        else:
            st.metric("Margen Operacional", "N/A")
    
    with col3:
        # ROA - necesitaríamos datos de activos
        st.metric("ROA", "Requiere Balance")
    
    with col4:
        # ROE - necesitaríamos datos de patrimonio
        st.metric("ROE", "Requiere Balance")

def mostrar_grafico_resultados(resultados_data: Dict[str, Any]):
    """Mostrar gráfico de composición de resultados"""
    
    st.markdown("### 📊 Análisis Gráfico")
    
    # Preparar datos para el gráfico
    ingresos_total = resultados_data.get('ingresos', {}).get('total_ingresos', 0)
    costos_total = resultados_data.get('costos', {}).get('total', 0)
    gastos_total = resultados_data.get('gastos', {}).get('total_gastos', 0)
    utilidad_neta = resultados_data.get('utilidad_neta', 0)
    
    # Gráfico de barras comparativo
    conceptos = ['Ingresos', 'Costos', 'Gastos', 'Utilidad Neta']
    valores = [ingresos_total, -costos_total, -gastos_total, utilidad_neta]
    colores = ['green', 'red', 'orange', 'blue' if utilidad_neta >= 0 else 'red']
    
    fig = go.Figure()
    
    for i, (concepto, valor, color) in enumerate(zip(conceptos, valores, colores)):
        fig.add_trace(go.Bar(
            x=[concepto],
            y=[valor],
            name=concepto,
            marker_color=color,
            text=[f'${abs(valor):,.0f}'],
            textposition='outside'
        ))
    
    fig.update_layout(
        title="Composición del Estado de Resultados",
        yaxis_title="Valor ($)",
        showlegend=False,
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)

def generar_descarga_resultados(resultados_data: Dict[str, Any]):
    """Generar archivo para descarga del estado de resultados"""
    
    st.markdown("### 📥 Descargar Reporte")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # CSV simplificado
        resumen_data = []
        
        # Agregar ingresos
        ingresos = resultados_data.get('ingresos', {})
        if 'ingresos_operacionales' in ingresos:
            for cuenta in ingresos['ingresos_operacionales'].get('cuentas', []):
                resumen_data.append({
                    'Tipo': 'Ingreso',
                    'Codigo': cuenta['codigo_cuenta'],
                    'Cuenta': cuenta['nombre_cuenta'],
                    'Saldo': cuenta['saldo']
                })
        
        # Agregar costos y gastos...
        
        if resumen_data:
            df_resumen = pd.DataFrame(resumen_data)
            csv = df_resumen.to_csv(index=False)
            
            st.download_button(
                label="📥 Descargar CSV",
                data=csv,
                file_name=f"estado_resultados_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv"
            )
    
    with col2:
        # JSON completo
        import json
        json_data = json.dumps(resultados_data, indent=2, ensure_ascii=False)
        
        st.download_button(
            label="📄 Descargar JSON",
            data=json_data,
            file_name=f"estado_resultados_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
            mime="application/json"
        )

def analisis_comparativo(backend_url: str):
    """Análisis comparativo entre períodos"""
    
    st.subheader("📊 Análisis Comparativo")
    st.markdown("Comparación de estados financieros entre diferentes períodos")
    
    # Selección de períodos para comparar
    try:
        response_periodos = requests.get(f"{backend_url}/api/periodos")
        periodos = response_periodos.json() if response_periodos.status_code == 200 else []
        
        if len(periodos) < 2:
            st.warning("Se necesitan al menos 2 períodos para realizar comparaciones")
            return
        
        opciones_periodos = [
            f"{p['descripcion']} ({p['fecha_inicio']} - {p['fecha_fin']})"
            for p in periodos
        ]
        
        col1, col2 = st.columns(2)
        
        with col1:
            periodo_base = st.selectbox("Período base:", opciones_periodos, key="comp_base")
        
        with col2:
            periodo_comparacion = st.selectbox("Período comparación:", opciones_periodos, key="comp_comp")
        
        # Tipo de análisis
        tipo_analisis = st.selectbox(
            "Tipo de análisis:",
            ["Balance General", "Estado de Resultados", "Análisis Integral"]
        )
        
        if st.button("📊 Generar Análisis Comparativo", use_container_width=True):
            if periodo_base != periodo_comparacion:
                generar_analisis_comparativo_ejecutar(
                    backend_url, 
                    periodo_base, 
                    periodo_comparacion, 
                    periodos,
                    tipo_analisis
                )
            else:
                st.error("Selecciona períodos diferentes para comparar")
                
    except:
        st.error("Error al cargar períodos")

def generar_analisis_comparativo_ejecutar(
    backend_url: str,
    periodo_base: str,
    periodo_comparacion: str,
    periodos: List[Dict],
    tipo_analisis: str
):
    """Ejecutar análisis comparativo"""
    
    try:
        # Obtener IDs de períodos
        nombre_base = periodo_base.split(" (")[0]
        nombre_comp = periodo_comparacion.split(" (")[0]
        
        periodo_obj_base = next((p for p in periodos if p['descripcion'] == nombre_base), None)
        periodo_obj_comp = next((p for p in periodos if p['descripcion'] == nombre_comp), None)
        
        if not periodo_obj_base or not periodo_obj_comp:
            st.error("Error al identificar los períodos")
            return
        
        with st.spinner("Generando análisis comparativo..."):
            # Aquí harías las llamadas al backend para obtener datos de ambos períodos
            # Por ahora, mostrar estructura del análisis
            
            st.markdown(f"### 📊 Análisis Comparativo: {nombre_base} vs {nombre_comp}")
            
            if tipo_analisis in ["Balance General", "Análisis Integral"]:
                st.markdown("#### 💰 Comparativo Balance General")
                st.info("📊 Aquí se mostraría la comparación de balances entre períodos")
            
            if tipo_analisis in ["Estado de Resultados", "Análisis Integral"]:
                st.markdown("#### 📈 Comparativo Estado de Resultados")
                st.info("📊 Aquí se mostraría la comparación de resultados entre períodos")
            
            if tipo_analisis == "Análisis Integral":
                st.markdown("#### 📊 Indicadores Financieros Comparativos")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("ROA", "12.5%", delta="2.3%")
                
                with col2:
                    st.metric("ROE", "18.7%", delta="1.8%")
                
                with col3:
                    st.metric("Liquidez", "1.45", delta="0.12")
                
                with col4:
                    st.metric("Endeudamiento", "35.2%", delta="-2.1%")
            
    except Exception as e:
        st.error(f"Error al generar análisis comparativo: {e}")

def reportes_financieros(backend_url: str):
    """Reportes financieros adicionales"""
    
    st.subheader("📋 Reportes Financieros Adicionales")
    st.markdown("Reportes especializados y análisis financieros")
    
    # Tipos de reportes disponibles
    tipo_reporte = st.selectbox(
        "Tipo de reporte:",
        [
            "Flujo de Efectivo",
            "Estado de Cambios en el Patrimonio",
            "Análisis de Tendencias",
            "Ratios Financieros Detallados",
            "Reporte Ejecutivo"
        ]
    )
    
    if tipo_reporte == "Flujo de Efectivo":
        generar_flujo_efectivo(backend_url)
    elif tipo_reporte == "Estado de Cambios en el Patrimonio":
        generar_estado_cambios_patrimonio(backend_url)
    elif tipo_reporte == "Análisis de Tendencias":
        generar_analisis_tendencias(backend_url)
    elif tipo_reporte == "Ratios Financieros Detallados":
        generar_ratios_detallados(backend_url)
    elif tipo_reporte == "Reporte Ejecutivo":
        generar_reporte_ejecutivo(backend_url)

def generar_flujo_efectivo(backend_url: str):
    """Generar reporte de flujo de efectivo"""
    
    st.markdown("#### 💧 Estado de Flujo de Efectivo")
    st.info("🚧 Módulo en desarrollo - Próximamente disponible")
    
    # Estructura básica del flujo de efectivo
    st.markdown("""
    **Estructura del Estado de Flujo de Efectivo:**
    
    1. **Flujos de Efectivo de las Actividades de Operación**
       - Utilidad neta
       - Ajustes por partidas que no representan efectivo
       - Cambios en activos y pasivos operacionales
    
    2. **Flujos de Efectivo de las Actividades de Inversión**
       - Compra/venta de activos fijos
       - Inversiones financieras
    
    3. **Flujos de Efectivo de las Actividades de Financiación**
       - Préstamos obtenidos/pagados
       - Aportes de capital
       - Distribución de dividendos
    """)

def generar_estado_cambios_patrimonio(backend_url: str):
    """Generar estado de cambios en el patrimonio"""
    
    st.markdown("#### 🏦 Estado de Cambios en el Patrimonio")
    st.info("🚧 Módulo en desarrollo - Próximamente disponible")

def generar_analisis_tendencias(backend_url: str):
    """Generar análisis de tendencias"""
    
    st.markdown("#### 📈 Análisis de Tendencias")
    st.info("🚧 Módulo en desarrollo - Próximamente disponible")

def generar_ratios_detallados(backend_url: str):
    """Generar análisis detallado de ratios"""
    
    st.markdown("#### 📊 Ratios Financieros Detallados")
    st.info("🚧 Módulo en desarrollo - Próximamente disponible")

def generar_reporte_ejecutivo(backend_url: str):
    """Generar reporte ejecutivo"""
    
    st.markdown("#### 📋 Reporte Ejecutivo")
    st.info("🚧 Módulo en desarrollo - Próximamente disponible")