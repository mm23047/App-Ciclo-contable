"""
Página Streamlit para gestionar Transacciones.
Proporciona formularios para crear, editar y listar transacciones.
"""
import streamlit as st
import requests
import pandas as pd
from datetime import datetime, date
import plotly.express as px
import plotly.graph_objects as go

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
    """Renderizar la página de gestión de transacciones"""
    st.title("💼 Gestión de Transacciones Contables")
    st.markdown("---")
    
    # Mostrar transacción actual si existe
    if 'transaccion_actual' in st.session_state and st.session_state.transaccion_actual:
        st.success(f"✅ Transacción Activa: **ID {st.session_state.transaccion_actual}** | Puedes crear asientos en el módulo de Asientos")
    
    # Tabs para mejor organización
    tab1, tab2, tab3 = st.tabs(["📝 Nueva Transacción", "📋 Lista de Transacciones", "📊 Resumen"])
    
    with tab1:
        create_transaction_form(backend_url)
    
    with tab2:
        # Formulario de edición (solo si hay una transacción seleccionada para editar)
        if 'edit_transaction_id' in st.session_state and 'edit_transaction_data' in st.session_state:
            with st.container():
                st.markdown("### ✏️ Modificar Transacción")
                edit_transaction_form(backend_url)
                st.markdown("---")
        
        list_transactions(backend_url)
    
    with tab3:
        show_transaction_summary(backend_url)

def create_transaction_form(backend_url: str):
    """Formulario para crear una nueva transacción"""
    st.markdown("### ➕ Crear Nueva Transacción")
    st.markdown("Registra una nueva operación contable en el sistema")
    
    # Cargar períodos disponibles
    periods = load_periods(backend_url)
    
    with st.form("create_transaction", clear_on_submit=True):
        # Información principal en tarjeta visual
        st.markdown("#### 📌 Información Principal")
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            descripcion = st.text_area(
                "📝 Descripción *",
                placeholder="Ej: Venta de productos, Pago de nómina, Compra de activos...",
                height=100,
                help="Descripción detallada de la transacción"
            )
        
        with col2:
            fecha_transaccion = st.date_input(
                "📅 Fecha de Transacción *",
                value=date.today(),
                help="Fecha cuando ocurrió la transacción"
            )
            
            tipo = st.selectbox(
                "🔄 Tipo de Transacción *",
                ["INGRESO", "EGRESO"],
                help="INGRESO: Entradas de dinero | EGRESO: Salidas de dinero"
            )
        
        with col3:
            moneda = st.selectbox(
                "💱 Moneda",
                ["USD", "EUR", "MXN", "COP"],
                index=0,
                help="Moneda de la transacción"
            )
        
        st.markdown("---")
        st.markdown("#### 🏢 Clasificación y Control")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Selector de período mejorado con iconos
            if periods:
                period_options = {}
                for period in periods:
                    icon = "📅"
                    display_text = f"{icon} {period['tipo_periodo']} | {period['fecha_inicio']} → {period['fecha_fin']}"
                    period_options[display_text] = period['id_periodo']
                
                selected_period_display = st.selectbox(
                    "📆 Período Contable *",
                    options=list(period_options.keys()),
                    help="Selecciona el período contable para la transacción"
                )
                selected_period_id = period_options[selected_period_display]
            else:
                st.error("❌ No se pudieron cargar los períodos disponibles")
                selected_period_id = None
        
        with col2:
            categoria = st.selectbox(
                "🏷️ Categoría",
                [
                    "VENTA",
                    "COMPRA",
                    "NÓMINA",
                    "SERVICIOS",
                    "IMPUESTOS",
                    "INVERSIÓN",
                    "PRÉSTAMO",
                    "ACTIVOS",
                    "GASTOS ADMINISTRATIVOS",
                    "GASTOS OPERATIVOS",
                    "OTROS"
                ],
                index=0,
                help="Categoría para clasificar la transacción"
            )
        
        with col3:
            usuario_creacion = st.text_input(
                "👤 Usuario *",
                placeholder="Nombre del usuario",
                help="Usuario responsable de la transacción"
            )
        
        # Campos opcionales en expander con mejor diseño
        with st.expander("📎 Información Adicional (Opcional)"):
            col1, col2 = st.columns(2)
            
            with col1:
                numero_referencia = st.text_input(
                    "🔢 Número de Referencia",
                    placeholder="Ej: FAC-2024-001, REF-12345",
                    help="Número de referencia externo o de documento"
                )
            
            with col2:
                observaciones = st.text_area(
                    "📋 Observaciones",
                    height=80,
                    placeholder="Notas adicionales sobre la transacción...",
                    help="Observaciones o comentarios adicionales"
                )
        
        st.markdown("---")
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col2:
            clear_button = st.form_submit_button("🔄 Limpiar", type="secondary", use_container_width=True)
        
        with col3:
            submitted = st.form_submit_button("✅ Crear Transacción", type="primary", use_container_width=True)
        
        if submitted:
            if not descripcion or not usuario_creacion:
                st.error("❌ Descripción y Usuario son campos obligatorios")
                return
            
            if not selected_period_id:
                st.error("❌ No se pudo seleccionar un período válido")
                return
            
            # Combine date with current time for datetime
            fecha_datetime = datetime.combine(fecha_transaccion, datetime.now().time())
            
            # Prepare request data
            transaction_data = {
                "fecha_transaccion": fecha_datetime.isoformat(),
                "descripcion": descripcion,
                "tipo": tipo,
                "moneda": moneda,
                "usuario_creacion": usuario_creacion,
                "id_periodo": selected_period_id,
                "categoria": categoria if categoria else None,
                "numero_referencia": numero_referencia if numero_referencia else None,
                "observaciones": observaciones if observaciones else None
            }
            
            try:
                response = requests.post(
                    f"{backend_url}/api/transacciones/",
                    json=transaction_data,
                    timeout=10
                )
                
                if response.status_code == 201:
                    data = response.json()
                    transaction_id = data.get("id_transaccion")
                    
                    # Set current transaction in session state
                    st.session_state.transaccion_actual = transaction_id
                    
                    st.success(f"✅ Transacción creada exitosamente (ID: {transaction_id})")
                    st.info("💡 Ahora puedes crear asientos para esta transacción")
                    st.rerun()
                else:
                    st.error(f"❌ Error al crear transacción: {response.text}")
                    
            except requests.exceptions.RequestException as e:
                st.error(f"❌ Error de conexión: {str(e)}")

def edit_transaction_form(backend_url: str):
    """Formulario para modificar una transacción existente"""
    transaction_data = st.session_state.edit_transaction_data
    transaction_id = st.session_state.edit_transaction_id
    
    # Cargar períodos para mostrar información descriptiva
    periods = load_periods(backend_url)
    
    st.info(f"🔄 Modificando Transacción ID: {transaction_id}")
    
    # Botón para cancelar edición
    if st.button("❌ Cancelar Edición"):
        if 'edit_transaction_id' in st.session_state:
            del st.session_state.edit_transaction_id
        if 'edit_transaction_data' in st.session_state:
            del st.session_state.edit_transaction_data
        st.rerun()
    
    with st.form("edit_transaction"):
        col1, col2 = st.columns(2)
        
        with col1:
            # Parse the existing date from ISO format
            try:
                existing_date = datetime.fromisoformat(transaction_data['fecha_transaccion'].replace('Z', '+00:00'))
            except (ValueError, KeyError):
                # Fallback to current date if parsing fails
                existing_date = datetime.now()
            
            fecha_transaccion = st.date_input(
                "Fecha de Transacción",
                value=existing_date.date(),
                help="Fecha cuando ocurrió la transacción"
            )
            
            tipo = st.selectbox(
                "Tipo de Transacción",
                ["INGRESO", "EGRESO"],
                index=0 if transaction_data.get('tipo') == 'INGRESO' else 1,
                help="Tipo de transacción contable"
            )
            
            usuario_creacion = st.text_input(
                "Usuario",
                value=transaction_data.get('usuario_creacion', ''),
                help="Usuario que crea la transacción"
            )
        
        with col2:
            descripcion = st.text_area(
                "Descripción",
                value=transaction_data.get('descripcion', ''),
                height=100,
                help="Descripción completa de la transacción"
            )
            
            # List of common currencies with current value selected
            currencies = ["USD", "EUR", "MXN", "COP"]
            current_currency = transaction_data.get('moneda', 'USD')
            currency_index = currencies.index(current_currency) if current_currency in currencies else 0
            
            moneda = st.selectbox(
                "Moneda",
                currencies,
                index=currency_index,
                help="Moneda de la transacción"
            )
            
            # Display current period information in a more user-friendly way
            current_period_id = transaction_data.get('id_periodo', 'N/A')
            if periods and current_period_id != 'N/A':
                # Find the current period in the list
                current_period = next((p for p in periods if p['id_periodo'] == current_period_id), None)
                if current_period:
                    period_display = f"{current_period['tipo_periodo']} {current_period['fecha_inicio']} - {current_period['fecha_fin']}"
                    st.info(f"📅 Período actual: {period_display} (ID: {current_period_id})")
                else:
                    st.info(f"📅 Período actual: ID {current_period_id} (no encontrado en períodos activos)")
            else:
                st.info(f"📅 Período actual: ID {current_period_id}")
        
        submitted = st.form_submit_button("💾 Guardar Cambios", type="primary")
        
        if submitted:
            if not descripcion or not usuario_creacion:
                st.error("❌ Descripción y Usuario son campos obligatorios")
                return
            
            # Combine date with existing time for datetime
            existing_time = existing_date.time()
            fecha_datetime = datetime.combine(fecha_transaccion, existing_time)
            
            # Prepare update data - only include fields that can be modified
            update_data = {
                "fecha_transaccion": fecha_datetime.isoformat(),
                "descripcion": descripcion,
                "tipo": tipo,
                "moneda": moneda,
                "usuario_creacion": usuario_creacion
                # Note: id_periodo is not included as per requirements
            }
            
            edit_transaction(backend_url, transaction_id, update_data)

def list_transactions(backend_url: str):
    """Listar transacciones existentes en una tabla"""
    st.markdown("### 📊 Transacciones Registradas")
    
    try:
        response = requests.get(f"{backend_url}/api/transacciones/", timeout=10)
        
        if response.status_code == 200:
            transactions = response.json()
            
            if not transactions:
                st.info("📭 No hay transacciones registradas. Crea tu primera transacción en la pestaña 'Nueva Transacción'.")
                return
            
            # Mostrar cantidad total
            st.metric("📈 Total de Transacciones", len(transactions))
            
            # Filtros
            col1, col2, col3 = st.columns(3)
            
            with col1:
                filter_tipo = st.selectbox(
                    "🔍 Filtrar por Tipo",
                    ["Todos", "INGRESO", "EGRESO"],
                    key="filter_tipo_trans"
                )
            
            with col2:
                filter_moneda = st.selectbox(
                    "💱 Filtrar por Moneda",
                    ["Todas", "USD", "EUR", "MXN", "COP"],
                    key="filter_moneda_trans"
                )
            
            with col3:
                search_term = st.text_input(
                    "🔎 Buscar",
                    placeholder="Buscar por descripción...",
                    key="search_trans"
                )
            
            # Aplicar filtros
            filtered_transactions = transactions
            if filter_tipo != "Todos":
                filtered_transactions = [t for t in filtered_transactions if t.get('tipo') == filter_tipo]
            if filter_moneda != "Todas":
                filtered_transactions = [t for t in filtered_transactions if t.get('moneda') == filter_moneda]
            if search_term:
                filtered_transactions = [t for t in filtered_transactions if search_term.lower() in t.get('descripcion', '').lower()]
            
            # Convert to DataFrame for display
            df = pd.DataFrame(filtered_transactions)
            
            # Format datetime columns
            if not df.empty:
                try:
                    df['fecha_transaccion'] = pd.to_datetime(df['fecha_transaccion'], format='mixed').dt.strftime('%Y-%m-%d %H:%M')
                    df['fecha_creacion'] = pd.to_datetime(df['fecha_creacion'], format='mixed').dt.strftime('%Y-%m-%d %H:%M')
                except:
                    df['fecha_transaccion'] = pd.to_datetime(df['fecha_transaccion'], infer_datetime_format=True).dt.strftime('%Y-%m-%d %H:%M')
                    df['fecha_creacion'] = pd.to_datetime(df['fecha_creacion'], infer_datetime_format=True).dt.strftime('%Y-%m-%d %H:%M')
                
                # Añadir columna de estado visual
                df['Estado'] = df['tipo'].apply(lambda x: '🟢 Ingreso' if x == 'INGRESO' else '🔴 Egreso')
            
            # Display table con estilo
            st.dataframe(
                df[['id_transaccion', 'fecha_transaccion', 'descripcion', 'Estado', 'moneda', 'usuario_creacion', 'categoria']],
                column_config={
                    "id_transaccion": st.column_config.NumberColumn("ID", width="small"),
                    "fecha_transaccion": st.column_config.TextColumn("📅 Fecha", width="medium"),
                    "descripcion": st.column_config.TextColumn("📝 Descripción", width="large"),
                    "Estado": st.column_config.TextColumn("📊 Tipo", width="small"),
                    "moneda": st.column_config.TextColumn("💱 Moneda", width="small"),
                    "usuario_creacion": st.column_config.TextColumn("👤 Usuario", width="medium"),
                    "categoria": st.column_config.TextColumn("🏷️ Categoría", width="medium"),
                },
                hide_index=True,
                use_container_width=True
            )
            
            st.markdown("---")
            st.markdown("### ⚙️ Acciones")
            
            # Action buttons for each transaction
            col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
            
            with col1:
                selected_id = st.selectbox(
                    "Seleccionar Transacción para Acciones",
                    options=[None] + [t['id_transaccion'] for t in filtered_transactions],
                    format_func=lambda x: "🔽 Selecciona una transacción..." if x is None else f"ID: {x}",
                    key="select_trans_action"
                )
            
            with col2:
                if st.button("🎯 Usar para Asientos", use_container_width=True) and selected_id:
                    st.session_state.transaccion_actual = selected_id
                    st.success(f"✅ Transacción {selected_id} seleccionada")
                    st.balloons()
                    st.rerun()
            
            with col3:
                if st.button("✏️ Modificar", type="secondary", use_container_width=True) and selected_id:
                    selected_transaction = next((t for t in filtered_transactions if t['id_transaccion'] == selected_id), None)
                    if selected_transaction:
                        st.session_state.edit_transaction_id = selected_id
                        st.session_state.edit_transaction_data = selected_transaction
                        st.rerun()
            
            with col4:
                if st.button("🗑️ Eliminar", type="secondary", use_container_width=True) and selected_id:
                    if st.checkbox(f"⚠️ Confirmar eliminación de ID {selected_id}", key=f"confirm_del_{selected_id}"):
                        delete_transaction(backend_url, selected_id)
        else:
            st.error(f"❌ Error al cargar transacciones: {response.text}")
            
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Error de conexión: {str(e)}")

def show_transaction_summary(backend_url: str):
    """Mostrar resumen estadístico de transacciones"""
    st.markdown("### 📊 Resumen y Estadísticas")
    
    try:
        response = requests.get(f"{backend_url}/api/transacciones/", timeout=10)
        
        if response.status_code == 200:
            transactions = response.json()
            
            if not transactions:
                st.info("📭 No hay transacciones para mostrar estadísticas")
                return
            
            df = pd.DataFrame(transactions)
            
            # Métricas principales
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("📝 Total Transacciones", len(transactions))
            
            with col2:
                ingresos = len([t for t in transactions if t.get('tipo') == 'INGRESO'])
                st.metric("🟢 Ingresos", ingresos)
            
            with col3:
                egresos = len([t for t in transactions if t.get('tipo') == 'EGRESO'])
                st.metric("🔴 Egresos", egresos)
            
            with col4:
                usuarios_unicos = len(set(t.get('usuario_creacion') for t in transactions if t.get('usuario_creacion')))
                st.metric("👥 Usuarios", usuarios_unicos)
            
            st.markdown("---")
            
            # Gráficos con plotly para mejor visualización
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 📊 Distribución por Tipo")
                tipo_count = df['tipo'].value_counts().reset_index()
                tipo_count.columns = ['Tipo', 'Cantidad']
                
                fig_tipo = px.pie(
                    tipo_count,
                    values='Cantidad',
                    names='Tipo',
                    color='Tipo',
                    color_discrete_map={'INGRESO': '#28a745', 'EGRESO': '#dc3545'},
                    hole=0.4
                )
                fig_tipo.update_traces(textposition='inside', textinfo='percent+label+value')
                fig_tipo.update_layout(
                    showlegend=True,
                    height=300,
                    margin=dict(t=0, b=0, l=0, r=0)
                )
                st.plotly_chart(fig_tipo, use_container_width=True)
            
            with col2:
                st.markdown("#### 💱 Distribución por Moneda")
                moneda_count = df['moneda'].value_counts().reset_index()
                moneda_count.columns = ['Moneda', 'Cantidad']
                
                fig_moneda = px.bar(
                    moneda_count,
                    x='Moneda',
                    y='Cantidad',
                    color='Moneda',
                    text='Cantidad',
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                fig_moneda.update_traces(texttemplate='%{text}', textposition='outside')
                fig_moneda.update_layout(
                    showlegend=False,
                    height=300,
                    margin=dict(t=20, b=0, l=0, r=0),
                    yaxis_title='Cantidad de Transacciones',
                    xaxis_title=''
                )
                st.plotly_chart(fig_moneda, use_container_width=True)
            
            # Gráfico de tendencia temporal
            if 'fecha_transaccion' in df.columns:
                st.markdown("#### 📈 Tendencia Temporal")
                df['fecha'] = pd.to_datetime(df['fecha_transaccion'], format='ISO8601').dt.date
                tendencia = df.groupby(['fecha', 'tipo']).size().reset_index(name='cantidad')
                
                fig_tendencia = px.line(
                    tendencia,
                    x='fecha',
                    y='cantidad',
                    color='tipo',
                    markers=True,
                    color_discrete_map={'INGRESO': '#28a745', 'EGRESO': '#dc3545'}
                )
                fig_tendencia.update_layout(
                    height=300,
                    xaxis_title='Fecha',
                    yaxis_title='Cantidad de Transacciones',
                    hovermode='x unified',
                    legend=dict(title='Tipo', orientation='h', y=1.1, x=0.5, xanchor='center')
                )
                st.plotly_chart(fig_tendencia, use_container_width=True)
                st.markdown("---")
            
            # Tabla de actividad por usuario
            st.markdown("#### 👥 Actividad por Usuario")
            user_activity = df.groupby('usuario_creacion').agg({
                'id_transaccion': 'count',
                'tipo': lambda x: (x == 'INGRESO').sum(),
            }).rename(columns={
                'id_transaccion': 'Total',
                'tipo': 'Ingresos'
            })
            user_activity['Egresos'] = df[df['tipo'] == 'EGRESO'].groupby('usuario_creacion').size()
            user_activity = user_activity.fillna(0).astype(int)
            
            st.dataframe(
                user_activity,
                column_config={
                    "Total": st.column_config.NumberColumn("📝 Total Transacciones"),
                    "Ingresos": st.column_config.NumberColumn("🟢 Ingresos"),
                    "Egresos": st.column_config.NumberColumn("🔴 Egresos"),
                },
                use_container_width=True
            )
            
    except Exception as e:
        st.error(f"❌ Error al generar resumen: {str(e)}")

def delete_transaction(backend_url: str, transaction_id: int):
    """Eliminar una transacción"""
    try:
        response = requests.delete(f"{backend_url}/api/transacciones/{transaction_id}", timeout=10)
        
        if response.status_code == 204:
            st.success(f"✅ Transacción {transaction_id} eliminada")
            # Clear from session if it was the current one
            if st.session_state.transaccion_actual == transaction_id:
                st.session_state.transaccion_actual = None
            st.rerun()
        else:
            st.error(f"❌ Error al eliminar transacción: {response.text}")
            
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Error de conexión: {str(e)}")

def edit_transaction(backend_url: str, transaction_id: int, transaction_data: dict):
    """Modificar una transacción existente"""
    try:
        response = requests.put(
            f"{backend_url}/api/transacciones/{transaction_id}", 
            json=transaction_data, 
            timeout=10
        )
        
        if response.status_code == 200:
            st.success(f"✅ Transacción {transaction_id} modificada exitosamente")
            # Limpiar el estado de edición
            if 'edit_transaction_id' in st.session_state:
                del st.session_state.edit_transaction_id
            if 'edit_transaction_data' in st.session_state:
                del st.session_state.edit_transaction_data
            st.rerun()
        else:
            st.error(f"❌ Error al modificar transacción: {response.text}")
            
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Error de conexión: {str(e)}")
