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
        response_periodos = requests.get(f"{backend_url}/api/periodos")
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
        # Opciones de configuración
        col1, col2 = st.columns(2)
        
        with col1:
            modo_configuracion = st.radio(
                "Modo de configuración:",
                ["Configuración individual", "Carga masiva"],
                help="Individual: una cuenta a la vez. Masiva: múltiples cuentas"
            )
        
        with col2:
            if st.button("🔄 Refrescar datos", help="Actualizar información de saldos"):
                st.rerun()
        
        if modo_configuracion == "Configuración individual":
            configuracion_individual(backend_url, periodo_obj)
        else:
            carga_masiva_saldos(backend_url, periodo_obj)

def configuracion_individual(backend_url: str, periodo: Dict[str, Any]):
    """Configuración individual de saldos"""
    
    st.markdown("### 📝 Configuración Individual")
    
    # Obtener cuentas que aceptan movimientos
    try:
        response_cuentas = requests.get(f"{backend_url}/api/catalogo-cuentas")
        cuentas = response_cuentas.json() if response_cuentas.status_code == 200 else []
        cuentas_disponibles = [c for c in cuentas if c['acepta_movimientos']]
    except:
        cuentas_disponibles = []
    
    if not cuentas_disponibles:
        st.warning("No hay cuentas disponibles para configurar saldos iniciales")
        return
    
    # Obtener saldos iniciales existentes
    try:
        response_saldos = requests.get(f"{backend_url}/api/balance-inicial/periodo/{periodo['id_periodo']}")
        saldos_existentes = {}
        if response_saldos.status_code == 200:
            saldos_data = response_saldos.json()
            saldos_existentes = {
                s['id_cuenta']: s['saldo_inicial'] 
                for s in saldos_data
            }
    except:
        saldos_existentes = {}
    
    # Formulario de configuración
    with st.form("form_saldo_individual", clear_on_submit=False):
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Selección de cuenta
            opciones_cuentas = [
                f"{c['codigo_cuenta']} - {c['nombre_cuenta']} ({c['tipo_cuenta']})"
                for c in cuentas_disponibles
            ]
            cuenta_seleccionada = st.selectbox("Seleccionar cuenta:", opciones_cuentas)
            
            # Obtener información de la cuenta seleccionada
            if cuenta_seleccionada:
                codigo_cuenta = cuenta_seleccionada.split(" - ")[0]
                cuenta_obj = next((c for c in cuentas_disponibles if c['codigo_cuenta'] == codigo_cuenta), None)
                
                if cuenta_obj:
                    # Mostrar información de la cuenta
                    st.info(f"📋 **Tipo:** {cuenta_obj['tipo_cuenta']} | **Código:** {cuenta_obj['codigo_cuenta']}")
                    
                    # Saldo actual si existe
                    saldo_actual = saldos_existentes.get(cuenta_obj['id_cuenta'], 0)
                    if saldo_actual != 0:
                        st.warning(f"⚠️ Esta cuenta ya tiene un saldo inicial configurado: ${saldo_actual:,.2f}")
        
        with col2:
            # Valor del saldo inicial
            saldo_inicial = st.number_input(
                "Saldo inicial ($):",
                step=0.01,
                format="%.2f",
                help="Valor del saldo inicial para esta cuenta"
            )
            
            # Naturaleza del saldo
            naturaleza_saldo = st.selectbox(
                "Naturaleza del saldo:",
                ["DEUDOR", "ACREEDOR"],
                help="Indica si el saldo es deudor o acreedor"
            )
            
            # Observaciones opcionales
            observaciones = st.text_area(
                "Observaciones (opcional):",
                height=80,
                help="Observaciones adicionales del saldo inicial"
            )
        
        # Botón para guardar
        submitted = st.form_submit_button(
            "💾 Configurar Saldo Inicial",
            use_container_width=True,
            type="primary"
        )
        
        if submitted and cuenta_obj:
            if saldo_inicial != 0:
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
                f"{backend_url}/api/balance-inicial",
                json=datos_saldo
            )
        
        if response.status_code == 201:
            st.success("✅ Saldo inicial configurado exitosamente!")
            st.rerun()
        else:
            error_detail = response.json().get('detail', 'Error desconocido')
            st.error(f"❌ Error al configurar saldo: {error_detail}")
            
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Error de conexión: {e}")

def carga_masiva_saldos(backend_url: str, periodo: Dict[str, Any]):
    """Carga masiva de saldos iniciales"""
    
    st.markdown("### 📊 Carga Masiva de Saldos")
    
    # Pestañas para diferentes métodos de carga
    tab_plantilla, tab_manual = st.tabs(["📋 Usar Plantilla", "✏️ Ingreso Manual"])
    
    with tab_plantilla:
        carga_con_plantilla(backend_url, periodo)
    
    with tab_manual:
        carga_manual_multiple(backend_url, periodo)

def carga_con_plantilla(backend_url: str, periodo: Dict[str, Any]):
    """Carga masiva usando plantilla"""
    
    st.markdown("#### 📋 Carga mediante Plantilla Excel/CSV")
    
    # Generar plantilla
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📥 Descargar Plantilla", use_container_width=True):
            generar_plantilla_saldos(backend_url)
    
    with col2:
        st.info("💡 Descarga la plantilla, complétala con los saldos y súbela")
    
    # Subir archivo
    uploaded_file = st.file_uploader(
        "Subir archivo de saldos:",
        type=['csv', 'xlsx'],
        help="Archivo con formato: codigo_cuenta, saldo_inicial, descripcion"
    )
    
    if uploaded_file is not None:
        try:
            # Leer archivo
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            
            # Validar estructura
            columnas_requeridas = ['codigo_cuenta', 'saldo_inicial']
            if all(col in df.columns for col in columnas_requeridas):
                
                # Preview de datos
                st.markdown("**Vista previa de datos:**")
                st.dataframe(df.head(10))
                
                if st.button("📊 Procesar Carga Masiva"):
                    procesar_carga_masiva(backend_url, periodo['id_periodo'], df)
                    
            else:
                st.error("❌ El archivo debe contener las columnas: codigo_cuenta, saldo_inicial")
                
        except Exception as e:
            st.error(f"❌ Error al leer archivo: {e}")

def generar_plantilla_saldos(backend_url: str):
    """Generar plantilla para carga masiva"""
    
    try:
        # Obtener cuentas que aceptan movimientos
        response = requests.get(f"{backend_url}/api/catalogo-cuentas")
        
        if response.status_code == 200:
            cuentas = response.json()
            cuentas_movimientos = [c for c in cuentas if c['acepta_movimientos']]
            
            # Crear DataFrame de plantilla
            plantilla_data = []
            for cuenta in cuentas_movimientos[:50]:  # Limitar a 50 para demo
                plantilla_data.append({
                    'codigo_cuenta': cuenta['codigo_cuenta'],
                    'nombre_cuenta': cuenta['nombre_cuenta'],
                    'tipo_cuenta': cuenta['tipo_cuenta'],
                    'saldo_inicial': 0.00,
                    'descripcion': ''
                })
            
            df_plantilla = pd.DataFrame(plantilla_data)
            csv = df_plantilla.to_csv(index=False)
            
            st.download_button(
                label="📥 Descargar Plantilla CSV",
                data=csv,
                file_name=f"plantilla_saldos_iniciales_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
            
    except Exception as e:
        st.error(f"Error al generar plantilla: {e}")

def carga_manual_multiple(backend_url: str, periodo: Dict[str, Any]):
    """Carga manual de múltiples saldos"""
    
    st.markdown("#### ✏️ Ingreso Manual Múltiple")
    
    # Obtener cuentas
    try:
        response_cuentas = requests.get(f"{backend_url}/api/catalogo-cuentas")
        cuentas = response_cuentas.json() if response_cuentas.status_code == 200 else []
        cuentas_disponibles = [c for c in cuentas if c['acepta_movimientos']]
    except:
        cuentas_disponibles = []
    
    if not cuentas_disponibles:
        st.warning("No hay cuentas disponibles")
        return
    
    # Gestión de saldos múltiples
    if 'saldos_multiples' not in st.session_state:
        st.session_state.saldos_multiples = []
    
    # Formulario para agregar saldo
    with st.expander("➕ Agregar Saldo", expanded=True):
        col1, col2, col3, col4 = st.columns([3, 1, 2, 1])
        
        with col1:
            opciones_cuentas = [
                f"{c['codigo_cuenta']} - {c['nombre_cuenta']}"
                for c in cuentas_disponibles
            ]
            cuenta_multiple = st.selectbox("Cuenta:", opciones_cuentas, key="cuenta_multiple")
        
        with col2:
            saldo_multiple = st.number_input("Saldo:", step=0.01, key="saldo_multiple")
        
        with col3:
            desc_multiple = st.text_input("Descripción:", key="desc_multiple")
        
        with col4:
            st.write("")  # Espaciado
            if st.button("➕", help="Agregar saldo"):
                if cuenta_multiple and saldo_multiple != 0:
                    codigo_cuenta = cuenta_multiple.split(" - ")[0]
                    cuenta_obj = next((c for c in cuentas_disponibles if c['codigo_cuenta'] == codigo_cuenta), None)
                    
                    # Verificar si ya existe
                    ya_existe = any(s['id_cuenta'] == cuenta_obj['id_cuenta'] for s in st.session_state.saldos_multiples)
                    
                    if not ya_existe:
                        nuevo_saldo = {
                            'id_cuenta': cuenta_obj['id_cuenta'],
                            'codigo_cuenta': codigo_cuenta,
                            'nombre_cuenta': cuenta_obj['nombre_cuenta'],
                            'tipo_cuenta': cuenta_obj['tipo_cuenta'],
                            'saldo_inicial': saldo_multiple,
                            'descripcion': desc_multiple
                        }
                        
                        st.session_state.saldos_multiples.append(nuevo_saldo)
                        st.rerun()
                    else:
                        st.error("Esta cuenta ya está en la lista")
    
    # Mostrar saldos agregados
    if st.session_state.saldos_multiples:
        st.markdown("### 📋 Saldos a Configurar")
        
        for i, saldo in enumerate(st.session_state.saldos_multiples):
            col1, col2, col3, col4, col5 = st.columns([2, 3, 1, 1, 1])
            
            with col1:
                st.text(saldo['codigo_cuenta'])
            
            with col2:
                st.text(saldo['nombre_cuenta'])
            
            with col3:
                st.text(saldo['tipo_cuenta'])
            
            with col4:
                st.text(f"${saldo['saldo_inicial']:,.2f}")
            
            with col5:
                if st.button("🗑️", key=f"eliminar_saldo_{i}", help="Eliminar"):
                    st.session_state.saldos_multiples.pop(i)
                    st.rerun()
        
        # Resumen
        total_activos = sum(s['saldo_inicial'] for s in st.session_state.saldos_multiples if s['tipo_cuenta'] == 'Activo')
        total_pasivos = sum(s['saldo_inicial'] for s in st.session_state.saldos_multiples if s['tipo_cuenta'] == 'Pasivo')
        total_capital = sum(s['saldo_inicial'] for s in st.session_state.saldos_multiples if s['tipo_cuenta'] == 'Capital')
        
        st.markdown("### 📊 Resumen")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Activos", f"${total_activos:,.2f}")
        
        with col2:
            st.metric("Pasivos", f"${total_pasivos:,.2f}")
        
        with col3:
            st.metric("Capital", f"${total_capital:,.2f}")
        
        with col4:
            diferencia = total_activos - total_pasivos - total_capital
            st.metric("Diferencia", f"${diferencia:,.2f}")
        
        # Validación de ecuación contable
        if abs(diferencia) > 0.01:
            st.warning("⚠️ ADVERTENCIA: La ecuación contable no está balanceada (Activos = Pasivos + Capital)")
        else:
            st.success("✅ Ecuación contable balanceada")
        
        # Botón para procesar
        if st.button("💾 Configurar Todos los Saldos", use_container_width=True, type="primary"):
            procesar_saldos_multiples(backend_url, periodo['id_periodo'], st.session_state.saldos_multiples)

def procesar_carga_masiva(backend_url: str, id_periodo: int, df: pd.DataFrame):
    """Procesar carga masiva de saldos"""
    
    try:
        # Obtener información de cuentas
        response_cuentas = requests.get(f"{backend_url}/api/catalogo-cuentas")
        cuentas = response_cuentas.json() if response_cuentas.status_code == 200 else []
        cuentas_dict = {c['codigo_cuenta']: c for c in cuentas}
        
        resultados = {"exitosos": 0, "errores": 0, "detalles_errores": []}
        
        with st.spinner(f"Procesando {len(df)} registros..."):
            for index, row in df.iterrows():
                try:
                    codigo_cuenta = str(row['codigo_cuenta']).strip()
                    saldo_inicial = float(row['saldo_inicial'])
                    descripcion = str(row.get('descripcion', '')).strip() if pd.notna(row.get('descripcion')) else None
                    
                    if codigo_cuenta in cuentas_dict and saldo_inicial != 0:
                        # Determinar naturaleza del saldo según tipo de cuenta
                        tipo_cuenta = cuentas_dict[codigo_cuenta].get('tipo_cuenta', '')
                        if tipo_cuenta in ['Activo', 'Egreso']:
                            naturaleza_saldo = 'DEUDOR' if saldo_inicial > 0 else 'ACREEDOR'
                        else:  # Pasivo, Capital, Ingreso
                            naturaleza_saldo = 'ACREEDOR' if saldo_inicial > 0 else 'DEUDOR'
                        
                        datos_saldo = {
                            "id_periodo": id_periodo,
                            "id_cuenta": cuentas_dict[codigo_cuenta]['id_cuenta'],
                            "saldo_inicial": abs(saldo_inicial),
                            "naturaleza_saldo": naturaleza_saldo,
                            "observaciones": descripcion
                        }
                        
                        response = requests.post(f"{backend_url}/api/balance-inicial", json=datos_saldo)
                        
                        if response.status_code == 201:
                            resultados["exitosos"] += 1
                        else:
                            resultados["errores"] += 1
                            resultados["detalles_errores"].append(f"Fila {index+1}: {response.json().get('detail', 'Error')}")
                    else:
                        resultados["errores"] += 1
                        resultados["detalles_errores"].append(f"Fila {index+1}: Cuenta '{codigo_cuenta}' no encontrada o saldo cero")
                        
                except Exception as e:
                    resultados["errores"] += 1
                    resultados["detalles_errores"].append(f"Fila {index+1}: {str(e)}")
        
        # Mostrar resultados
        if resultados["exitosos"] > 0:
            st.success(f"✅ {resultados['exitosos']} saldos configurados exitosamente")
        
        if resultados["errores"] > 0:
            st.error(f"❌ {resultados['errores']} errores encontrados")
            with st.expander("Ver detalles de errores"):
                for error in resultados["detalles_errores"]:
                    st.text(error)
        
        if resultados["exitosos"] > 0:
            st.rerun()
            
    except Exception as e:
        st.error(f"Error al procesar carga masiva: {e}")

def procesar_saldos_multiples(backend_url: str, id_periodo: int, saldos: List[Dict]):
    """Procesar saldos múltiples"""
    
    try:
        resultados = {"exitosos": 0, "errores": 0, "detalles_errores": []}
        
        with st.spinner(f"Configurando {len(saldos)} saldos..."):
            for saldo in saldos:
                try:
                    # Determinar naturaleza del saldo según tipo de cuenta
                    tipo_cuenta = saldo.get('tipo_cuenta', '')
                    saldo_valor = saldo['saldo_inicial']
                    if tipo_cuenta in ['Activo', 'Egreso']:
                        naturaleza_saldo = 'DEUDOR' if saldo_valor > 0 else 'ACREEDOR'
                    else:  # Pasivo, Capital, Ingreso
                        naturaleza_saldo = 'ACREEDOR' if saldo_valor > 0 else 'DEUDOR'
                    
                    datos_saldo = {
                        "id_periodo": id_periodo,
                        "id_cuenta": saldo['id_cuenta'],
                        "saldo_inicial": abs(saldo_valor),
                        "naturaleza_saldo": naturaleza_saldo,
                        "observaciones": saldo['descripcion'] if saldo['descripcion'] else None
                    }
                    
                    response = requests.post(f"{backend_url}/api/balance-inicial", json=datos_saldo)
                    
                    if response.status_code == 201:
                        resultados["exitosos"] += 1
                    else:
                        resultados["errores"] += 1
                        resultados["detalles_errores"].append(
                            f"{saldo['codigo_cuenta']}: {response.json().get('detail', 'Error')}"
                        )
                        
                except Exception as e:
                    resultados["errores"] += 1
                    resultados["detalles_errores"].append(f"{saldo['codigo_cuenta']}: {str(e)}")
        
        # Mostrar resultados
        if resultados["exitosos"] > 0:
            st.success(f"✅ {resultados['exitosos']} saldos configurados exitosamente")
            st.session_state.saldos_multiples = []  # Limpiar lista
        
        if resultados["errores"] > 0:
            st.error(f"❌ {resultados['errores']} errores encontrados")
            with st.expander("Ver detalles de errores"):
                for error in resultados["detalles_errores"]:
                    st.text(error)
        
        if resultados["exitosos"] > 0:
            st.rerun()
            
    except Exception as e:
        st.error(f"Error al procesar saldos múltiples: {e}")

def consultar_balance_inicial(backend_url: str):
    """Consultar balance inicial configurado"""
    
    st.subheader("📋 Consultar Balance Inicial")
    
    # Selección de período
    try:
        response_periodos = requests.get(f"{backend_url}/api/periodos")
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
        # Construir parámetros
        params = {}
        if tipo_filtro != "Todos":
            params["tipo_cuenta"] = tipo_filtro
        if solo_con_saldo:
            params["solo_con_saldo"] = True
        
        with st.spinner("Consultando balance inicial..."):
            response = requests.get(f"{backend_url}/api/balance-inicial/periodo/{id_periodo}", params=params)
        
        if response.status_code == 200:
            saldos = response.json()
            
            if saldos:
                # Convertir a DataFrame
                df_saldos = pd.DataFrame(saldos)
                
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
                diferencia = activos - pasivos - capital
                
                st.markdown("### ⚖️ Validación Ecuación Contable")
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Activos", f"${activos:,.2f}")
                
                with col2:
                    st.metric("Pasivos", f"${pasivos:,.2f}")
                
                with col3:
                    st.metric("Capital", f"${capital:,.2f}")
                
                with col4:
                    st.metric("Diferencia", f"${diferencia:,.2f}")
                
                if abs(diferencia) > 0.01:
                    st.error("❌ La ecuación contable no está balanceada (Activos ≠ Pasivos + Capital)")
                else:
                    st.success("✅ Ecuación contable balanceada correctamente")
                
                # Tabla detallada
                st.markdown("### 📋 Detalle de Saldos Iniciales")
                
                # Formatear para visualización
                df_display = df_saldos.copy()
                df_display['saldo_inicial'] = df_display['saldo_inicial'].apply(lambda x: f"${x:,.2f}")
                df_display['fecha_configuracion'] = pd.to_datetime(df_display['fecha_configuracion']).dt.strftime('%d/%m/%Y')
                
                # Seleccionar columnas a mostrar
                columnas_mostrar = ['codigo_cuenta', 'nombre_cuenta', 'tipo_cuenta', 'saldo_inicial', 'descripcion', 'fecha_configuracion']
                nombres_columnas = ['Código', 'Nombre Cuenta', 'Tipo', 'Saldo Inicial', 'Descripción', 'Fecha Config.']
                
                df_final = df_display[columnas_mostrar].copy()
                df_final.columns = nombres_columnas
                
                st.dataframe(df_final, use_container_width=True, hide_index=True)
                
                # Opciones de descarga y edición
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    # Descargar CSV
                    csv = df_final.to_csv(index=False)
                    st.download_button(
                        label="📥 Descargar CSV",
                        data=csv,
                        file_name=f"balance_inicial_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )
                
                with col2:
                    # Opción para editar saldos
                    if st.button("✏️ Editar Saldos"):
                        st.info("💡 Para editar saldos, ve a la pestaña 'Configurar Saldos' y actualiza las cuentas necesarias")
                
                with col3:
                    # Eliminar todos los saldos del período
                    if st.button("🗑️ Limpiar Balance", help="Eliminar todos los saldos de este período"):
                        if st.button("⚠️ Confirmar eliminación", type="primary"):
                            eliminar_balance_periodo(backend_url, id_periodo)
                
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
        response_periodos = requests.get(f"{backend_url}/api/periodos")
        periodos = response_periodos.json() if response_periodos.status_code == 200 else []
        
        if periodos:
            opciones_periodos = [
                f"{p['descripcion']} ({p['fecha_inicio']} - {p['fecha_fin']})"
                for p in periodos
            ]
            periodo_validacion = st.selectbox("Período a validar:", opciones_periodos, key="validacion_periodo")
            
            if st.button("🔍 Ejecutar Validación", use_container_width=True):
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
            response = requests.get(f"{backend_url}/api/balance-inicial/validacion/{id_periodo}")
        
        if response.status_code == 200:
            validacion = response.json()
            
            st.markdown("### 📊 Resultados de la Validación")
            
            # Estado general
            if validacion.get('es_valido', False):
                st.success("✅ El balance inicial es válido")
            else:
                st.error("❌ Se encontraron problemas en el balance inicial")
            
            # Ecuación contable
            st.markdown("#### ⚖️ Ecuación Contable")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                activos = validacion.get('totales', {}).get('activos', 0)
                st.metric("Activos", f"${activos:,.2f}")
            
            with col2:
                pasivos = validacion.get('totales', {}).get('pasivos', 0)
                st.metric("Pasivos", f"${pasivos:,.2f}")
            
            with col3:
                capital = validacion.get('totales', {}).get('capital', 0)
                st.metric("Capital", f"${capital:,.2f}")
            
            with col4:
                diferencia = activos - pasivos - capital
                color = "normal" if abs(diferencia) < 0.01 else "inverse"
                st.metric("Diferencia", f"${diferencia:,.2f}")
            
            # Problemas encontrados
            if 'problemas' in validacion and validacion['problemas']:
                st.markdown("#### ⚠️ Problemas Encontrados")
                for problema in validacion['problemas']:
                    st.warning(f"• {problema}")
            
            # Recomendaciones
            if 'recomendaciones' in validacion and validacion['recomendaciones']:
                st.markdown("#### 💡 Recomendaciones")
                for recomendacion in validacion['recomendaciones']:
                    st.info(f"• {recomendacion}")
            
            # Estadísticas adicionales
            if 'estadisticas' in validacion:
                stats = validacion['estadisticas']
                
                st.markdown("#### 📊 Estadísticas")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Cuentas con Saldo", stats.get('cuentas_con_saldo', 0))
                
                with col2:
                    st.metric("Cuentas sin Saldo", stats.get('cuentas_sin_saldo', 0))
                
                with col3:
                    st.metric("Total Configurado", f"${stats.get('total_configurado', 0):,.2f}")
            
        else:
            st.error(f"Error al ejecutar validación: {response.status_code}")
            
    except Exception as e:
        st.error(f"Error en validación: {e}")