"""
Módulo Streamlit para Gestión de Productos.
Sistema completo de administración de productos y servicios para facturación.
"""
import streamlit as st
import requests
import pandas as pd
from datetime import datetime, date
from typing import Dict, Any, List
import plotly.express as px
import plotly.graph_objects as go

def render_page(backend_url: str):
    """Renderizar página de gestión de productos"""
    
    st.header("📦 Gestión de Productos")
    st.markdown("Sistema completo de administración de productos y servicios para facturación")
    
    # Tabs para organizar funcionalidades
    tab1, tab2, tab3, tab4 = st.tabs(["📝 Registrar Producto", "📋 Lista de Productos", "📊 Análisis", "🏷️ Categorías"])
    
    with tab1:
        registrar_producto(backend_url)
    
    with tab2:
        lista_productos(backend_url)
    
    with tab3:
        analisis_productos(backend_url)
    
    with tab4:
        gestion_categorias(backend_url)

def registrar_producto(backend_url: str):
    """Registrar nuevo producto"""
    
    st.subheader("📝 Registrar Nuevo Producto/Servicio")
    
    with st.form("form_registro_producto", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📋 Información Básica")
            
            codigo_producto = st.text_input(
                "Código Producto*:",
                help="Código único identificador del producto"
            )
            
            nombre = st.text_input(
                "Nombre*:",
                help="Nombre descriptivo del producto o servicio"
            )
            
            tipo_producto = st.selectbox(
                "Tipo*:",
                ["PRODUCTO", "SERVICIO", "COMBO"],
                help="Clasificación como producto físico o servicio"
            )
            
            categoria_producto = st.text_input(
                "Categoría:",
                help="Categoría o familia del producto"
            )
            
            unidad_medida = st.selectbox(
                "Unidad de Medida:",
                ["UNIDAD", "KG", "METRO", "LITRO", "CAJA", "PAQUETE", "DOCENA", "PAR", "HORA", "SERVICIO"],
                help="Unidad de medida para ventas"
            )
        
        with col2:
            st.markdown("#### 💰 Información Comercial")
            
            precio_venta = st.number_input(
                "Precio de Venta*:",
                min_value=0.0,
                step=0.01,
                help="Precio de venta al público"
            )
            
            precio_compra = st.number_input(
                "Precio de Compra:",
                min_value=0.0,
                step=0.01,
                help="Costo de adquisición o producción"
            )
            
            margen_utilidad = st.number_input(
                "Margen de Utilidad (%):",
                min_value=0.0,
                value=0.0,
                step=0.1,
                help="Margen de utilidad del producto"
            )
            
            aplica_iva = st.checkbox(
                "Aplica IVA",
                value=True,
                help="Indica si el producto tiene IVA"
            )
            
            porcentaje_iva = st.selectbox(
                "IVA (%):",
                [0, 5, 13, 19],
                index=2,
                help="Porcentaje de IVA aplicable"
            )
        
        # Información de inventario (solo para productos)
        maneja_inventario = st.selectbox("¿Maneja inventario?", ["No", "Sí"], key="maneja_inventario") == "Sí"
        
        if maneja_inventario:
            st.markdown("#### 📦 Control de Inventario")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                stock_actual = st.number_input(
                    "Stock Actual:",
                    min_value=0.0,
                    value=0.0,
                    step=1.0
                )
            
            with col2:
                stock_minimo = st.number_input(
                    "Stock Mínimo:",
                    min_value=0.0,
                    value=0.0,
                    step=1.0,
                    help="Cantidad mínima antes de alerta"
                )
            
            with col3:
                stock_maximo = st.number_input(
                    "Stock Máximo:",
                    min_value=0.0,
                    value=0.0,
                    step=1.0,
                    help="Cantidad máxima recomendada"
                )
        else:
            stock_actual = None
            stock_minimo = None
            stock_maximo = None
        
        # Estados y configuraciones
        st.markdown("#### ⚙️ Estados y Configuración")
        
        col1, col2 = st.columns(2)
        
        with col1:
            estado_producto = st.selectbox(
                "Estado:",
                ["ACTIVO", "INACTIVO", "DESCONTINUADO"],
                help="Estado del producto en el sistema"
            )
        
        with col2:
            codigo_impuesto = st.text_input(
                "Código de Impuesto:",
                help="Código de impuesto para reportes"
            )
        
        descripcion = st.text_area(
            "Descripción:",
            help="Descripción detallada del producto"
        )
        
        # Botón de envío
        submitted = st.form_submit_button(
            "📦 Registrar Producto",
            use_container_width=True,
            type="primary"
        )
        
        if submitted:
            if not codigo_producto or not nombre or not precio_venta or precio_venta <= 0:
                st.error("❌ Complete los campos obligatorios marcados con *")
            else:
                crear_producto_completo(
                    backend_url,
                    {
                        "codigo_producto": codigo_producto,
                        "nombre": nombre,
                        "descripcion": descripcion if descripcion else None,
                        "tipo_producto": tipo_producto,
                        "categoria_producto": categoria_producto if categoria_producto else None,
                        "unidad_medida": unidad_medida,
                        "precio_venta": precio_venta,
                        "precio_compra": precio_compra,
                        "margen_utilidad": margen_utilidad,
                        "aplica_iva": aplica_iva,
                        "porcentaje_iva": float(porcentaje_iva),
                        "codigo_impuesto": codigo_impuesto if codigo_impuesto else None,
                        "maneja_inventario": maneja_inventario,
                        "stock_actual": float(stock_actual) if stock_actual is not None else 0.0,
                        "stock_minimo": float(stock_minimo) if stock_minimo is not None else 0.0,
                        "stock_maximo": float(stock_maximo) if stock_maximo is not None else 0.0,
                        "estado_producto": estado_producto
                    }
                )

def crear_producto_completo(backend_url: str, datos_producto: Dict[str, Any]):
    """Crear producto con datos completos"""
    
    try:
        # Limpiar datos vacíos (excepto False y 0 que son válidos)
        datos_limpios = {
            k: v for k, v in datos_producto.items() 
            if v is not None and v != ""
        }
        
        with st.spinner("Registrando producto..."):
            response = requests.post(f"{backend_url}/api/productos", json=datos_limpios)
        
        if response.status_code == 201:
            producto_creado = response.json()
            st.success(f"✅ Producto '{datos_producto['nombre']}' registrado exitosamente!")
            st.balloons()
            
            # Mostrar resumen del producto creado
            with st.expander("📄 Resumen del Producto Registrado", expanded=True):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**ID:** {producto_creado.get('id_producto', 'N/A')}")
                    st.write(f"**Código:** {producto_creado.get('codigo_producto')}")
                    st.write(f"**Nombre:** {producto_creado.get('nombre')}")
                    st.write(f"**Tipo:** {producto_creado.get('tipo_producto')}")
                
                with col2:
                    precio_v = float(producto_creado.get('precio_venta', 0))
                    iva_p = float(producto_creado.get('porcentaje_iva', 0))
                    st.write(f"**Precio Venta:** ${precio_v:,.2f}")
                    st.write(f"**IVA:** {iva_p}%")
                    st.write(f"**Estado:** {producto_creado.get('estado_producto')}")
            
        else:
            error_detail = response.json().get('detail', 'Error desconocido')
            st.error(f"❌ Error al registrar producto: {error_detail}")
            
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Error de conexión: {e}")
    except Exception as e:
        st.error(f"❌ Error inesperado: {e}")

def lista_productos(backend_url: str):
    """Lista y gestión de productos existentes"""
    
    st.subheader("📋 Lista de Productos")
    
    # Controles superiores
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        buscar_texto = st.text_input(
            "🔍 Buscar:",
            placeholder="Nombre, código..."
        )
    
    with col2:
        filtro_tipo = st.selectbox(
            "Tipo:",
            ["Todos", "PRODUCTO", "SERVICIO", "COMBO"]
        )
    
    with col3:
        filtro_estado = st.selectbox(
            "Estado:",
            ["Todos", "Activos", "Inactivos"]
        )
    
    with col4:
        if st.button("🔄 Actualizar", use_container_width=True):
            st.rerun()
    
    # Obtener y mostrar productos
    try:
        params = {}
        if buscar_texto:
            params["buscar"] = buscar_texto
        if filtro_tipo != "Todos":
            params["tipo"] = filtro_tipo
        if filtro_estado != "Todos":
            params["activo"] = filtro_estado == "Activos"
        
        with st.spinner("Cargando productos..."):
            response = requests.get(f"{backend_url}/api/productos", params=params)
        
        if response.status_code == 200:
            productos = response.json()
            
            if productos:
                mostrar_tabla_productos(productos, backend_url)
            else:
                st.info("📭 No se encontraron productos con los criterios especificados")
        else:
            st.error(f"Error al cargar productos: {response.status_code}")
            
    except Exception as e:
        st.error(f"Error al cargar productos: {e}")

def mostrar_tabla_productos(productos: List[Dict], backend_url: str):
    """Mostrar tabla de productos con opciones de gestión"""
    
    # Métricas resumen
    total_productos = len(productos)
    productos_activos = len([p for p in productos if p.get('estado_producto') == 'ACTIVO'])
    productos_servicios = len([p for p in productos if p.get('tipo_producto') == 'SERVICIO'])
    
    # Calcular valor de inventario con conversión segura de tipos
    valor_inventario = 0
    for p in productos:
        try:
            precio = float(p.get('precio_venta', 0))
            stock = float(p.get('stock_actual', 0))
            valor_inventario += precio * stock
        except (ValueError, TypeError):
            continue
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Productos", total_productos)
    
    with col2:
        st.metric("Activos", productos_activos)
    
    with col3:
        st.metric("Servicios", productos_servicios)
    
    with col4:
        st.metric("Valor Inventario", f"${valor_inventario:,.0f}")
    
    # Tabla de productos
    df_productos = pd.DataFrame(productos)
    
    # Preparar columnas para mostrar
    if not df_productos.empty:
        # Formatear columnas
        df_display = df_productos.copy()
        
        # Formatear precios con conversión segura a float
        if 'precio_venta' in df_display.columns:
            df_display['precio_venta_fmt'] = df_display['precio_venta'].apply(
                lambda x: f"${float(x):,.2f}" if x is not None else "$0.00"
            )
        elif 'precio' in df_display.columns:
            df_display['precio_fmt'] = df_display['precio'].apply(
                lambda x: f"${float(x):,.2f}" if x is not None else "$0.00"
            )
        
        # Estado como emoji - usar estado_producto en lugar de activo
        if 'estado_producto' in df_display.columns:
            df_display['estado_emoji'] = df_display['estado_producto'].apply(
                lambda x: "🟢 Activo" if x == "ACTIVO" else "🔴 Inactivo"
            )
        elif 'activo' in df_display.columns:
            df_display['estado_emoji'] = df_display['activo'].apply(
                lambda x: "🟢 Activo" if x else "🔴 Inactivo"
            )
        
        # Stock con alertas
        if 'stock_actual' in df_display.columns and 'stock_minimo' in df_display.columns:
            def formato_stock(row):
                try:
                    stock = float(row['stock_actual']) if row['stock_actual'] is not None else 0.0
                    minimo = float(row['stock_minimo']) if row['stock_minimo'] is not None else 0.0
                    if stock <= minimo and minimo > 0:
                        return f"⚠️ {stock:.0f}"
                    return f"{stock:.0f}"
                except (ValueError, TypeError, KeyError):
                    return "0"
            
            df_display['stock_fmt'] = df_display.apply(formato_stock, axis=1)
        elif 'stock_actual' in df_display.columns:
            # Si solo existe stock_actual sin stock_minimo
            df_display['stock_fmt'] = df_display['stock_actual'].apply(
                lambda x: f"{float(x):.0f}" if x is not None else "0"
            )
        
        # Normalizar nombre de columna categoria
        if 'categoria_producto' in df_display.columns and 'categoria' not in df_display.columns:
            df_display['categoria'] = df_display['categoria_producto']
        
        # Seleccionar columnas principales
        columnas_principales = [
            'codigo_producto', 'nombre', 'tipo_producto', 'categoria',
            'precio_venta_fmt', 'precio_fmt', 'stock_fmt', 'estado_emoji'
        ]
        
        # Verificar que las columnas existan
        columnas_mostrar = [col for col in columnas_principales if col in df_display.columns]
        
        if columnas_mostrar:
            df_tabla = df_display[columnas_mostrar].copy()
            
            # Renombrar columnas
            nombres_columnas = {
                'codigo_producto': 'Código',
                'nombre': 'Nombre',
                'tipo_producto': 'Tipo',
                'categoria': 'Categoría',
                'precio_venta_fmt': 'Precio',
                'precio_fmt': 'Precio',
                'stock_fmt': 'Stock',
                'estado_emoji': 'Estado'
            }
            
            df_tabla.columns = [nombres_columnas.get(col, col) for col in df_tabla.columns]
            
            # Preparar dataframe editable con stock numérico
            df_editable = df_display[['id_producto', 'codigo_producto', 'nombre', 'tipo_producto', 
                                       'categoria', 'precio_venta', 'stock_actual', 'stock_minimo', 
                                       'stock_maximo', 'estado_producto']].copy() if all(col in df_display.columns for col in ['id_producto', 'stock_actual']) else None
            
            # Mostrar tabla editable si tiene columnas de stock
            if df_editable is not None and 'stock_actual' in df_editable.columns:
                st.markdown("##### 📝 Editar Stock Directamente en la Tabla")
                st.caption("Modifique los valores de stock y presione Enter para guardar")
                
                edited_df = st.data_editor(
                    df_editable,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "id_producto": st.column_config.NumberColumn("ID", disabled=True),
                        "codigo_producto": st.column_config.TextColumn("Código", disabled=True),
                        "nombre": st.column_config.TextColumn("Nombre", disabled=True),
                        "tipo_producto": st.column_config.TextColumn("Tipo", disabled=True),
                        "categoria": st.column_config.TextColumn("Categoría", disabled=True),
                        "precio_venta": st.column_config.NumberColumn("Precio", disabled=True, format="$%.2f"),
                        "stock_actual": st.column_config.NumberColumn("Stock Actual", min_value=0, step=1, format="%.0f"),
                        "stock_minimo": st.column_config.NumberColumn("Stock Mínimo", min_value=0, step=1, format="%.0f"),
                        "stock_maximo": st.column_config.NumberColumn("Stock Máximo", min_value=0, step=1, format="%.0f"),
                        "estado_producto": st.column_config.TextColumn("Estado", disabled=True)
                    },
                    disabled=["id_producto", "codigo_producto", "nombre", "tipo_producto", "categoria", "precio_venta", "estado_producto"],
                    key="editor_productos"
                )
                
                # Detectar cambios y actualizar
                if not edited_df.equals(df_editable):
                    col1, col2 = st.columns([1, 4])
                    with col1:
                        if st.button("💾 Guardar Cambios de Stock", type="primary"):
                            actualizar_stocks_masivo(backend_url, df_editable, edited_df)
                    with col2:
                        st.info("⚠️ Hay cambios sin guardar. Presione 'Guardar Cambios de Stock' para aplicarlos.")
                
                st.markdown("---")
                st.markdown("##### 📋 Vista de Solo Lectura")
            
            # Mostrar tabla de solo lectura
            event = st.dataframe(
                df_tabla,
                use_container_width=True,
                hide_index=True,
                on_select="rerun",
                selection_mode="single-row"
            )
            
            # Acciones sobre producto seleccionado
            if event.selection.rows:
                producto_idx = event.selection.rows[0]
                producto_seleccionado = productos[producto_idx]
                
                st.markdown("---")
                st.markdown("### 🔧 Acciones sobre Producto Seleccionado")
                
                # Botones de acción
                col1, col2, col3, col4, col5 = st.columns(5)
                
                ver_detalles = False
                editar = False
                actualizar_precio = False
                
                with col1:
                    if st.button("👁️ Ver Detalles", use_container_width=True, key="btn_ver_detalles"):
                        ver_detalles = True
                
                with col2:
                    if st.button("✏️ Editar", use_container_width=True, key="btn_editar"):
                        editar = True
                
                with col3:
                    if st.button("💰 Actualizar Precio", use_container_width=True, key="btn_actualizar_precio"):
                        actualizar_precio = True
                
                with col4:
                    estado_actual = producto_seleccionado.get('estado_producto', 'ACTIVO')
                    if estado_actual == 'ACTIVO':
                        nuevo_estado = 'INACTIVO'
                        accion_estado = "🔴 Desactivar"
                    else:
                        nuevo_estado = 'ACTIVO'
                        accion_estado = "🟢 Activar"
                    
                    if st.button(accion_estado, use_container_width=True, key="btn_cambiar_estado"):
                        cambiar_estado_producto(backend_url, producto_seleccionado['id_producto'], nuevo_estado)
                
                with col5:
                    if st.button("🗑️ Eliminar", use_container_width=True, key="btn_eliminar"):
                        if st.checkbox("Confirmar eliminación", key=f"confirm_del_prod_{producto_seleccionado['id_producto']}"):
                            eliminar_producto(backend_url, producto_seleccionado['id_producto'])
                
                # Mostrar vistas en contenedor de ancho completo
                st.markdown("---")
                
                if ver_detalles:
                    with st.container():
                        mostrar_detalle_producto(producto_seleccionado)
                
                if editar:
                    with st.container():
                        editar_producto(backend_url, producto_seleccionado)
                
                if actualizar_precio:
                    with st.container():
                        actualizar_precio_producto(backend_url, producto_seleccionado)

def mostrar_detalle_producto(producto: Dict[str, Any]):
    """Mostrar detalle completo de un producto"""
    
    # Encabezado destacado
    st.markdown(f"## 📦 {producto.get('nombre', 'N/A')}")
    st.caption(f"Código: {producto.get('codigo_producto', 'N/A')}")
    
    st.markdown("---")
    
    # Información principal en tarjetas con mejor espaciado
    col1, col2 = st.columns(2, gap="large")
    
    with col1:
        with st.container():
            st.markdown("### 📋 Información Básica")
            st.markdown("")
            
            # Usar tabla para mejor visualización
            info_data = {
                "Campo": ["Tipo", "Categoría", "Unidad de Medida"],
                "Valor": [
                    producto.get('tipo_producto', 'N/A'),
                    producto.get('categoria_producto', producto.get('categoria', 'N/A')),
                    producto.get('unidad_medida', 'N/A')
                ]
            }
            st.table(pd.DataFrame(info_data))
            
            if producto.get('descripcion'):
                st.markdown("")
                st.markdown("**📝 Descripción:**")
                st.info(producto['descripcion'])
    
    with col2:
        with st.container():
            st.markdown("### 💰 Información Comercial")
            st.markdown("")
            
            # Convertir precios a float de manera segura
            try:
                precio_venta = float(producto.get('precio_venta', 0))
                precio_compra = float(producto.get('precio_compra', producto.get('precio_costo', 0)))
                porcentaje_iva = float(producto.get('porcentaje_iva', producto.get('iva_porcentaje', 0)))
            except (ValueError, TypeError):
                precio_venta = 0.0
                precio_compra = 0.0
                porcentaje_iva = 0.0
            
            # Calcular margen
            if precio_compra > 0:
                margen = ((precio_venta - precio_compra) / precio_compra) * 100
            else:
                margen = 0
            
            # Métricas grandes y visibles
            col_a, col_b = st.columns(2)
            with col_a:
                st.metric("💵 Precio Venta", f"${precio_venta:,.2f}")
                st.metric("📈 Margen", f"{margen:.1f}%")
            
            with col_b:
                st.metric("💳 Precio Compra", f"${precio_compra:,.2f}")
                st.metric("📊 IVA", f"{porcentaje_iva:.0f}%")
            
            # Estado con color
            estado = producto.get('estado_producto', 'N/A')
            if estado == 'ACTIVO':
                st.success(f"✅ Estado: {estado}")
            elif estado == 'INACTIVO':
                st.error(f"❌ Estado: {estado}")
            else:
                st.warning(f"⚠️ Estado: {estado}")
    
    # Información de inventario si existe
    if producto.get('stock_actual') is not None or producto.get('maneja_inventario'):
        st.markdown("")
        st.markdown("---")
        st.markdown("### 📦 Control de Inventario")
        st.markdown("")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            stock_actual = float(producto.get('stock_actual', 0))
            st.metric("📦 Stock Actual", f"{stock_actual:.0f} unidades")
        
        with col2:
            stock_minimo = float(producto.get('stock_minimo', 0))
            st.metric("⚠️ Stock Mínimo", f"{stock_minimo:.0f} unidades")
        
        with col3:
            stock_maximo = float(producto.get('stock_maximo', 0))
            st.metric("📈 Stock Máximo", f"{stock_maximo:.0f} unidades")
        
        with col4:
            if stock_actual > 0 and precio_venta > 0:
                valor_inventario = stock_actual * precio_venta
                st.metric("💰 Valor Inventario", f"${valor_inventario:,.2f}")

def editar_producto(backend_url: str, producto: Dict[str, Any]):
    """Formulario para editar producto"""
    
    st.markdown(f"## ✏️ Editar Producto")
    st.markdown(f"### {producto.get('nombre', 'N/A')}")
    st.caption(f"Código: {producto.get('codigo_producto', 'N/A')}")
    st.markdown("---")
    
    with st.form(f"form_editar_producto_{producto['id_producto']}", clear_on_submit=False):
        col1, col2 = st.columns(2, gap="large")
        
        with col1:
            st.markdown("#### 📋 Información Básica")
            
            codigo_producto = st.text_input(
                "Código Producto:",
                value=producto.get('codigo_producto', ''),
                disabled=True,
                help="El código no se puede modificar"
            )
            
            nombre = st.text_input(
                "Nombre*:",
                value=producto.get('nombre', ''),
                help="Nombre del producto o servicio"
            )
            
            tipo_producto = st.selectbox(
                "Tipo:",
                ["PRODUCTO", "SERVICIO", "COMBO"],
                index=["PRODUCTO", "SERVICIO", "COMBO"].index(producto.get('tipo_producto', 'PRODUCTO')) if producto.get('tipo_producto') in ["PRODUCTO", "SERVICIO", "COMBO"] else 0,
                help="Tipo de producto"
            )
            
            categoria_producto = st.text_input(
                "Categoría:",
                value=producto.get('categoria_producto', ''),
                help="Categoría del producto"
            )
            
            unidad_medida = st.selectbox(
                "Unidad de Medida:",
                ["UNIDAD", "KG", "METRO", "LITRO", "CAJA", "PAQUETE", "DOCENA", "PAR", "HORA", "SERVICIO"],
                index=["UNIDAD", "KG", "METRO", "LITRO", "CAJA", "PAQUETE", "DOCENA", "PAR", "HORA", "SERVICIO"].index(producto.get('unidad_medida', 'UNIDAD')) if producto.get('unidad_medida') in ["UNIDAD", "KG", "METRO", "LITRO", "CAJA", "PAQUETE", "DOCENA", "PAR", "HORA", "SERVICIO"] else 0,
                help="Unidad de medida"
            )
            
            descripcion = st.text_area(
                "Descripción:",
                value=producto.get('descripcion', ''),
                help="Descripción detallada"
            )
        
        with col2:
            st.markdown("#### 💰 Información Comercial")
            
            precio_venta = producto.get('precio_venta', 0)
            precio_venta_float = float(precio_venta) if precio_venta else 0.0
            
            precio = st.number_input(
                "Precio de Venta*:",
                value=precio_venta_float,
                min_value=0.0,
                step=0.01,
                help="Precio de venta al público"
            )
            
            precio_compra = producto.get('precio_compra', 0)
            precio_compra_float = float(precio_compra) if precio_compra else 0.0
            
            precio_costo = st.number_input(
                "Precio de Compra:",
                value=precio_compra_float,
                min_value=0.0,
                step=0.01,
                help="Costo de adquisición"
            )
            
            # Calcular margen de utilidad
            if precio_costo > 0 and precio > 0:
                margen_actual = ((precio - precio_costo) / precio_costo) * 100
                st.info(f"📊 Margen de Utilidad Actual: {margen_actual:.1f}%")
            
            porcentaje_iva_actual = producto.get('porcentaje_iva', 13)
            try:
                porcentaje_iva_actual = int(float(porcentaje_iva_actual))
            except (ValueError, TypeError):
                porcentaje_iva_actual = 13
            
            iva_porcentaje = st.selectbox(
                "IVA (%):",
                [0, 5, 13, 19],
                index=[0, 5, 13, 19].index(porcentaje_iva_actual) if porcentaje_iva_actual in [0, 5, 13, 19] else 2,
                help="Porcentaje de IVA"
            )
            
            st.markdown("#### ⚙️ Estado")
            
            estado_producto = st.selectbox(
                "Estado del Producto:",
                ["ACTIVO", "INACTIVO", "DESCONTINUADO"],
                index=["ACTIVO", "INACTIVO", "DESCONTINUADO"].index(producto.get('estado_producto', 'ACTIVO')) if producto.get('estado_producto') in ["ACTIVO", "INACTIVO", "DESCONTINUADO"] else 0,
                help="Estado del producto en el sistema"
            )
        
        # Información de inventario si existe
        if producto.get('maneja_inventario') or producto.get('stock_actual') is not None:
            st.markdown("#### 📦 Control de Inventario")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                stock_actual = st.number_input(
                    "Stock Actual:",
                    value=float(producto.get('stock_actual', 0)),
                    min_value=0.0,
                    step=1.0
                )
            
            with col2:
                stock_minimo = st.number_input(
                    "Stock Mínimo:",
                    value=float(producto.get('stock_minimo', 0)),
                    min_value=0.0,
                    step=1.0
                )
            
            with col3:
                stock_maximo = st.number_input(
                    "Stock Máximo:",
                    value=float(producto.get('stock_maximo', 0)),
                    min_value=0.0,
                    step=1.0
                )
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            submitted = st.form_submit_button("💾 Actualizar Producto", use_container_width=True, type="primary")
        
        with col2:
            cancelar = st.form_submit_button("❌ Cancelar", use_container_width=True)
        
        if submitted:
            if not nombre or not precio or precio <= 0:
                st.error("❌ Complete los campos obligatorios marcados con *")
            else:
                datos_actualizacion = {
                    "nombre": nombre,
                    "descripcion": descripcion if descripcion else None,
                    "tipo_producto": tipo_producto,
                    "categoria_producto": categoria_producto if categoria_producto else None,
                    "unidad_medida": unidad_medida,
                    "precio_venta": precio,
                    "precio_compra": precio_costo,
                    "porcentaje_iva": float(iva_porcentaje),
                    "estado_producto": estado_producto
                }
                
                # Agregar datos de inventario si existen
                if producto.get('maneja_inventario') or producto.get('stock_actual') is not None:
                    datos_actualizacion["stock_actual"] = stock_actual
                    datos_actualizacion["stock_minimo"] = stock_minimo
                    datos_actualizacion["stock_maximo"] = stock_maximo
                
                actualizar_producto_backend(backend_url, producto['id_producto'], datos_actualizacion)
        
        if cancelar:
            st.rerun()

def actualizar_precio_producto(backend_url: str, producto: Dict[str, Any]):
    """Actualización rápida de precio"""
    
    st.markdown(f"## 💰 Actualizar Precio")
    st.markdown(f"### {producto.get('nombre', 'N/A')}")
    st.caption(f"Código: {producto.get('codigo_producto', 'N/A')}")
    st.markdown("---")
    
    # Convertir precio actual a float de manera segura
    try:
        precio_actual = float(producto.get('precio_venta', producto.get('precio', 0)))
    except (ValueError, TypeError):
        precio_actual = 0.0
    
    with st.form(f"form_precio_{producto['id_producto']}", clear_on_submit=False):
        st.markdown("### 📊 Información Actual")
        st.markdown("")
        
        col1, col2, col3 = st.columns(3, gap="medium")
        
        with col1:
            st.metric("💵 Precio Actual", f"${precio_actual:,.2f}")
        
        with col2:
            try:
                precio_compra = float(producto.get('precio_compra', producto.get('precio_costo', 0)))
            except (ValueError, TypeError):
                precio_compra = 0.0
            st.metric("💳 Precio Compra", f"${precio_compra:,.2f}")
        
        with col3:
            if precio_compra > 0 and precio_actual > 0:
                margen_actual = ((precio_actual - precio_compra) / precio_compra) * 100
                st.metric("📈 Margen Actual", f"{margen_actual:.1f}%")
        
        st.markdown("---")
        
        nuevo_precio = st.number_input(
            "💰 Nuevo Precio de Venta*:",
            value=precio_actual,
            step=0.01,
            min_value=0.01,
            help="Ingrese el nuevo precio de venta"
        )
        
        # Mostrar variación y nuevo margen
        col1, col2 = st.columns(2)
        
        with col1:
            if precio_actual > 0:
                variacion = ((nuevo_precio - precio_actual) / precio_actual) * 100
                delta_color = "normal" if variacion >= 0 else "inverse"
                st.metric("Variación", f"{variacion:+.1f}%", delta=f"${nuevo_precio - precio_actual:+,.2f}")
        
        with col2:
            if precio_compra > 0:
                nuevo_margen = ((nuevo_precio - precio_compra) / precio_compra) * 100
                st.metric("Nuevo Margen", f"{nuevo_margen:.1f}%")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            submitted = st.form_submit_button("💰 Actualizar Precio", use_container_width=True, type="primary")
        
        with col2:
            cancelar = st.form_submit_button("❌ Cancelar", use_container_width=True)
        
        if submitted:
            if nuevo_precio <= 0:
                st.error("❌ El precio debe ser mayor a 0")
            else:
                datos_precio = {
                    "precio_venta": nuevo_precio
                }
                actualizar_producto_backend(backend_url, producto['id_producto'], datos_precio)
        
        if cancelar:
            st.rerun()

def actualizar_producto_backend(backend_url: str, id_producto: int, datos: Dict[str, Any]):
    """Actualizar producto en el backend"""
    
    try:
        with st.spinner("Actualizando producto..."):
            response = requests.put(f"{backend_url}/api/productos/{id_producto}", json=datos)
        
        if response.status_code == 200:
            st.success("✅ Producto actualizado exitosamente")
            st.rerun()
        else:
            error_detail = response.json().get('detail', 'Error desconocido')
            st.error(f"❌ Error al actualizar producto: {error_detail}")
            
    except Exception as e:
        st.error(f"❌ Error al actualizar producto: {e}")

def actualizar_stocks_masivo(backend_url: str, df_original: pd.DataFrame, df_editado: pd.DataFrame):
    """Actualizar stocks de múltiples productos que fueron editados"""
    
    try:
        cambios = []
        errores = []
        
        # Detectar cambios fila por fila
        for idx in df_editado.index:
            id_producto = int(df_editado.loc[idx, 'id_producto'])
            
            # Verificar si hubo cambios en stock
            stock_actual_original = float(df_original.loc[idx, 'stock_actual']) if df_original.loc[idx, 'stock_actual'] is not None else 0
            stock_minimo_original = float(df_original.loc[idx, 'stock_minimo']) if df_original.loc[idx, 'stock_minimo'] is not None else 0
            stock_maximo_original = float(df_original.loc[idx, 'stock_maximo']) if df_original.loc[idx, 'stock_maximo'] is not None else 0
            
            stock_actual_nuevo = float(df_editado.loc[idx, 'stock_actual']) if df_editado.loc[idx, 'stock_actual'] is not None else 0
            stock_minimo_nuevo = float(df_editado.loc[idx, 'stock_minimo']) if df_editado.loc[idx, 'stock_minimo'] is not None else 0
            stock_maximo_nuevo = float(df_editado.loc[idx, 'stock_maximo']) if df_editado.loc[idx, 'stock_maximo'] is not None else 0
            
            if (stock_actual_original != stock_actual_nuevo or 
                stock_minimo_original != stock_minimo_nuevo or 
                stock_maximo_original != stock_maximo_nuevo):
                
                datos_actualizacion = {
                    "stock_actual": stock_actual_nuevo,
                    "stock_minimo": stock_minimo_nuevo,
                    "stock_maximo": stock_maximo_nuevo
                }
                
                response = requests.put(f"{backend_url}/api/productos/{id_producto}", json=datos_actualizacion)
                
                if response.status_code == 200:
                    nombre_producto = df_editado.loc[idx, 'nombre']
                    cambios.append(f"✅ {nombre_producto}: Stock actualizado")
                else:
                    nombre_producto = df_editado.loc[idx, 'nombre']
                    error_detail = response.json().get('detail', 'Error desconocido')
                    errores.append(f"❌ {nombre_producto}: {error_detail}")
        
        # Mostrar resultados
        if cambios:
            st.success(f"✅ {len(cambios)} producto(s) actualizado(s) exitosamente")
            with st.expander("Ver detalles de actualización"):
                for cambio in cambios:
                    st.write(cambio)
            st.rerun()
        
        if errores:
            st.error(f"❌ {len(errores)} error(es) al actualizar")
            with st.expander("Ver errores"):
                for error in errores:
                    st.write(error)
        
        if not cambios and not errores:
            st.info("ℹ️ No se detectaron cambios en los stocks")
            
    except Exception as e:
        st.error(f"❌ Error al actualizar stocks: {e}")

def cambiar_estado_producto(backend_url: str, id_producto: int, nuevo_estado_producto: str):
    """Cambiar estado del producto (ACTIVO/INACTIVO/DESCONTINUADO)"""
    
    try:
        with st.spinner("Cambiando estado..."):
            # Usar PUT para actualizar el estado del producto
            response = requests.put(
                f"{backend_url}/api/productos/{id_producto}",
                json={"estado_producto": nuevo_estado_producto}
            )
        
        if response.status_code == 200:
            st.success(f"✅ Producto actualizado a estado: {nuevo_estado_producto}")
            st.rerun()
        else:
            error_detail = response.json().get('detail', 'Error desconocido')
            st.error(f"❌ Error al cambiar estado: {error_detail}")
            
    except Exception as e:
        st.error(f"❌ Error al cambiar estado: {e}")

def eliminar_producto(backend_url: str, id_producto: int):
    """Eliminar producto"""
    
    try:
        with st.spinner("Eliminando producto..."):
            response = requests.delete(f"{backend_url}/api/productos/{id_producto}")
        
        if response.status_code == 200:
            st.success("✅ Producto eliminado exitosamente")
            st.rerun()
        else:
            st.error(f"Error al eliminar producto: {response.status_code}")
            
    except Exception as e:
        st.error(f"Error al eliminar producto: {e}")

def analisis_productos(backend_url: str):
    """Análisis y estadísticas de productos"""
    
    st.subheader("📊 Análisis de Productos")
    
    try:
        # Obtener datos para análisis
        with st.spinner("Cargando datos para análisis..."):
            response = requests.get(f"{backend_url}/api/productos/analisis")
        
        if response.status_code == 200:
            datos_analisis = response.json()
            mostrar_analisis_productos(datos_analisis)
        else:
            # Si no existe endpoint específico, usar datos de productos normales
            response_productos = requests.get(f"{backend_url}/api/productos")
            if response_productos.status_code == 200:
                productos = response_productos.json()
                generar_analisis_basico_productos(productos)
            else:
                st.error("Error al cargar datos para análisis")
                
    except Exception as e:
        st.error(f"Error al cargar análisis: {e}")

def mostrar_analisis_productos(datos: Dict[str, Any]):
    """Mostrar análisis completo de productos"""
    
    # Métricas principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Productos", datos.get('total_productos', 0))
    
    with col2:
        st.metric("Productos Activos", datos.get('productos_activos', 0))
    
    with col3:
        st.metric("Categorías", datos.get('total_categorias', 0))
    
    with col4:
        st.metric("Valor Promedio", f"${datos.get('precio_promedio', 0):,.2f}")
    
    # Gráficos de análisis
    if 'distribucion_tipos' in datos:
        st.markdown("### 📊 Distribución por Tipo")
        
        tipos = datos['distribucion_tipos']
        df_tipos = pd.DataFrame(list(tipos.items()), columns=['Tipo', 'Cantidad'])
        
        fig_pie = px.pie(df_tipos, values='Cantidad', names='Tipo', 
                        title='Distribución de Productos por Tipo')
        st.plotly_chart(fig_pie, use_container_width=True)

def generar_analisis_basico_productos(productos: List[Dict]):
    """Generar análisis básico con datos de productos"""
    
    if not productos:
        st.info("📭 No hay datos de productos para analizar")
        return
    
    df_productos = pd.DataFrame(productos)
    
    # Métricas básicas
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Productos", len(df_productos))
    
    with col2:
        productos_activos = len(df_productos[df_productos.get('activo', True) == True])
        st.metric("Productos Activos", productos_activos)
    
    with col3:
        if 'categoria' in df_productos.columns:
            categorias_unicas = df_productos['categoria'].nunique()
            st.metric("Categorías", categorias_unicas)
        else:
            st.metric("Categorías", "N/A")
    
    with col4:
        # Obtener precio de cualquier columna disponible
        precio_col = None
        for col in ['precio_venta', 'precio']:
            if col in df_productos.columns:
                precio_col = col
                break
        
        if precio_col:
            precio_promedio = df_productos[precio_col].mean()
            st.metric("Precio Promedio", f"${precio_promedio:,.2f}")
        else:
            st.metric("Precio Promedio", "N/A")
    
    # Gráfico de distribución por tipo
    if 'tipo_producto' in df_productos.columns:
        st.markdown("### 📊 Distribución por Tipo de Producto")
        
        tipo_counts = df_productos['tipo_producto'].value_counts()
        fig_tipo = px.pie(values=tipo_counts.values, names=tipo_counts.index,
                         title='Distribución por Tipo de Producto')
        st.plotly_chart(fig_tipo, use_container_width=True)
    
    # Análisis de precios
    if precio_col:
        st.markdown("### 💰 Análisis de Precios")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Histograma de precios
            fig_hist = px.histogram(df_productos, x=precio_col, 
                                  title='Distribución de Precios',
                                  nbins=20)
            st.plotly_chart(fig_hist, use_container_width=True)
        
        with col2:
            # Top productos por precio
            top_productos = df_productos.nlargest(10, precio_col)
            fig_bar = px.bar(top_productos, x='nombre', y=precio_col,
                           title='Top 10 Productos por Precio')
            fig_bar.update_xaxes(tickangle=45)
            st.plotly_chart(fig_bar, use_container_width=True)
    
    # Análisis de stock si existe
    if 'stock_actual' in df_productos.columns and 'stock_minimo' in df_productos.columns:
        st.markdown("### 📦 Análisis de Inventario")
        
        # Productos con stock bajo
        df_stock_bajo = df_productos[
            (df_productos['stock_actual'] <= df_productos['stock_minimo']) & 
            (df_productos['stock_minimo'] > 0)
        ]
        
        if len(df_stock_bajo) > 0:
            st.warning(f"⚠️ {len(df_stock_bajo)} productos con stock bajo")
            
            # Mostrar productos con stock bajo
            df_stock_display = df_stock_bajo[['codigo_producto', 'nombre', 'stock_actual', 'stock_minimo']].copy()
            df_stock_display.columns = ['Código', 'Producto', 'Stock Actual', 'Stock Mínimo']
            st.dataframe(df_stock_display, use_container_width=True, hide_index=True)
        else:
            st.success("✅ Todos los productos tienen stock adecuado")

def gestion_categorias(backend_url: str):
    """Gestión de categorías de productos"""
    
    st.subheader("🏷️ Gestión de Categorías")
    
    # Tabs para categorías
    tab_lista, tab_nueva = st.tabs(["📋 Lista de Categorías", "➕ Nueva Categoría"])
    
    with tab_lista:
        listar_categorias(backend_url)
    
    with tab_nueva:
        crear_categoria(backend_url)

def listar_categorias(backend_url: str):
    """Listar categorías existentes"""
    
    try:
        # Obtener productos para extraer categorías
        response = requests.get(f"{backend_url}/api/productos")
        
        if response.status_code == 200:
            productos = response.json()
            
            # Extraer categorías únicas
            categorias = set()
            productos_por_categoria = {}
            
            for producto in productos:
                categoria = producto.get('categoria_producto')
                if categoria and categoria.strip():
                    categorias.add(categoria)
                    if categoria not in productos_por_categoria:
                        productos_por_categoria[categoria] = []
                    productos_por_categoria[categoria].append(producto)
            
            if categorias:
                st.markdown("### 📋 Categorías Existentes")
                
                for categoria in sorted(categorias):
                    productos_en_categoria = len(productos_por_categoria.get(categoria, []))
                    
                    with st.expander(f"🏷️ {categoria} ({productos_en_categoria} productos)"):
                        productos_cat = productos_por_categoria.get(categoria, [])
                        
                        if productos_cat:
                            # Mostrar estadísticas de la categoría
                            col1, col2, col3 = st.columns(3)
                            
                            # Convertir precios a float de manera segura
                            precios = []
                            for p in productos_cat:
                                try:
                                    precio = p.get('precio_venta', p.get('precio', 0))
                                    precios.append(float(precio) if precio else 0)
                                except (ValueError, TypeError):
                                    precios.append(0)
                            
                            with col1:
                                st.metric("Productos", len(productos_cat))
                            
                            with col2:
                                if precios and sum(precios) > 0:
                                    precio_promedio = sum(precios) / len(precios)
                                    st.metric("Precio Promedio", f"${precio_promedio:,.2f}")
                                else:
                                    st.metric("Precio Promedio", "$0.00")
                            
                            with col3:
                                productos_activos_cat = len([p for p in productos_cat if p.get('estado_producto') == 'ACTIVO'])
                                st.metric("Activos", productos_activos_cat)
                            
                            # Lista de productos
                            df_cat = pd.DataFrame(productos_cat)
                            if not df_cat.empty:
                                df_display = df_cat[['codigo_producto', 'nombre']].copy()
                                df_display.columns = ['Código', 'Nombre']
                                st.dataframe(df_display, use_container_width=True, hide_index=True)
            else:
                st.info("📭 No hay categorías definidas")
        else:
            st.error("Error al cargar productos para análisis de categorías")
            
    except Exception as e:
        st.error(f"Error al listar categorías: {e}")

def crear_categoria(backend_url: str):
    """Crear nueva categoría"""
    
    st.markdown("### ➕ Crear Nueva Categoría")
    st.info("ℹ️ Las categorías se crean automáticamente al asignar productos. Esta función te permite visualizar y planificar tus categorías.")
    
    with st.form("form_nueva_categoria", clear_on_submit=True):
        nombre_categoria = st.text_input(
            "Nombre de la Categoría*:",
            help="Nombre descriptivo de la categoría"
        )
        
        descripcion_categoria = st.text_area(
            "Descripción:",
            help="Descripción detallada de la categoría"
        )
        
        activa = st.checkbox("Categoría Activa", value=True)
        
        submitted = st.form_submit_button("🏷️ Registrar Categoría", use_container_width=True, type="primary")
    
    if submitted:
        if nombre_categoria.strip():
            st.success(f"✅ Categoría '{nombre_categoria}' registrada exitosamente!")
            st.info("💡 Para asignar productos a esta categoría, ve a 'Registrar Producto' o edita productos existentes.")
            
            # Mostrar resumen
            with st.expander("📄 Detalles de la Categoría", expanded=True):
                st.write(f"**Nombre:** {nombre_categoria}")
                if descripcion_categoria:
                    st.write(f"**Descripción:** {descripcion_categoria}")
                st.write(f"**Estado:** {'Activa' if activa else 'Inactiva'}")
        else:
            st.error("❌ Ingrese un nombre para la categoría")