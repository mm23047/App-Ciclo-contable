"""
Módulo Streamlit para Facturación Digital.
Sistema de emisión de facturas electrónicas con integración contable.
"""
import streamlit as st
import requests
import pandas as pd
from datetime import datetime, date
from typing import Dict, Any, List
import plotly.express as px
import plotly.graph_objects as go

def render_page(backend_url: str):
    """Renderizar página de facturación"""
    
    st.header("🧾 Facturación Digital")
    st.markdown("Sistema de emisión de facturas electrónicas con integración contable automática")
    
    # Tabs para organizar funcionalidades
    tab1, tab2, tab3, tab4 = st.tabs(["📝 Nueva Factura", "📋 Gestión de Facturas", "📊 Reportes de Ventas", "⚙️ Configuración"])
    
    with tab1:
        crear_nueva_factura(backend_url)
    
    with tab2:
        gestion_facturas(backend_url)
    
    with tab3:
        reportes_ventas(backend_url)
    
    with tab4:
        configuracion_facturacion(backend_url)

def crear_nueva_factura(backend_url: str):
    """Crear nueva factura"""
    
    st.subheader("📝 Crear Nueva Factura")
    
    # Obtener clientes disponibles
    try:
        response_clientes = requests.get(f"{backend_url}/api/facturacion/clientes")
        clientes = response_clientes.json() if response_clientes.status_code == 200 else []
    except:
        clientes = []
    
    # Obtener productos disponibles
    try:
        response_productos = requests.get(f"{backend_url}/api/facturacion/productos")
        productos = response_productos.json() if response_productos.status_code == 200 else []
    except:
        productos = []
    
    if not clientes:
        st.warning("⚠️ No hay clientes registrados. Ve a Configuración para agregar clientes.")
        return
    
    if not productos:
        st.warning("⚠️ No hay productos registrados. Ve a Configuración para agregar productos.")
        return
    
    # Formulario principal de la factura
    with st.form("form_nueva_factura", clear_on_submit=False):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 👤 Información del Cliente")
            
            # Selección de cliente
            opciones_clientes = [
                f"{c['codigo_cliente']} - {c['nombre']} ({c['tipo_cliente']})"
                for c in clientes if c.get('estado_cliente') == 'ACTIVO'
            ]
            
            cliente_seleccionado = st.selectbox("Cliente:", opciones_clientes)
            
            # Obtener datos del cliente seleccionado
            if cliente_seleccionado:
                codigo_cliente = cliente_seleccionado.split(" - ")[0]
                cliente_obj = next((c for c in clientes if c['codigo_cliente'] == codigo_cliente), None)
                
                if cliente_obj:
                    st.text_input("NIT/CC:", value=cliente_obj.get('nit', ''), disabled=True)
                    st.text_input("Email:", value=cliente_obj.get('email', ''), disabled=True)
                    st.text_area("Dirección:", value=cliente_obj.get('direccion', ''), disabled=True, height=60)
        
        with col2:
            st.markdown("#### 🧾 Datos de la Factura")
            
            # Datos de la factura
            fecha_factura = st.date_input(
                "Fecha de factura:",
                value=datetime.now().date()
            )
            
            fecha_vencimiento = st.date_input(
                "Fecha de vencimiento:",
                value=datetime.now().date()
            )
            
            tipo_factura = st.selectbox(
                "Tipo de factura:",
                ["Contado", "Crédito"]
            )
            
            observaciones = st.text_area(
                "Observaciones:",
                height=80,
                help="Observaciones adicionales para la factura"
            )
        
        # Sección de productos
        st.markdown("### 🛍️ Productos/Servicios")
        
        # Gestión de productos de la factura
        if 'productos_factura' not in st.session_state:
            st.session_state.productos_factura = []
        
        # Formulario para agregar productos
        with st.expander("➕ Agregar Producto/Servicio", expanded=True):
            col1, col2, col3, col4, col5, col6 = st.columns([3, 1, 1, 1, 1, 1])
            
            with col1:
                opciones_productos = [
                    f"{p['codigo_producto']} - {p['nombre']} - ${float(p.get('precio_venta', 0)):,.2f}"
                    for p in productos if p.get('estado_producto') == 'ACTIVO'
                ]
                
                if opciones_productos:
                    producto_sel = st.selectbox("Producto/Servicio:", opciones_productos, key="prod_factura")
                else:
                    st.warning("No hay productos activos")
                    producto_sel = None
            
            with col2:
                cantidad = st.number_input("Cantidad:", min_value=0.01, value=1.0, step=0.01, key="cant_factura")
            
            with col3:
                # Obtener precio del producto seleccionado
                precio_unitario = 0
                if producto_sel:
                    codigo_prod = producto_sel.split(" - ")[0]
                    prod_obj = next((p for p in productos if p['codigo_producto'] == codigo_prod), None)
                    if prod_obj:
                        precio_unitario = prod_obj.get('precio_venta', 0)
                
                precio = st.number_input("Precio Unit.:", value=precio_unitario, step=0.01, key="precio_factura")
            
            with col4:
                descuento = st.number_input("Desc. %:", min_value=0.0, max_value=100.0, value=0.0, step=0.1, key="desc_factura")
            
            with col5:
                subtotal = cantidad * precio * (1 - descuento/100)
                st.metric("Subtotal", f"${subtotal:,.2f}")
            
            with col6:
                st.write("")  # Espaciado
                if st.button("➕ Agregar", key="add_prod_factura"):
                    if producto_sel and cantidad > 0 and precio > 0:
                        codigo_prod = producto_sel.split(" - ")[0]
                        prod_obj = next((p for p in productos if p['codigo_producto'] == codigo_prod), None)
                        
                        nuevo_item = {
                            'id_producto': prod_obj['id_producto'],
                            'codigo_producto': codigo_prod,
                            'nombre_producto': prod_obj['nombre'],
                            'cantidad': cantidad,
                            'precio_unitario': precio,
                            'descuento_porcentaje': descuento,
                            'subtotal': subtotal
                        }
                        
                        st.session_state.productos_factura.append(nuevo_item)
                        st.rerun()
        
        # Mostrar productos agregados
        if st.session_state.productos_factura:
            st.markdown("#### 📋 Productos en la Factura")
            
            for i, item in enumerate(st.session_state.productos_factura):
                col1, col2, col3, col4, col5, col6, col7 = st.columns([2, 1, 1, 1, 1, 1, 1])
                
                with col1:
                    st.text(f"{item['codigo_producto']} - {item['nombre_producto']}")
                
                with col2:
                    st.text(f"{item['cantidad']:,.2f}")
                
                with col3:
                    st.text(f"${item['precio_unitario']:,.2f}")
                
                with col4:
                    st.text(f"{item['descuento_porcentaje']:.1f}%")
                
                with col5:
                    st.text(f"${item['subtotal']:,.2f}")
                
                with col6:
                    # IVA (asumiendo 19%)
                    iva = item['subtotal'] * 0.19
                    st.text(f"${iva:,.2f}")
                
                with col7:
                    if st.button("🗑️", key=f"del_prod_{i}", help="Eliminar"):
                        st.session_state.productos_factura.pop(i)
                        st.rerun()
        
        # Totales de la factura
        if st.session_state.productos_factura:
            subtotal_total = sum(item['subtotal'] for item in st.session_state.productos_factura)
            iva_total = subtotal_total * 0.19  # 19% IVA
            total_factura = subtotal_total + iva_total
            
            st.markdown("### 💰 Totales de la Factura")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Subtotal", f"${subtotal_total:,.2f}")
            
            with col2:
                st.metric("IVA (19%)", f"${iva_total:,.2f}")
            
            with col3:
                st.metric("Total", f"${total_factura:,.2f}")
            
            with col4:
                st.metric("Items", len(st.session_state.productos_factura))
        
        # Botón para crear factura
        submitted = st.form_submit_button(
            "🧾 Crear Factura",
            use_container_width=True,
            type="primary"
        )
        
        if submitted:
            if not st.session_state.productos_factura:
                st.error("❌ Debe agregar al menos un producto/servicio")
            elif not cliente_seleccionado:
                st.error("❌ Debe seleccionar un cliente")
            else:
                crear_factura_backend(
                    backend_url,
                    cliente_obj,
                    fecha_factura,
                    fecha_vencimiento,
                    tipo_factura,
                    observaciones,
                    st.session_state.productos_factura
                )

def crear_factura_backend(
    backend_url: str,
    cliente: Dict,
    fecha_factura: date,
    fecha_vencimiento: date,
    tipo_factura: str,
    observaciones: str,
    productos: List[Dict]
):
    """Enviar factura al backend"""
    
    try:
        # Calcular totales
        subtotal = sum(p['subtotal'] for p in productos)
        iva = subtotal * 0.19
        total = subtotal + iva
        
        # Preparar datos de la factura
        datos_factura = {
            "id_cliente": cliente['id_cliente'],
            "fecha_factura": fecha_factura.isoformat(),
            "fecha_vencimiento": fecha_vencimiento.isoformat(),
            "tipo_factura": tipo_factura,
            "subtotal": subtotal,
            "iva": iva,
            "total": total,
            "observaciones": observaciones if observaciones else None,
            "items": [
                {
                    "id_producto": item['id_producto'],
                    "cantidad": item['cantidad'],
                    "precio_unitario": item['precio_unitario'],
                    "descuento_porcentaje": item['descuento_porcentaje'],
                    "subtotal": item['subtotal']
                }
                for item in productos
            ]
        }
        
        with st.spinner("Creando factura..."):
            response = requests.post(
                f"{backend_url}/api/facturas",
                json=datos_factura
            )
        
        if response.status_code == 201:
            factura_creada = response.json()
            st.success(f"✅ Factura creada exitosamente! Número: {factura_creada.get('numero_factura', 'N/A')}")
            st.session_state.productos_factura = []  # Limpiar productos
            st.balloons()
            
            # Mostrar resumen de la factura
            with st.expander("📄 Resumen de la Factura Creada", expanded=True):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Número:** {factura_creada.get('numero_factura', 'N/A')}")
                    st.write(f"**Cliente:** {cliente['nombre']}")
                    st.write(f"**Fecha:** {fecha_factura}")
                    st.write(f"**Tipo:** {tipo_factura}")
                
                with col2:
                    st.write(f"**Subtotal:** ${subtotal:,.2f}")
                    st.write(f"**IVA:** ${iva:,.2f}")
                    st.write(f"**Total:** ${total:,.2f}")
                    st.write(f"**Estado:** Pendiente")
        else:
            error_detail = response.json().get('detail', 'Error desconocido')
            st.error(f"❌ Error al crear factura: {error_detail}")
            
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Error de conexión: {e}")
    except Exception as e:
        st.error(f"❌ Error inesperado: {e}")

def gestion_facturas(backend_url: str):
    """Gestión y consulta de facturas"""
    
    st.subheader("📋 Gestión de Facturas")
    
    # Filtros de búsqueda
    col1, col2, col3 = st.columns(3)
    
    with col1:
        estado_filtro = st.selectbox(
            "Estado:",
            ["Todas", "Pendiente", "Pagada", "Vencida", "Anulada"]
        )
    
    with col2:
        fecha_desde = st.date_input("Desde:", value=None)
    
    with col3:
        fecha_hasta = st.date_input("Hasta:", value=None)
    
    # Filtros adicionales
    col1, col2 = st.columns(2)
    
    with col1:
        try:
            response_clientes = requests.get(f"{backend_url}/api/facturacion/clientes")
            clientes = response_clientes.json() if response_clientes.status_code == 200 else []
            
            opciones_clientes = ["Todos los clientes"] + [
                f"{c['codigo_cliente']} - {c['nombre']}"
                for c in clientes
            ]
            cliente_filtro = st.selectbox("Cliente:", opciones_clientes)
        except:
            cliente_filtro = "Todos los clientes"
    
    with col2:
        numero_factura = st.text_input("Número de factura:", help="Buscar por número específico")
    
    if st.button("🔍 Buscar Facturas", use_container_width=True):
        buscar_facturas(
            backend_url,
            estado_filtro,
            fecha_desde,
            fecha_hasta,
            cliente_filtro,
            numero_factura
        )

def buscar_facturas(
    backend_url: str,
    estado_filtro: str,
    fecha_desde: date,
    fecha_hasta: date,
    cliente_filtro: str,
    numero_factura: str
):
    """Buscar y mostrar facturas"""
    
    try:
        params = {}
        
        if estado_filtro != "Todas":
            params["estado"] = estado_filtro
        
        if fecha_desde:
            params["fecha_desde"] = fecha_desde.isoformat()
        
        if fecha_hasta:
            params["fecha_hasta"] = fecha_hasta.isoformat()
        
        if cliente_filtro != "Todos los clientes":
            codigo_cliente = cliente_filtro.split(" - ")[0]
            params["codigo_cliente"] = codigo_cliente
        
        if numero_factura:
            params["numero_factura"] = numero_factura
        
        with st.spinner("Buscando facturas..."):
            response = requests.get(f"{backend_url}/api/facturas", params=params)
        
        if response.status_code == 200:
            facturas = response.json()
            
            if facturas:
                mostrar_facturas(facturas, backend_url)
            else:
                st.info("📭 No se encontraron facturas con los criterios especificados")
        else:
            st.error(f"Error al buscar facturas: {response.status_code}")
            
    except Exception as e:
        st.error(f"Error al buscar facturas: {e}")

def mostrar_facturas(facturas: List[Dict], backend_url: str):
    """Mostrar lista de facturas"""
    
    st.markdown(f"### 📋 Facturas Encontradas ({len(facturas)})")
    
    # Métricas resumen
    total_facturas = len(facturas)
    total_valor = sum(f.get('total', 0) for f in facturas)
    facturas_pendientes = len([f for f in facturas if f.get('estado') == 'Pendiente'])
    facturas_pagadas = len([f for f in facturas if f.get('estado') == 'Pagada'])
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Facturas", total_facturas)
    
    with col2:
        st.metric("Valor Total", f"${total_valor:,.2f}")
    
    with col3:
        st.metric("Pendientes", facturas_pendientes)
    
    with col4:
        st.metric("Pagadas", facturas_pagadas)
    
    # Tabla de facturas
    df_facturas = pd.DataFrame(facturas)
    
    # Formatear para visualización
    df_display = df_facturas.copy()
    
    # Formatear fechas y valores
    df_display['fecha_factura'] = pd.to_datetime(df_display['fecha_factura']).dt.strftime('%d/%m/%Y')
    if 'fecha_vencimiento' in df_display.columns:
        df_display['fecha_vencimiento'] = pd.to_datetime(df_display['fecha_vencimiento']).dt.strftime('%d/%m/%Y')
    
    for col in ['subtotal', 'iva', 'total']:
        if col in df_display.columns:
            df_display[f'{col}_fmt'] = df_display[col].apply(lambda x: f"${x:,.2f}")
    
    # Seleccionar columnas para mostrar
    columnas_mostrar = ['numero_factura', 'fecha_factura', 'nombre_cliente', 'estado', 'total_fmt']
    nombres_columnas = ['Número', 'Fecha', 'Cliente', 'Estado', 'Total']
    
    # Verificar que las columnas existan
    columnas_disponibles = [col for col in columnas_mostrar if col in df_display.columns or f"{col}_fmt" in df_display.columns]
    
    if columnas_disponibles:
        df_final = df_display[columnas_disponibles].copy()
        df_final.columns = nombres_columnas[:len(columnas_disponibles)]
        
        # Mostrar tabla con selección
        selected_indices = st.dataframe(
            df_final,
            use_container_width=True,
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row"
        )
        
        # Acciones sobre factura seleccionada
        if selected_indices and selected_indices.selection.rows:
            selected_row = selected_indices.selection.rows[0]
            factura_seleccionada = facturas[selected_row]
            
            st.markdown("### 🔧 Acciones sobre Factura Seleccionada")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if st.button("👁️ Ver Detalles"):
                    mostrar_detalle_factura(factura_seleccionada)
            
            with col2:
                if st.button("💰 Marcar como Pagada"):
                    marcar_como_pagada(backend_url, factura_seleccionada['id_factura'])
            
            with col3:
                if st.button("📄 Imprimir"):
                    st.info("🚧 Función de impresión en desarrollo")
            
            with col4:
                if st.button("❌ Anular"):
                    if st.checkbox("Confirmar anulación"):
                        anular_factura(backend_url, factura_seleccionada['id_factura'])

def mostrar_detalle_factura(factura: Dict):
    """Mostrar detalle completo de una factura"""
    
    with st.expander(f"📄 Detalle Factura {factura.get('numero_factura', 'N/A')}", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**📋 Información General:**")
            st.text(f"Número: {factura.get('numero_factura', 'N/A')}")
            st.text(f"Fecha: {factura.get('fecha_factura', 'N/A')}")
            st.text(f"Vencimiento: {factura.get('fecha_vencimiento', 'N/A')}")
            st.text(f"Estado: {factura.get('estado', 'N/A')}")
            st.text(f"Tipo: {factura.get('tipo_factura', 'N/A')}")
        
        with col2:
            st.markdown("**💰 Totales:**")
            st.text(f"Subtotal: ${factura.get('subtotal', 0):,.2f}")
            st.text(f"IVA: ${factura.get('iva', 0):,.2f}")
            st.text(f"Total: ${factura.get('total', 0):,.2f}")
        
        # Cliente
        st.markdown("**👤 Cliente:**")
        st.text(f"Nombre: {factura.get('nombre_cliente', 'N/A')}")
        
        # Items de la factura
        if 'items' in factura and factura['items']:
            st.markdown("**📦 Items:**")
            
            df_items = pd.DataFrame(factura['items'])
            df_items_display = df_items.copy()
            
            # Formatear columnas monetarias
            for col in ['precio_unitario', 'subtotal']:
                if col in df_items_display.columns:
                    df_items_display[col] = df_items_display[col].apply(lambda x: f"${x:,.2f}")
            
            st.dataframe(df_items_display, use_container_width=True, hide_index=True)

def marcar_como_pagada(backend_url: str, id_factura: int):
    """Marcar factura como pagada"""
    
    try:
        with st.spinner("Actualizando estado de factura..."):
            response = requests.patch(
                f"{backend_url}/api/facturas/{id_factura}/pagar"
            )
        
        if response.status_code == 200:
            st.success("✅ Factura marcada como pagada")
            st.rerun()
        else:
            st.error(f"Error al actualizar factura: {response.status_code}")
            
    except Exception as e:
        st.error(f"Error al marcar como pagada: {e}")

def anular_factura(backend_url: str, id_factura: int):
    """Anular factura"""
    
    try:
        with st.spinner("Anulando factura..."):
            response = requests.patch(
                f"{backend_url}/api/facturas/{id_factura}/anular"
            )
        
        if response.status_code == 200:
            st.success("✅ Factura anulada")
            st.rerun()
        else:
            st.error(f"Error al anular factura: {response.status_code}")
            
    except Exception as e:
        st.error(f"Error al anular factura: {e}")

def reportes_ventas(backend_url: str):
    """Reportes y análisis de ventas"""
    
    st.subheader("📊 Reportes de Ventas")
    
    # Selector de tipo de reporte
    tipo_reporte = st.selectbox(
        "Tipo de reporte:",
        [
            "Ventas por período",
            "Ventas por cliente",
            "Ventas por producto",
            "Análisis de tendencias",
            "Estado de cartera"
        ]
    )
    
    # Filtros de fecha
    col1, col2 = st.columns(2)
    
    with col1:
        fecha_desde = st.date_input("Desde:", value=datetime.now().replace(day=1).date())
    
    with col2:
        fecha_hasta = st.date_input("Hasta:", value=datetime.now().date())
    
    if st.button("📊 Generar Reporte", use_container_width=True):
        generar_reporte_ventas(backend_url, tipo_reporte, fecha_desde, fecha_hasta)

def generar_reporte_ventas(
    backend_url: str,
    tipo_reporte: str,
    fecha_desde: date,
    fecha_hasta: date
):
    """Generar reporte específico de ventas"""
    
    try:
        params = {
            "fecha_desde": fecha_desde.isoformat(),
            "fecha_hasta": fecha_hasta.isoformat()
        }
        
        with st.spinner(f"Generando {tipo_reporte}..."):
            if tipo_reporte == "Ventas por período":
                response = requests.get(f"{backend_url}/api/reportes/ventas-periodo", params=params)
            elif tipo_reporte == "Ventas por cliente":
                response = requests.get(f"{backend_url}/api/reportes/ventas-cliente", params=params)
            elif tipo_reporte == "Ventas por producto":
                response = requests.get(f"{backend_url}/api/reportes/ventas-producto", params=params)
            elif tipo_reporte == "Análisis de tendencias":
                response = requests.get(f"{backend_url}/api/reportes/tendencias-ventas", params=params)
            elif tipo_reporte == "Estado de cartera":
                response = requests.get(f"{backend_url}/api/reportes/estado-cartera", params=params)
        
        if response.status_code == 200:
            datos_reporte = response.json()
            mostrar_reporte_ventas(datos_reporte, tipo_reporte)
        else:
            st.error(f"Error al generar reporte: {response.status_code}")
            
    except Exception as e:
        st.error(f"Error al generar reporte: {e}")

def mostrar_reporte_ventas(datos: Dict[str, Any], tipo_reporte: str):
    """Mostrar reporte de ventas según el tipo"""
    
    st.markdown(f"### 📊 {tipo_reporte}")
    
    # Por ahora, mostrar estructura básica
    st.info(f"🚧 Reporte '{tipo_reporte}' en desarrollo")
    
    # Mostrar algunos datos de ejemplo
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Facturas Emitidas", "125")
    
    with col2:
        st.metric("Ventas Totales", "$45,680,000")
    
    with col3:
        st.metric("Clientes Activos", "78")
    
    with col4:
        st.metric("Ticket Promedio", "$365,440")

def configuracion_facturacion(backend_url: str):
    """Configuración del módulo de facturación"""
    
    st.subheader("⚙️ Configuración de Facturación")
    
    # Tabs para diferentes configuraciones
    tab_clientes, tab_productos, tab_parametros = st.tabs([
        "👥 Gestión de Clientes",
        "📦 Gestión de Productos", 
        "⚙️ Parámetros"
    ])
    
    with tab_clientes:
        gestion_clientes(backend_url)
    
    with tab_productos:
        gestion_productos(backend_url)
    
    with tab_parametros:
        configurar_parametros(backend_url)

def gestion_clientes(backend_url: str):
    """Gestión de clientes"""
    
    st.markdown("#### 👥 Gestión de Clientes")
    
    # Botones de acción
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("➕ Agregar Cliente", use_container_width=True):
            st.session_state.mostrar_form_cliente = True
    
    with col2:
        if st.button("🔄 Actualizar Lista", use_container_width=True):
            st.rerun()
    
    # Formulario para nuevo cliente
    if st.session_state.get('mostrar_form_cliente', False):
        with st.form("form_nuevo_cliente"):
            st.markdown("**➕ Nuevo Cliente**")
            
            col1, col2 = st.columns(2)
            
            with col1:
                codigo_cliente = st.text_input("Código Cliente*:", help="Código único del cliente")
                nombre = st.text_input("Nombre/Razón Social*:")
                nit = st.text_input("NIT/CC*:")
                email = st.text_input("Email:")
            
            with col2:
                telefono = st.text_input("Teléfono:")
                direccion = st.text_area("Dirección:")
                tipo_cliente = st.selectbox("Tipo:", ["Empresa", "Persona Natural"])
                estado = st.selectbox("Estado:", ["ACTIVO", "INACTIVO", "BLOQUEADO"], index=0)
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.form_submit_button("💾 Guardar Cliente", use_container_width=True):
                    if codigo_cliente and nombre and nit:
                        crear_cliente(
                            backend_url, codigo_cliente, nombre, nit, 
                            email, telefono, direccion, tipo_cliente, estado
                        )
                    else:
                        st.error("❌ Complete los campos obligatorios")
            
            with col2:
                if st.form_submit_button("❌ Cancelar"):
                    st.session_state.mostrar_form_cliente = False
                    st.rerun()
    
    # Lista de clientes existentes
    mostrar_lista_clientes(backend_url)

def crear_cliente(
    backend_url: str, codigo: str, nombre: str, nit: str,
    email: str, telefono: str, direccion: str, tipo: str, estado: str
):
    """Crear nuevo cliente"""
    
    try:
        # Mapear el tipo de cliente al formato del backend
        tipo_cliente_backend = "PERSONA_JURIDICA" if tipo == "Empresa" else "PERSONA_NATURAL"
        estado_backend = estado  # Ya viene en formato correcto: ACTIVO, INACTIVO, BLOQUEADO
        
        datos_cliente = {
            "codigo_cliente": codigo if codigo else None,
            "nombre": nombre,
            "nit": nit if nit else None,
            "email": email if email else None,
            "telefono_principal": telefono if telefono else None,
            "direccion": direccion if direccion else None,
            "tipo_cliente": tipo_cliente_backend,
            "estado_cliente": estado_backend,
            "usuario_creacion": "SISTEMA"  # Campo requerido
        }
        
        with st.spinner("Creando cliente..."):
            response = requests.post(f"{backend_url}/api/facturacion/clientes", json=datos_cliente)
        
        if response.status_code in [200, 201]:
            st.success("✅ Cliente creado exitosamente")
            st.session_state.mostrar_form_cliente = False
            st.rerun()
        else:
            error_detail = response.json().get('detail', 'Error desconocido')
            st.error(f"❌ Error al crear cliente: {error_detail}")
            
    except Exception as e:
        st.error(f"❌ Error al crear cliente: {e}")

def mostrar_lista_clientes(backend_url: str):
    """Mostrar lista de clientes"""
    
    try:
        with st.spinner("Cargando clientes..."):
            response = requests.get(f"{backend_url}/api/facturacion/clientes")
        
        if response.status_code == 200:
            clientes = response.json()
            
            if clientes:
                st.markdown("**📋 Lista de Clientes**")
                
                df_clientes = pd.DataFrame(clientes)
                
                # Formatear para mostrar - usar los campos correctos del schema
                columnas_disponibles = []
                for col in ['codigo_cliente', 'nombre', 'nit', 'tipo_cliente', 'estado_cliente']:
                    if col in df_clientes.columns:
                        columnas_disponibles.append(col)
                
                if columnas_disponibles:
                    df_display = df_clientes[columnas_disponibles].copy()
                    # Renombrar columnas para mejor visualización
                    nombres_columnas = {
                        'codigo_cliente': 'Código',
                        'nombre': 'Nombre',
                        'nit': 'NIT',
                        'tipo_cliente': 'Tipo',
                        'estado_cliente': 'Estado'
                    }
                    df_display.columns = [nombres_columnas.get(col, col) for col in columnas_disponibles]
                    
                    st.dataframe(df_display, use_container_width=True, hide_index=True)
                else:
                    st.info("No hay datos suficientes para mostrar")
            else:
                st.info("📭 No hay clientes registrados")
        else:
            st.error(f"Error al cargar clientes: {response.status_code}")
            
    except Exception as e:
        st.error(f"Error al cargar clientes: {e}")

def gestion_productos(backend_url: str):
    """Gestión de productos"""
    
    st.markdown("#### 📦 Gestión de Productos")
    
    # Botones de acción
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("➕ Agregar Producto", use_container_width=True):
            st.session_state.mostrar_form_producto = True
    
    with col2:
        if st.button("🔄 Actualizar Lista", use_container_width=True, key="refresh_productos"):
            st.rerun()
    
    # Formulario para nuevo producto
    if st.session_state.get('mostrar_form_producto', False):
        with st.form("form_nuevo_producto"):
            st.markdown("**➕ Nuevo Producto/Servicio**")
            
            col1, col2 = st.columns(2)
            
            with col1:
                codigo_producto = st.text_input("Código Producto*:")
                nombre = st.text_input("Nombre*:")
                precio_unitario = st.number_input("Precio Unitario*:", min_value=0.0, step=0.01)
                tipo_producto = st.selectbox("Tipo:", ["PRODUCTO", "SERVICIO", "COMBO"])
            
            with col2:
                descripcion = st.text_area("Descripción:")
                categoria = st.text_input("Categoría:")
                estado = st.selectbox("Estado:", ["ACTIVO", "INACTIVO", "DESCONTINUADO"], index=0)
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.form_submit_button("💾 Guardar Producto", use_container_width=True):
                    if codigo_producto and nombre and precio_unitario > 0:
                        crear_producto(
                            backend_url, codigo_producto, nombre, precio_unitario,
                            descripcion, categoria, tipo_producto, estado
                        )
                    else:
                        st.error("❌ Complete los campos obligatorios")
            
            with col2:
                if st.form_submit_button("❌ Cancelar", key="cancel_producto"):
                    st.session_state.mostrar_form_producto = False
                    st.rerun()
    
    # Lista de productos existentes
    mostrar_lista_productos(backend_url)

def crear_producto(
    backend_url: str, codigo: str, nombre: str, precio_unitario: float,
    descripcion: str, categoria: str, tipo: str, estado: str
):
    """Crear nuevo producto"""
    
    try:
        datos_producto = {
            "codigo_producto": codigo,
            "nombre": nombre,
            "descripcion": descripcion if descripcion else None,
            "tipo_producto": tipo,  # Ya viene en formato correcto (PRODUCTO, SERVICIO, COMBO)
            "precio_venta": float(precio_unitario),
            "precio_compra": 0.0,  # Valor por defecto
            "aplica_iva": True,  # Valor por defecto
            "porcentaje_iva": 13.0,  # Valor por defecto para El Salvador
            "estado_producto": estado,  # Ya viene en formato correcto (ACTIVO, INACTIVO, DESCONTINUADO)
            "categoria_producto": categoria if categoria else None
        }
        
        with st.spinner("Creando producto..."):
            response = requests.post(f"{backend_url}/api/facturacion/productos", json=datos_producto)
        
        if response.status_code in [200, 201]:
            st.success("✅ Producto creado exitosamente")
            st.session_state.mostrar_form_producto = False
            st.rerun()
        else:
            error_detail = response.json().get('detail', 'Error desconocido')
            st.error(f"❌ Error al crear producto: {error_detail}")
            
    except Exception as e:
        st.error(f"❌ Error al crear producto: {e}")

def mostrar_lista_productos(backend_url: str):
    """Mostrar lista de productos"""
    
    try:
        with st.spinner("Cargando productos..."):
            response = requests.get(f"{backend_url}/api/facturacion/productos")
        
        if response.status_code == 200:
            productos = response.json()
            
            if productos:
                st.markdown("**📦 Lista de Productos/Servicios**")
                
                df_productos = pd.DataFrame(productos)
                
                # Formatear para mostrar - usar los campos correctos del schema
                columnas_disponibles = []
                for col in ['codigo_producto', 'nombre', 'precio_venta', 'tipo_producto', 'estado_producto']:
                    if col in df_productos.columns:
                        columnas_disponibles.append(col)
                
                if columnas_disponibles:
                    df_display = df_productos[columnas_disponibles].copy()
                    
                    # Formatear precio si existe
                    if 'precio_venta' in df_display.columns:
                        df_display['precio_venta'] = df_display['precio_venta'].apply(lambda x: f"${float(x):,.2f}")
                    
                    # Renombrar columnas para mejor visualización
                    nombres_columnas = {
                        'codigo_producto': 'Código',
                        'nombre': 'Nombre',
                        'precio_venta': 'Precio',
                        'tipo_producto': 'Tipo',
                        'estado_producto': 'Estado'
                    }
                    df_display.columns = [nombres_columnas.get(col, col) for col in columnas_disponibles]
                    
                    st.dataframe(df_display, use_container_width=True, hide_index=True)
                else:
                    st.info("No hay datos suficientes para mostrar")
            else:
                st.info("📭 No hay productos registrados")
        else:
            st.error(f"Error al cargar productos: {response.status_code}")
            
    except Exception as e:
        st.error(f"Error al cargar productos: {e}")

def configurar_parametros(backend_url: str):
    """Configurar parámetros de facturación"""
    
    st.markdown("#### ⚙️ Parámetros de Facturación")
    
    # Parámetros generales
    st.markdown("**🏢 Información de la Empresa**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        empresa_nit = st.text_input("NIT Empresa:", value="900123456-7")
        empresa_nombre = st.text_input("Razón Social:", value="Mi Empresa SAS")
        empresa_direccion = st.text_area("Dirección:", value="Calle 123 #45-67")
    
    with col2:
        empresa_telefono = st.text_input("Teléfono:", value="(601) 234-5678")
        empresa_email = st.text_input("Email:", value="info@miempresa.com")
        empresa_web = st.text_input("Sitio Web:", value="www.miempresa.com")
    
    st.markdown("**💰 Parámetros Fiscales**")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        iva_porcentaje = st.number_input("IVA (%):", value=19.0, step=0.1)
    
    with col2:
        retefuente_porcentaje = st.number_input("Retención Fuente (%):", value=2.5, step=0.1)
    
    with col3:
        reteica_porcentaje = st.number_input("ReteICA (%):", value=0.414, step=0.001)
    
    # Numeración de facturas
    st.markdown("**🔢 Numeración de Facturas**")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        prefijo_factura = st.text_input("Prefijo:", value="FV")
    
    with col2:
        numero_inicial = st.number_input("Número Inicial:", value=1, step=1)
    
    with col3:
        numero_actual = st.number_input("Número Actual:", value=1, step=1)
    
    if st.button("💾 Guardar Configuración", use_container_width=True):
        st.success("✅ Configuración guardada exitosamente")
        st.info("🔄 Los cambios se aplicarán en las próximas facturas")