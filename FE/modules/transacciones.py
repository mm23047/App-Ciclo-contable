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

def on_edit_click(transaction_id, transaction_data):
    """Callback cuando se hace click en Modificar"""
    st.session_state.edit_transaction_id = transaction_id
    st.session_state.edit_transaction_data = transaction_data
    # No cambiar pestaña automáticamente, dejar que el usuario navegue

def on_delete_click(transaction_id):
    """Callback cuando se hace click en Eliminar"""
    if 'confirm_delete_id' not in st.session_state:
        st.session_state.confirm_delete_id = None
    st.session_state.confirm_delete_id = transaction_id

def render_page(backend_url: str):
    """Renderizar la página de gestión de transacciones"""
    st.title("💼 Gestión de Transacciones Contables")
    st.markdown("---")
    
    # Mostrar transacción actual si existe con más detalles
    if 'transaccion_actual' in st.session_state and st.session_state.transaccion_actual:
        col_info1, col_info2 = st.columns([3, 1])
        with col_info1:
            st.success(f"✅ **Transacción Activa: ID {st.session_state.transaccion_actual}** | Puedes crear asientos en el módulo de Asientos")
        with col_info2:
            if st.button("🔄 Deseleccionar", key="deselect_trans"):
                st.session_state.transaccion_actual = None
                st.rerun()
    
    # Si hay transacción en modo edición, mostrar SOLO el formulario de edición
    if 'edit_transaction_id' in st.session_state and st.session_state.edit_transaction_id:
        st.markdown("---")
        create_transaction_form(backend_url)
        st.markdown("---")
        st.info("💡 **Sugerencia**: Para ver la lista de transacciones, primero completa o cancela la edición")
        return  # No mostrar las tabs cuando está editando
    
    # Tabs para mejor organización
    tab1, tab2, tab3 = st.tabs(["📝 Nueva Transacción", "📋 Lista de Transacciones", "📊 Resumen"])
    
    with tab1:
        create_transaction_form(backend_url)
    
    with tab2:
        list_transactions(backend_url)
    
    with tab3:
        show_transaction_summary(backend_url)

def create_transaction_form(backend_url: str):
    """Formulario para crear o editar una transacción"""
    # Detectar modo edición
    modo_edicion = 'edit_transaction_id' in st.session_state and st.session_state.edit_transaction_id
    
    if modo_edicion:
        st.markdown("### ✏️ Modificar Transacción")
        st.info(f"🔄 **Editando Transacción ID: {st.session_state.edit_transaction_id}** | Modifica los campos necesarios y haz click en 'Actualizar Transacción'")
        transaction_data = st.session_state.edit_transaction_data
        
        # Botón para cancelar edición
        if st.button("❌ Cancelar Edición", type="secondary"):
            del st.session_state.edit_transaction_id
            del st.session_state.edit_transaction_data
            st.rerun()
    else:
        st.markdown("### ➕ Crear Nueva Transacción")
        st.markdown("Registra una nueva operación contable en el sistema")
        transaction_data = None
    
    # Cargar períodos disponibles
    periods = load_periods(backend_url)
    
    with st.form("create_transaction", clear_on_submit=True):
        # Información principal en tarjeta visual
        st.markdown("#### 📌 Información Principal")
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            # Prellenar descripción si está en modo edición
            default_descripcion = transaction_data.get('descripcion', '') if transaction_data else ''
            descripcion = st.text_area(
                "📝 Descripción *",
                value=default_descripcion,
                placeholder="Ej: Venta de productos, Pago de nómina, Compra de activos...",
                height=100,
                help="Descripción detallada de la transacción"
            )
        
        with col2:
            # Prellenar fecha si está en modo edición
            if transaction_data:
                try:
                    # Manejar diferentes formatos de fecha ISO
                    fecha_str = transaction_data['fecha_transaccion']
                    # Eliminar 'Z' y agregar timezone si existe
                    fecha_str = fecha_str.replace('Z', '+00:00')
                    # Si no tiene microsegundos, agregarlos
                    if 'T' in fecha_str and '.' not in fecha_str.split('T')[1].split('+')[0].split('-')[0]:
                        fecha_str = fecha_str.replace('+', '.000000+').replace('T', 'T', 1).replace('.000000+', '+', 1)
                        if '+' not in fecha_str and '-' not in fecha_str.split('T')[1]:
                            fecha_str = fecha_str.split('T')[0] + 'T' + fecha_str.split('T')[1].split('.')[0] + '.000000'
                    existing_date = datetime.fromisoformat(fecha_str)
                    default_date = existing_date.date()
                except Exception as e:
                    print(f"Error parseando fecha: {e}")
                    default_date = date.today()
            else:
                default_date = date.today()
            
            fecha_transaccion = st.date_input(
                "📅 Fecha de Transacción *",
                value=default_date,
                help="Fecha cuando ocurrió la transacción"
            )
            
            # Prellenar tipo si está en modo edición
            tipo_index = 0
            if transaction_data and transaction_data.get('tipo') == 'EGRESO':
                tipo_index = 1
            
            tipo = st.selectbox(
                "🔄 Tipo de Transacción *",
                ["INGRESO", "EGRESO"],
                index=tipo_index,
                help="INGRESO: Entradas de dinero | EGRESO: Salidas de dinero"
            )
        
        with col3:
            # Prellenar moneda si está en modo edición
            currencies = ["USD", "EUR", "MXN", "COP"]
            moneda_index = 0
            if transaction_data:
                current_currency = transaction_data.get('moneda', 'USD')
                moneda_index = currencies.index(current_currency) if current_currency in currencies else 0
            
            moneda = st.selectbox(
                "💱 Moneda",
                currencies,
                index=moneda_index,
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
                
                # Prellenar período si está en modo edición
                period_index = 0
                if transaction_data and transaction_data.get('id_periodo'):
                    # Buscar índice del período actual
                    for idx, (display, pid) in enumerate(period_options.items()):
                        if pid == transaction_data['id_periodo']:
                            period_index = idx
                            break
                
                selected_period_display = st.selectbox(
                    "📆 Período Contable *",
                    options=list(period_options.keys()),
                    index=period_index,
                    help="Selecciona el período contable para la transacción. Solo se permiten períodos ABIERTOS"
                )
                selected_period_id = period_options[selected_period_display]
            else:
                st.error("❌ No se pudieron cargar los períodos disponibles")
                selected_period_id = None
        
        with col2:
            # Prellenar categoría si está en modo edición
            categorias_lista = [
                "VENTA",
                "COMPRA",
                "NÓMINA",
                "SERVICIOS",
                "IMPUESTOS",
                "INVERSIÓN",
                "PRÉSTAMO",
                "PRESTAMO",
                "ACTIVOS",
                "CAPITAL",
                "GASTOS ADMINISTRATIVOS",
                "GASTOS OPERATIVOS",
                "GASTO",
                "COBRO",
                "PAGO",
                "OTROS"
            ]
            categoria_index = 0
            if transaction_data and transaction_data.get('categoria'):
                try:
                    categoria_index = categorias_lista.index(transaction_data['categoria'])
                except ValueError:
                    categoria_index = 0
            
            categoria = st.selectbox(
                "🏷️ Categoría",
                categorias_lista,
                index=categoria_index,
                help="Categoría para clasificar la transacción (según catálogo permitido)"
            )
        
        with col3:
            # Obtener usuario logueado automáticamente
            if transaction_data:
                # En modo edición, usar el usuario de la transacción
                default_usuario = transaction_data.get('usuario_creacion', '')
            else:
                # En modo creación, usar el usuario logueado
                default_usuario = st.session_state.get('username', '')
            
            usuario_creacion = st.text_input(
                "👤 Usuario *",
                value=default_usuario,
                disabled=not modo_edicion,  # Deshabilitado en modo creación, habilitado en edición
                placeholder="Usuario logueado" if not modo_edicion else "Nombre del usuario",
                help="Usuario responsable de la transacción (detectado automáticamente)"
            )
        
        # Campos opcionales en expander con mejor diseño
        with st.expander("📎 Información Adicional (Opcional)", expanded=modo_edicion):
            col1, col2 = st.columns(2)
            
            with col1:
                # Prellenar número de referencia si está en modo edición
                default_referencia = transaction_data.get('numero_referencia', '') if transaction_data else ''
                numero_referencia = st.text_input(
                    "🔢 Número de Referencia",
                    value=default_referencia,
                    placeholder="Ej: FAC-2024-001, REF-12345",
                    help="Número de referencia externo o de documento"
                )
            
            with col2:
                # Prellenar observaciones si está en modo edición
                default_observaciones = transaction_data.get('observaciones', '') if transaction_data else ''
                observaciones = st.text_area(
                    "📋 Observaciones",
                    value=default_observaciones,
                    height=80,
                    placeholder="Notas adicionales sobre la transacción...",
                    help="Observaciones o comentarios adicionales"
                )
        
        st.markdown("---")
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col2:
            if not modo_edicion:
                clear_button = st.form_submit_button("🔄 Limpiar", type="secondary", use_container_width=True)
        
        with col3:
            if modo_edicion:
                submitted = st.form_submit_button("💾 Actualizar Transacción", type="primary", use_container_width=True)
            else:
                submitted = st.form_submit_button("✅ Crear Transacción", type="primary", use_container_width=True)
        
        if submitted:
            if not descripcion or not usuario_creacion:
                st.error("❌ Descripción y Usuario son campos obligatorios")
                return
            
            if not selected_period_id:
                st.error("❌ No se pudo seleccionar un período válido")
                return
            
            # Combine date with time
            if modo_edicion and transaction_data:
                # Usar tiempo existente si es edición
                try:
                    # Manejar diferentes formatos de fecha ISO
                    fecha_str = transaction_data['fecha_transaccion']
                    fecha_str = fecha_str.replace('Z', '').replace('+00:00', '')
                    # Parsear solo la parte de fecha y hora sin timezone
                    if 'T' in fecha_str:
                        fecha_str = fecha_str.split('+')[0].split('Z')[0]
                    existing_dt = datetime.fromisoformat(fecha_str)
                    fecha_datetime = datetime.combine(fecha_transaccion, existing_dt.time())
                except Exception as e:
                    print(f"Error parseando fecha: {e}")
                    fecha_datetime = datetime.combine(fecha_transaccion, datetime.now().time())
            else:
                # Usar tiempo actual si es creación
                fecha_datetime = datetime.combine(fecha_transaccion, datetime.now().time())
            
            # Prepare request data
            request_data = {
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
                if modo_edicion:
                    # Actualizar transacción existente
                    response = requests.put(
                        f"{backend_url}/api/transacciones/{st.session_state.edit_transaction_id}",
                        json=request_data,
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        st.success(f"✅ Transacción {st.session_state.edit_transaction_id} actualizada exitosamente")
                        # Limpiar estado de edición
                        del st.session_state.edit_transaction_id
                        del st.session_state.edit_transaction_data
                        st.rerun()
                    else:
                        st.error(f"❌ Error al actualizar transacción: {response.text}")
                else:
                    # Crear nueva transacción
                    response = requests.post(
                        f"{backend_url}/api/transacciones/",
                        json=request_data,
                        timeout=10
                    )
                    
                    if response.status_code == 201:
                        data = response.json()
                        transaction_id = data.get("id_transaccion")
                        
                        if transaction_id:
                            # Set current transaction in session state
                            st.session_state.transaccion_actual = transaction_id
                            
                            st.success(f"✅ Transacción creada exitosamente (ID: {transaction_id})")
                            st.info("💡 Ahora puedes crear asientos para esta transacción")
                            st.rerun()
                        else:
                            st.error("❌ No se pudo obtener el ID de la transacción creada")
                    else:
                        st.error(f"❌ Error al crear transacción: {response.text}")
                    
            except requests.exceptions.RequestException as e:
                st.error(f"❌ Error de conexión: {str(e)}")

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
            
            # Verificar si hay resultados después del filtro
            if not filtered_transactions:
                st.info("🔍 No se encontraron transacciones con los filtros aplicados")
                return
            
            # Configuración de paginación
            total_transacciones = len(filtered_transactions)
            
            col_info, col_items = st.columns([3, 1])
            with col_info:
                st.info(f"📊 **Transacciones filtradas:** {total_transacciones}")
            with col_items:
                items_per_page = st.selectbox(
                    "Transacciones por página:",
                    options=[10, 20, 50, 100],
                    index=0,  # 10 por defecto
                    key="items_per_page_trans"
                )
            
            total_pages = (total_transacciones + items_per_page - 1) // items_per_page
            
            # Inicializar página actual
            if 'current_page_trans' not in st.session_state:
                st.session_state.current_page_trans = 1
            
            # Ajustar página si está fuera de rango
            if st.session_state.current_page_trans > total_pages:
                st.session_state.current_page_trans = total_pages
            
            # Calcular índices
            start_idx = (st.session_state.current_page_trans - 1) * items_per_page
            end_idx = min(start_idx + items_per_page, total_transacciones)
            
            # Obtener transacciones de la página actual
            transacciones_pagina = filtered_transactions[start_idx:end_idx]
            
            # Convert to DataFrame for display
            df = pd.DataFrame(transacciones_pagina)
            
            # Format datetime columns (con manejo flexible de formatos)
            df['fecha_transaccion'] = pd.to_datetime(df['fecha_transaccion'], format='mixed', utc=True).dt.strftime('%Y-%m-%d %H:%M')
            df['fecha_creacion'] = pd.to_datetime(df['fecha_creacion'], format='mixed', utc=True).dt.strftime('%Y-%m-%d %H:%M')
            
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
            
            # Mostrar rango
            st.caption(f"Mostrando transacciones {start_idx + 1} - {end_idx} de {total_transacciones}")
            
            # Controles de paginación (solo abajo)
            if total_pages > 1:
                st.markdown("---")
                col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])
                
                with col1:
                    if st.button("⏮️ Primera", key="first_trans", use_container_width=True, disabled=st.session_state.current_page_trans == 1):
                        st.session_state.current_page_trans = 1
                        st.rerun()
                
                with col2:
                    if st.button("◀️ Anterior", key="prev_trans", use_container_width=True, disabled=st.session_state.current_page_trans == 1):
                        st.session_state.current_page_trans -= 1
                        st.rerun()
                
                with col3:
                    st.markdown(f"<div style='text-align: center; padding: 8px;'><strong>Página {st.session_state.current_page_trans} de {total_pages}</strong></div>", unsafe_allow_html=True)
                
                with col4:
                    if st.button("▶️ Siguiente", key="next_trans", use_container_width=True, disabled=st.session_state.current_page_trans == total_pages):
                        st.session_state.current_page_trans += 1
                        st.rerun()
                
                with col5:
                    if st.button("⏭️ Última", key="last_trans", use_container_width=True, disabled=st.session_state.current_page_trans == total_pages):
                        st.session_state.current_page_trans = total_pages
                        st.rerun()
            
            st.markdown("---")
            st.markdown("### ⚙️ Acciones")
            
            # Action buttons for each transaction
            col1, col2, col3 = st.columns([4, 2, 2])
            
            with col1:
                # Obtener valor por defecto (transacción actual si existe)
                default_value = st.session_state.get('transaccion_actual', None)
                
                # Usar todas las transacciones filtradas para el selector (no solo las de la página)
                selected_id = st.selectbox(
                    "Seleccionar Transacción",
                    options=[None] + [t['id_transaccion'] for t in filtered_transactions],
                    index=0 if not default_value else ([None] + [t['id_transaccion'] for t in filtered_transactions]).index(default_value) if default_value in [t['id_transaccion'] for t in filtered_transactions] else 0,
                    format_func=lambda x: "🔽 Selecciona una transacción..." if x is None else f"✅ ID: {x} (Activa para asientos)",
                    key="select_trans_action",
                    help="La transacción seleccionada se usará automáticamente para crear asientos"
                )
                
                # Actualizar transacción actual SIN hacer rerun
                if selected_id:
                    st.session_state.transaccion_actual = selected_id
            
            with col2:
                if st.button("✏️ Modificar", type="primary", use_container_width=True, disabled=not selected_id):
                    if selected_id:
                        selected_transaction = next((t for t in filtered_transactions if t['id_transaccion'] == selected_id), None)
                        if selected_transaction:
                            on_edit_click(selected_id, selected_transaction)
                            st.rerun()
            
            with col3:
                if st.button("🗑️ Eliminar", type="secondary", use_container_width=True, disabled=not selected_id):
                    if selected_id:
                        on_delete_click(selected_id)
            
            # Mostrar confirmación fuera de las columnas
            if 'confirm_delete_id' in st.session_state and st.session_state.confirm_delete_id:
                st.warning(f"⚠️ ¿Confirmas eliminar la transacción ID {st.session_state.confirm_delete_id}?")
                col_conf1, col_conf2, col_conf3 = st.columns([2, 1, 1])
                with col_conf2:
                    if st.button("✅ Sí, Eliminar", type="primary", key="confirm_yes"):
                        delete_transaction(backend_url, st.session_state.confirm_delete_id)
                        st.session_state.confirm_delete_id = None
                with col_conf3:
                    if st.button("❌ Cancelar", key="confirm_no"):
                        st.session_state.confirm_delete_id = None
                        st.rerun()
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
            
            # Gráfico de distribución por tipo (pantalla completa)
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
                height=400,
                margin=dict(t=20, b=20, l=20, r=20)
            )
            st.plotly_chart(fig_tipo, use_container_width=True)
            
            st.markdown("---")
            
            # Gráfico de tendencia temporal
            if 'fecha_transaccion' in df.columns:
                st.markdown("#### 📈 Tendencia Temporal")
                df['fecha'] = pd.to_datetime(df['fecha_transaccion'], format='mixed', errors='coerce').dt.date
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

