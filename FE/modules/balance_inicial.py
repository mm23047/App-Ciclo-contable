"""
Módulo Streamlit para el Balance Inicial.
Configuración de saldos iniciales de cuentas contables.
"""
import streamlit as st
import requests
import pandas as pd
from datetime import datetime, date
from typing import Dict, Any, List

def render_page(backend_url: str):
    """Renderizar página de balance inicial"""
    
    st.header("📊 Balance Inicial")
    st.markdown("Configuración y gestión de saldos iniciales de cuentas contables")
    
    # Tabs para organizar funcionalidades
    tab1, tab2, tab3 = st.tabs(["⚙️ Configurar Saldos", "📋 Consultar Balance", "📊 Validación"])
    
    with tab1:
        configurar_saldos_iniciales(backend_url)
    
    with tab2:
        consultar_balance_inicial(backend_url)
    
    with tab3:
        validar_balance_inicial(backend_url)

def configurar_saldos_iniciales(backend_url: str):
    """Configurar saldos iniciales"""
    
    st.subheader("⚙️ Configurar Saldos Iniciales")
    
    # Obtener períodos disponibles
    try:
        response_periodos = requests.get(f"{backend_url}/api/periodos/")
        periodos = response_periodos.json() if response_periodos.status_code == 200 else []
    except:
        periodos = []
    
    if not periodos:
        st.warning("⚠️ No hay períodos configurados. Configura un período primero.")
        return
    
    # Selección de período
    opciones_periodos = [
        f"{p['descripcion']} ({p['fecha_inicio']} - {p['fecha_fin']})"
        for p in periodos
    ]
    periodo_seleccionado = st.selectbox("Período contable:", opciones_periodos)
    
    # Extraer información del período
    nombre_periodo = periodo_seleccionado.split(" (")[0]
    periodo_obj = next((p for p in periodos if p['descripcion'] == nombre_periodo), None)
    
    if periodo_obj:
        # Botón de refrescar
        if st.button("🔄 Refrescar datos", help="Actualizar información de saldos"):
            st.rerun()
        
        # Mostrar solo configuración individual
        configuracion_individual(backend_url, periodo_obj)

def configuracion_individual(backend_url: str, periodo: Dict[str, Any]):
    """Configuración individual de saldos"""
    
    st.markdown("### 📝 Configuración Individual")
    
    # Inicializar estado de sesión
    if 'cuenta_seleccionada_id' not in st.session_state:
        st.session_state.cuenta_seleccionada_id = None
    if 'modo_edicion_balance' not in st.session_state:
        st.session_state.modo_edicion_balance = False
    
    # Obtener cuentas que aceptan movimientos
    try:
        response_cuentas = requests.get(f"{backend_url}/api/catalogo-cuentas/")
        cuentas = response_cuentas.json() if response_cuentas.status_code == 200 else []
        cuentas_disponibles = [c for c in cuentas if c['acepta_movimientos']]
    except:
        cuentas_disponibles = []
    
    if not cuentas_disponibles:
        st.warning("No hay cuentas disponibles para configurar saldos iniciales")
        return
    
    # Obtener saldos iniciales existentes con información completa
    try:
        response_saldos = requests.get(f"{backend_url}/api/balance-inicial/periodo/{periodo['id_periodo']}")
        saldos_completos = {}
        if response_saldos.status_code == 200:
            try:
                saldos_data = response_saldos.json()
                for s in saldos_data:
                    saldos_completos[s['id_cuenta']] = s
            except:
                saldos_completos = {}
    except:
        saldos_completos = {}
    
    # Crear opciones de cuentas
    opciones_cuentas = [
        f"{c['codigo_cuenta']} - {c['nombre_cuenta']} ({c['tipo_cuenta']})"
        for c in cuentas_disponibles
    ]
    
    # Selección de cuenta (fuera del form para que sea reactivo)
    cuenta_seleccionada = st.selectbox(
        "Seleccionar cuenta:", 
        opciones_cuentas,
        key='select_cuenta_balance'
    )
    
    # Obtener información de la cuenta seleccionada
    cuenta_obj = None
    balance_existente = None
    
    if cuenta_seleccionada:
        codigo_cuenta = cuenta_seleccionada.split(" - ")[0]
        cuenta_obj = next((c for c in cuentas_disponibles if c['codigo_cuenta'] == codigo_cuenta), None)
        
        if cuenta_obj:
            # Detectar cambio de cuenta y resetear modo de edición
            if st.session_state.cuenta_seleccionada_id != cuenta_obj['id_cuenta']:
                st.session_state.cuenta_seleccionada_id = cuenta_obj['id_cuenta']
                st.session_state.modo_edicion_balance = False
            
            # Verificar si existe balance
            balance_existente = saldos_completos.get(cuenta_obj['id_cuenta'])
            
            # Si la cuenta no tiene balance, asegurar que no esté en modo edición
            if balance_existente is None:
                st.session_state.modo_edicion_balance = False
    
    # Determinar valores por defecto basados en si existe balance
    if balance_existente:
        default_saldo = float(balance_existente['saldo_inicial'])
        default_naturaleza = balance_existente['naturaleza_saldo']
        default_observaciones = balance_existente.get('observaciones', '')
    else:
        default_saldo = 0.0
        default_naturaleza = "DEUDOR"
        default_observaciones = ""
    
    # Formulario de configuración
    with st.form("form_saldo_individual", clear_on_submit=False):
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Valor del saldo inicial (prellenado si existe balance)
            saldo_inicial = st.number_input(
                "Saldo inicial ($):",
                value=default_saldo,
                step=0.01,
                format="%.2f",
                help="Valor del saldo inicial para esta cuenta",
                disabled=balance_existente is not None and not st.session_state.modo_edicion_balance
            )
        
        with col2:
            # Naturaleza del saldo (prellenada si existe balance)
            naturaleza_index = 0 if default_naturaleza == "DEUDOR" else 1
            naturaleza_saldo = st.selectbox(
                "Naturaleza del saldo:",
                ["DEUDOR", "ACREEDOR"],
                index=naturaleza_index,
                help="Indica si el saldo es deudor o acreedor",
                disabled=balance_existente is not None and not st.session_state.modo_edicion_balance
            )
        
        # Observaciones (prellenadas si existen)
        observaciones = st.text_area(
            "Observaciones (opcional):",
            value=default_observaciones,
            height=80,
            help="Observaciones adicionales del saldo inicial",
            disabled=balance_existente is not None and not st.session_state.modo_edicion_balance
        )
        
        # Botones de acción
        if balance_existente:
            # Cuenta CON balance existente
            if not st.session_state.modo_edicion_balance:
                # Modo visualización: solo botón Editar
                col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 1])
                with col_btn2:
                    editar_clicked = st.form_submit_button(
                        "✏️ Editar",
                        use_container_width=True,
                        type="primary"
                    )
                actualizar_clicked = False
                cancelar_clicked = False
                guardar_clicked = False
            else:
                # Modo edición: botones Actualizar y Cancelar
                col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 1])
                with col_btn1:
                    actualizar_clicked = st.form_submit_button(
                        "✅ Actualizar",
                        use_container_width=True,
                        type="primary"
                    )
                with col_btn3:
                    cancelar_clicked = st.form_submit_button(
                        "❌ Cancelar",
                        use_container_width=True
                    )
                editar_clicked = False
                guardar_clicked = False
        else:
            # Cuenta SIN balance: solo botón Guardar
            col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 1])
            with col_btn2:
                guardar_clicked = st.form_submit_button(
                    "💾 Guardar",
                    use_container_width=True,
                    type="primary"
                )
            editar_clicked = False
            actualizar_clicked = False
            cancelar_clicked = False
        
        # Procesar acciones
        if editar_clicked:
            st.session_state.modo_edicion_balance = True
            st.rerun()
        
        if cancelar_clicked:
            st.session_state.modo_edicion_balance = False
            st.rerun()
        
        if guardar_clicked and cuenta_obj:
            if saldo_inicial != 0:
                # Crear nuevo balance
                configurar_saldo_individual(
                    backend_url,
                    periodo['id_periodo'],
                    cuenta_obj['id_cuenta'],
                    saldo_inicial,
                    naturaleza_saldo,
                    observaciones
                )
            else:
                st.warning("⚠️ Ingresa un saldo inicial diferente de cero")
        
        if actualizar_clicked and cuenta_obj and balance_existente:
            if saldo_inicial != 0:
                # Resetear modo de edición ANTES de actualizar
                st.session_state.modo_edicion_balance = False
                # Actualizar balance existente
                actualizar_saldo_individual(
                    backend_url,
                    balance_existente['id_balance_inicial'],
                    saldo_inicial,
                    naturaleza_saldo,
                    observaciones
                )
            else:
                st.warning("⚠️ Ingresa un saldo inicial diferente de cero")
    
    # Mostrar indicador de modo
    if st.session_state.modo_edicion_balance and balance_existente:
        st.info("✏️ **Modo edición activado** - Puedes modificar los campos y guardar los cambios")
    elif balance_existente:
        st.info("👁️ **Modo visualización** - Haz clic en 'Editar' para modificar los valores")

def configurar_saldo_individual(
    backend_url: str,
    id_periodo: int,
    id_cuenta: int,
    saldo_inicial: float,
    naturaleza_saldo: str,
    observaciones: str
):
    """Configurar saldo inicial individual"""
    
    try:
        datos_saldo = {
            "id_periodo": id_periodo,
            "id_cuenta": id_cuenta,
            "saldo_inicial": saldo_inicial,
            "naturaleza_saldo": naturaleza_saldo,
            "observaciones": observaciones if observaciones else None
        }
        
        with st.spinner("Configurando saldo inicial..."):
            response = requests.post(
                f"{backend_url}/api/balance-inicial/",
                json=datos_saldo
            )
        
        if response.status_code in [200, 201]:
            st.success("✅ Saldo inicial configurado exitosamente!")
            st.rerun()
        else:
            try:
                error_detail = response.json().get('detail', 'Error desconocido')
            except:
                error_detail = response.text if response.text else f'Error HTTP {response.status_code}'
            st.error(f"❌ Error al configurar saldo: {error_detail}")
            
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Error de conexión: {e}")
    except Exception as e:
        st.error(f"❌ Error inesperado: {e}")

def actualizar_saldo_individual(
    backend_url: str,
    id_balance: int,
    saldo_inicial: float,
    naturaleza_saldo: str,
    observaciones: str
):
    """Actualizar saldo inicial existente"""
    
    try:
        datos_actualizacion = {
            "saldo_inicial": saldo_inicial,
            "naturaleza_saldo": naturaleza_saldo,
            "observaciones": observaciones if observaciones else None
        }
        
        with st.spinner("Actualizando saldo inicial..."):
            response = requests.put(
                f"{backend_url}/api/balance-inicial/{id_balance}",
                json=datos_actualizacion
            )
        
        if response.status_code == 200:
            st.success("✅ Saldo inicial actualizado exitosamente!")
            st.rerun()
        else:
            try:
                error_detail = response.json().get('detail', 'Error desconocido')
            except:
                error_detail = response.text if response.text else f'Error HTTP {response.status_code}'
            st.error(f"❌ Error al actualizar saldo: {error_detail}")
            
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Error de conexión: {e}")
    except Exception as e:
        st.error(f"❌ Error inesperado: {e}")

def consultar_balance_inicial(backend_url: str):
    """Consultar balance inicial configurado"""
    
    st.subheader("📋 Consultar Balance Inicial")
    
    # Selección de período
    try:
        response_periodos = requests.get(f"{backend_url}/api/periodos/")
        periodos = response_periodos.json() if response_periodos.status_code == 200 else []
        
        if periodos:
            opciones_periodos = [
                f"{p['descripcion']} ({p['fecha_inicio']} - {p['fecha_fin']})"
                for p in periodos
            ]
            periodo_consulta = st.selectbox("Período:", opciones_periodos, key="consulta_periodo")
            
            # Filtros adicionales
            col1, col2 = st.columns(2)
            
            with col1:
                tipo_filtro = st.selectbox("Filtrar por tipo:", ["Todos", "Activo", "Pasivo", "Capital"])
            
            with col2:
                solo_con_saldo = st.checkbox("Solo cuentas con saldo", value=True)
            
            if st.button("🔍 Consultar Balance Inicial"):
                nombre_periodo = periodo_consulta.split(" (")[0]
                periodo_obj = next((p for p in periodos if p['descripcion'] == nombre_periodo), None)
                
                if periodo_obj:
                    mostrar_balance_inicial(backend_url, periodo_obj['id_periodo'], tipo_filtro, solo_con_saldo)
        else:
            st.warning("No hay períodos configurados")
            
    except:
        st.error("Error al cargar períodos")

def mostrar_balance_inicial(backend_url: str, id_periodo: int, tipo_filtro: str, solo_con_saldo: bool):
    """Mostrar balance inicial"""
    
    try:
        with st.spinner("Consultando balance inicial..."):
            response = requests.get(f"{backend_url}/api/balance-inicial/periodo/{id_periodo}")
        
        if response.status_code == 200:
            try:
                saldos = response.json()
            except:
                st.error("❌ Error al procesar respuesta del servidor")
                return
            
            if saldos:
                # Convertir a DataFrame
                df_saldos = pd.DataFrame(saldos)
                
                # Asegurar que existan todas las columnas necesarias
                columnas_requeridas = {
                    'codigo_cuenta': '',
                    'nombre_cuenta': '',
                    'tipo_cuenta': '',
                    'naturaleza_saldo': '',
                    'saldo_inicial': 0.0,
                    'fecha_creacion': None,
                    'observaciones': None
                }
                for col, default in columnas_requeridas.items():
                    if col not in df_saldos.columns:
                        df_saldos[col] = default
                
                # Aplicar filtros en el frontend
                if tipo_filtro != "Todos":
                    df_saldos = df_saldos[df_saldos['tipo_cuenta'] == tipo_filtro]
                
                if solo_con_saldo:
                    df_saldos = df_saldos[df_saldos['saldo_inicial'] != 0]
                
                if df_saldos.empty:
                    st.info("📭 No hay saldos que coincidan con los filtros seleccionados")
                    return
                
                # Calcular totales por tipo
                resumen_tipos = df_saldos.groupby('tipo_cuenta')['saldo_inicial'].sum()
                
                # Mostrar totales
                st.markdown("### 📊 Resumen por Tipo de Cuenta")
                
                cols = st.columns(len(resumen_tipos))
                for i, (tipo, total) in enumerate(resumen_tipos.items()):
                    with cols[i]:
                        st.metric(tipo, f"${total:,.2f}")
                
                # Validación ecuación contable
                activos = resumen_tipos.get('Activo', 0)
                pasivos = resumen_tipos.get('Pasivo', 0)
                capital = resumen_tipos.get('Capital', 0)
                patrimonio = resumen_tipos.get('Patrimonio', 0)
                capital_total = capital + patrimonio
                diferencia = activos - pasivos - capital_total
                
                st.markdown("### ⚖️ Validación Ecuación Contable")
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Activos", f"${activos:,.2f}")
                
                with col2:
                    st.metric("Pasivos", f"${pasivos:,.2f}")
                
                with col3:
                    st.metric("Capital + Patrimonio", f"${capital_total:,.2f}")
                
                with col4:
                    st.metric("Diferencia", f"${diferencia:,.2f}")
                
                if abs(diferencia) > 0.01:
                    st.error("❌ La ecuación contable no está balanceada (Activos ≠ Pasivos + Capital + Patrimonio)")
                else:
                    st.success("✅ Ecuación contable balanceada correctamente")
                
                # Tabla detallada
                st.markdown("### 📋 Detalle de Saldos Iniciales")
                
                # Formatear para visualización
                df_display = df_saldos.copy()
                df_display['saldo_inicial'] = df_display['saldo_inicial'].apply(lambda x: f"${x:,.2f}")
                # Formatear fecha solo si existe
                if 'fecha_creacion' in df_display.columns and df_display['fecha_creacion'].notna().any():
                    df_display['fecha_creacion'] = pd.to_datetime(df_display['fecha_creacion'], errors='coerce').dt.strftime('%d/%m/%Y')
                else:
                    df_display['fecha_creacion'] = 'N/A'
                
                # Seleccionar columnas a mostrar
                columnas_mostrar = ['codigo_cuenta', 'nombre_cuenta', 'tipo_cuenta', 'naturaleza_saldo', 'saldo_inicial', 'fecha_creacion']
                nombres_columnas = ['Código', 'Nombre Cuenta', 'Tipo', 'Naturaleza', 'Saldo Inicial', 'Fecha Config.']
                
                df_final = df_display[columnas_mostrar].copy()
                df_final.columns = nombres_columnas
                
                st.dataframe(df_final, width="stretch", hide_index=True)
                
                # Opciones de descarga y eliminación
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    # Descargar CSV - Obtener TODOS los balances del período sin filtros
                    try:
                        with st.spinner("Preparando descarga..."):
                            response_completo = requests.get(f"{backend_url}/api/balance-inicial/periodo/{id_periodo}")
                        
                        if response_completo.status_code == 200:
                            saldos_completos = response_completo.json()
                            if saldos_completos:
                                # Crear DataFrame para CSV con todos los datos
                                df_csv = pd.DataFrame(saldos_completos)
                                
                                # Seleccionar y ordenar columnas para el CSV
                                columnas_csv = ['codigo_cuenta', 'nombre_cuenta', 'tipo_cuenta', 'naturaleza_saldo', 'saldo_inicial', 'observaciones', 'fecha_creacion']
                                
                                # Asegurar que existan las columnas
                                for col in columnas_csv:
                                    if col not in df_csv.columns:
                                        df_csv[col] = ''
                                
                                df_csv = df_csv[columnas_csv].copy()
                                
                                # Formatear fecha para CSV
                                if 'fecha_creacion' in df_csv.columns:
                                    df_csv['fecha_creacion'] = pd.to_datetime(df_csv['fecha_creacion'], errors='coerce').dt.strftime('%Y-%m-%d %H:%M:%S')
                                
                                # Renombrar columnas para el CSV (sin tildes para evitar problemas de encoding)
                                df_csv.columns = ['Codigo Cuenta', 'Nombre Cuenta', 'Tipo Cuenta', 'Naturaleza', 'Saldo Inicial', 'Observaciones', 'Fecha Creacion']
                                
                                # Generar CSV con separador punto y coma para Excel en español
                                csv_data = df_csv.to_csv(index=False, encoding='latin-1', sep=';', errors='replace')
                                
                                st.download_button(
                                    label="📥 Descargar Balance (Excel)",
                                    data=csv_data,
                                    file_name=f"balance_inicial_periodo_{id_periodo}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                    mime="text/csv",
                                    help="Descarga el balance inicial completo del período en formato Excel"
                                )
                            else:
                                st.warning("No hay datos para descargar")
                        else:
                            st.error("Error al obtener datos para descarga")
                    except Exception as e:
                        st.error(f"Error al preparar descarga: {e}")
                
                with col3:
                    # Eliminar todos los saldos del período
                    if 'confirmar_eliminar_balance' not in st.session_state:
                        st.session_state.confirmar_eliminar_balance = False
                    
                    if not st.session_state.confirmar_eliminar_balance:
                        if st.button("🗑️ Limpiar Balance", help="Eliminar todos los saldos de este período"):
                            st.session_state.confirmar_eliminar_balance = True
                            st.rerun()
                    else:
                        col_a, col_b = st.columns(2)
                        with col_a:
                            if st.button("⚠️ Confirmar", type="primary"):
                                eliminar_balance_periodo(backend_url, id_periodo)
                                st.session_state.confirmar_eliminar_balance = False
                        with col_b:
                            if st.button("❌ Cancelar"):
                                st.session_state.confirmar_eliminar_balance = False
                                st.rerun()
                
            else:
                st.info("📭 No hay saldos iniciales configurados para este período")
                
        else:
            st.error(f"Error al consultar balance inicial: {response.status_code}")
            
    except Exception as e:
        st.error(f"Error al mostrar balance inicial: {e}")

def eliminar_balance_periodo(backend_url: str, id_periodo: int):
    """Eliminar todos los saldos de un período"""
    
    try:
        with st.spinner("Eliminando saldos iniciales..."):
            response = requests.delete(f"{backend_url}/api/balance-inicial/periodo/{id_periodo}")
        
        if response.status_code == 200:
            st.success("✅ Saldos iniciales eliminados exitosamente")
            st.rerun()
        else:
            st.error(f"Error al eliminar saldos: {response.status_code}")
            
    except Exception as e:
        st.error(f"Error al eliminar saldos: {e}")

def validar_balance_inicial(backend_url: str):
    """Validar balance inicial"""
    
    st.subheader("📊 Validación de Balance Inicial")
    
    # Selección de período
    try:
        response_periodos = requests.get(f"{backend_url}/api/periodos/")
        periodos = response_periodos.json() if response_periodos.status_code == 200 else []
        
        if periodos:
            opciones_periodos = [
                f"{p['descripcion']} ({p['fecha_inicio']} - {p['fecha_fin']})"
                for p in periodos
            ]
            periodo_validacion = st.selectbox("Período a validar:", opciones_periodos, key="validacion_periodo")
            
            if st.button("🔍 Ejecutar Validación", width="stretch"):
                nombre_periodo = periodo_validacion.split(" (")[0]
                periodo_obj = next((p for p in periodos if p['descripcion'] == nombre_periodo), None)
                
                if periodo_obj:
                    ejecutar_validacion_balance(backend_url, periodo_obj['id_periodo'])
        else:
            st.warning("No hay períodos configurados")
            
    except:
        st.error("Error al cargar períodos")

def ejecutar_validacion_balance(backend_url: str, id_periodo: int):
    """Ejecutar validación completa del balance"""
    
    try:
        with st.spinner("Ejecutando validación..."):
            # Obtener resumen del período
            response = requests.get(f"{backend_url}/api/balance-inicial/resumen/{id_periodo}")
        
        if response.status_code == 200:
            try:
                resumen = response.json()
            except:
                st.error("❌ Error al procesar respuesta de validación")
                return
            
            st.markdown("### 📊 Resultados de la Validación")
            
            # Extraer datos del resumen
            resumen_por_tipo = resumen.get('resumen_por_tipo', {})
            total_general = resumen.get('total_general', {})
            
            # Calcular totales por tipo
            total_activos = float(resumen_por_tipo.get('Activo', {}).get('total_saldo', 0))
            total_pasivos = float(resumen_por_tipo.get('Pasivo', {}).get('total_saldo', 0))
            total_capital = float(resumen_por_tipo.get('Capital', {}).get('total_saldo', 0))
            total_patrimonio = float(resumen_por_tipo.get('Patrimonio', {}).get('total_saldo', 0))
            
            # Sumar Capital y Patrimonio
            total_capital_patrimonio = total_capital + total_patrimonio
            
            # Calcular diferencia (Activos - (Pasivos + Capital))
            diferencia = total_activos - (total_pasivos + total_capital_patrimonio)
            
            # Estado general
            if abs(diferencia) < 0.01:
                st.success("✅ El balance inicial está balanceado correctamente")
                st.markdown("**Ecuación contable cumplida:** Activos = Pasivos + Capital/Patrimonio")
            else:
                st.error("❌ El balance inicial NO está balanceado")
                if diferencia > 0:
                    st.warning(f"💡 **Sugerencia:** Faltan ${abs(diferencia):,.2f} en Pasivos + Capital")
                else:
                    st.warning(f"💡 **Sugerencia:** Sobran ${abs(diferencia):,.2f} en Pasivos + Capital")
            
            # Ecuación contable
            st.markdown("#### ⚖️ Ecuación Contable")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("💰 Activos", f"${total_activos:,.2f}")
            
            with col2:
                st.metric("📋 Pasivos", f"${total_pasivos:,.2f}")
            
            with col3:
                label_capital = "🏦 Capital/Patrimonio"
                st.metric(label_capital, f"${total_capital_patrimonio:,.2f}")
            
            with col4:
                color = "normal" if abs(diferencia) < 0.01 else "inverse"
                delta_text = "Balanceado ✅" if abs(diferencia) < 0.01 else "Desbalanceado ⚠️"
                st.metric(
                    "⚖️ Diferencia", 
                    f"${abs(diferencia):,.2f}",
                    delta=delta_text,
                    delta_color=color
                )
            
            st.markdown("---")
            
            # Estadísticas adicionales
            st.markdown("#### 📊 Estadísticas del Balance")
            col1, col2, col3 = st.columns(3)
            
            total_cuentas = total_general.get('cantidad_cuentas', 0)
            cuentas_con_saldo = sum(1 for tipo_data in resumen_por_tipo.values() if tipo_data.get('total_saldo', 0) != 0)
            
            with col1:
                st.metric("📝 Cuentas Configuradas", total_cuentas)
            
            with col2:
                st.metric("🔢 Tipos de Cuenta", len(resumen_por_tipo))
            
            with col3:
                total_configurado = total_activos + total_pasivos + total_capital_patrimonio
                st.metric("💵 Total Configurado", f"${total_configurado:,.2f}")
            
            # Detalles por tipo de cuenta
            if resumen_por_tipo:
                st.markdown("---")
                st.markdown("#### 📋 Detalle por Tipo de Cuenta")
                
                detalle_data = []
                
                emoji_map = {
                    'Activo': '💰',
                    'Pasivo': '📋',
                    'Capital': '🏦',
                    'Patrimonio': '🏛️',
                    'Ingreso': '💵',
                    'Egreso': '💸'
                }
                
                for tipo, data in resumen_por_tipo.items():
                    detalle_data.append({
                        'Emoji': emoji_map.get(tipo, '📊'),
                        'Tipo': tipo,
                        'Cuentas': data.get('cantidad_cuentas', 0),
                        'Total': f"${float(data.get('total_saldo', 0)):,.2f}"
                    })
                
                if detalle_data:
                    df_detalle = pd.DataFrame(detalle_data)
                    st.dataframe(
                        df_detalle,
                        column_config={
                            "Emoji": st.column_config.TextColumn("", width="small"),
                            "Tipo": st.column_config.TextColumn("Tipo de Cuenta", width="medium"),
                            "Cuentas": st.column_config.NumberColumn("# Cuentas", width="small"),
                            "Total": st.column_config.TextColumn("Total", width="medium"),
                        },
                        hide_index=True,
                        use_container_width=True
                    )
            
            # Recomendaciones
            st.markdown("---")
            st.markdown("#### 💡 Recomendaciones")
            
            if abs(diferencia) < 0.01:
                st.info("✅ El balance está correctamente configurado. Puedes proceder con las operaciones del período.")
            else:
                st.warning("⚠️ Ajusta los saldos iniciales para que la ecuación contable se cumpla:")
                st.markdown("- Revisa que todas las cuentas estén correctamente clasificadas (Activo, Pasivo, Capital/Patrimonio)")
                st.markdown("- Verifica los montos ingresados en cada cuenta")
                st.markdown("- Recuerda: **Activos = Pasivos + Capital/Patrimonio**")
            
            if total_cuentas == 0:
                st.info("💡 No hay saldos iniciales configurados. Configura al menos una cuenta en la pestaña 'Configurar Saldos'.")
            
        elif response.status_code == 404:
            st.info("💡 No se encontraron saldos iniciales para este período. Configúralos en la pestaña 'Configurar Saldos'.")
        else:
            st.error(f"❌ Error al ejecutar validación: {response.status_code}")
            
    except Exception as e:
        st.error(f"❌ Error al ejecutar validación: {str(e)}")
