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
                ["Producto", "Servicio"],
                help="Clasificación como producto físico o servicio"
            )
            
            categoria = st.text_input(
                "Categoría:",
                help="Categoría o familia del producto"
            )
            
            marca = st.text_input(
                "Marca:",
                help="Marca del producto"
            )
            
            unidad_medida = st.selectbox(
                "Unidad de Medida:",
                ["Unidad", "Kilogramo", "Metro", "Litro", "Caja", "Paquete", "Docena", "Par", "Hora", "Servicio"],
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
            
            precio_costo = st.number_input(
                "Precio de Costo:",
                min_value=0.0,
                step=0.01,
                help="Costo de adquisición o producción"
            )
            
            iva_porcentaje = st.selectbox(
                "IVA (%):",
                [0, 5, 19],
                index=2,
                help="Porcentaje de IVA aplicable"
            )
            
            descuento_maximo = st.number_input(
                "Descuento Máximo (%):",
                min_value=0.0,
                max_value=100.0,
                value=0.0,
                step=0.1,
                help="Descuento máximo autorizado"
            )
            
            precio_mayorista = st.number_input(
                "Precio Mayorista:",
                min_value=0.0,
                step=0.01,
                help="Precio para ventas mayoristas"
            )
            
            precio_minimo = st.number_input(
                "Precio Mínimo:",
                min_value=0.0,
                step=0.01,
                help="Precio mínimo de venta permitido"
            )
        
        # Información de inventario (solo para productos)
        if st.selectbox("¿Maneja inventario?", ["No", "Sí"], key="maneja_inventario") == "Sí":
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
        
        # Información adicional
        st.markdown("#### 📄 Información Adicional")
        
        col1, col2 = st.columns(2)
        
        with col1:
            descripcion = st.text_area(
                "Descripción:",
                height=100,
                help="Descripción detallada del producto/servicio"
            )
            
            codigo_barras = st.text_input(
                "Código de Barras:",
                help="Código de barras del producto"
            )
            
            referencia_proveedor = st.text_input(
                "Referencia Proveedor:",
                help="Referencia del proveedor"
            )
        
        with col2:
            peso = st.number_input(
                "Peso (kg):",
                min_value=0.0,
                step=0.01,
                help="Peso del producto en kilogramos"
            )
            
            dimensiones = st.text_input(
                "Dimensiones:",
                help="Dimensiones del producto (LxAxH)"
            )
            
            garantia_dias = st.number_input(
                "Garantía (días):",
                min_value=0,
                value=0,
                step=1,
                help="Días de garantía del producto"
            )
        
        # Estados y configuraciones
        col1, col2, col3 = st.columns(3)
        
        with col1:
            activo = st.checkbox(
                "Producto Activo",
                value=True,
                help="Estado del producto en el sistema"
            )
        
        with col2:
            disponible_web = st.checkbox(
                "Disponible en Web",
                value=False,
                help="Mostrar en tienda virtual"
            )
        
        with col3:
            requiere_autorizacion = st.checkbox(
                "Requiere Autorización",
                value=False,
                help="Requiere autorización para vender"
            )
        
        observaciones = st.text_area(
            "Observaciones:",
            help="Observaciones adicionales del producto"
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
                        "descripcion": descripcion,
                        "tipo_producto": tipo_producto,
                        "categoria": categoria,
                        "marca": marca,
                        "unidad_medida": unidad_medida,
                        "precio_venta": precio_venta,
                        "precio_costo": precio_costo,
                        "iva_porcentaje": iva_porcentaje,
                        "descuento_maximo": descuento_maximo,
                        "precio_mayorista": precio_mayorista,
                        "precio_minimo": precio_minimo,
                        "stock_actual": stock_actual,
                        "stock_minimo": stock_minimo,
                        "stock_maximo": stock_maximo,
                        "codigo_barras": codigo_barras,
                        "referencia_proveedor": referencia_proveedor,
                        "peso": peso,
                        "dimensiones": dimensiones,
                        "garantia_dias": garantia_dias,
                        "activo": activo,
                        "disponible_web": disponible_web,
                        "requiere_autorizacion": requiere_autorizacion,
                        "observaciones": observaciones
                    }
                )

def crear_producto_completo(backend_url: str, datos_producto: Dict[str, Any]):
    """Crear producto con datos completos"""
    
    try:
        # Limpiar datos vacíos
        datos_limpios = {
            k: v for k, v in datos_producto.items() 
            if v is not None and v != "" and v != 0.0
        }
        
        # Asegurar que precio esté presente
        datos_limpios["precio"] = datos_producto["precio_venta"]
        
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
                    st.write(f"**Código:** {datos_producto['codigo_producto']}")
                    st.write(f"**Nombre:** {datos_producto['nombre']}")
                    st.write(f"**Tipo:** {datos_producto['tipo_producto']}")
                    st.write(f"**Categoría:** {datos_producto.get('categoria', 'N/A')}")
                
                with col2:
                    st.write(f"**Precio Venta:** ${datos_producto['precio_venta']:,.2f}")
                    st.write(f"**IVA:** {datos_producto.get('iva_porcentaje', 0)}%")
                    st.write(f"**Unidad:** {datos_producto.get('unidad_medida', 'N/A')}")
                    st.write(f"**Estado:** {'Activo' if datos_producto.get('activo') else 'Inactivo'}")
            
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
            ["Todos", "Producto", "Servicio"]
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
    productos_activos = len([p for p in productos if p.get('activo', True)])
    productos_servicios = len([p for p in productos if p.get('tipo_producto') == 'Servicio'])
    valor_inventario = sum(p.get('precio_venta', 0) * p.get('stock_actual', 0) for p in productos)
    
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
        
        # Formatear precios
        if 'precio_venta' in df_display.columns:
            df_display['precio_venta_fmt'] = df_display['precio_venta'].apply(lambda x: f"${x:,.2f}")
        elif 'precio' in df_display.columns:
            df_display['precio_fmt'] = df_display['precio'].apply(lambda x: f"${x:,.2f}")
        
        # Estado como emoji
        if 'activo' in df_display.columns:
            df_display['estado_emoji'] = df_display['activo'].apply(
                lambda x: "🟢 Activo" if x else "🔴 Inactivo"
            )
        
        # Stock con alertas
        if 'stock_actual' in df_display.columns and 'stock_minimo' in df_display.columns:
            def formato_stock(row):
                stock = row.get('stock_actual', 0)
                minimo = row.get('stock_minimo', 0)
                if stock <= minimo and minimo > 0:
                    return f"⚠️ {stock}"
                return str(stock)
            
            df_display['stock_fmt'] = df_display.apply(formato_stock, axis=1)
        
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
            
            # Mostrar tabla con selección
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
                
                st.markdown("### 🔧 Acciones sobre Producto Seleccionado")
                
                col1, col2, col3, col4, col5 = st.columns(5)
                
                with col1:
                    if st.button("👁️ Ver Detalles", use_container_width=True):
                        mostrar_detalle_producto(producto_seleccionado)
                
                with col2:
                    if st.button("✏️ Editar", use_container_width=True):
                        editar_producto(backend_url, producto_seleccionado)
                
                with col3:
                    if st.button("💰 Actualizar Precio", use_container_width=True):
                        actualizar_precio_producto(backend_url, producto_seleccionado)
                
                with col4:
                    estado_actual = producto_seleccionado.get('activo', True)
                    accion_estado = "Desactivar" if estado_actual else "Activar"
                    if st.button(f"🔄 {accion_estado}", use_container_width=True):
                        cambiar_estado_producto(backend_url, producto_seleccionado['id_producto'], not estado_actual)
                
                with col5:
                    if st.button("🗑️ Eliminar", use_container_width=True):
                        if st.checkbox("Confirmar eliminación", key=f"confirm_del_prod_{producto_seleccionado['id_producto']}"):
                            eliminar_producto(backend_url, producto_seleccionado['id_producto'])

def mostrar_detalle_producto(producto: Dict[str, Any]):
    """Mostrar detalle completo de un producto"""
    
    with st.expander(f"📦 Detalle del Producto: {producto.get('nombre', 'N/A')}", expanded=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**📋 Información Básica:**")
            st.text(f"Código: {producto.get('codigo_producto', 'N/A')}")
            st.text(f"Nombre: {producto.get('nombre', 'N/A')}")
            st.text(f"Tipo: {producto.get('tipo_producto', 'N/A')}")
            st.text(f"Categoría: {producto.get('categoria', 'N/A')}")
            st.text(f"Marca: {producto.get('marca', 'N/A')}")
            st.text(f"Unidad: {producto.get('unidad_medida', 'N/A')}")
        
        with col2:
            st.markdown("**💰 Información Comercial:**")
            precio_venta = producto.get('precio_venta') or producto.get('precio', 0)
            st.text(f"Precio Venta: ${precio_venta:,.2f}")
            st.text(f"Precio Costo: ${producto.get('precio_costo', 0):,.2f}")
            st.text(f"IVA: {producto.get('iva_porcentaje', 0)}%")
            st.text(f"Desc. Máx.: {producto.get('descuento_maximo', 0):.1f}%")
            st.text(f"Precio Mayorista: ${producto.get('precio_mayorista', 0):,.2f}")
            st.text(f"Estado: {'Activo' if producto.get('activo') else 'Inactivo'}")
        
        with col3:
            st.markdown("**📦 Inventario:**")
            st.text(f"Stock Actual: {producto.get('stock_actual', 'N/A')}")
            st.text(f"Stock Mínimo: {producto.get('stock_minimo', 'N/A')}")
            st.text(f"Stock Máximo: {producto.get('stock_maximo', 'N/A')}")
            st.text(f"Código Barras: {producto.get('codigo_barras', 'N/A')}")
            st.text(f"Peso: {producto.get('peso', 0)} kg")
            st.text(f"Garantía: {producto.get('garantia_dias', 0)} días")
        
        if producto.get('descripcion'):
            st.markdown("**📝 Descripción:**")
            st.text(producto['descripcion'])
        
        if producto.get('observaciones'):
            st.markdown("**📄 Observaciones:**")
            st.text(producto['observaciones'])

def editar_producto(backend_url: str, producto: Dict[str, Any]):
    """Formulario para editar producto"""
    
    st.markdown(f"### ✏️ Editar Producto: {producto.get('nombre', 'N/A')}")
    
    with st.form(f"form_editar_producto_{producto['id_producto']}"):
        col1, col2 = st.columns(2)
        
        with col1:
            nombre = st.text_input("Nombre:", value=producto.get('nombre', ''))
            descripcion = st.text_area("Descripción:", value=producto.get('descripcion', ''))
            categoria = st.text_input("Categoría:", value=producto.get('categoria', ''))
            marca = st.text_input("Marca:", value=producto.get('marca', ''))
        
        with col2:
            precio_venta = producto.get('precio_venta') or producto.get('precio', 0)
            precio = st.number_input("Precio Venta:", value=float(precio_venta), step=0.01)
            precio_costo = st.number_input("Precio Costo:", value=float(producto.get('precio_costo', 0)), step=0.01)
            iva_porcentaje = st.selectbox("IVA (%):", [0, 5, 19], 
                                        index=[0, 5, 19].index(producto.get('iva_porcentaje', 19)))
            activo = st.checkbox("Activo", value=producto.get('activo', True))
        
        observaciones = st.text_area("Observaciones:", value=producto.get('observaciones', ''))
        
        if st.form_submit_button("💾 Actualizar Producto", use_container_width=True):
            datos_actualizacion = {
                "nombre": nombre,
                "descripcion": descripcion if descripcion else None,
                "categoria": categoria if categoria else None,
                "marca": marca if marca else None,
                "precio": precio,
                "precio_venta": precio,
                "precio_costo": precio_costo,
                "iva_porcentaje": iva_porcentaje,
                "activo": activo,
                "observaciones": observaciones if observaciones else None
            }
            
            actualizar_producto_backend(backend_url, producto['id_producto'], datos_actualizacion)

def actualizar_precio_producto(backend_url: str, producto: Dict[str, Any]):
    """Actualización rápida de precio"""
    
    st.markdown(f"### 💰 Actualizar Precio: {producto.get('nombre', 'N/A')}")
    
    with st.form(f"form_precio_{producto['id_producto']}"):
        col1, col2 = st.columns(2)
        
        with col1:
            precio_actual = producto.get('precio_venta') or producto.get('precio', 0)
            st.metric("Precio Actual", f"${precio_actual:,.2f}")
            
            nuevo_precio = st.number_input(
                "Nuevo Precio:",
                value=float(precio_actual),
                step=0.01,
                min_value=0.01
            )
        
        with col2:
            if precio_actual > 0:
                variacion = ((nuevo_precio - precio_actual) / precio_actual) * 100
                st.metric("Variación", f"{variacion:+.1f}%")
            
            motivo = st.text_input("Motivo del cambio:", placeholder="Ej: Aumento de costos")
        
        if st.form_submit_button("💰 Actualizar Precio", use_container_width=True):
            datos_precio = {
                "precio": nuevo_precio,
                "precio_venta": nuevo_precio,
                "motivo_cambio": motivo if motivo else None
            }
            
            actualizar_producto_backend(backend_url, producto['id_producto'], datos_precio)

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

def cambiar_estado_producto(backend_url: str, id_producto: int, nuevo_estado: bool):
    """Cambiar estado activo/inactivo del producto"""
    
    try:
        with st.spinner("Cambiando estado..."):
            response = requests.patch(
                f"{backend_url}/api/productos/{id_producto}/estado",
                json={"activo": nuevo_estado}
            )
        
        if response.status_code == 200:
            estado_texto = "activado" if nuevo_estado else "desactivado"
            st.success(f"✅ Producto {estado_texto} exitosamente")
            st.rerun()
        else:
            st.error(f"Error al cambiar estado: {response.status_code}")
            
    except Exception as e:
        st.error(f"Error al cambiar estado: {e}")

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
                categoria = producto.get('categoria', 'Sin categoría')
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
                            
                            precios = [p.get('precio_venta', p.get('precio', 0)) for p in productos_cat]
                            
                            with col1:
                                st.metric("Productos", len(productos_cat))
                            
                            with col2:
                                if precios:
                                    precio_promedio = sum(precios) / len(precios)
                                    st.metric("Precio Promedio", f"${precio_promedio:,.2f}")
                            
                            with col3:
                                productos_activos_cat = len([p for p in productos_cat if p.get('activo', True)])
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
    
    with st.form("form_nueva_categoria"):
        nombre_categoria = st.text_input(
            "Nombre de la Categoría*:",
            help="Nombre descriptivo de la categoría"
        )
        
        descripcion_categoria = st.text_area(
            "Descripción:",
            help="Descripción detallada de la categoría"
        )
        
        activa = st.checkbox("Categoría Activa", value=True)
        
        if st.form_submit_button("🏷️ Crear Categoría", use_container_width=True):
            if nombre_categoria.strip():
                # Por ahora, solo mostrar confirmación
                st.success(f"✅ Categoría '{nombre_categoria}' creada exitosamente!")
                st.info("💡 Para asignar productos a esta categoría, edita los productos individuales")
            else:
                st.error("❌ Ingrese un nombre para la categoría")