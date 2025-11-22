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
    
    if st.button("📊 Generar Balance General", type="primary", use_container_width=True):
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
            "guardar": False  # No guardar automáticamente
        }
        
        with st.spinner("Generando Balance General..."):
            response = requests.get(f"{backend_url}/api/estados-financieros/balance-general/{id_periodo}", params=params)
        
        if response.status_code == 200:
            balance_data = response.json()
            mostrar_balance_general(balance_data, mostrar_codigos, comparativo, incluir_saldo_cero)
        elif response.status_code == 404:
            st.error("❌ Período no encontrado")
        else:
            error_detail = response.json().get('detail', 'Error desconocido') if response.headers.get('content-type') == 'application/json' else str(response.status_code)
            st.error(f"❌ Error al generar balance general: {error_detail}")
            
    except requests.exceptions.ConnectionError:
        st.error("❌ Error de conexión con el servidor. Verifique que el backend esté en ejecución.")
    except Exception as e:
        st.error(f"❌ Error inesperado: {str(e)}")

def mostrar_balance_general(balance_data: Dict[str, Any], mostrar_codigos: bool, comparativo: bool, incluir_saldo_cero: bool = False):
    """Mostrar el balance general formateado"""
    
    # Encabezado del reporte
    empresa = balance_data.get('empresa', {})
    periodo = balance_data.get('periodo', {})
    
    st.markdown("### 💰 BALANCE GENERAL")
    st.markdown(f"**{empresa.get('nombre', 'Empresa')}**")
    if empresa.get('nit'):
        st.caption(f"NIT: {empresa.get('nit')}")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Período", f"{periodo.get('tipo', 'N/A')}")
    
    with col2:
        fecha_inicio = periodo.get('fecha_inicio', 'N/A')
        fecha_fin = periodo.get('fecha_fin', 'N/A')
        st.metric("Rango", f"{fecha_inicio} / {fecha_fin}")
    
    with col3:
        fecha_generacion = balance_data.get('fecha_generacion', datetime.now().strftime('%Y-%m-%d'))
        st.metric("Fecha Generación", fecha_generacion)
    
    # ACTIVOS
    st.markdown("#### 📈 ACTIVOS")
    activos = balance_data.get('activos', {})
    
    # Activos Corrientes
    corrientes = activos.get('corrientes', [])
    if corrientes:
        with st.expander("💧 Activos Corrientes", expanded=True):
            mostrar_cuentas_balance(corrientes, mostrar_codigos, incluir_saldo_cero)
            total_corrientes = sum(c.get('saldo_final', 0) for c in corrientes)
            st.markdown(f"**Total Activos Corrientes: ${total_corrientes:,.2f}**")
    
    # Activos No Corrientes
    no_corrientes = activos.get('no_corrientes', [])
    if no_corrientes:
        with st.expander("🏢 Activos No Corrientes", expanded=True):
            mostrar_cuentas_balance(no_corrientes, mostrar_codigos, incluir_saldo_cero)
            total_no_corrientes = sum(c.get('saldo_final', 0) for c in no_corrientes)
            st.markdown(f"**Total Activos No Corrientes: ${total_no_corrientes:,.2f}**")
    
    total_activos = float(activos.get('total_activos', activos.get('total', activos.get('activos', 0))))
    st.markdown(f"### 💰 **TOTAL ACTIVOS: ${total_activos:,.2f}**")
    
    # PASIVOS Y PATRIMONIO
    st.markdown("#### 📉 PASIVOS Y PATRIMONIO")
    
    pasivos = balance_data.get('pasivos', {})
    patrimonio = balance_data.get('patrimonio', {})
    
    # Pasivos Corrientes
    pasivos_corrientes = pasivos.get('corrientes', [])
    if pasivos_corrientes:
        with st.expander("⚡ Pasivos Corrientes", expanded=True):
            mostrar_cuentas_balance(pasivos_corrientes, mostrar_codigos, incluir_saldo_cero)
            total_pasivos_corrientes = sum(c.get('saldo_final', 0) for c in pasivos_corrientes)
            st.markdown(f"**Total Pasivos Corrientes: ${total_pasivos_corrientes:,.2f}**")
    
    # Pasivos No Corrientes
    pasivos_no_corrientes = pasivos.get('no_corrientes', [])
    if pasivos_no_corrientes:
        with st.expander("📅 Pasivos No Corrientes", expanded=True):
            mostrar_cuentas_balance(pasivos_no_corrientes, mostrar_codigos, incluir_saldo_cero)
            total_pasivos_no_corrientes = sum(c.get('saldo_final', 0) for c in pasivos_no_corrientes)
            st.markdown(f"**Total Pasivos No Corrientes: ${total_pasivos_no_corrientes:,.2f}**")
    
    total_pasivos = float(pasivos.get('total_pasivos', pasivos.get('total', pasivos.get('pasivos', 0))))
    st.markdown(f"**Total Pasivos: ${total_pasivos:,.2f}**")
    
    # Patrimonio
    capital_cuentas = patrimonio.get('capital', [])
    utilidades_cuentas = patrimonio.get('utilidades', [])
    
    if capital_cuentas or utilidades_cuentas:
        with st.expander("🏦 Patrimonio", expanded=True):
            todas_patrimonio = capital_cuentas + utilidades_cuentas
            mostrar_cuentas_balance(todas_patrimonio, mostrar_codigos, incluir_saldo_cero)
    
    total_patrimonio = float(patrimonio.get('total_patrimonio', patrimonio.get('total', patrimonio.get('patrimonio', 0))))
    st.markdown(f"**Total Patrimonio: ${total_patrimonio:,.2f}**")
    
    # Total Pasivos + Patrimonio
    total_pasivos_patrimonio = float(balance_data.get('total_pasivo_patrimonio', total_pasivos + total_patrimonio))
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

def mostrar_cuentas_balance(cuentas: List[Dict], mostrar_codigos: bool, incluir_saldo_cero: bool):
    """Mostrar lista de cuentas del balance"""
    
    if not cuentas:
        st.info("No hay cuentas en esta sección")
        return
    
    data = []
    
    for cuenta in cuentas:
        saldo_final = cuenta.get('saldo_final', 0)
        
        # Filtrar cuentas con saldo cero si es necesario
        if not incluir_saldo_cero and abs(saldo_final) < 0.01:
            continue
        
        fila = {}
        
        if mostrar_codigos:
            fila['Cuenta'] = f"{cuenta['codigo']} - {cuenta['nombre']}"
        else:
            fila['Cuenta'] = cuenta['nombre']
        
        fila['Saldo Inicial'] = f"${float(cuenta.get('saldo_inicial', 0)):,.2f}"
        fila['Debe'] = f"${float(cuenta.get('movimientos_debe', 0)):,.2f}"
        fila['Haber'] = f"${float(cuenta.get('movimientos_haber', 0)):,.2f}"
        fila['Saldo Final'] = f"${float(saldo_final):,.2f}"
        
        data.append(fila)
    
    if data:
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No hay movimientos para mostrar")

def mostrar_seccion_balance(seccion: Dict[str, Any], mostrar_codigos: bool, comparativo: bool):
    """Mostrar una sección del balance general (legacy - para compatibilidad)"""
    
    if 'cuentas' in seccion:
        data = []
        
        for cuenta in seccion['cuentas']:
            fila = {}
            
            if mostrar_codigos:
                fila['Cuenta'] = f"{cuenta.get('codigo_cuenta', cuenta.get('codigo', ''))} - {cuenta.get('nombre_cuenta', cuenta.get('nombre', ''))}"
            else:
                fila['Cuenta'] = cuenta.get('nombre_cuenta', cuenta.get('nombre', ''))
            
            fila['Saldo'] = f"${float(cuenta.get('saldo', cuenta.get('saldo_final', 0))):,.2f}"
            
            if comparativo and 'saldo_anterior' in cuenta:
                fila['Saldo Anterior'] = f"${float(cuenta['saldo_anterior']):,.2f}"
                variacion = float(cuenta.get('saldo', cuenta.get('saldo_final', 0))) - float(cuenta['saldo_anterior'])
                fila['Variación'] = f"${variacion:,.2f}"
                if cuenta['saldo_anterior'] != 0:
                    porcentaje = (variacion / abs(float(cuenta['saldo_anterior']))) * 100
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
    activos = balance_data.get('activos', {})
    pasivos = balance_data.get('pasivos', {})
    
    activos_corrientes_lista = activos.get('corrientes', [])
    activos_corrientes = sum(c.get('saldo_final', 0) for c in activos_corrientes_lista)
    
    pasivos_corrientes_lista = pasivos.get('corrientes', [])
    pasivos_corrientes = sum(c.get('saldo_final', 0) for c in pasivos_corrientes_lista)
    
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
        
        # Activos corrientes
        for cuenta in activos.get('corrientes', []):
            resumen_data.append({
                'Tipo': 'Activo Corriente',
                'Codigo': cuenta.get('codigo', ''),
                'Cuenta': cuenta.get('nombre', ''),
                'Saldo_Inicial': cuenta.get('saldo_inicial', 0),
                'Debe': cuenta.get('debe', 0),
                'Haber': cuenta.get('haber', 0),
                'Saldo_Final': cuenta.get('saldo_final', 0)
            })
        
        # Activos no corrientes
        for cuenta in activos.get('no_corrientes', []):
            resumen_data.append({
                'Tipo': 'Activo No Corriente',
                'Codigo': cuenta.get('codigo', ''),
                'Cuenta': cuenta.get('nombre', ''),
                'Saldo_Inicial': cuenta.get('saldo_inicial', 0),
                'Debe': cuenta.get('debe', 0),
                'Haber': cuenta.get('haber', 0),
                'Saldo_Final': cuenta.get('saldo_final', 0)
            })
        
        # Agregar pasivos
        pasivos = balance_data.get('pasivos', {})
        
        # Pasivos corrientes
        for cuenta in pasivos.get('corrientes', []):
            resumen_data.append({
                'Tipo': 'Pasivo Corriente',
                'Codigo': cuenta.get('codigo', ''),
                'Cuenta': cuenta.get('nombre', ''),
                'Saldo_Inicial': cuenta.get('saldo_inicial', 0),
                'Debe': cuenta.get('debe', 0),
                'Haber': cuenta.get('haber', 0),
                'Saldo_Final': cuenta.get('saldo_final', 0)
            })
        
        # Pasivos no corrientes
        for cuenta in pasivos.get('no_corrientes', []):
            resumen_data.append({
                'Tipo': 'Pasivo No Corriente',
                'Codigo': cuenta.get('codigo', ''),
                'Cuenta': cuenta.get('nombre', ''),
                'Saldo_Inicial': cuenta.get('saldo_inicial', 0),
                'Debe': cuenta.get('debe', 0),
                'Haber': cuenta.get('haber', 0),
                'Saldo_Final': cuenta.get('saldo_final', 0)
            })
        
        # Agregar patrimonio
        patrimonio = balance_data.get('patrimonio', {})
        
        # Capital
        for cuenta in patrimonio.get('capital', []):
            resumen_data.append({
                'Tipo': 'Capital',
                'Codigo': cuenta.get('codigo', ''),
                'Cuenta': cuenta.get('nombre', ''),
                'Saldo_Inicial': cuenta.get('saldo_inicial', 0),
                'Debe': cuenta.get('debe', 0),
                'Haber': cuenta.get('haber', 0),
                'Saldo_Final': cuenta.get('saldo_final', 0)
            })
        
        # Utilidades
        for cuenta in patrimonio.get('utilidades', []):
            resumen_data.append({
                'Tipo': 'Utilidades',
                'Codigo': cuenta.get('codigo', ''),
                'Cuenta': cuenta.get('nombre', ''),
                'Saldo_Inicial': cuenta.get('saldo_inicial', 0),
                'Debe': cuenta.get('debe', 0),
                'Haber': cuenta.get('haber', 0),
                'Saldo_Final': cuenta.get('saldo_final', 0)
            })
        
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
    
    if st.button("📊 Generar Estado de Resultados", type="primary", use_container_width=True):
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
            "guardar": False  # No guardar automáticamente
        }
        
        with st.spinner("Generando Estado de Resultados..."):
            # Endpoint correcto del backend es estado-pyg
            response = requests.get(f"{backend_url}/api/estados-financieros/estado-pyg/{id_periodo}", params=params)
        
        if response.status_code == 200:
            resultados_data = response.json()
            mostrar_estado_resultados(resultados_data, mostrar_margenes, incluir_cuentas_cero)
        elif response.status_code == 404:
            st.error("❌ Período no encontrado")
        else:
            error_detail = response.json().get('detail', 'Error desconocido') if response.headers.get('content-type') == 'application/json' else str(response.status_code)
            st.error(f"❌ Error al generar estado de resultados: {error_detail}")
            
    except requests.exceptions.ConnectionError:
        st.error("❌ Error de conexión con el servidor. Verifique que el backend esté en ejecución.")
    except Exception as e:
        st.error(f"❌ Error inesperado: {str(e)}")

def mostrar_estado_resultados(resultados_data: Dict[str, Any], mostrar_margenes: bool, incluir_cuentas_cero: bool = False):
    """Mostrar el estado de resultados formateado"""
    
    # Encabezado del reporte
    empresa = resultados_data.get('empresa', {})
    periodo = resultados_data.get('periodo', {})
    resumen = resultados_data.get('resumen', {})
    
    st.markdown("### 📈 ESTADO DE PÉRDIDAS Y GANANCIAS")
    st.markdown(f"**{empresa.get('nombre', 'Empresa')}**")
    if empresa.get('nit'):
        st.caption(f"NIT: {empresa.get('nit')}")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Período", periodo.get('tipo', 'N/A'))
    
    with col2:
        fecha_inicio = periodo.get('fecha_inicio', 'N/A')
        fecha_fin = periodo.get('fecha_fin', 'N/A')
        st.metric("Rango", f"{fecha_inicio} / {fecha_fin}")
    
    with col3:
        fecha_generacion = resultados_data.get('fecha_generacion', datetime.now().strftime('%Y-%m-%d'))
        st.metric("Fecha Generación", fecha_generacion)
    
    # INGRESOS
    st.markdown("#### 💰 INGRESOS")
    ingresos = resultados_data.get('ingresos', {})
    total_ingresos = float(resumen.get('total_ingresos', 0))
    
    if ingresos:
        with st.expander("📈 Ingresos por Categoría", expanded=True):
            data_ingresos = []
            for categoria, monto in ingresos.items():
                monto_float = float(monto)
                if incluir_cuentas_cero or abs(monto_float) >= 0.01:
                    data_ingresos.append({
                        'Categoría': categoria.replace('_', ' ').title(),
                        'Monto': f"${monto_float:,.2f}"
                    })
            
            if data_ingresos:
                df_ingresos = pd.DataFrame(data_ingresos)
                st.dataframe(df_ingresos, use_container_width=True, hide_index=True)
            else:
                st.info("No hay ingresos registrados")
    
    st.markdown(f"### 💵 **TOTAL INGRESOS: ${total_ingresos:,.2f}**")
    
    # EGRESOS (COSTOS Y GASTOS)
    st.markdown("#### 📉 EGRESOS")
    
    egresos = resultados_data.get('egresos', {})
    total_egresos = float(resumen.get('total_egresos', 0))
    
    if egresos:
        with st.expander("🏢 Egresos por Categoría", expanded=True):
            data_egresos = []
            for categoria, monto in egresos.items():
                monto_float = float(monto)
                if incluir_cuentas_cero or abs(monto_float) >= 0.01:
                    data_egresos.append({
                        'Categoría': categoria.replace('_', ' ').title(),
                        'Monto': f"${monto_float:,.2f}"
                    })
            
            if data_egresos:
                df_egresos = pd.DataFrame(data_egresos)
                st.dataframe(df_egresos, use_container_width=True, hide_index=True)
            else:
                st.info("No hay egresos registrados")
    
    st.markdown(f"**Total Egresos: ${total_egresos:,.2f}**")
    
    # Utilidad Bruta
    utilidad_bruta = float(resumen.get('utilidad_bruta', total_ingresos - total_egresos))
    st.markdown(f"### 📊 **UTILIDAD BRUTA: ${utilidad_bruta:,.2f}**")
    
    if mostrar_margenes and total_ingresos > 0:
        margen_bruto = (utilidad_bruta / total_ingresos) * 100
        st.info(f"📊 Margen Bruto: {margen_bruto:.1f}%")
    
    # UTILIDAD NETA
    utilidad_neta = float(resumen.get('utilidad_neta', 0))
    
    st.markdown("---")
    if utilidad_neta >= 0:
        st.success(f"### 🎉 **UTILIDAD NETA: ${utilidad_neta:,.2f}**")
    else:
        st.error(f"### 😞 **PÉRDIDA NETA: ${abs(utilidad_neta):,.2f}**")
    
    # Márgenes de rentabilidad
    if mostrar_margenes and total_ingresos > 0:
        st.markdown("### 📊 Márgenes de Rentabilidad")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            margen_neto = (utilidad_neta / total_ingresos) * 100
            st.metric("Margen Neto", f"{margen_neto:.2f}%")
        
        with col2:
            margen_bruto_pct = (utilidad_bruta / total_ingresos) * 100
            st.metric("Margen Bruto", f"{margen_bruto_pct:.2f}%")
        
        with col3:
            if total_egresos > 0:
                ratio_gastos = (total_egresos / total_ingresos) * 100
                st.metric("% Gastos/Ingresos", f"{ratio_gastos:.2f}%")
    
    # Gráfico de composición
    mostrar_grafico_resultados(total_ingresos, total_egresos, utilidad_neta)
    
    # Descargar reporte
    generar_descarga_resultados(resultados_data)

def mostrar_seccion_resultados(seccion: Dict[str, Any]):
    """Mostrar una sección del estado de resultados (legacy)"""
    
    if 'cuentas' in seccion:
        data = []
        
        for cuenta in seccion['cuentas']:
            data.append({
                'Cuenta': f"{cuenta.get('codigo_cuenta', cuenta.get('codigo', ''))} - {cuenta.get('nombre_cuenta', cuenta.get('nombre', ''))}",
                'Saldo': f"${float(cuenta.get('saldo', cuenta.get('saldo_final', 0))):,.2f}"
            })
        
        if data:
            df = pd.DataFrame(data)
            st.dataframe(df, use_container_width=True, hide_index=True)
    elif isinstance(seccion, dict):
        # Si la sección es un diccionario de categorías con montos
        data = []
        for categoria, monto in seccion.items():
            if categoria not in ['total', 'total_ingresos', 'total_egresos', 'total_gastos']:
                data.append({
                    'Categoría': categoria.replace('_', ' ').title(),
                    'Monto': f"${float(monto):,.2f}"
                })
        
        if data:
            df = pd.DataFrame(data)
            st.dataframe(df, use_container_width=True, hide_index=True)

def mostrar_margenes_rentabilidad(total_ingresos: float, utilidad_neta: float, resultados_data: Dict):
    """Mostrar márgenes de rentabilidad (función legacy - ya no se usa directamente)"""
    
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
        egresos = resultados_data.get('egresos', {})
        total_egresos = sum(egresos.values()) if isinstance(egresos, dict) else 0
        utilidad_bruta = total_ingresos - total_egresos
        
        if total_ingresos > 0:
            margen_bruto = (utilidad_bruta / total_ingresos) * 100
            st.metric("Margen Bruto", f"{margen_bruto:.1f}%")
        else:
            st.metric("Margen Bruto", "N/A")
    
    with col3:
        st.metric("ROA", "Requiere Balance")
    
    with col4:
        st.metric("ROE", "Requiere Balance")

def mostrar_grafico_resultados(total_ingresos: float, total_egresos: float, utilidad_neta: float):
    """Mostrar gráfico de composición de resultados"""
    
    st.markdown("### 📊 Análisis Gráfico")
    
    # Gráfico de barras comparativo
    conceptos = ['Ingresos', 'Egresos', 'Utilidad Neta']
    valores = [total_ingresos, total_egresos, utilidad_neta]
    colores = ['#2ecc71', '#e74c3c', '#3498db' if utilidad_neta >= 0 else '#e74c3c']
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=conceptos,
        y=valores,
        marker_color=colores,
        text=[f'${abs(v):,.0f}' for v in valores],
        textposition='outside',
        textfont=dict(size=14)
    ))
    
    fig.update_layout(
        title="Composición del Estado de Resultados",
        yaxis_title="Valor ($)",
        xaxis_title="Concepto",
        showlegend=False,
        height=400,
        yaxis=dict(tickformat="$,.0f")
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Gráfico de pastel para distribución de egresos si hay datos
    col1, col2 = st.columns(2)
    
    with col1:
        if total_ingresos > 0 and total_egresos > 0:
            fig_composicion = go.Figure(data=[go.Pie(
                labels=['Ingresos', 'Egresos', 'Utilidad Neta'],
                values=[total_ingresos, total_egresos, abs(utilidad_neta)],
                hole=.3
            )])
            fig_composicion.update_layout(title="Composición General", height=300)
            st.plotly_chart(fig_composicion, use_container_width=True)

def generar_descarga_resultados(resultados_data: Dict[str, Any]):
    """Generar archivo para descarga del estado de resultados"""
    
    st.markdown("### 📥 Descargar Reporte")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # CSV simplificado
        resumen_data = []
        
        # Agregar ingresos
        ingresos = resultados_data.get('ingresos', {})
        for categoria, monto in ingresos.items():
            if categoria not in ['total', 'total_ingresos']:
                resumen_data.append({
                    'Tipo': 'Ingreso',
                    'Categoría': categoria.replace('_', ' ').title(),
                    'Monto': monto
                })
        
        # Agregar egresos
        egresos = resultados_data.get('egresos', {})
        for categoria, monto in egresos.items():
            if categoria not in ['total', 'total_egresos', 'total_gastos']:
                resumen_data.append({
                    'Tipo': 'Egreso',
                    'Categoría': categoria.replace('_', ' ').title(),
                    'Monto': monto
                })
        
        # Agregar resumen
        resumen = resultados_data.get('resumen', {})
        resumen_data.extend([
            {
                'Tipo': 'Resumen',
                'Categoría': 'Total Ingresos',
                'Monto': resumen.get('total_ingresos', 0)
            },
            {
                'Tipo': 'Resumen',
                'Categoría': 'Total Egresos',
                'Monto': resumen.get('total_egresos', 0)
            },
            {
                'Tipo': 'Resumen',
                'Categoría': 'Utilidad Bruta',
                'Monto': resumen.get('utilidad_bruta', 0)
            },
            {
                'Tipo': 'Resumen',
                'Categoría': 'Utilidad Neta',
                'Monto': resumen.get('utilidad_neta', 0)
            }
        ])
        
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
            # Obtener datos de ambos períodos
            try:
                response_balance_base = requests.get(f"{backend_url}/api/estados-financieros/balance-general/{periodo_obj_base['id_periodo']}")
                response_balance_comp = requests.get(f"{backend_url}/api/estados-financieros/balance-general/{periodo_obj_comp['id_periodo']}")
                response_pyg_base = requests.get(f"{backend_url}/api/estados-financieros/estado-pyg/{periodo_obj_base['id_periodo']}")
                response_pyg_comp = requests.get(f"{backend_url}/api/estados-financieros/estado-pyg/{periodo_obj_comp['id_periodo']}")
                
                if all(r.status_code == 200 for r in [response_balance_base, response_balance_comp, response_pyg_base, response_pyg_comp]):
                    balance_base = response_balance_base.json()
                    balance_comp = response_balance_comp.json()
                    pyg_base = response_pyg_base.json()
                    pyg_comp = response_pyg_comp.json()
                    
                    st.success("✅ Datos comparativos obtenidos")
                    st.markdown(f"### 📊 Análisis Comparativo: {nombre_base} vs {nombre_comp}")
                    
                    # Extraer valores y convertir a float
                    activos_base = float(balance_base.get('activos', {}).get('total_activos', balance_base.get('activos', {}).get('total', 0)))
                    activos_comp = float(balance_comp.get('activos', {}).get('total_activos', balance_comp.get('activos', {}).get('total', 0)))
                    
                    pasivos_base = float(balance_base.get('pasivos', {}).get('total_pasivos', balance_base.get('pasivos', {}).get('total', 0)))
                    pasivos_comp = float(balance_comp.get('pasivos', {}).get('total_pasivos', balance_comp.get('pasivos', {}).get('total', 0)))
                    
                    patrimonio_base = float(balance_base.get('patrimonio', {}).get('total_patrimonio', balance_base.get('patrimonio', {}).get('total', 0)))
                    patrimonio_comp = float(balance_comp.get('patrimonio', {}).get('total_patrimonio', balance_comp.get('patrimonio', {}).get('total', 0)))
                    
                    ingresos_base = float(pyg_base.get('resumen', {}).get('total_ingresos', 0))
                    ingresos_comp = float(pyg_comp.get('resumen', {}).get('total_ingresos', 0))
                    
                    egresos_base = float(pyg_base.get('resumen', {}).get('total_egresos', 0))
                    egresos_comp = float(pyg_comp.get('resumen', {}).get('total_egresos', 0))
                    
                    utilidad_base = float(pyg_base.get('resumen', {}).get('utilidad_neta', 0))
                    utilidad_comp = float(pyg_comp.get('resumen', {}).get('utilidad_neta', 0))
                    
                    if tipo_analisis in ["Balance General", "Análisis Integral"]:
                        st.markdown("#### 💰 Comparativo Balance General")
                        
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            variacion_activos = activos_comp - activos_base
                            pct_activos = (variacion_activos / activos_base * 100) if activos_base != 0 else 0
                            st.metric(
                                "Activos",
                                f"${activos_comp:,.2f}",
                                delta=f"{pct_activos:+.2f}% (${variacion_activos:,.2f})"
                            )
                        
                        with col2:
                            variacion_pasivos = pasivos_comp - pasivos_base
                            pct_pasivos = (variacion_pasivos / pasivos_base * 100) if pasivos_base != 0 else 0
                            st.metric(
                                "Pasivos",
                                f"${pasivos_comp:,.2f}",
                                delta=f"{pct_pasivos:+.2f}% (${variacion_pasivos:,.2f})"
                            )
                        
                        with col3:
                            variacion_patrimonio = patrimonio_comp - patrimonio_base
                            pct_patrimonio = (variacion_patrimonio / patrimonio_base * 100) if patrimonio_base != 0 else 0
                            st.metric(
                                "Patrimonio",
                                f"${patrimonio_comp:,.2f}",
                                delta=f"{pct_patrimonio:+.2f}% (${variacion_patrimonio:,.2f})"
                            )
                        
                        # Gráfico comparativo de balance
                        df_balance = pd.DataFrame({
                            'Concepto': ['Activos', 'Pasivos', 'Patrimonio'],
                            nombre_base: [activos_base, pasivos_base, patrimonio_base],
                            nombre_comp: [activos_comp, pasivos_comp, patrimonio_comp]
                        })
                        
                        fig_balance = px.bar(
                            df_balance,
                            x='Concepto',
                            y=[nombre_base, nombre_comp],
                            barmode='group',
                            title='Comparación de Balance General',
                            labels={'value': 'Monto ($)', 'variable': 'Período'}
                        )
                        st.plotly_chart(fig_balance, use_container_width=True, config={'displayModeBar': False})
                    
                    if tipo_analisis in ["Estado de Resultados", "Análisis Integral"]:
                        st.markdown("#### 📈 Comparativo Estado de Resultados")
                        
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            variacion_ingresos = ingresos_comp - ingresos_base
                            pct_ingresos = (variacion_ingresos / ingresos_base * 100) if ingresos_base != 0 else 0
                            st.metric(
                                "Ingresos",
                                f"${ingresos_comp:,.2f}",
                                delta=f"{pct_ingresos:+.2f}% (${variacion_ingresos:,.2f})"
                            )
                        
                        with col2:
                            variacion_egresos = egresos_comp - egresos_base
                            pct_egresos = (variacion_egresos / egresos_base * 100) if egresos_base != 0 else 0
                            st.metric(
                                "Egresos",
                                f"${egresos_comp:,.2f}",
                                delta=f"{pct_egresos:+.2f}% (${variacion_egresos:,.2f})",
                                delta_color="inverse"
                            )
                        
                        with col3:
                            variacion_utilidad = utilidad_comp - utilidad_base
                            pct_utilidad = (variacion_utilidad / utilidad_base * 100) if utilidad_base != 0 else 0
                            st.metric(
                                "Utilidad Neta",
                                f"${utilidad_comp:,.2f}",
                                delta=f"{pct_utilidad:+.2f}% (${variacion_utilidad:,.2f})"
                            )
                        
                        # Gráfico comparativo de resultados
                        df_resultados = pd.DataFrame({
                            'Concepto': ['Ingresos', 'Egresos', 'Utilidad Neta'],
                            nombre_base: [ingresos_base, egresos_base, utilidad_base],
                            nombre_comp: [ingresos_comp, egresos_comp, utilidad_comp]
                        })
                        
                        fig_resultados = px.bar(
                            df_resultados,
                            x='Concepto',
                            y=[nombre_base, nombre_comp],
                            barmode='group',
                            title='Comparación de Resultados',
                            labels={'value': 'Monto ($)', 'variable': 'Período'}
                        )
                        st.plotly_chart(fig_resultados, use_container_width=True, config={'displayModeBar': False})
                    
                    if tipo_analisis == "Análisis Integral":
                        st.divider()
                        st.markdown("#### 📊 Indicadores Financieros Comparativos")
                        
                        col1, col2, col3, col4 = st.columns(4)
                        
                        # Calcular activos y pasivos corrientes
                        activos_corrientes_base = float(sum(float(c.get('saldo_final', 0)) for c in balance_base.get('activos', {}).get('corrientes', [])))
                        pasivos_corrientes_base = float(sum(float(c.get('saldo_final', 0)) for c in balance_base.get('pasivos', {}).get('corrientes', [])))
                        
                        activos_corrientes_comp = float(sum(float(c.get('saldo_final', 0)) for c in balance_comp.get('activos', {}).get('corrientes', [])))
                        pasivos_corrientes_comp = float(sum(float(c.get('saldo_final', 0)) for c in balance_comp.get('pasivos', {}).get('corrientes', [])))
                        
                        with col1:
                            roa_base = (utilidad_base / activos_base * 100) if activos_base != 0 else 0
                            roa_comp = (utilidad_comp / activos_comp * 100) if activos_comp != 0 else 0
                            st.metric("ROA", f"{roa_comp:.2f}%", delta=f"{roa_comp - roa_base:+.2f}%")
                        
                        with col2:
                            roe_base = (utilidad_base / patrimonio_base * 100) if patrimonio_base != 0 else 0
                            roe_comp = (utilidad_comp / patrimonio_comp * 100) if patrimonio_comp != 0 else 0
                            st.metric("ROE", f"{roe_comp:.2f}%", delta=f"{roe_comp - roe_base:+.2f}%")
                        
                        with col3:
                            liquidez_base = (activos_corrientes_base / pasivos_corrientes_base) if pasivos_corrientes_base != 0 else 0
                            liquidez_comp = (activos_corrientes_comp / pasivos_corrientes_comp) if pasivos_corrientes_comp != 0 else 0
                            st.metric("Liquidez", f"{liquidez_comp:.2f}", delta=f"{liquidez_comp - liquidez_base:+.2f}")
                        
                        with col4:
                            endeud_base = (pasivos_base / activos_base * 100) if activos_base != 0 else 0
                            endeud_comp = (pasivos_comp / activos_comp * 100) if activos_comp != 0 else 0
                            st.metric("Endeudamiento", f"{endeud_comp:.2f}%", delta=f"{endeud_comp - endeud_base:+.2f}%", delta_color="inverse")
                else:
                    st.error("No se pudo obtener la información financiera de ambos períodos")
                    
            except Exception as e:
                st.error(f"Error al obtener datos comparativos: {e}")
            
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
    
    # Selección de período
    try:
        response_periodos = requests.get(f"{backend_url}/api/periodos")
        periodos = response_periodos.json() if response_periodos.status_code == 200 else []
        
        if not periodos:
            st.warning("No hay períodos configurados")
            return
            
        opciones_periodos = [
            f"{p['descripcion']} ({p['fecha_inicio']} - {p['fecha_fin']})"
            for p in periodos
        ]
        periodo_seleccionado = st.selectbox("Seleccione período:", opciones_periodos, key="flujo_periodo")
        
        if st.button("💧 Generar Flujo de Efectivo", type="primary"):
            nombre_periodo = periodo_seleccionado.split(" (")[0]
            periodo_obj = next((p for p in periodos if p['descripcion'] == nombre_periodo), None)
            
            if periodo_obj:
                with st.spinner("Calculando flujo de efectivo..."):
                    # Obtener balance y estado de resultados
                    try:
                        response_balance = requests.get(f"{backend_url}/api/estados-financieros/balance-general/{periodo_obj['id_periodo']}")
                        response_pyg = requests.get(f"{backend_url}/api/estados-financieros/estado-pyg/{periodo_obj['id_periodo']}")
                        
                        if response_balance.status_code == 200 and response_pyg.status_code == 200:
                            balance_data = response_balance.json()
                            pyg_data = response_pyg.json()
                            
                            st.success("✅ Flujo de efectivo generado")
                            
                            # Header
                            st.markdown("### 💧 ESTADO DE FLUJO DE EFECTIVO")
                            st.markdown(f"**Período:** {periodo_obj['descripcion']}")
                            
                            # Obtener utilidad neta y convertir a float
                            utilidad_neta = float(pyg_data.get('resumen', {}).get('utilidad_neta', 0))
                            
                            # Actividades de Operación
                            st.markdown("#### 🔄 Flujos de Efectivo de Actividades de Operación")
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                st.metric("Utilidad Neta", f"${utilidad_neta:,.2f}")
                            
                            with col2:
                                # Depreciación estimada (si existe en cuentas)
                                depreciacion = 0.0  # Calcular desde cuentas de gasto
                                st.metric("Ajustes no efectivo", f"${depreciacion:,.2f}")
                            
                            flujo_operacion = utilidad_neta + depreciacion
                            st.markdown(f"**💰 Flujo Neto de Actividades de Operación: ${flujo_operacion:,.2f}**")
                            
                            st.divider()
                            
                            # Actividades de Inversión
                            st.markdown("#### 🏢 Flujos de Efectivo de Actividades de Inversión")
                            st.info("📊 Compra/Venta de activos fijos (requiere datos adicionales)")
                            flujo_inversion = 0.0
                            st.markdown(f"**💰 Flujo Neto de Actividades de Inversión: ${flujo_inversion:,.2f}**")
                            
                            st.divider()
                            
                            # Actividades de Financiación
                            st.markdown("#### 💳 Flujos de Efectivo de Actividades de Financiación")
                            st.info("📊 Préstamos, aportes de capital (requiere datos adicionales)")
                            flujo_financiacion = 0.0
                            st.markdown(f"**💰 Flujo Neto de Actividades de Financiación: ${flujo_financiacion:,.2f}**")
                            
                            st.divider()
                            
                            # Resumen
                            aumento_efectivo = flujo_operacion + flujo_inversion + flujo_financiacion
                            
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("💵 Aumento Neto en Efectivo", f"${aumento_efectivo:,.2f}")
                            with col2:
                                efectivo_inicial = 0.0  # Obtener del balance inicial
                                st.metric("💰 Efectivo Inicial", f"${efectivo_inicial:,.2f}")
                            with col3:
                                efectivo_final = efectivo_inicial + aumento_efectivo
                                st.metric("💰 Efectivo Final", f"${efectivo_final:,.2f}")
                            
                        else:
                            st.error("No se pudo obtener la información financiera")
                            
                    except Exception as e:
                        st.error(f"Error al generar flujo: {e}")
                        
    except Exception as e:
        st.error(f"Error al cargar períodos: {e}")

def generar_estado_cambios_patrimonio(backend_url: str):
    """Generar estado de cambios en el patrimonio"""
    
    st.markdown("#### 🏦 Estado de Cambios en el Patrimonio")
    
    # Selección de período
    try:
        response_periodos = requests.get(f"{backend_url}/api/periodos")
        periodos = response_periodos.json() if response_periodos.status_code == 200 else []
        
        if not periodos:
            st.warning("No hay períodos configurados")
            return
            
        opciones_periodos = [
            f"{p['descripcion']} ({p['fecha_inicio']} - {p['fecha_fin']})"
            for p in periodos
        ]
        periodo_seleccionado = st.selectbox("Seleccione período:", opciones_periodos, key="patrimonio_periodo")
        
        if st.button("🏦 Generar Estado de Cambios", type="primary"):
            nombre_periodo = periodo_seleccionado.split(" (")[0]
            periodo_obj = next((p for p in periodos if p['descripcion'] == nombre_periodo), None)
            
            if periodo_obj:
                with st.spinner("Generando estado de cambios en el patrimonio..."):
                    try:
                        response_balance = requests.get(f"{backend_url}/api/estados-financieros/balance-general/{periodo_obj['id_periodo']}")
                        response_pyg = requests.get(f"{backend_url}/api/estados-financieros/estado-pyg/{periodo_obj['id_periodo']}")
                        
                        if response_balance.status_code == 200 and response_pyg.status_code == 200:
                            balance_data = response_balance.json()
                            pyg_data = response_pyg.json()
                            
                            st.markdown("### 🏦 ESTADO DE CAMBIOS EN EL PATRIMONIO")
                            st.markdown(f"**Período:** {periodo_obj['descripcion']}")
                            
                            patrimonio = balance_data.get('patrimonio', {})
                            utilidad_neta = float(pyg_data.get('resumen', {}).get('utilidad_neta', 0))
                            
                            # Extraer componentes del patrimonio
                            cuentas_capital = patrimonio.get('capital', [])
                            cuentas_utilidades = patrimonio.get('utilidades', [])
                            
                            total_capital = float(sum(float(c.get('saldo_final', 0)) for c in cuentas_capital))
                            total_utilidades = float(sum(float(c.get('saldo_final', 0)) for c in cuentas_utilidades))
                            total_patrimonio = float(patrimonio.get('total_patrimonio', patrimonio.get('total', 0)))
                            
                            # Estructura del estado de cambios
                            st.markdown("#### 📊 Composición del Patrimonio")
                            
                            col1, col2, col3 = st.columns(3)
                            
                            with col1:
                                st.metric("💰 Capital Social", f"${total_capital:,.2f}")
                            
                            with col2:
                                st.metric("📈 Utilidades Acumuladas", f"${total_utilidades:,.2f}")
                            
                            with col3:
                                st.metric("🏦 Total Patrimonio", f"${total_patrimonio:,.2f}")
                            
                            st.divider()
                            
                            # Movimientos del período
                            st.markdown("#### 🔄 Movimientos del Período")
                            
                            # Crear tabla de movimientos
                            movimientos_data = []
                            
                            # Capital
                            for cuenta in cuentas_capital:
                                movimientos_data.append({
                                    'Concepto': cuenta.get('nombre', 'N/A'),
                                    'Saldo Inicial': float(cuenta.get('saldo_inicial', 0)),
                                    'Aumentos': float(cuenta.get('debe', 0)),
                                    'Disminuciones': float(cuenta.get('haber', 0)),
                                    'Saldo Final': float(cuenta.get('saldo_final', 0))
                                })
                            
                            # Utilidades
                            for cuenta in cuentas_utilidades:
                                movimientos_data.append({
                                    'Concepto': cuenta.get('nombre', 'N/A'),
                                    'Saldo Inicial': float(cuenta.get('saldo_inicial', 0)),
                                    'Aumentos': float(cuenta.get('haber', 0)),
                                    'Disminuciones': float(cuenta.get('debe', 0)),
                                    'Saldo Final': float(cuenta.get('saldo_final', 0))
                                })
                            
                            # Agregar utilidad del período
                            movimientos_data.append({
                                'Concepto': 'Utilidad del Período',
                                'Saldo Inicial': 0.0,
                                'Aumentos': float(utilidad_neta) if utilidad_neta > 0 else 0.0,
                                'Disminuciones': abs(float(utilidad_neta)) if utilidad_neta < 0 else 0.0,
                                'Saldo Final': float(utilidad_neta)
                            })
                            
                            if movimientos_data:
                                df_movimientos = pd.DataFrame(movimientos_data)
                                df_movimientos['Saldo Inicial'] = df_movimientos['Saldo Inicial'].apply(lambda x: f"${x:,.2f}")
                                df_movimientos['Aumentos'] = df_movimientos['Aumentos'].apply(lambda x: f"${x:,.2f}")
                                df_movimientos['Disminuciones'] = df_movimientos['Disminuciones'].apply(lambda x: f"${x:,.2f}")
                                df_movimientos['Saldo Final'] = df_movimientos['Saldo Final'].apply(lambda x: f"${x:,.2f}")
                                
                                st.dataframe(df_movimientos, width="stretch", hide_index=True)
                            
                            st.divider()
                            
                            # Gráfico de composición
                            st.markdown("#### 📊 Composición del Patrimonio")
                            
                            if total_capital > 0 or total_utilidades > 0 or utilidad_neta != 0:
                                labels = []
                                values = []
                                
                                if total_capital > 0:
                                    labels.append('Capital Social')
                                    values.append(total_capital)
                                
                                if total_utilidades > 0:
                                    labels.append('Utilidades Acumuladas')
                                    values.append(total_utilidades)
                                
                                if utilidad_neta != 0:
                                    labels.append('Utilidad del Período')
                                    values.append(abs(utilidad_neta))
                                
                                if labels and values:
                                    fig = px.pie(
                                        names=labels,
                                        values=values,
                                        title='Distribución del Patrimonio',
                                        hole=0.4
                                    )
                                    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
                            
                        else:
                            st.error("No se pudo obtener la información financiera")
                            
                    except Exception as e:
                        st.error(f"Error al generar estado: {e}")
                        
    except Exception as e:
        st.error(f"Error al cargar períodos: {e}")

def generar_analisis_tendencias(backend_url: str):
    """Generar análisis de tendencias"""
    
    st.markdown("#### 📈 Análisis de Tendencias")
    
    # Selección de períodos
    try:
        response_periodos = requests.get(f"{backend_url}/api/periodos")
        periodos = response_periodos.json() if response_periodos.status_code == 200 else []
        
        if not periodos:
            st.warning("No hay períodos configurados")
            return
        
        # Filtrar solo períodos del mismo tipo para comparación
        tipo_periodo = st.selectbox(
            "Tipo de período:",
            ["MENSUAL", "TRIMESTRAL", "SEMESTRAL", "ANUAL"],
            key="tendencias_tipo"
        )
        
        periodos_filtrados = [p for p in periodos if p['tipo_periodo'] == tipo_periodo]
        
        if not periodos_filtrados:
            st.warning(f"No hay períodos de tipo {tipo_periodo}")
            return
        
        num_periodos = st.slider(
            "Número de períodos a analizar:",
            min_value=2,
            max_value=min(12, len(periodos_filtrados)),
            value=min(6, len(periodos_filtrados)),
            key="tendencias_num"
        )
        
        if st.button("📈 Generar Análisis de Tendencias", type="primary"):
            with st.spinner("Analizando tendencias..."):
                try:
                    # Tomar los últimos N períodos
                    periodos_analizar = periodos_filtrados[:num_periodos]
                    
                    # Recopilar datos de cada período
                    datos_tendencias = []
                    
                    for periodo in periodos_analizar:
                        try:
                            response_balance = requests.get(f"{backend_url}/api/estados-financieros/balance-general/{periodo['id_periodo']}")
                            response_pyg = requests.get(f"{backend_url}/api/estados-financieros/estado-pyg/{periodo['id_periodo']}")
                            
                            if response_balance.status_code == 200 and response_pyg.status_code == 200:
                                balance_data = response_balance.json()
                                pyg_data = response_pyg.json()
                                
                                activos = balance_data.get('activos', {})
                                pasivos = balance_data.get('pasivos', {})
                                patrimonio = balance_data.get('patrimonio', {})
                                resumen = pyg_data.get('resumen', {})
                                
                                datos_tendencias.append({
                                    'Período': periodo['descripcion'],
                                    'Fecha': periodo['fecha_fin'],
                                    'Activos': activos.get('total_activos', activos.get('total', 0)),
                                    'Pasivos': pasivos.get('total_pasivos', pasivos.get('total', 0)),
                                    'Patrimonio': patrimonio.get('total_patrimonio', patrimonio.get('total', 0)),
                                    'Ingresos': resumen.get('total_ingresos', 0),
                                    'Egresos': resumen.get('total_egresos', 0),
                                    'Utilidad': resumen.get('utilidad_neta', 0)
                                })
                        except:
                            continue
                    
                    if datos_tendencias:
                        df_tendencias = pd.DataFrame(datos_tendencias)
                        df_tendencias = df_tendencias.sort_values('Fecha')
                        
                        st.success(f"✅ Análisis de tendencias generado para {len(datos_tendencias)} períodos")
                        
                        st.markdown("### 📈 ANÁLISIS DE TENDENCIAS")
                        st.markdown(f"**Tipo de período:** {tipo_periodo}")
                        st.markdown(f"**Períodos analizados:** {len(datos_tendencias)}")
                        
                        # Gráfico de Balance General
                        st.markdown("#### 💰 Evolución del Balance General")
                        
                        fig_balance = go.Figure()
                        
                        fig_balance.add_trace(go.Scatter(
                            x=df_tendencias['Período'],
                            y=df_tendencias['Activos'],
                            mode='lines+markers',
                            name='Activos',
                            line=dict(color='#2ecc71', width=3),
                            marker=dict(size=8)
                        ))
                        
                        fig_balance.add_trace(go.Scatter(
                            x=df_tendencias['Período'],
                            y=df_tendencias['Pasivos'],
                            mode='lines+markers',
                            name='Pasivos',
                            line=dict(color='#e74c3c', width=3),
                            marker=dict(size=8)
                        ))
                        
                        fig_balance.add_trace(go.Scatter(
                            x=df_tendencias['Período'],
                            y=df_tendencias['Patrimonio'],
                            mode='lines+markers',
                            name='Patrimonio',
                            line=dict(color='#3498db', width=3),
                            marker=dict(size=8)
                        ))
                        
                        fig_balance.update_layout(
                            title='Tendencia de Componentes del Balance',
                            xaxis_title='Período',
                            yaxis_title='Monto ($)',
                            hovermode='x unified',
                            height=400
                        )
                        
                        st.plotly_chart(fig_balance, use_container_width=True, config={'displayModeBar': False})
                        
                        st.divider()
                        
                        # Gráfico de Resultados
                        st.markdown("#### 📊 Evolución de Resultados")
                        
                        fig_resultados = go.Figure()
                        
                        fig_resultados.add_trace(go.Bar(
                            x=df_tendencias['Período'],
                            y=df_tendencias['Ingresos'],
                            name='Ingresos',
                            marker_color='#2ecc71'
                        ))
                        
                        fig_resultados.add_trace(go.Bar(
                            x=df_tendencias['Período'],
                            y=df_tendencias['Egresos'],
                            name='Egresos',
                            marker_color='#e74c3c'
                        ))
                        
                        fig_resultados.add_trace(go.Scatter(
                            x=df_tendencias['Período'],
                            y=df_tendencias['Utilidad'],
                            mode='lines+markers',
                            name='Utilidad Neta',
                            line=dict(color='#3498db', width=3),
                            marker=dict(size=10),
                            yaxis='y2'
                        ))
                        
                        fig_resultados.update_layout(
                            title='Tendencia de Ingresos, Egresos y Utilidad',
                            xaxis_title='Período',
                            yaxis_title='Ingresos/Egresos ($)',
                            yaxis2=dict(
                                title='Utilidad ($)',
                                overlaying='y',
                                side='right'
                            ),
                            barmode='group',
                            hovermode='x unified',
                            height=400
                        )
                        
                        st.plotly_chart(fig_resultados, use_container_width=True, config={'displayModeBar': False})
                        
                        st.divider()
                        
                        # Tabla de datos
                        st.markdown("#### 📋 Datos Detallados")
                        
                        df_display = df_tendencias.copy()
                        df_display['Activos'] = df_display['Activos'].apply(lambda x: f"${float(x):,.2f}")
                        df_display['Pasivos'] = df_display['Pasivos'].apply(lambda x: f"${float(x):,.2f}")
                        df_display['Patrimonio'] = df_display['Patrimonio'].apply(lambda x: f"${float(x):,.2f}")
                        df_display['Ingresos'] = df_display['Ingresos'].apply(lambda x: f"${float(x):,.2f}")
                        df_display['Egresos'] = df_display['Egresos'].apply(lambda x: f"${float(x):,.2f}")
                        df_display['Utilidad'] = df_display['Utilidad'].apply(lambda x: f"${float(x):,.2f}")
                        
                        st.dataframe(df_display[['Período', 'Activos', 'Pasivos', 'Patrimonio', 'Ingresos', 'Egresos', 'Utilidad']], 
                                   width="stretch", hide_index=True)
                        
                        # Análisis de crecimiento
                        st.divider()
                        st.markdown("#### 📊 Análisis de Crecimiento")
                        
                        if len(df_tendencias) >= 2:
                            # Comparar primer y último período
                            periodo_inicial = df_tendencias.iloc[0]
                            periodo_final = df_tendencias.iloc[-1]
                            
                            col1, col2, col3, col4 = st.columns(4)
                            
                            with col1:
                                activos_ini = float(periodo_inicial['Activos'])
                                activos_fin = float(periodo_final['Activos'])
                                crecimiento_activos = ((activos_fin - activos_ini) / activos_ini * 100) if activos_ini != 0 else 0
                                st.metric("Crecimiento Activos", f"{crecimiento_activos:.2f}%",
                                        delta=f"${activos_fin - activos_ini:,.2f}")
                            
                            with col2:
                                patrimonio_ini = float(periodo_inicial['Patrimonio'])
                                patrimonio_fin = float(periodo_final['Patrimonio'])
                                crecimiento_patrimonio = ((patrimonio_fin - patrimonio_ini) / patrimonio_ini * 100) if patrimonio_ini != 0 else 0
                                st.metric("Crecimiento Patrimonio", f"{crecimiento_patrimonio:.2f}%",
                                        delta=f"${patrimonio_fin - patrimonio_ini:,.2f}")
                            
                            with col3:
                                ingresos_ini = float(periodo_inicial['Ingresos'])
                                ingresos_fin = float(periodo_final['Ingresos'])
                                crecimiento_ingresos = ((ingresos_fin - ingresos_ini) / ingresos_ini * 100) if ingresos_ini != 0 else 0
                                st.metric("Crecimiento Ingresos", f"{crecimiento_ingresos:.2f}%",
                                        delta=f"${ingresos_fin - ingresos_ini:,.2f}")
                            
                            with col4:
                                utilidad_fin = float(periodo_final['Utilidad'])
                                utilidad_ini = float(periodo_inicial['Utilidad'])
                                mejora_utilidad = utilidad_fin - utilidad_ini
                                st.metric("Mejora Utilidad", f"${mejora_utilidad:,.2f}",
                                        delta="Positiva" if mejora_utilidad > 0 else "Negativa")
                    
                    else:
                        st.warning("No se pudo recopilar suficiente información para el análisis")
                        
                except Exception as e:
                    st.error(f"Error al generar análisis: {e}")
                    
    except Exception as e:
        st.error(f"Error al cargar períodos: {e}")

def generar_ratios_detallados(backend_url: str):
    """Generar análisis detallado de ratios"""
    
    st.markdown("#### 📊 Ratios Financieros Detallados")
    
    # Selección de período
    try:
        response_periodos = requests.get(f"{backend_url}/api/periodos")
        periodos = response_periodos.json() if response_periodos.status_code == 200 else []
        
        if not periodos:
            st.warning("No hay períodos configurados")
            return
            
        opciones_periodos = [
            f"{p['descripcion']} ({p['fecha_inicio']} - {p['fecha_fin']})"
            for p in periodos
        ]
        periodo_seleccionado = st.selectbox("Seleccione período:", opciones_periodos, key="ratios_periodo")
        
        if st.button("📊 Calcular Ratios", type="primary"):
            nombre_periodo = periodo_seleccionado.split(" (")[0]
            periodo_obj = next((p for p in periodos if p['descripcion'] == nombre_periodo), None)
            
            if periodo_obj:
                with st.spinner("Calculando ratios financieros..."):
                    try:
                        response_balance = requests.get(f"{backend_url}/api/estados-financieros/balance-general/{periodo_obj['id_periodo']}")
                        response_pyg = requests.get(f"{backend_url}/api/estados-financieros/estado-pyg/{periodo_obj['id_periodo']}")
                        
                        if response_balance.status_code == 200 and response_pyg.status_code == 200:
                            balance_data = response_balance.json()
                            pyg_data = response_pyg.json()
                            
                            st.success("✅ Ratios calculados exitosamente")
                            
                            # Obtener valores
                            activos = balance_data.get('activos', {})
                            pasivos = balance_data.get('pasivos', {})
                            patrimonio = balance_data.get('patrimonio', {})
                            resumen = pyg_data.get('resumen', {})
                            
                            total_activos = float(activos.get('total_activos', activos.get('total', 0)))
                            total_pasivos = float(pasivos.get('total_pasivos', pasivos.get('total', 0)))
                            total_patrimonio = float(patrimonio.get('total_patrimonio', patrimonio.get('total', 0)))
                            
                            # Calcular activos y pasivos corrientes
                            activos_corrientes = float(sum(float(c.get('saldo_final', 0)) for c in activos.get('corrientes', [])))
                            pasivos_corrientes = float(sum(float(c.get('saldo_final', 0)) for c in pasivos.get('corrientes', [])))
                            
                            utilidad_neta = float(resumen.get('utilidad_neta', 0))
                            total_ingresos = float(resumen.get('total_ingresos', 0))
                            
                            st.markdown("### 📊 ANÁLISIS DE RATIOS FINANCIEROS")
                            st.markdown(f"**Período:** {periodo_obj['descripcion']}")
                            
                            # RATIOS DE LIQUIDEZ
                            st.markdown("#### 💧 Ratios de Liquidez")
                            
                            col1, col2, col3 = st.columns(3)
                            
                            with col1:
                                if pasivos_corrientes > 0:
                                    razon_corriente = activos_corrientes / pasivos_corrientes
                                    st.metric("Razón Corriente", f"{razon_corriente:.2f}")
                                    if razon_corriente >= 2:
                                        st.success("✅ Excelente liquidez")
                                    elif razon_corriente >= 1:
                                        st.info("⚠️ Liquidez aceptable")
                                    else:
                                        st.warning("⚠️ Liquidez baja")
                                else:
                                    st.metric("Razón Corriente", "N/A")
                            
                            with col2:
                                if pasivos_corrientes > 0:
                                    capital_trabajo = activos_corrientes - pasivos_corrientes
                                    st.metric("Capital de Trabajo", f"${capital_trabajo:,.2f}")
                            
                            with col3:
                                if activos_corrientes > 0:
                                    prueba_acida = (activos_corrientes - 0) / pasivos_corrientes if pasivos_corrientes > 0 else 0
                                    st.metric("Prueba Ácida", f"{prueba_acida:.2f}")
                                else:
                                    st.metric("Prueba Ácida", "N/A")
                            
                            st.divider()
                            
                            # RATIOS DE ENDEUDAMIENTO
                            st.markdown("#### 💳 Ratios de Endeudamiento")
                            
                            col1, col2, col3 = st.columns(3)
                            
                            with col1:
                                if total_activos > 0:
                                    nivel_endeudamiento = (total_pasivos / total_activos) * 100
                                    st.metric("Nivel de Endeudamiento", f"{nivel_endeudamiento:.2f}%")
                                    if nivel_endeudamiento < 50:
                                        st.success("✅ Endeudamiento saludable")
                                    elif nivel_endeudamiento < 70:
                                        st.warning("⚠️ Endeudamiento moderado")
                                    else:
                                        st.error("❌ Endeudamiento alto")
                                else:
                                    st.metric("Nivel de Endeudamiento", "N/A")
                            
                            with col2:
                                if total_patrimonio > 0:
                                    apalancamiento = total_pasivos / total_patrimonio
                                    st.metric("Apalancamiento", f"{apalancamiento:.2f}")
                                else:
                                    st.metric("Apalancamiento", "N/A")
                            
                            with col3:
                                if total_activos > 0:
                                    autonomia = (total_patrimonio / total_activos) * 100
                                    st.metric("Autonomía", f"{autonomia:.2f}%")
                                else:
                                    st.metric("Autonomía", "N/A")
                            
                            st.divider()
                            
                            # RATIOS DE RENTABILIDAD
                            st.markdown("#### 📈 Ratios de Rentabilidad")
                            
                            col1, col2, col3 = st.columns(3)
                            
                            with col1:
                                if total_activos > 0:
                                    roa = (utilidad_neta / total_activos) * 100
                                    st.metric("ROA (Return on Assets)", f"{roa:.2f}%")
                                    if roa > 10:
                                        st.success("✅ Excelente rentabilidad")
                                    elif roa > 5:
                                        st.info("⚠️ Rentabilidad moderada")
                                    else:
                                        st.warning("⚠️ Rentabilidad baja")
                                else:
                                    st.metric("ROA", "N/A")
                            
                            with col2:
                                if total_patrimonio > 0:
                                    roe = (utilidad_neta / total_patrimonio) * 100
                                    st.metric("ROE (Return on Equity)", f"{roe:.2f}%")
                                    if roe > 15:
                                        st.success("✅ Excelente retorno")
                                    elif roe > 8:
                                        st.info("⚠️ Retorno moderado")
                                    else:
                                        st.warning("⚠️ Retorno bajo")
                                else:
                                    st.metric("ROE", "N/A")
                            
                            with col3:
                                if total_ingresos > 0:
                                    margen_neto = (utilidad_neta / total_ingresos) * 100
                                    st.metric("Margen Neto", f"{margen_neto:.2f}%")
                                else:
                                    st.metric("Margen Neto", "N/A")
                            
                            # Gráfico de ratios
                            st.divider()
                            st.markdown("#### 📊 Visualización de Ratios")
                            
                            if total_activos > 0 and total_patrimonio > 0:
                                ratios_df = pd.DataFrame({
                                    'Ratio': ['ROA', 'ROE', 'Razón Corriente', 'Endeudamiento'],
                                    'Valor': [
                                        roa if total_activos > 0 else 0,
                                        roe if total_patrimonio > 0 else 0,
                                        razon_corriente * 10 if pasivos_corrientes > 0 else 0,  # Escalar para visualización
                                        nivel_endeudamiento if total_activos > 0 else 0
                                    ]
                                })
                                
                                fig = px.bar(ratios_df, x='Ratio', y='Valor', 
                                           title='Principales Ratios Financieros',
                                           color='Ratio',
                                           labels={'Valor': 'Valor (%)'})
                                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
                            
                        else:
                            st.error("No se pudo obtener la información financiera")
                            
                    except Exception as e:
                        st.error(f"Error al calcular ratios: {e}")
                        
    except Exception as e:
        st.error(f"Error al cargar períodos: {e}")

def generar_reporte_ejecutivo(backend_url: str):
    """Generar reporte ejecutivo"""
    
    st.markdown("#### 📋 Reporte Ejecutivo")
    
    # Selección de período
    try:
        response_periodos = requests.get(f"{backend_url}/api/periodos")
        periodos = response_periodos.json() if response_periodos.status_code == 200 else []
        
        if not periodos:
            st.warning("No hay períodos configurados")
            return
            
        opciones_periodos = [
            f"{p['descripcion']} ({p['fecha_inicio']} - {p['fecha_fin']})"
            for p in periodos
        ]
        periodo_seleccionado = st.selectbox("Seleccione período:", opciones_periodos, key="ejecutivo_periodo")
        
        if st.button("📋 Generar Reporte Ejecutivo", type="primary"):
            nombre_periodo = periodo_seleccionado.split(" (")[0]
            periodo_obj = next((p for p in periodos if p['descripcion'] == nombre_periodo), None)
            
            if periodo_obj:
                with st.spinner("Generando reporte ejecutivo..."):
                    try:
                        response_balance = requests.get(f"{backend_url}/api/estados-financieros/balance-general/{periodo_obj['id_periodo']}")
                        response_pyg = requests.get(f"{backend_url}/api/estados-financieros/estado-pyg/{periodo_obj['id_periodo']}")
                        
                        if response_balance.status_code == 200 and response_pyg.status_code == 200:
                            balance_data = response_balance.json()
                            pyg_data = response_pyg.json()
                            
                            st.markdown("### 📋 REPORTE EJECUTIVO")
                            st.markdown(f"**Período:** {periodo_obj['descripcion']}")
                            st.markdown(f"**Fecha de generación:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
                            
                            # Resumen Ejecutivo
                            st.markdown("#### 📌 Resumen Ejecutivo")
                            
                            activos = balance_data.get('activos', {})
                            pasivos = balance_data.get('pasivos', {})
                            patrimonio = balance_data.get('patrimonio', {})
                            resumen = pyg_data.get('resumen', {})
                            
                            total_activos = float(activos.get('total_activos', activos.get('total', 0)))
                            total_pasivos = float(pasivos.get('total_pasivos', pasivos.get('total', 0)))
                            total_patrimonio = float(patrimonio.get('total_patrimonio', patrimonio.get('total', 0)))
                            utilidad_neta = float(resumen.get('utilidad_neta', 0))
                            total_ingresos = float(resumen.get('total_ingresos', 0))
                            total_egresos = float(resumen.get('total_egresos', 0))
                            
                            # Métricas Principales
                            col1, col2, col3, col4 = st.columns(4)
                            
                            with col1:
                                st.metric("💰 Total Activos", f"${total_activos:,.2f}")
                            
                            with col2:
                                st.metric("💳 Total Pasivos", f"${total_pasivos:,.2f}")
                            
                            with col3:
                                st.metric("🏦 Patrimonio", f"${total_patrimonio:,.2f}")
                            
                            with col4:
                                color = "normal" if utilidad_neta >= 0 else "inverse"
                                st.metric("💵 Utilidad Neta", f"${utilidad_neta:,.2f}")
                            
                            st.divider()
                            
                            # Indicadores de Desempeño
                            st.markdown("#### 📊 Indicadores Clave de Desempeño (KPIs)")
                            
                            col1, col2, col3, col4 = st.columns(4)
                            
                            # Calcular KPIs
                            activos_corrientes = float(sum(float(c.get('saldo_final', 0)) for c in activos.get('corrientes', [])))
                            pasivos_corrientes = float(sum(float(c.get('saldo_final', 0)) for c in pasivos.get('corrientes', [])))
                            
                            with col1:
                                if pasivos_corrientes > 0:
                                    liquidez = activos_corrientes / pasivos_corrientes
                                    st.metric("💧 Liquidez", f"{liquidez:.2f}", 
                                            delta="Saludable" if liquidez >= 1.5 else "Bajo")
                                else:
                                    st.metric("💧 Liquidez", "N/A")
                            
                            with col2:
                                if total_activos > 0:
                                    roa = (utilidad_neta / total_activos) * 100
                                    st.metric("📈 ROA", f"{roa:.2f}%",
                                            delta="Bueno" if roa > 5 else "Mejorar")
                                else:
                                    st.metric("📈 ROA", "N/A")
                            
                            with col3:
                                if total_patrimonio > 0:
                                    roe = (utilidad_neta / total_patrimonio) * 100
                                    st.metric("💹 ROE", f"{roe:.2f}%",
                                            delta="Bueno" if roe > 10 else "Mejorar")
                                else:
                                    st.metric("💹 ROE", "N/A")
                            
                            with col4:
                                if total_ingresos > 0:
                                    margen = (utilidad_neta / total_ingresos) * 100
                                    st.metric("📊 Margen Neto", f"{margen:.2f}%",
                                            delta="Bueno" if margen > 10 else "Mejorar")
                                else:
                                    st.metric("📊 Margen Neto", "N/A")
                            
                            st.divider()
                            
                            # Análisis de Situación Financiera
                            st.markdown("#### 💼 Análisis de Situación Financiera")
                            
                            # Ecuación contable
                            diferencia = abs(total_activos - (total_pasivos + total_patrimonio))
                            if diferencia < 0.01:
                                st.success(f"✅ La ecuación contable está balanceada: Activos (${total_activos:,.2f}) = Pasivos (${total_pasivos:,.2f}) + Patrimonio (${total_patrimonio:,.2f})")
                            else:
                                st.warning(f"⚠️ Diferencia en ecuación contable: ${diferencia:,.2f}")
                            
                            # Estructura financiera
                            if total_activos > 0:
                                col1, col2 = st.columns(2)
                                
                                with col1:
                                    st.markdown("**Estructura de Activos:**")
                                    pct_corrientes = (activos_corrientes / total_activos) * 100 if total_activos > 0 else 0
                                    pct_no_corrientes = 100 - pct_corrientes
                                    
                                    st.write(f"- Activos Corrientes: {pct_corrientes:.1f}%")
                                    st.write(f"- Activos No Corrientes: {pct_no_corrientes:.1f}%")
                                
                                with col2:
                                    st.markdown("**Estructura de Financiamiento:**")
                                    pct_pasivos = (total_pasivos / total_activos) * 100 if total_activos > 0 else 0
                                    pct_patrimonio = (total_patrimonio / total_activos) * 100 if total_activos > 0 else 0
                                    
                                    st.write(f"- Financiamiento Externo (Pasivos): {pct_pasivos:.1f}%")
                                    st.write(f"- Financiamiento Propio (Patrimonio): {pct_patrimonio:.1f}%")
                            
                            st.divider()
                            
                            # Resultados del Período
                            st.markdown("#### 💰 Resultados del Período")
                            
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.metric("📈 Ingresos Totales", f"${total_ingresos:,.2f}")
                                st.metric("📉 Egresos Totales", f"${total_egresos:,.2f}")
                            
                            with col2:
                                utilidad_bruta = float(resumen.get('utilidad_bruta', 0))
                                st.metric("💵 Utilidad Bruta", f"${utilidad_bruta:,.2f}")
                                st.metric("💰 Utilidad Neta", f"${utilidad_neta:,.2f}")
                            
                            # Gráfico de composición
                            if total_ingresos > 0 or total_egresos > 0:
                                st.divider()
                                st.markdown("#### 📊 Composición de Resultados")
                                
                                fig = go.Figure(data=[
                                    go.Bar(name='Ingresos', x=['Resultados'], y=[total_ingresos], marker_color='#2ecc71'),
                                    go.Bar(name='Egresos', x=['Resultados'], y=[total_egresos], marker_color='#e74c3c'),
                                    go.Bar(name='Utilidad Neta', x=['Resultados'], y=[utilidad_neta], marker_color='#3498db')
                                ])
                                
                                fig.update_layout(
                                    title='Composición de Resultados del Período',
                                    barmode='group',
                                    yaxis_title='Monto ($)',
                                    showlegend=True,
                                    height=400
                                )
                                
                                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
                            
                            # Recomendaciones
                            st.divider()
                            st.markdown("#### 💡 Recomendaciones")
                            
                            recomendaciones = []
                            
                            if pasivos_corrientes > 0 and activos_corrientes / pasivos_corrientes < 1:
                                recomendaciones.append("⚠️ **Liquidez:** La razón corriente está por debajo de 1. Considere mejorar la liquidez.")
                            
                            if total_activos > 0 and (total_pasivos / total_activos) > 0.7:
                                recomendaciones.append("⚠️ **Endeudamiento:** El nivel de endeudamiento es alto (>70%). Evalúe opciones de reducción.")
                            
                            if utilidad_neta < 0:
                                recomendaciones.append("❌ **Rentabilidad:** El período muestra pérdidas. Revise estructura de costos e ingresos.")
                            
                            if total_ingresos > 0 and (utilidad_neta / total_ingresos) < 0.05:
                                recomendaciones.append("⚠️ **Margen:** El margen de utilidad es bajo (<5%). Considere optimización de procesos.")
                            
                            if not recomendaciones:
                                st.success("✅ Los indicadores financieros muestran una situación saludable")
                            else:
                                for rec in recomendaciones:
                                    st.warning(rec)
                            
                        else:
                            st.error("No se pudo obtener la información financiera")
                            
                    except Exception as e:
                        st.error(f"Error al generar reporte: {e}")
                        
    except Exception as e:
        st.error(f"Error al cargar períodos: {e}")
