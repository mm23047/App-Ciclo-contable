"""
Página Streamlit para gestionar Asientos Contables.
Proporciona formularios para crear, editar y listar asientos contables.
Solo accesible cuando se ha seleccionado una transacción.
"""
import streamlit as st
import requests
import pandas as pd
from decimal import Decimal
from typing import Optional, List, Dict

def render_page(backend_url: str):
    """Renderizar la página de gestión de asientos contables"""
    st.title("📝 Gestión de Asientos Contables")
    st.markdown("---")
    
    # Check if a transaction is selected
    current_transaction = st.session_state.get("transaccion_actual")
    
    if not current_transaction:
        st.warning("⚠️ **Debes seleccionar una transacción antes de crear asientos**")
        st.info("💡 **Pasos a seguir:**")
        st.markdown("""
        1. Ve a la página de **Transacciones**
        2. Crea una nueva transacción o selecciona una existente en la lista
        3. La transacción seleccionada se activará automáticamente para crear asientos
        4. Regresa a esta página para crear los asientos contables
        """)
        
        # Botón directo a transacciones
        if st.button("📋 Ir a Transacciones", type="primary"):
            st.info("Navega a Transacciones usando el menú lateral")
        return
    
    # Mostrar info de transacción actual
    st.success(f"✅ **Trabajando con Transacción ID: {current_transaction}**")
    
    # Botón para cambiar de transacción
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("🔄 Cambiar Transacción", type="secondary"):
            st.session_state.transaccion_actual = None
            st.rerun()
    
    # Load available accounts
    accounts = load_accounts(backend_url)
    
    # Si hay asiento en modo edición, mostrar SOLO el formulario de edición
    if 'edit_asiento_id' in st.session_state and st.session_state.edit_asiento_id:
        st.markdown("---")
        create_asiento_form(backend_url, current_transaction, accounts)
        st.markdown("---")
        st.info("💡 **Sugerencia**: Para ver la lista de asientos, primero completa o cancela la edición")
        return  # No mostrar las tabs cuando está editando
    
    # Tabs para mejor organización
    tab1, tab2, tab3 = st.tabs(["➕ Nuevo Asiento", "📋 Asientos Registrados", "📊 Validación"])
    
    with tab1:
        create_asiento_form(backend_url, current_transaction, accounts)
    
    with tab2:
        list_asientos_for_transaction(backend_url, current_transaction, accounts)
    
    with tab3:
        validate_asientos(backend_url, current_transaction)

def load_accounts(backend_url: str) -> List[Dict]:
    """Cargar cuentas disponibles desde la API"""
    try:
        response = requests.get(f"{backend_url}/api/catalogo-cuentas/", timeout=10)
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"❌ Error al cargar catálogo de cuentas: {response.text}")
            return []
            
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Error de conexión al cargar cuentas: {str(e)}")
        return []

def create_asiento_form(backend_url: str, transaction_id: int, accounts: List[Dict]):
    """Formulario para crear o editar un asiento contable"""
    # Detectar modo edición
    modo_edicion = 'edit_asiento_id' in st.session_state and st.session_state.edit_asiento_id
    
    if modo_edicion:
        st.markdown("### ✏️ Modificar Asiento Contable")
        st.info(f"🔄 Editando Asiento ID: {st.session_state.edit_asiento_id}")
        asiento_data = st.session_state.edit_asiento_data
    else:
        st.markdown("### ➕ Crear Nuevo Asiento Contable")
        st.markdown("Registra los movimientos contables de la transacción")
    
    if not accounts:
        st.error("❌ No hay cuentas disponibles. Crea cuentas en el catálogo primero.")
        st.info("💡 Ve al módulo de **Catálogo de Cuentas** para crear las cuentas necesarias")
        return
    
    # Botón para cancelar edición
    if modo_edicion:
        if st.button("❌ Cancelar Edición", type="secondary"):
            if 'edit_asiento_id' in st.session_state:
                del st.session_state.edit_asiento_id
            if 'edit_asiento_data' in st.session_state:
                del st.session_state.edit_asiento_data
            st.rerun()
    
    with st.form("create_asiento", clear_on_submit=True):
        # Sección de cuenta
        st.markdown("#### 🏦 Selección de Cuenta")
        
        # Account selection con búsqueda mejorada
        account_options = {
            f"{acc['codigo_cuenta']} | {acc['nombre_cuenta']} ({acc['tipo_cuenta']})": acc['id_cuenta']
            for acc in accounts
            if acc.get('estado') == 'ACTIVA'  # Solo cuentas activas
        }
        
        if not account_options:
            st.error("❌ No hay cuentas activas disponibles")
            st.stop()
        
        # Pre-seleccionar cuenta en modo edición
        default_index = 0
        if modo_edicion:
            current_account_id = asiento_data.get('id_cuenta')
            for idx, (display, id_val) in enumerate(account_options.items()):
                if id_val == current_account_id:
                    default_index = idx
                    break
        
        selected_account_display = st.selectbox(
            "📋 Cuenta Contable *",
            options=list(account_options.keys()),
            index=default_index,
            help="Selecciona la cuenta para registrar el movimiento"
        )
        
        selected_account_id = account_options[selected_account_display]
        
        st.markdown("---")
        st.markdown("#### 💰 Detalle del Movimiento")
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            # Determinar tipo y monto en modo edición
            if modo_edicion:
                current_debe = float(asiento_data.get('debe', 0))
                current_haber = float(asiento_data.get('haber', 0))
                default_type_index = 0 if current_debe > 0 else 1
                default_amount = current_debe if current_debe > 0 else current_haber
            else:
                default_type_index = 0
                default_amount = 100.00
            
            # Amount type selection con cards visuales
            st.markdown("**Tipo de Movimiento:**")
            amount_type = st.radio(
                "Selecciona el tipo",
                ["Débito (Debe)", "Crédito (Haber)"],
                index=default_type_index,
                help="📘 Débito: Aumenta activos/gastos | Disminuye pasivos/ingresos\n📕 Crédito: Disminuye activos/gastos | Aumenta pasivos/ingresos",
                label_visibility="collapsed"
            )
        
        with col2:
            # Amount input
            amount = st.number_input(
                "💵 Monto *",
                min_value=0.01,
                value=float(default_amount),
                step=0.01,
                format="%.2f",
                help="Ingresa el monto del asiento (debe ser mayor que 0)"
            )
            
            # Mostrar el monto formateado
            st.info(f"💰 Monto: **${amount:,.2f}**")
        
        st.markdown("---")
        
        # Optional description
        default_descripcion = asiento_data.get('descripcion_asiento', '') if modo_edicion else ''
        descripcion_asiento = st.text_area(
            "📝 Descripción del Asiento (Opcional)",
            value=default_descripcion,
            height=100,
            placeholder="Ej: Registro de venta al contado, Provisión de gastos, Pago a proveedores...",
            help="Descripción detallada del asiento contable"
        )
        
        st.markdown("---")
        
        # Botones de acción
        if modo_edicion:
            col1, col2 = st.columns([1, 1])
            with col2:
                submitted = st.form_submit_button("💾 Guardar Cambios", type="primary", use_container_width=True)
        else:
            col1, col2, col3 = st.columns([2, 1, 1])
            with col2:
                clear_button = st.form_submit_button("🔄 Limpiar", type="secondary", use_container_width=True)
            with col3:
                submitted = st.form_submit_button("✅ Crear Asiento", type="primary", use_container_width=True)
        
        if submitted:
            # Determine debe/haber based on selection
            es_debito = "Débito" in amount_type
            
            # Prepare request data
            request_data = {
                "id_transaccion": transaction_id,
                "id_cuenta": selected_account_id,
                "debe": float(amount) if es_debito else 0.0,
                "haber": 0.0 if es_debito else float(amount),
                "descripcion_asiento": descripcion_asiento if descripcion_asiento else None
            }
            
            try:
                if modo_edicion:
                    # Actualizar asiento existente
                    response = requests.put(
                        f"{backend_url}/api/asientos/{st.session_state.edit_asiento_id}",
                        json=request_data,
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        st.success(f"✅ Asiento {st.session_state.edit_asiento_id} modificado exitosamente")
                        # Limpiar estado de edición
                        if 'edit_asiento_id' in st.session_state:
                            del st.session_state.edit_asiento_id
                        if 'edit_asiento_data' in st.session_state:
                            del st.session_state.edit_asiento_data
                        st.rerun()
                    else:
                        st.error(f"❌ Error al modificar asiento: {response.text}")
                else:
                    # Crear nuevo asiento
                    response = requests.post(
                        f"{backend_url}/api/asientos/",
                        json=request_data,
                        timeout=10
                    )
                    
                    if response.status_code == 201:
                        data = response.json()
                        asiento_id = data.get("id_asiento")
                        
                        if asiento_id:
                            st.success(f"✅ Asiento creado exitosamente (ID: {asiento_id})")
                            st.rerun()
                        else:
                            st.error("❌ No se pudo obtener el ID del asiento creado")
                    else:
                        st.error(f"❌ Error al crear asiento: {response.text}")
                    
            except requests.exceptions.RequestException as e:
                st.error(f"❌ Error de conexión: {str(e)}")



def list_asientos_for_transaction(backend_url: str, transaction_id: int, accounts: List[Dict]):
    """Listar asientos contables para la transacción actual"""
    try:
        response = requests.get(
            f"{backend_url}/api/asientos/",
            params={"id_transaccion": transaction_id},
            timeout=10
        )
        
        if response.status_code == 200:
            asientos = response.json()
            
            if not asientos:
                st.info("📭 No hay asientos registrados para esta transacción")
                return
            
            # Enrich data with account information
            account_map = {acc['id_cuenta']: acc for acc in accounts}
            
            for asiento in asientos:
                account_info = account_map.get(asiento['id_cuenta'], {})
                asiento['codigo_cuenta'] = account_info.get('codigo_cuenta', 'N/A')
                asiento['nombre_cuenta'] = account_info.get('nombre_cuenta', 'N/A')
                asiento['tipo_cuenta'] = account_info.get('tipo_cuenta', 'N/A')
            
            # Configuración de paginación
            total_asientos = len(asientos)
            
            col_info, col_items = st.columns([3, 1])
            with col_info:
                st.info(f"📊 **Total de asientos:** {total_asientos}")
            with col_items:
                items_per_page = st.selectbox(
                    "Asientos por página:",
                    options=[5, 10, 20, 50, 100],
                    index=1,  # 10 por defecto
                    key="items_per_page_lista"
                )
            
            total_pages = (total_asientos + items_per_page - 1) // items_per_page
            
            # Inicializar página actual
            if 'current_page_lista' not in st.session_state:
                st.session_state.current_page_lista = 1
            
            # Ajustar página si está fuera de rango
            if st.session_state.current_page_lista > total_pages:
                st.session_state.current_page_lista = total_pages
            
            # Calcular índices
            start_idx = (st.session_state.current_page_lista - 1) * items_per_page
            end_idx = min(start_idx + items_per_page, total_asientos)
            
            # Obtener asientos de la página actual
            asientos_pagina = asientos[start_idx:end_idx]
            
            # Convert to DataFrame
            df = pd.DataFrame(asientos_pagina)
            
            # Display table with relevant columns
            display_columns = [
                'id_asiento', 'codigo_cuenta', 'nombre_cuenta', 
                'tipo_cuenta', 'debe', 'haber'
            ]
            
            st.dataframe(
                df[display_columns],
                column_config={
                    "id_asiento": st.column_config.NumberColumn("ID", width="small"),
                    "codigo_cuenta": st.column_config.TextColumn("🔢 Código", width="small"),
                    "nombre_cuenta": st.column_config.TextColumn("📝 Cuenta", width="large"),
                    "tipo_cuenta": st.column_config.TextColumn("🏷️ Tipo", width="small"),
                    "debe": st.column_config.NumberColumn("🟢 Debe", format="$%.2f", width="medium"),
                    "haber": st.column_config.NumberColumn("🔴 Haber", format="$%.2f", width="medium"),
                },
                hide_index=True,
                use_container_width=True
            )
            
            # Mostrar rango
            st.caption(f"Mostrando asientos {start_idx + 1} - {end_idx} de {total_asientos}")
            
            # Controles de paginación (solo abajo)
            if total_pages > 1:
                st.markdown("---")
                col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])
                
                with col1:
                    if st.button("⏮️ Primera", key="first_lista", use_container_width=True, disabled=st.session_state.current_page_lista == 1):
                        st.session_state.current_page_lista = 1
                        st.rerun()
                
                with col2:
                    if st.button("◀️ Anterior", key="prev_lista", use_container_width=True, disabled=st.session_state.current_page_lista == 1):
                        st.session_state.current_page_lista -= 1
                        st.rerun()
                
                with col3:
                    st.markdown(f"<div style='text-align: center; padding: 8px;'><strong>Página {st.session_state.current_page_lista} de {total_pages}</strong></div>", unsafe_allow_html=True)
                
                with col4:
                    if st.button("▶️ Siguiente", key="next_lista", use_container_width=True, disabled=st.session_state.current_page_lista == total_pages):
                        st.session_state.current_page_lista += 1
                        st.rerun()
                
                with col5:
                    if st.button("⏭️ Última", key="last_lista", use_container_width=True, disabled=st.session_state.current_page_lista == total_pages):
                        st.session_state.current_page_lista = total_pages
                        st.rerun()
            
            st.markdown("---")
            
            # Calculate and display totals
            total_debe = sum(float(a['debe']) for a in asientos)
            total_haber = sum(float(a['haber']) for a in asientos)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("💰 Total Débito", f"${total_debe:,.2f}")
            with col2:
                st.metric("💰 Total Crédito", f"${total_haber:,.2f}")
            with col3:
                difference = total_debe - total_haber
                st.metric(
                    "⚖️ Balance", 
                    f"${difference:,.2f}",
                    delta=None if difference == 0 else "⚠️ Desbalanceado"
                )
            
            if difference != 0:
                st.warning("⚠️ Los asientos no están balanceados. El total de débitos debe igual al total de créditos.")
            
            # Delete and edit asiento functionality
            st.markdown("---")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                selected_asiento_id = st.selectbox(
                    "Seleccionar Asiento",
                    options=[None] + [a['id_asiento'] for a in asientos],
                    format_func=lambda x: "Selecciona..." if x is None else f"Asiento ID: {x}"
                )
            
            with col2:
                if st.button("✏️ Modificar Asiento") and selected_asiento_id:
                    # Encontrar el asiento seleccionado para el formulario de edición
                    selected_asiento = next((a for a in asientos if a['id_asiento'] == selected_asiento_id), None)
                    if selected_asiento:
                        st.session_state.edit_asiento_id = selected_asiento_id
                        st.session_state.edit_asiento_data = selected_asiento
                        st.rerun()
            
            with col3:
                if st.button("🗑️ Eliminar Asiento") and selected_asiento_id:
                    delete_asiento(backend_url, selected_asiento_id)
        
        else:
            st.error(f"❌ Error al cargar asientos: {response.text}")
            
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Error de conexión: {str(e)}")

def delete_asiento(backend_url: str, asiento_id: int):
    """Eliminar un asiento contable"""
    try:
        response = requests.delete(f"{backend_url}/api/asientos/{asiento_id}", timeout=10)
        
        if response.status_code == 204:
            st.success(f"✅ Asiento {asiento_id} eliminado")
            st.rerun()
        else:
            st.error(f"❌ Error al eliminar asiento: {response.text}")
            
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Error de conexión: {str(e)}")



def validate_asientos(backend_url: str, transaction_id: int):
    """Validar que los asientos cumplan con la partida doble"""
    st.markdown("### 📊 Validación de Partida Doble")
    st.markdown("Verifica que los asientos cumplan con el principio contable de partida doble")
    
    try:
        response = requests.get(f"{backend_url}/api/asientos/?id_transaccion={transaction_id}", timeout=10)
        
        if response.status_code == 200:
            asientos = response.json()
            
            if not asientos:
                st.info("📭 No hay asientos registrados para validar")
                st.markdown("""
                **💡 Recordatorio:**
                - Cada transacción debe tener al menos 2 asientos
                - El total de débitos debe ser igual al total de créditos
                - Esto garantiza el equilibrio contable
                """)
                return
            
            # Calcular totales
            total_debe = float(sum(float(a['debe']) for a in asientos))
            total_haber = float(sum(float(a['haber']) for a in asientos))
            diferencia = total_debe - total_haber
            
            # Métricas visuales
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    "🟢 Total Débitos",
                    f"${total_debe:,.2f}",
                    help="Suma de todos los débitos"
                )
            
            with col2:
                st.metric(
                    "🔴 Total Créditos",
                    f"${total_haber:,.2f}",
                    help="Suma de todos los créditos"
                )
            
            with col3:
                st.metric(
                    "⚖️ Diferencia",
                    f"${abs(diferencia):,.2f}",
                    delta="Balanceado ✅" if abs(diferencia) < 0.01 else "Desbalanceado ⚠️",
                    delta_color="normal" if abs(diferencia) < 0.01 else "inverse"
                )
            
            st.markdown("---")
            
            # Estado de validación
            if abs(diferencia) < 0.01:
                st.success("✅ **¡Partida Doble Correcta!**")
                st.markdown("""
                Los asientos están correctamente balanceados:
                - ✅ Débitos = Créditos
                - ✅ Principio de partida doble cumplido
                - ✅ La transacción está lista para ser registrada en el libro diario
                """)
                
                # Mostrar resumen
                st.markdown("#### 📋 Resumen de Asientos")
                st.info(f"**Total de asientos:** {len(asientos)}")
                
            else:
                st.error("❌ **Error en Partida Doble**")
                st.markdown(f"""
                Los asientos NO están balanceados:
                - ⚠️ Diferencia de: **${abs(diferencia):,.2f}**
                - ⚠️ {'Faltan créditos' if diferencia > 0 else 'Faltan débitos'}
                - ⚠️ Debes corregir los asientos antes de continuar
                """)
                
                st.warning(f"💡 **Sugerencia:** {'Agrega créditos por $' + f'{diferencia:,.2f}' if diferencia > 0 else 'Agrega débitos por $' + f'{abs(diferencia):,.2f}'}")
            
            # Tabla de asientos para referencia con paginación
            st.markdown("---")
            st.markdown("#### 📋 Detalle de Asientos")
            
            # Configuración de paginación para validación
            total_asientos_val = len(asientos)
            
            col_info_val, col_items_val = st.columns([3, 1])
            with col_info_val:
                st.info(f"📊 **Total de asientos:** {total_asientos_val}")
            with col_items_val:
                items_per_page_val = st.selectbox(
                    "Asientos por página:",
                    options=[5, 10, 20, 50, 100],
                    index=1,  # 10 por defecto
                    key="items_per_page_validacion"
                )
            
            total_pages_val = (total_asientos_val + items_per_page_val - 1) // items_per_page_val
            
            # Inicializar página actual
            if 'current_page_validacion' not in st.session_state:
                st.session_state.current_page_validacion = 1
            
            # Ajustar página si está fuera de rango
            if st.session_state.current_page_validacion > total_pages_val:
                st.session_state.current_page_validacion = total_pages_val
            
            # Calcular índices
            start_idx_val = (st.session_state.current_page_validacion - 1) * items_per_page_val
            end_idx_val = min(start_idx_val + items_per_page_val, total_asientos_val)
            
            # Obtener asientos de la página actual
            asientos_pagina_val = asientos[start_idx_val:end_idx_val]
            
            asientos_df = pd.DataFrame(asientos_pagina_val)
            asientos_df['debe_fmt'] = asientos_df['debe'].apply(lambda x: f"${float(x):,.2f}")
            asientos_df['haber_fmt'] = asientos_df['haber'].apply(lambda x: f"${float(x):,.2f}")
            
            st.dataframe(
                asientos_df[['id_asiento', 'id_cuenta', 'debe_fmt', 'haber_fmt']],
                column_config={
                    "id_asiento": st.column_config.NumberColumn("ID", width="small"),
                    "id_cuenta": st.column_config.NumberColumn("Cuenta", width="small"),
                    "debe_fmt": st.column_config.TextColumn("🟢 Debe", width="medium"),
                    "haber_fmt": st.column_config.TextColumn("🔴 Haber", width="medium"),
                },
                hide_index=True,
                use_container_width=True
            )
            
            # Mostrar rango
            st.caption(f"Mostrando asientos {start_idx_val + 1} - {end_idx_val} de {total_asientos_val}")
            
            # Controles de paginación (solo abajo)
            if total_pages_val > 1:
                st.markdown("---")
                col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])
                
                with col1:
                    if st.button("⏮️ Primera", key="first_val", use_container_width=True, disabled=st.session_state.current_page_validacion == 1):
                        st.session_state.current_page_validacion = 1
                        st.rerun()
                
                with col2:
                    if st.button("◀️ Anterior", key="prev_val", use_container_width=True, disabled=st.session_state.current_page_validacion == 1):
                        st.session_state.current_page_validacion -= 1
                        st.rerun()
                
                with col3:
                    st.markdown(f"<div style='text-align: center; padding: 8px;'><strong>Página {st.session_state.current_page_validacion} de {total_pages_val}</strong></div>", unsafe_allow_html=True)
                
                with col4:
                    if st.button("▶️ Siguiente", key="next_val", use_container_width=True, disabled=st.session_state.current_page_validacion == total_pages_val):
                        st.session_state.current_page_validacion += 1
                        st.rerun()
                
                with col5:
                    if st.button("⏭️ Última", key="last_val", use_container_width=True, disabled=st.session_state.current_page_validacion == total_pages_val):
                        st.session_state.current_page_validacion = total_pages_val
                        st.rerun()
            
    except Exception as e:
        st.error(f"❌ Error al validar asientos: {str(e)}")
