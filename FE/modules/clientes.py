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
    tab1, tab2, tab3 = st.tabs(["📝 Registrar Cliente", "📋 Lista de Clientes", "📊 Análisis"])
    
    with tab1:
        registrar_cliente(backend_url)
    
    with tab2:
        lista_clientes(backend_url)
    
    with tab3:
        analisis_clientes(backend_url)

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
            
            telefono_input = st.text_input(
                "Teléfono:",
                help="Número de teléfono - ingrese 8 dígitos (se formateará automáticamente)",
                placeholder="Ej: 22501234",
                max_chars=9,
                key="telefono_registro"
            )
            
            # Formatear teléfono automáticamente con guión
            telefono = telefono_input
            if telefono_input:
                # Eliminar caracteres no numéricos
                telefono_numeros = ''.join(filter(str.isdigit, telefono_input))
                # Si tiene 8 dígitos, formatear con guión
                if len(telefono_numeros) == 8:
                    telefono = f"{telefono_numeros[:4]}-{telefono_numeros[4:]}"
                elif len(telefono_numeros) > 0 and len(telefono_numeros) < 8:
                    # Mostrar advertencia si no tiene 8 dígitos
                    st.caption(f"⚠️ Faltan {8 - len(telefono_numeros)} dígito(s)")
            
            celular_input = st.text_input(
                "Celular:",
                help="Número de celular - ingrese 8 dígitos (se formateará automáticamente)",
                placeholder="Ej: 71234567",
                max_chars=9,
                key="celular_registro"
            )
            
            # Formatear celular automáticamente con guión
            celular = celular_input
            if celular_input:
                # Eliminar caracteres no numéricos
                celular_numeros = ''.join(filter(str.isdigit, celular_input))
                # Si tiene 8 dígitos, formatear con guión
                if len(celular_numeros) == 8:
                    celular = f"{celular_numeros[:4]}-{celular_numeros[4:]}"
                elif len(celular_numeros) > 0 and len(celular_numeros) < 8:
                    # Mostrar advertencia si no tiene 8 dígitos
                    st.caption(f"⚠️ Faltan {8 - len(celular_numeros)} dígito(s)")
            
            direccion = st.text_area(
                "Dirección*:",
                height=100,
                help="Dirección completa del cliente (obligatorio)",
                placeholder="Ingrese la dirección completa"
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
            # Validaciones
            errores = []
            
            if not codigo_cliente or not nombre or not nit:
                errores.append("Complete los campos obligatorios: Código Cliente, Nombre y NIT")
            
            if not direccion or direccion.strip() == "":
                errores.append("La dirección es obligatoria")
            
            # Validar celular si fue ingresado
            if celular and celular.strip():
                celular_limpio = celular.strip().replace("-", "").replace(" ", "")
                if not celular_limpio.isdigit():
                    errores.append("El celular solo debe contener números")
                elif len(celular_limpio) != 8:
                    errores.append("El celular debe tener exactamente 8 dígitos")
            
            # Validar teléfono si fue ingresado
            if telefono and telefono.strip():
                telefono_limpio = telefono.strip().replace("-", "").replace(" ", "")
                if not telefono_limpio.isdigit():
                    errores.append("El teléfono solo debe contener números (puede incluir guión)")
            
            if errores:
                for error in errores:
                    st.error(f"❌ {error}")
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
    
    # Renderizar formulario de edición fuera del bloque de selección
    if st.session_state.get('accion_cliente') == 'editar' and st.session_state.get('cliente_editar'):
        st.markdown("---")
        editar_cliente(backend_url, st.session_state.cliente_editar)

def mostrar_tabla_clientes(clientes: List[Dict], backend_url: str):
    """Mostrar tabla de clientes con opciones de gestión"""
    
    # Métricas resumen
    total_clientes = len(clientes)
    # Mapear estado_cliente a activo
    clientes_activos = len([c for c in clientes if c.get('estado_cliente', 'ACTIVO') == 'ACTIVO'])
    clientes_vip = len([c for c in clientes if c.get('categoria_cliente') == 'VIP'])
    limite_credito_total = sum(float(c.get('limite_credito', 0)) for c in clientes)
    
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
                lambda x: f"${float(x):,.0f}" if float(x) > 0 else "-"
            )
        
        # Estado como emoji (mapear estado_cliente a activo)
        if 'estado_cliente' in df_display.columns:
            df_display['activo'] = df_display['estado_cliente'].apply(
                lambda x: x == 'ACTIVO' if x else True
            )
            df_display['estado_emoji'] = df_display['activo'].apply(
                lambda x: "🟢 Activo" if x else "🔴 Inactivo"
            )
        elif 'activo' in df_display.columns:
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
                
                # Crear estado persistente para las acciones
                if 'accion_cliente' not in st.session_state:
                    st.session_state.accion_cliente = None
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("👁️ Ver Detalles", use_container_width=True, key=f"ver_det_{cliente_seleccionado['id_cliente']}"):
                        st.session_state.accion_cliente = 'ver_detalles'
                
                with col2:
                    if st.button("✏️ Editar", use_container_width=True, key=f"editar_{cliente_seleccionado['id_cliente']}"):
                        st.session_state.accion_cliente = 'editar'
                        st.session_state.cliente_editar = cliente_seleccionado
                
                with col3:
                    estado_actual = cliente_seleccionado.get('estado_cliente', 'ACTIVO') == 'ACTIVO'
                    accion_estado = "🔴 Desactivar" if estado_actual else "🟢 Activar"
                    if st.button(accion_estado, use_container_width=True, key=f"estado_{cliente_seleccionado['id_cliente']}"):
                        cambiar_estado_cliente(backend_url, cliente_seleccionado['id_cliente'], not estado_actual)
                
                # Renderizar la vista seleccionada en contenedor de ancho completo
                if st.session_state.accion_cliente == 'ver_detalles':
                    with st.container():
                        mostrar_detalle_cliente(cliente_seleccionado)

def mostrar_detalle_cliente(cliente: Dict[str, Any]):
    """Mostrar detalle completo de un cliente"""
    
    st.markdown(f"## 👤 Detalle del Cliente: {cliente.get('nombre', 'N/A')}")
    st.markdown("---")
    
    # Información básica en tabla
    st.markdown("### 📋 Información Básica")
    info_basica = {
        "Código": cliente.get('codigo_cliente', 'N/A'),
        "Nombre/Razón Social": cliente.get('nombre', 'N/A'),
        "Tipo de Cliente": cliente.get('tipo_cliente', 'N/A'),
        "NIT/Cédula": cliente.get('nit', 'N/A'),
        "Email": cliente.get('email', 'N/A'),
        "Teléfono": cliente.get('telefono', 'N/A'),
        "Celular": cliente.get('celular', 'N/A') if cliente.get('celular') else 'N/A',
        "Ciudad": cliente.get('municipio', cliente.get('ciudad', 'N/A'))
    }
    df_info = pd.DataFrame(list(info_basica.items()), columns=['Campo', 'Valor'])
    st.table(df_info)
    
    # Métricas financieras grandes
    st.markdown("### 💰 Información Financiera")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        limite = float(cliente.get('limite_credito', 0))
        st.metric(
            "Límite de Crédito",
            f"${limite:,.2f}",
            help="Límite de crédito autorizado"
        )
    
    with col2:
        st.metric(
            "Días de Crédito",
            f"{cliente.get('dias_credito', 0)} días",
            help="Plazo de crédito en días"
        )
    
    with col3:
        descuento = float(cliente.get('descuento_habitual', cliente.get('descuento_comercial', 0)))
        st.metric(
            "Descuento Comercial",
            f"{descuento:.1f}%",
            help="Descuento habitual aplicable"
        )
    
    # Información comercial
    st.markdown("### 🏷️ Clasificación Comercial")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.info(f"**Categoría:** {cliente.get('categoria_cliente', 'N/A')}")
    
    with col2:
        canal = cliente.get('canal_ventas', 'N/A')
        if canal != 'N/A':
            st.info(f"**Canal de Ventas:** {canal}")
    
    with col3:
        # Estado con color
        estado_activo = cliente.get('estado_cliente', 'ACTIVO') == 'ACTIVO'
        if estado_activo:
            st.success("✅ **Estado:** Activo")
        else:
            st.error("🔴 **Estado:** Inactivo")
    
    # Dirección y observaciones en secciones separadas
    if cliente.get('direccion'):
        st.markdown("### 📍 Dirección")
        st.info(cliente['direccion'])
    
    if cliente.get('observaciones'):
        st.markdown("### 📝 Observaciones")
        st.text_area("", value=cliente['observaciones'], height=100, disabled=True, label_visibility="collapsed")

def editar_cliente(backend_url: str, cliente: Dict[str, Any]):
    """Formulario para editar cliente"""
    
    st.markdown(f"## ✏️ Editar Cliente: {cliente.get('nombre', 'N/A')}")
    st.caption(f"Código: {cliente.get('codigo_cliente', 'N/A')}")
    st.markdown("---")
    
    with st.form(f"form_editar_cliente_{cliente['id_cliente']}"):
        col1, col2 = st.columns(2, gap="large")
        
        with col1:
            nombre = st.text_input("Nombre/Razón Social*:", value=cliente.get('nombre', ''))
            email = st.text_input("Email:", value=cliente.get('email', '') or '')
            
            telefono_value = cliente.get('telefono', '') or ''
            telefono_input = st.text_input(
                "Teléfono:", 
                value=telefono_value,
                placeholder="Ej: 22501234",
                max_chars=9,
                help="Ingrese 8 dígitos (se formateará automáticamente)",
                key=f"telefono_edit_{cliente['id_cliente']}"
            )
            
            # Formatear teléfono automáticamente
            telefono = telefono_input
            if telefono_input:
                telefono_numeros = ''.join(filter(str.isdigit, telefono_input))
                if len(telefono_numeros) == 8:
                    telefono = f"{telefono_numeros[:4]}-{telefono_numeros[4:]}"
                elif len(telefono_numeros) > 0 and len(telefono_numeros) < 8:
                    st.caption(f"⚠️ Faltan {8 - len(telefono_numeros)} dígito(s)")
            
            celular_value = cliente.get('celular', '') or ''
            celular_input = st.text_input(
                "Celular:", 
                value=celular_value,
                placeholder="Ej: 71234567",
                max_chars=9,
                help="Ingrese 8 dígitos (se formateará automáticamente)",
                key=f"celular_edit_{cliente['id_cliente']}"
            )
            
            # Formatear celular automáticamente
            celular = celular_input
            if celular_input:
                celular_numeros = ''.join(filter(str.isdigit, celular_input))
                if len(celular_numeros) == 8:
                    celular = f"{celular_numeros[:4]}-{celular_numeros[4:]}"
                elif len(celular_numeros) > 0 and len(celular_numeros) < 8:
                    st.caption(f"⚠️ Faltan {8 - len(celular_numeros)} dígito(s)")
            
            # Manejar categoría de forma segura
            categorias_validas = ["VIP", "Corporativo", "PYME", "Nuevo", "Mayorista", "Minorista"]
            categoria_actual = cliente.get('categoria_cliente')
            
            # Si la categoría es None o no está en la lista, usar "Nuevo" como default
            if categoria_actual not in categorias_validas:
                categoria_index = categorias_validas.index("Nuevo")
            else:
                categoria_index = categorias_validas.index(categoria_actual)
            
            categoria = st.selectbox(
                "Categoría:",
                categorias_validas,
                index=categoria_index
            )
        
        with col2:
            direccion = st.text_area(
                "Dirección*:", 
                value=cliente.get('direccion', ''),
                help="Campo obligatorio"
            )
            limite_credito = st.number_input("Límite de Crédito:", value=float(cliente.get('limite_credito', 0.0)))
            dias_credito = st.number_input("Días de Crédito:", value=int(cliente.get('dias_credito', 30)))
            activo = st.checkbox("Activo", value=cliente.get('activo', True))
        
        observaciones = st.text_area("Observaciones:", value=cliente.get('observaciones', ''))
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            submitted = st.form_submit_button("💾 Actualizar Cliente", use_container_width=True, type="primary")
        
        with col2:
            cancelar = st.form_submit_button("❌ Cancelar", use_container_width=True)
        
        if cancelar:
            st.session_state.accion_cliente = None
            st.session_state.cliente_editar = None
            st.rerun()
        
        if submitted:
            # Validaciones
            errores = []
            
            if not nombre or nombre.strip() == "":
                errores.append("El nombre es obligatorio")
            
            if not direccion or direccion.strip() == "":
                errores.append("La dirección es obligatoria")
            
            # Validar celular si fue ingresado
            if celular and celular.strip():
                celular_limpio = celular.strip().replace("-", "").replace(" ", "")
                if not celular_limpio.isdigit():
                    errores.append("El celular solo debe contener números")
                elif len(celular_limpio) != 8:
                    errores.append("El celular debe tener exactamente 8 dígitos")
            
            # Validar teléfono si fue ingresado
            if telefono and telefono.strip():
                telefono_limpio = telefono.strip().replace("-", "").replace(" ", "")
                if not telefono_limpio.isdigit():
                    errores.append("El teléfono solo debe contener números")
            
            if errores:
                for error in errores:
                    st.error(f"❌ {error}")
            else:
                datos_actualizacion = {
                    "nombre": nombre,
                    "email": email if email else None,
                    "telefono": telefono if telefono else None,
                    "celular": celular if celular else None,
                    "direccion": direccion,
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
            # Limpiar estado de sesión
            st.session_state.accion_cliente = None
            st.session_state.cliente_editar = None
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
            # El endpoint espera el parámetro 'activo' como query parameter
            response = requests.patch(
                f"{backend_url}/api/clientes/{id_cliente}/estado",
                params={"activo": nuevo_estado}
            )
        
        if response.status_code == 200:
            estado_texto = "activado" if nuevo_estado else "desactivado"
            st.success(f"✅ Cliente {estado_texto} exitosamente")
            st.rerun()
        else:
            error_detail = "Error desconocido"
            try:
                error_detail = response.json().get('detail', error_detail)
            except:
                pass
            st.error(f"❌ Error al cambiar estado: {error_detail}")
            
    except Exception as e:
        st.error(f"❌ Error al cambiar estado: {e}")

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
        st.metric("Clientes Activos", datos.get('clientes_activos', 0))
    
    with col3:
        st.metric("Clientes Inactivos", datos.get('clientes_inactivos', 0))
    
    with col4:
        st.metric("Nuevos Este Mes", datos.get('nuevos_mes', 0))
    
    # Gráficos de análisis
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if 'distribucion_categorias' in datos and datos['distribucion_categorias']:
            st.markdown("### 📊 Distribución por Categorías")
            
            categorias = datos['distribucion_categorias']
            df_cat = pd.DataFrame(list(categorias.items()), columns=['Categoría', 'Cantidad'])
            
            fig_pie = px.pie(df_cat, values='Cantidad', names='Categoría', 
                            title='Clientes por Categoría')
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("Sin datos de categorías")
    
    with col2:
        if 'distribucion_tipos' in datos and datos['distribucion_tipos']:
            st.markdown("### 🏢 Distribución por Tipo")
            
            tipos = datos['distribucion_tipos']
            df_tipos = pd.DataFrame(list(tipos.items()), columns=['Tipo', 'Cantidad'])
            
            fig_bar = px.bar(df_tipos, x='Tipo', y='Cantidad',
                            title='Clientes por Tipo')
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("Sin datos de tipos")

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
            df_clientes['limite_credito'] = df_clientes['limite_credito'].apply(lambda x: float(x) if x else 0.0)
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

