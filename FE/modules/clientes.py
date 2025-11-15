"""
Módulo Streamlit para Gestión de Clientes.
Sistema completo de administración de clientes para facturación.
"""
import streamlit as st
import requests
import pandas as pd
from datetime import datetime, date
from typing import Dict, Any, List
import plotly.express as px

def render_page(backend_url: str):
    """Renderizar página de gestión de clientes"""
    
    st.header("👥 Gestión de Clientes")
    st.markdown("Sistema completo de administración de clientes para el módulo de facturación")
    
    # Tabs para organizar funcionalidades
    tab1, tab2, tab3, tab4 = st.tabs(["📝 Registrar Cliente", "📋 Lista de Clientes", "📊 Análisis", "🔍 Búsqueda Avanzada"])
    
    with tab1:
        registrar_cliente(backend_url)
    
    with tab2:
        lista_clientes(backend_url)
    
    with tab3:
        analisis_clientes(backend_url)
    
    with tab4:
        busqueda_avanzada_clientes(backend_url)

def registrar_cliente(backend_url: str):
    """Registrar nuevo cliente"""
    
    st.subheader("📝 Registrar Nuevo Cliente")
    
    with st.form("form_registro_cliente", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📋 Información Básica")
            
            codigo_cliente = st.text_input(
                "Código Cliente*:",
                help="Código único identificador del cliente"
            )
            
            nombre = st.text_input(
                "Nombre/Razón Social*:",
                help="Nombre completo o razón social de la empresa"
            )
            
            tipo_cliente = st.selectbox(
                "Tipo de Cliente*:",
                ["Empresa", "Persona Natural"],
                help="Clasificación del tipo de cliente"
            )
            
            nit = st.text_input(
                "NIT/Cédula*:",
                help="Número de identificación tributaria o cédula"
            )
            
            digito_verificacion = st.text_input(
                "Dígito de Verificación:",
                help="Dígito de verificación del NIT (solo para empresas)"
            )
        
        with col2:
            st.markdown("#### 📞 Información de Contacto")
            
            email = st.text_input(
                "Email:",
                help="Correo electrónico principal"
            )
            
            telefono = st.text_input(
                "Teléfono:",
                help="Número de teléfono principal"
            )
            
            celular = st.text_input(
                "Celular:",
                help="Número de celular"
            )
            
            direccion = st.text_area(
                "Dirección:",
                height=100,
                help="Dirección completa del cliente"
            )
            
            ciudad = st.text_input(
                "Ciudad:",
                help="Ciudad de residencia o sede principal"
            )
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 🏷️ Clasificación Comercial")
            
            categoria_cliente = st.selectbox(
                "Categoría:",
                ["VIP", "Corporativo", "PYME", "Nuevo", "Mayorista", "Minorista"],
                help="Categoría comercial del cliente"
            )
            
            canal_ventas = st.selectbox(
                "Canal de Ventas:",
                ["Directo", "Distribuidor", "Online", "Telefónico", "Referido"],
                help="Canal principal de ventas"
            )
            
            zona_comercial = st.text_input(
                "Zona Comercial:",
                help="Zona geográfica comercial asignada"
            )
        
        with col2:
            st.markdown("#### 💰 Información Financiera")
            
            limite_credito = st.number_input(
                "Límite de Crédito:",
                min_value=0.0,
                value=0.0,
                step=100000.0,
                help="Límite de crédito autorizado"
            )
            
            dias_credito = st.number_input(
                "Días de Crédito:",
                min_value=0,
                value=30,
                step=1,
                help="Días de crédito autorizados"
            )
            
            descuento_comercial = st.number_input(
                "Descuento Comercial (%):",
                min_value=0.0,
                max_value=100.0,
                value=0.0,
                step=0.1,
                help="Descuento comercial aplicable"
            )
        
        # Información adicional
        st.markdown("#### 📄 Información Adicional")
        
        col1, col2 = st.columns(2)
        
        with col1:
            responsable_iva = st.checkbox(
                "Responsable de IVA",
                value=True,
                help="Marcar si el cliente es responsable de IVA"
            )
            
            gran_contribuyente = st.checkbox(
                "Gran Contribuyente",
                help="Marcar si es gran contribuyente"
            )
            
            autorretenedor = st.checkbox(
                "Autorretenedor",
                help="Marcar si es autorretenedor"
            )
        
        with col2:
            activo = st.checkbox(
                "Cliente Activo",
                value=True,
                help="Estado del cliente en el sistema"
            )
            
            acepta_email = st.checkbox(
                "Acepta Email Marketing",
                value=True,
                help="Cliente acepta recibir emails promocionales"
            )
        
        observaciones = st.text_area(
            "Observaciones:",
            help="Observaciones adicionales sobre el cliente"
        )
        
        # Botón de envío
        submitted = st.form_submit_button(
            "👥 Registrar Cliente",
            use_container_width=True,
            type="primary"
        )
        
        if submitted:
            if not codigo_cliente or not nombre or not nit:
                st.error("❌ Complete los campos obligatorios marcados con *")
            else:
                crear_cliente_completo(
                    backend_url,
                    {
                        "codigo_cliente": codigo_cliente,
                        "nombre": nombre,
                        "tipo_cliente": tipo_cliente,
                        "nit": nit,
                        "digito_verificacion": digito_verificacion,
                        "email": email,
                        "telefono": telefono,
                        "celular": celular,
                        "direccion": direccion,
                        "ciudad": ciudad,
                        "categoria_cliente": categoria_cliente,
                        "canal_ventas": canal_ventas,
                        "zona_comercial": zona_comercial,
                        "limite_credito": limite_credito,
                        "dias_credito": dias_credito,
                        "descuento_comercial": descuento_comercial,
                        "responsable_iva": responsable_iva,
                        "gran_contribuyente": gran_contribuyente,
                        "autorretenedor": autorretenedor,
                        "activo": activo,
                        "acepta_email": acepta_email,
                        "observaciones": observaciones
                    }
                )

def crear_cliente_completo(backend_url: str, datos_cliente: Dict[str, Any]):
    """Crear cliente con datos completos"""
    
    try:
        # Limpiar datos vacíos
        datos_limpios = {
            k: v for k, v in datos_cliente.items() 
            if v is not None and v != "" and v != 0.0
        }
        
        with st.spinner("Registrando cliente..."):
            response = requests.post(f"{backend_url}/api/clientes", json=datos_limpios)
        
        if response.status_code == 201:
            cliente_creado = response.json()
            st.success(f"✅ Cliente '{datos_cliente['nombre']}' registrado exitosamente!")
            st.balloons()
            
            # Mostrar resumen del cliente creado
            with st.expander("📄 Resumen del Cliente Registrado", expanded=True):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**ID:** {cliente_creado.get('id_cliente', 'N/A')}")
                    st.write(f"**Código:** {datos_cliente['codigo_cliente']}")
                    st.write(f"**Nombre:** {datos_cliente['nombre']}")
                    st.write(f"**Tipo:** {datos_cliente['tipo_cliente']}")
                    st.write(f"**NIT:** {datos_cliente['nit']}")
                
                with col2:
                    st.write(f"**Categoría:** {datos_cliente.get('categoria_cliente', 'N/A')}")
                    st.write(f"**Límite Crédito:** ${datos_cliente.get('limite_credito', 0):,.2f}")
                    st.write(f"**Días Crédito:** {datos_cliente.get('dias_credito', 0)}")
                    st.write(f"**Estado:** {'Activo' if datos_cliente.get('activo') else 'Inactivo'}")
            
        else:
            error_detail = response.json().get('detail', 'Error desconocido')
            st.error(f"❌ Error al registrar cliente: {error_detail}")
            
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Error de conexión: {e}")
    except Exception as e:
        st.error(f"❌ Error inesperado: {e}")

def lista_clientes(backend_url: str):
    """Lista y gestión de clientes existentes"""
    
    st.subheader("📋 Lista de Clientes")
    
    # Controles superiores
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        buscar_texto = st.text_input(
            "🔍 Buscar cliente:",
            placeholder="Buscar por nombre, código o NIT..."
        )
    
    with col2:
        filtro_estado = st.selectbox(
            "Estado:",
            ["Todos", "Activos", "Inactivos"]
        )
    
    with col3:
        if st.button("🔄 Actualizar", use_container_width=True):
            st.rerun()
    
    # Obtener y mostrar clientes
    try:
        params = {}
        if buscar_texto:
            params["buscar"] = buscar_texto
        if filtro_estado != "Todos":
            params["activo"] = filtro_estado == "Activos"
        
        with st.spinner("Cargando clientes..."):
            response = requests.get(f"{backend_url}/api/clientes", params=params)
        
        if response.status_code == 200:
            clientes = response.json()
            
            if clientes:
                mostrar_tabla_clientes(clientes, backend_url)
            else:
                st.info("📭 No se encontraron clientes con los criterios especificados")
        else:
            st.error(f"Error al cargar clientes: {response.status_code}")
            
    except Exception as e:
        st.error(f"Error al cargar clientes: {e}")

def mostrar_tabla_clientes(clientes: List[Dict], backend_url: str):
    """Mostrar tabla de clientes con opciones de gestión"""
    
    # Métricas resumen
    total_clientes = len(clientes)
    clientes_activos = len([c for c in clientes if c.get('activo', True)])
    clientes_vip = len([c for c in clientes if c.get('categoria_cliente') == 'VIP'])
    limite_credito_total = sum(c.get('limite_credito', 0) for c in clientes)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Clientes", total_clientes)
    
    with col2:
        st.metric("Clientes Activos", clientes_activos)
    
    with col3:
        st.metric("Clientes VIP", clientes_vip)
    
    with col4:
        st.metric("Crédito Total", f"${limite_credito_total:,.0f}")
    
    # Tabla de clientes
    df_clientes = pd.DataFrame(clientes)
    
    # Preparar columnas para mostrar
    if not df_clientes.empty:
        # Formatear columnas
        df_display = df_clientes.copy()
        
        # Formatear límite de crédito
        if 'limite_credito' in df_display.columns:
            df_display['limite_credito_fmt'] = df_display['limite_credito'].apply(
                lambda x: f"${x:,.0f}" if x > 0 else "-"
            )
        
        # Estado como emoji
        if 'activo' in df_display.columns:
            df_display['estado_emoji'] = df_display['activo'].apply(
                lambda x: "🟢 Activo" if x else "🔴 Inactivo"
            )
        
        # Seleccionar columnas principales
        columnas_principales = [
            'codigo_cliente', 'nombre', 'tipo_cliente', 'nit', 
            'categoria_cliente', 'limite_credito_fmt', 'estado_emoji'
        ]
        
        # Verificar que las columnas existan
        columnas_mostrar = [col for col in columnas_principales if col in df_display.columns]
        
        if columnas_mostrar:
            df_tabla = df_display[columnas_mostrar].copy()
            
            # Renombrar columnas
            nombres_columnas = {
                'codigo_cliente': 'Código',
                'nombre': 'Nombre/Razón Social',
                'tipo_cliente': 'Tipo',
                'nit': 'NIT/CC',
                'categoria_cliente': 'Categoría',
                'limite_credito_fmt': 'Límite Crédito',
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
            
            # Acciones sobre cliente seleccionado
            if event.selection.rows:
                cliente_idx = event.selection.rows[0]
                cliente_seleccionado = clientes[cliente_idx]
                
                st.markdown("### 🔧 Acciones sobre Cliente Seleccionado")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    if st.button("👁️ Ver Detalles", use_container_width=True):
                        mostrar_detalle_cliente(cliente_seleccionado)
                
                with col2:
                    if st.button("✏️ Editar", use_container_width=True):
                        editar_cliente(backend_url, cliente_seleccionado)
                
                with col3:
                    estado_actual = cliente_seleccionado.get('activo', True)
                    accion_estado = "Desactivar" if estado_actual else "Activar"
                    if st.button(f"🔄 {accion_estado}", use_container_width=True):
                        cambiar_estado_cliente(backend_url, cliente_seleccionado['id_cliente'], not estado_actual)
                
                with col4:
                    if st.button("🗑️ Eliminar", use_container_width=True):
                        if st.checkbox("Confirmar eliminación", key=f"confirm_del_{cliente_seleccionado['id_cliente']}"):
                            eliminar_cliente(backend_url, cliente_seleccionado['id_cliente'])

def mostrar_detalle_cliente(cliente: Dict[str, Any]):
    """Mostrar detalle completo de un cliente"""
    
    with st.expander(f"👤 Detalle del Cliente: {cliente.get('nombre', 'N/A')}", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**📋 Información Básica:**")
            st.text(f"Código: {cliente.get('codigo_cliente', 'N/A')}")
            st.text(f"Nombre: {cliente.get('nombre', 'N/A')}")
            st.text(f"Tipo: {cliente.get('tipo_cliente', 'N/A')}")
            st.text(f"NIT/CC: {cliente.get('nit', 'N/A')}")
            st.text(f"Email: {cliente.get('email', 'N/A')}")
            st.text(f"Teléfono: {cliente.get('telefono', 'N/A')}")
            st.text(f"Ciudad: {cliente.get('ciudad', 'N/A')}")
        
        with col2:
            st.markdown("**💰 Información Comercial:**")
            st.text(f"Categoría: {cliente.get('categoria_cliente', 'N/A')}")
            st.text(f"Canal Ventas: {cliente.get('canal_ventas', 'N/A')}")
            st.text(f"Límite Crédito: ${cliente.get('limite_credito', 0):,.2f}")
            st.text(f"Días Crédito: {cliente.get('dias_credito', 0)}")
            st.text(f"Descuento: {cliente.get('descuento_comercial', 0):.1f}%")
            st.text(f"Estado: {'Activo' if cliente.get('activo') else 'Inactivo'}")
        
        if cliente.get('direccion'):
            st.markdown("**📍 Dirección:**")
            st.text(cliente['direccion'])
        
        if cliente.get('observaciones'):
            st.markdown("**📝 Observaciones:**")
            st.text(cliente['observaciones'])

def editar_cliente(backend_url: str, cliente: Dict[str, Any]):
    """Formulario para editar cliente"""
    
    st.markdown(f"### ✏️ Editar Cliente: {cliente.get('nombre', 'N/A')}")
    
    with st.form(f"form_editar_cliente_{cliente['id_cliente']}"):
        col1, col2 = st.columns(2)
        
        with col1:
            nombre = st.text_input("Nombre/Razón Social:", value=cliente.get('nombre', ''))
            email = st.text_input("Email:", value=cliente.get('email', ''))
            telefono = st.text_input("Teléfono:", value=cliente.get('telefono', ''))
            categoria = st.selectbox(
                "Categoría:",
                ["VIP", "Corporativo", "PYME", "Nuevo", "Mayorista", "Minorista"],
                index=["VIP", "Corporativo", "PYME", "Nuevo", "Mayorista", "Minorista"].index(cliente.get('categoria_cliente', 'Nuevo'))
            )
        
        with col2:
            direccion = st.text_area("Dirección:", value=cliente.get('direccion', ''))
            limite_credito = st.number_input("Límite de Crédito:", value=cliente.get('limite_credito', 0.0))
            dias_credito = st.number_input("Días de Crédito:", value=cliente.get('dias_credito', 30))
            activo = st.checkbox("Activo", value=cliente.get('activo', True))
        
        observaciones = st.text_area("Observaciones:", value=cliente.get('observaciones', ''))
        
        if st.form_submit_button("💾 Actualizar Cliente", use_container_width=True):
            datos_actualizacion = {
                "nombre": nombre,
                "email": email if email else None,
                "telefono": telefono if telefono else None,
                "direccion": direccion if direccion else None,
                "categoria_cliente": categoria,
                "limite_credito": limite_credito,
                "dias_credito": dias_credito,
                "activo": activo,
                "observaciones": observaciones if observaciones else None
            }
            
            actualizar_cliente_backend(backend_url, cliente['id_cliente'], datos_actualizacion)

def actualizar_cliente_backend(backend_url: str, id_cliente: int, datos: Dict[str, Any]):
    """Actualizar cliente en el backend"""
    
    try:
        with st.spinner("Actualizando cliente..."):
            response = requests.put(f"{backend_url}/api/clientes/{id_cliente}", json=datos)
        
        if response.status_code == 200:
            st.success("✅ Cliente actualizado exitosamente")
            st.rerun()
        else:
            error_detail = response.json().get('detail', 'Error desconocido')
            st.error(f"❌ Error al actualizar cliente: {error_detail}")
            
    except Exception as e:
        st.error(f"❌ Error al actualizar cliente: {e}")

def cambiar_estado_cliente(backend_url: str, id_cliente: int, nuevo_estado: bool):
    """Cambiar estado activo/inactivo del cliente"""
    
    try:
        with st.spinner("Cambiando estado..."):
            response = requests.patch(
                f"{backend_url}/api/clientes/{id_cliente}/estado",
                json={"activo": nuevo_estado}
            )
        
        if response.status_code == 200:
            estado_texto = "activado" if nuevo_estado else "desactivado"
            st.success(f"✅ Cliente {estado_texto} exitosamente")
            st.rerun()
        else:
            st.error(f"Error al cambiar estado: {response.status_code}")
            
    except Exception as e:
        st.error(f"Error al cambiar estado: {e}")

def eliminar_cliente(backend_url: str, id_cliente: int):
    """Eliminar cliente"""
    
    try:
        with st.spinner("Eliminando cliente..."):
            response = requests.delete(f"{backend_url}/api/clientes/{id_cliente}")
        
        if response.status_code == 200:
            st.success("✅ Cliente eliminado exitosamente")
            st.rerun()
        else:
            st.error(f"Error al eliminar cliente: {response.status_code}")
            
    except Exception as e:
        st.error(f"Error al eliminar cliente: {e}")

def analisis_clientes(backend_url: str):
    """Análisis y estadísticas de clientes"""
    
    st.subheader("📊 Análisis de Clientes")
    
    try:
        # Obtener datos para análisis
        with st.spinner("Cargando datos para análisis..."):
            response = requests.get(f"{backend_url}/api/clientes/analisis")
        
        if response.status_code == 200:
            datos_analisis = response.json()
            mostrar_analisis_clientes(datos_analisis)
        else:
            # Si no existe endpoint específico, usar datos de clientes normales
            response_clientes = requests.get(f"{backend_url}/api/clientes")
            if response_clientes.status_code == 200:
                clientes = response_clientes.json()
                generar_analisis_basico(clientes)
            else:
                st.error("Error al cargar datos para análisis")
                
    except Exception as e:
        st.error(f"Error al cargar análisis: {e}")

def mostrar_analisis_clientes(datos: Dict[str, Any]):
    """Mostrar análisis completo de clientes"""
    
    # Métricas principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Clientes", datos.get('total_clientes', 0))
    
    with col2:
        st.metric("Nuevos Este Mes", datos.get('nuevos_mes', 0))
    
    with col3:
        st.metric("Clientes Activos", datos.get('clientes_activos', 0))
    
    with col4:
        st.metric("Tasa Retención", f"{datos.get('tasa_retencion', 0):.1f}%")
    
    # Gráficos de análisis
    if 'distribucion_categorias' in datos:
        st.markdown("### 📊 Distribución por Categorías")
        
        categorias = datos['distribucion_categorias']
        df_cat = pd.DataFrame(list(categorias.items()), columns=['Categoría', 'Cantidad'])
        
        fig_pie = px.pie(df_cat, values='Cantidad', names='Categoría', 
                        title='Distribución de Clientes por Categoría')
        st.plotly_chart(fig_pie, use_container_width=True)
    
    # Más análisis específicos pueden agregarse aquí

def generar_analisis_basico(clientes: List[Dict]):
    """Generar análisis básico con datos de clientes"""
    
    if not clientes:
        st.info("📭 No hay datos de clientes para analizar")
        return
    
    df_clientes = pd.DataFrame(clientes)
    
    # Métricas básicas
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Clientes", len(df_clientes))
    
    with col2:
        clientes_activos = len(df_clientes[df_clientes.get('activo', True) == True])
        st.metric("Clientes Activos", clientes_activos)
    
    with col3:
        if 'categoria_cliente' in df_clientes.columns:
            clientes_vip = len(df_clientes[df_clientes['categoria_cliente'] == 'VIP'])
            st.metric("Clientes VIP", clientes_vip)
        else:
            st.metric("Clientes VIP", "N/A")
    
    with col4:
        if 'limite_credito' in df_clientes.columns:
            credito_promedio = df_clientes['limite_credito'].mean()
            st.metric("Crédito Promedio", f"${credito_promedio:,.0f}")
        else:
            st.metric("Crédito Promedio", "N/A")
    
    # Gráfico de distribución por tipo
    if 'tipo_cliente' in df_clientes.columns:
        st.markdown("### 📊 Distribución por Tipo de Cliente")
        
        tipo_counts = df_clientes['tipo_cliente'].value_counts()
        fig_tipo = px.pie(values=tipo_counts.values, names=tipo_counts.index,
                         title='Distribución por Tipo de Cliente')
        st.plotly_chart(fig_tipo, use_container_width=True)
    
    # Gráfico de distribución por categoría
    if 'categoria_cliente' in df_clientes.columns:
        st.markdown("### 🏷️ Distribución por Categoría")
        
        cat_counts = df_clientes['categoria_cliente'].value_counts()
        fig_cat = px.bar(x=cat_counts.index, y=cat_counts.values,
                        title='Cantidad de Clientes por Categoría')
        st.plotly_chart(fig_cat, use_container_width=True)

def busqueda_avanzada_clientes(backend_url: str):
    """Búsqueda avanzada de clientes con múltiples filtros"""
    
    st.subheader("🔍 Búsqueda Avanzada de Clientes")
    
    with st.form("form_busqueda_avanzada"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**📋 Información Básica**")
            
            codigo_buscar = st.text_input("Código Cliente:")
            nombre_buscar = st.text_input("Nombre/Razón Social:")
            nit_buscar = st.text_input("NIT/CC:")
            tipo_buscar = st.selectbox("Tipo:", ["Todos", "Empresa", "Persona Natural"])
        
        with col2:
            st.markdown("**🏷️ Clasificación**")
            
            categoria_buscar = st.selectbox(
                "Categoría:",
                ["Todas", "VIP", "Corporativo", "PYME", "Nuevo", "Mayorista", "Minorista"]
            )
            
            canal_buscar = st.selectbox(
                "Canal de Ventas:",
                ["Todos", "Directo", "Distribuidor", "Online", "Telefónico", "Referido"]
            )
            
            zona_buscar = st.text_input("Zona Comercial:")
            ciudad_buscar = st.text_input("Ciudad:")
        
        with col3:
            st.markdown("**💰 Criterios Financieros**")
            
            limite_min = st.number_input("Límite Crédito Mín.:", min_value=0.0, value=0.0)
            limite_max = st.number_input("Límite Crédito Máx.:", min_value=0.0, value=0.0)
            
            dias_credito_min = st.number_input("Días Crédito Mín.:", min_value=0, value=0)
            dias_credito_max = st.number_input("Días Crédito Máx.:", min_value=0, value=0)
            
            estado_buscar = st.selectbox("Estado:", ["Todos", "Activos", "Inactivos"])
        
        if st.form_submit_button("🔍 Buscar Clientes", use_container_width=True):
            ejecutar_busqueda_avanzada(
                backend_url,
                {
                    "codigo": codigo_buscar,
                    "nombre": nombre_buscar,
                    "nit": nit_buscar,
                    "tipo": tipo_buscar if tipo_buscar != "Todos" else None,
                    "categoria": categoria_buscar if categoria_buscar != "Todas" else None,
                    "canal": canal_buscar if canal_buscar != "Todos" else None,
                    "zona": zona_buscar,
                    "ciudad": ciudad_buscar,
                    "limite_min": limite_min if limite_min > 0 else None,
                    "limite_max": limite_max if limite_max > 0 else None,
                    "dias_min": dias_credito_min if dias_credito_min > 0 else None,
                    "dias_max": dias_credito_max if dias_credito_max > 0 else None,
                    "estado": estado_buscar if estado_buscar != "Todos" else None
                }
            )

def ejecutar_busqueda_avanzada(backend_url: str, criterios: Dict[str, Any]):
    """Ejecutar búsqueda avanzada con criterios específicos"""
    
    try:
        # Filtrar criterios no vacíos
        params = {k: v for k, v in criterios.items() if v is not None and v != ""}
        
        with st.spinner("Ejecutando búsqueda avanzada..."):
            response = requests.get(f"{backend_url}/api/clientes/busqueda-avanzada", params=params)
        
        if response.status_code == 200:
            clientes_encontrados = response.json()
            
            if clientes_encontrados:
                st.success(f"✅ Se encontraron {len(clientes_encontrados)} clientes")
                mostrar_tabla_clientes(clientes_encontrados, backend_url)
            else:
                st.info("📭 No se encontraron clientes con los criterios especificados")
        else:
            # Fallback: usar búsqueda simple
            response_simple = requests.get(f"{backend_url}/api/clientes")
            if response_simple.status_code == 200:
                todos_clientes = response_simple.json()
                clientes_filtrados = filtrar_clientes_localmente(todos_clientes, criterios)
                
                if clientes_filtrados:
                    st.success(f"✅ Se encontraron {len(clientes_filtrados)} clientes")
                    mostrar_tabla_clientes(clientes_filtrados, backend_url)
                else:
                    st.info("📭 No se encontraron clientes con los criterios especificados")
            else:
                st.error("Error al ejecutar búsqueda")
                
    except Exception as e:
        st.error(f"Error en búsqueda avanzada: {e}")

def filtrar_clientes_localmente(clientes: List[Dict], criterios: Dict[str, Any]):
    """Filtrar clientes localmente cuando no hay endpoint específico"""
    
    clientes_filtrados = clientes.copy()
    
    for criterio, valor in criterios.items():
        if valor is None:
            continue
        
        if criterio == "codigo" and valor:
            clientes_filtrados = [c for c in clientes_filtrados 
                                if valor.lower() in str(c.get('codigo_cliente', '')).lower()]
        
        elif criterio == "nombre" and valor:
            clientes_filtrados = [c for c in clientes_filtrados 
                                if valor.lower() in str(c.get('nombre', '')).lower()]
        
        elif criterio == "nit" and valor:
            clientes_filtrados = [c for c in clientes_filtrados 
                                if valor in str(c.get('nit', ''))]
        
        elif criterio == "tipo" and valor:
            clientes_filtrados = [c for c in clientes_filtrados 
                                if c.get('tipo_cliente') == valor]
        
        elif criterio == "categoria" and valor:
            clientes_filtrados = [c for c in clientes_filtrados 
                                if c.get('categoria_cliente') == valor]
        
        elif criterio == "estado" and valor:
            estado_bool = valor == "Activos"
            clientes_filtrados = [c for c in clientes_filtrados 
                                if c.get('activo', True) == estado_bool]
        
        # Agregar más filtros según necesidad
    
    return clientes_filtrados