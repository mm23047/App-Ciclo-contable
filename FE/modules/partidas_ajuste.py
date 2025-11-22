"""
Módulo Streamlit para Partidas de Ajuste.
Manejo de ajustes contables de fin de período.
"""
import streamlit as st
import requests
import pandas as pd
from datetime import datetime, date
from typing import Dict, Any, List

def render_page(backend_url: str):
    """Renderizar página de partidas de ajuste"""
    
    st.header("⚖️ Partidas de Ajuste")
    st.markdown("Gestión de ajustes contables de fin de período")
    
    # Tabs para organizar funcionalidades
    tab1, tab2, tab3 = st.tabs(["📝 Crear Ajuste", "📋 Consultar Ajustes", "📊 Reportes"])
    
    with tab1:
        crear_partida_ajuste(backend_url)
    
    with tab2:
        consultar_partidas_ajuste(backend_url)
    
    with tab3:
        reportes_ajustes(backend_url)

def crear_partida_ajuste(backend_url: str):
    """Crear nueva partida de ajuste"""
    
    st.subheader("📝 Crear Nueva Partida de Ajuste")
    
    # Obtener períodos disponibles
    try:
        response_periodos = requests.get(f"{backend_url}/api/periodos")
        periodos = response_periodos.json() if response_periodos.status_code == 200 else []
    except:
        periodos = []
    
    if not periodos:
        st.warning("⚠️ No hay períodos configurados. Configura un período primero.")
        return
    
    with st.form("form_crear_ajuste", clear_on_submit=False):
        col1, col2 = st.columns(2)
        
        with col1:
            # Selección de período
            opciones_periodos = [
                f"{p['descripcion']} ({p['fecha_inicio']} - {p['fecha_fin']})"
                for p in periodos
            ]
            periodo_seleccionado = st.selectbox("Período contable:", opciones_periodos)
            
            # Fecha del ajuste
            fecha_ajuste = st.date_input(
                "Fecha del ajuste:",
                value=datetime.now().date(),
                help="Fecha de registro del ajuste"
            )
            
            # Número de partida
            numero_partida = st.text_input(
                "Número de partida:",
                max_chars=20,
                help="Número único de la partida de ajuste (máximo 20 caracteres)"
            )
            
            # Tipo de ajuste
            tipos_ajuste_display = {
                "DEPRECIACION": "Depreciación de activos fijos",
                "PROVISION": "Provisión para cuentas incobrables", 
                "AJUSTE_INVENTARIO": "Ajuste de inventarios",
                "DIFERIDO": "Gastos anticipados / Ingresos diferidos",
                "DEVENGO": "Ajuste de devengos",
                "RECLASIFICACION": "Reclasificación de cuentas",
                "CORRECCION_ERROR": "Corrección de errores",
                "AJUSTE_CAMBIO": "Ajuste por cambio de método contable",
                "OTROS": "Otro tipo de ajuste"
            }
            
            tipo_ajuste_seleccionado = st.selectbox(
                "Tipo de ajuste:", 
                options=list(tipos_ajuste_display.keys()),
                format_func=lambda x: tipos_ajuste_display[x]
            )
            
            # Si selecciona OTROS, permitir especificar
            if tipo_ajuste_seleccionado == "OTROS":
                motivo_adicional = st.text_input("Especificar tipo de ajuste:", help="Describa el tipo de ajuste personalizado")
        
        with col2:
            # Descripción del ajuste
            descripcion = st.text_area(
                "Descripción del ajuste:",
                height=100,
                help="Descripción detallada del motivo y naturaleza del ajuste"
            )
            
            # Motivo del ajuste
            motivo_ajuste = st.text_area(
                "Motivo del ajuste:",
                height=80,
                help="Justificación técnica o legal del ajuste"
            )
            
            # Usuario creación
            usuario_creacion = st.text_input(
                "Usuario de creación:",
                max_chars=50,
                value=st.session_state.get('usuario_actual', ''),
                help="Nombre del usuario que registra el ajuste (máximo 50 caracteres)"
            )
        
        # Botón para guardar datos del encabezado
        guardar_encabezado = st.form_submit_button(
            "💾 Guardar Encabezado", 
            width="stretch"
        )
        
        if guardar_encabezado:
            st.session_state.ajuste_encabezado = {
                'periodo_seleccionado': periodo_seleccionado,
                'fecha_ajuste': fecha_ajuste,
                'numero_partida': numero_partida,
                'tipo_ajuste': tipo_ajuste_seleccionado,
                'descripcion': descripcion,
                'motivo_ajuste': motivo_ajuste,
                'usuario_creacion': usuario_creacion
            }
            st.success("✅ Encabezado guardado. Ahora agrega los movimientos.")
    
    # Gestión de movimientos (fuera del form)
    st.markdown("### 📊 Movimientos del Ajuste")
    st.markdown("Agrega los movimientos que componen esta partida de ajuste:")
    
    # Gestión de movimientos
    if 'movimientos_ajuste' not in st.session_state:
        st.session_state.movimientos_ajuste = []
    
    # Formulario para agregar movimiento
    with st.expander("➕ Agregar Movimiento", expanded=True):
            col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
            
            with col1:
                # Obtener cuentas que aceptan movimientos
                try:
                    response_cuentas = requests.get(f"{backend_url}/api/catalogo-cuentas")
                    cuentas = response_cuentas.json() if response_cuentas.status_code == 200 else []
                    cuentas_disponibles = [
                        c for c in cuentas if c['acepta_movimientos']
                    ]
                except:
                    cuentas_disponibles = []
                
                opciones_cuentas = [
                    f"{c['codigo_cuenta']} - {c['nombre_cuenta']}"
                    for c in cuentas_disponibles
                ]
                
                if opciones_cuentas:
                    cuenta_mov = st.selectbox("Cuenta:", opciones_cuentas, key="cuenta_movimiento")
                else:
                    st.warning("No hay cuentas disponibles")
                    cuenta_mov = None
            
            with col2:
                descripcion_detalle_mov = st.text_input("Descripción del detalle:", key="desc_movimiento")
            
            with col3:
                debe = st.number_input("Debe:", min_value=0.0, step=0.01, key="debe_mov")
            
            with col4:
                haber = st.number_input("Haber:", min_value=0.0, step=0.01, key="haber_mov")
            
            if st.button("➕ Agregar Movimiento"):
                if cuenta_mov and descripcion_detalle_mov and (debe > 0 or haber > 0):
                    if debe > 0 and haber > 0:
                        st.error("Un movimiento no puede tener valores en debe y haber al mismo tiempo")
                    else:
                        codigo_cuenta = cuenta_mov.split(" - ")[0]
                        cuenta_obj = next((c for c in cuentas_disponibles if c['codigo_cuenta'] == codigo_cuenta), None)
                        
                        nuevo_movimiento = {
                            'id_cuenta': cuenta_obj['id_cuenta'],
                            'codigo_cuenta': codigo_cuenta,
                            'nombre_cuenta': cuenta_obj['nombre_cuenta'],
                            'descripcion_detalle': descripcion_detalle_mov,
                            'debe': debe,
                            'haber': haber
                        }
                        
                        st.session_state.movimientos_ajuste.append(nuevo_movimiento)
                        st.rerun()
                else:
                    st.error("Complete todos los campos requeridos")
    
    # Mostrar movimientos agregados
    if st.session_state.movimientos_ajuste:
        st.markdown("#### Movimientos agregados:")
        
        for i, mov in enumerate(st.session_state.movimientos_ajuste):
            col1, col2, col3, col4, col5 = st.columns([2, 3, 1, 1, 1])
            
            with col1:
                st.text(mov['codigo_cuenta'])
            
            with col2:
                st.text(mov['nombre_cuenta'])
            
            with col3:
                st.text(f"${mov['debe']:,.2f}" if mov['debe'] > 0 else "-")
            
            with col4:
                st.text(f"${mov['haber']:,.2f}" if mov['haber'] > 0 else "-")
            
            with col5:
                if st.button("🗑️", key=f"eliminar_{i}", help="Eliminar movimiento"):
                    st.session_state.movimientos_ajuste.pop(i)
                    st.rerun()
        
        # Validar balance
        total_debe = sum(m['debe'] for m in st.session_state.movimientos_ajuste)
        total_haber = sum(m['haber'] for m in st.session_state.movimientos_ajuste)
        diferencia = total_debe - total_haber
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Debe", f"${total_debe:,.2f}")
        with col2:
            st.metric("Total Haber", f"${total_haber:,.2f}")
        with col3:
            st.metric(
                "Diferencia", 
                f"${abs(diferencia):,.2f}",
                delta=f"{'Debe' if diferencia > 0 else 'Haber' if diferencia < 0 else 'Balanceado'}"
            )
        
        if abs(diferencia) > 0.01:
            st.warning("⚠️ Los movimientos no están balanceados. Debe = Haber")
    
    # Botón para crear la partida (fuera del form, usa datos de session_state)
    if st.button("💾 Crear Partida de Ajuste", width="stretch", type="primary"):
        encabezado = st.session_state.get('ajuste_encabezado', {})
        
        if not encabezado:
            st.error("❌ Primero debes guardar el encabezado del ajuste")
        elif not encabezado.get('numero_partida'):
            st.error("❌ El número de partida es requerido")
        elif not encabezado.get('usuario_creacion'):
            st.error("❌ El usuario de creación es requerido")
        elif not st.session_state.movimientos_ajuste:
            st.error("❌ Debe agregar al menos un movimiento")
        elif abs(sum(m['debe'] for m in st.session_state.movimientos_ajuste) - 
                sum(m['haber'] for m in st.session_state.movimientos_ajuste)) > 0.01:
            st.error("❌ Los movimientos deben estar balanceados (Debe = Haber)")
        elif not encabezado.get('descripcion'):
            st.error("❌ La descripción es requerida")
        elif not encabezado.get('motivo_ajuste'):
            st.error("❌ El motivo del ajuste es requerido")
        else:
            crear_ajuste_backend(
                backend_url, 
                encabezado['periodo_seleccionado'], 
                periodos,
                encabezado['numero_partida'],
                encabezado['fecha_ajuste'],
                encabezado['tipo_ajuste'],
                encabezado['descripcion'],
                encabezado['motivo_ajuste'],
                encabezado['usuario_creacion'],
                st.session_state.movimientos_ajuste
            )

def crear_ajuste_backend(
    backend_url: str, 
    periodo_seleccionado: str,
    periodos: List[Dict],
    numero_partida: str,
    fecha_ajuste: date,
    tipo_ajuste: str,
    descripcion: str,
    motivo_ajuste: str,
    usuario_creacion: str,
    movimientos: List[Dict]
):
    """Enviar partida de ajuste al backend"""
    
    try:
        # Obtener ID del período
        nombre_periodo = periodo_seleccionado.split(" (")[0]
        periodo_obj = next((p for p in periodos if p['descripcion'] == nombre_periodo), None)
        
        if not periodo_obj:
            st.error("❌ Error al identificar el período")
            return
        
        # Preparar datos
        datos_ajuste = {
            "numero_partida": numero_partida,
            "id_periodo": periodo_obj['id_periodo'],
            "fecha_ajuste": fecha_ajuste.isoformat(),
            "tipo_ajuste": tipo_ajuste,
            "descripcion": descripcion,
            "motivo_ajuste": motivo_ajuste,
            "usuario_creacion": usuario_creacion,
            "estado": "PENDIENTE",
            "asientos_ajuste": [
                {
                    "id_cuenta": mov['id_cuenta'],
                    "descripcion_detalle": mov['descripcion_detalle'],
                    "debe": mov['debe'],
                    "haber": mov['haber']
                }
                for mov in movimientos
            ]
        }
        
        # Enviar al backend
        with st.spinner("Creando partida de ajuste..."):
            response = requests.post(
                f"{backend_url}/api/partidas-ajuste",
                json=datos_ajuste
            )
        
        if response.status_code in [200, 201]:
            st.success("✅ Partida de ajuste creada exitosamente!")
            st.session_state.movimientos_ajuste = []  # Limpiar movimientos
            if 'ajuste_encabezado' in st.session_state:
                del st.session_state.ajuste_encabezado  # Limpiar encabezado
            
            # Mostrar información del ajuste creado
            ajuste_creado = response.json()
            st.info(f"📄 Ajuste creado con ID: {ajuste_creado.get('id_partida_ajuste', ajuste_creado.get('id_ajuste', 'N/A'))}")
            
        else:
            error_detail = response.json().get('detail', 'Error desconocido')
            st.error(f"❌ Error al crear partida de ajuste: {error_detail}")
            
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Error de conexión: {e}")
    except Exception as e:
        st.error(f"❌ Error inesperado: {e}")

def consultar_partidas_ajuste(backend_url: str):
    """Consultar partidas de ajuste existentes"""
    
    st.subheader("📋 Consultar Partidas de Ajuste")
    
    # Filtros
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Obtener períodos
        try:
            response_periodos = requests.get(f"{backend_url}/api/periodos")
            periodos = response_periodos.json() if response_periodos.status_code == 200 else []
            
            opciones_periodos = ["Todos los períodos"] + [
                f"{p['descripcion']} ({p['fecha_inicio']} - {p['fecha_fin']})"
                for p in periodos
            ]
            
            periodo_filtro = st.selectbox("Período:", opciones_periodos)
            
        except:
            periodo_filtro = "Todos los períodos"
            periodos = []
    
    with col2:
        # Filtro por tipo de ajuste
        tipos_ajuste = [
            "Todos los tipos",
            "Depreciación de activos fijos",
            "Provision para cuentas incobrables",
            "Ajuste de inventarios",
            "Gastos anticipados",
            "Ingresos diferidos",
            "Provision para impuestos",
            "Provision para prestaciones laborales",
            "Ajuste de devengos",
            "Corrección de errores",
            "Otro"
        ]
        tipo_filtro = st.selectbox("Tipo de ajuste:", tipos_ajuste)
    
    with col3:
        # Filtro por fecha
        fecha_desde = st.date_input("Desde:", value=None, help="Fecha opcional para filtrar")
        fecha_hasta = st.date_input("Hasta:", value=None, help="Fecha opcional para filtrar")
    
    if st.button("🔍 Buscar Partidas de Ajuste", width="stretch"):
        obtener_partidas_ajuste(
            backend_url, 
            periodo_filtro,
            periodos,
            tipo_filtro,
            fecha_desde,
            fecha_hasta
        )

def obtener_partidas_ajuste(
    backend_url: str,
    periodo_filtro: str,
    periodos: List[Dict],
    tipo_filtro: str,
    fecha_desde: date = None,
    fecha_hasta: date = None
):
    """Obtener y mostrar partidas de ajuste"""
    
    try:
        # Determinar el período
        if periodo_filtro != "Todos los períodos":
            nombre_periodo = periodo_filtro.split(" (")[0]
            periodo_obj = next((p for p in periodos if p['descripcion'] == nombre_periodo), None)
            if not periodo_obj:
                st.error("❌ Error: Período no encontrado")
                return
            periodo_id = periodo_obj['id_periodo']
        else:
            # Si no hay período específico, usar el primer período disponible o mostrar advertencia
            if not periodos:
                st.warning("⚠️ No hay períodos disponibles para consultar")
                return
            periodo_id = periodos[0]['id_periodo']  # Usar primer período como default
        
        # Construir parámetros de consulta
        params = {}
        
        if tipo_filtro != "Todos los tipos":
            params["tipo_ajuste"] = tipo_filtro
        
        # Realizar consulta usando el endpoint correcto
        with st.spinner("Consultando partidas de ajuste..."):
            response = requests.get(f"{backend_url}/api/partidas-ajuste/periodo/{periodo_id}", params=params)
        
        if response.status_code == 200:
            partidas = response.json()
            
            if partidas:
                mostrar_partidas_ajuste(partidas)
            else:
                st.info("📭 No se encontraron partidas de ajuste con los filtros aplicados")
                
        else:
            st.error(f"Error al consultar partidas: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        st.error(f"Error de conexión: {e}")

def mostrar_partidas_ajuste(partidas: List[Dict[str, Any]]):
    """Mostrar lista de partidas de ajuste"""
    
    st.markdown(f"### 📋 Partidas de Ajuste Encontradas ({len(partidas)})")
    
    for i, partida in enumerate(partidas):
        with st.expander(
            f"🔍 ID: {partida['id_partida_ajuste']} - {partida['tipo_ajuste']} - "
            f"{partida['fecha_ajuste']} - Estado: {partida.get('estado', 'N/A')}",
            expanded=False
        ):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**📋 Información General:**")
                st.text(f"ID: {partida['id_partida_ajuste']}")
                st.text(f"Número: {partida['numero_partida']}")
                st.text(f"Fecha: {partida['fecha_ajuste']}")
                st.text(f"Tipo: {partida['tipo_ajuste']}")
                st.text(f"Estado: {partida.get('estado', 'ACTIVO')}")
                
                if partida.get('usuario_creacion'):
                    st.text(f"Usuario: {partida['usuario_creacion']}")
            
            with col2:
                st.markdown("**📅 Fechas:**")
                
                if partida.get('fecha_creacion'):
                    st.text(f"Creación: {partida['fecha_creacion'][:10]}")
                
                if partida.get('fecha_aprobacion'):
                    st.text(f"Aprobación: {partida['fecha_aprobacion'][:10]}")
                
                if partida.get('usuario_aprobacion'):
                    st.text(f"Aprobado por: {partida['usuario_aprobacion']}")
            
            # Descripción
            if partida.get('descripcion'):
                st.markdown("**📝 Descripción:**")
                st.text(partida['descripcion'])
            
            # Motivo del ajuste
            if partida.get('motivo_ajuste'):
                st.markdown("**📄 Motivo del Ajuste:**")
                st.text(partida['motivo_ajuste'])
            
            # Asientos de ajuste
            if 'asientos_ajuste' in partida and partida['asientos_ajuste']:
                st.markdown("**📊 Asientos de Ajuste:**")
                
                # Calcular totales
                total_debe = sum(float(a.get('debe', 0)) for a in partida['asientos_ajuste'])
                total_haber = sum(float(a.get('haber', 0)) for a in partida['asientos_ajuste'])
                
                col_t1, col_t2 = st.columns(2)
                with col_t1:
                    st.metric("Total Debe", f"${total_debe:,.2f}")
                with col_t2:
                    st.metric("Total Haber", f"${total_haber:,.2f}")
                
                # Tabla de asientos
                asientos_data = []
                for asiento in partida['asientos_ajuste']:
                    asientos_data.append({
                        'ID Cuenta': asiento.get('id_cuenta', 'N/A'),
                        'Descripción': asiento.get('descripcion_detalle', 'N/A'),
                        'Debe': f"${float(asiento.get('debe', 0)):,.2f}" if float(asiento.get('debe', 0)) > 0 else "-",
                        'Haber': f"${float(asiento.get('haber', 0)):,.2f}" if float(asiento.get('haber', 0)) > 0 else "-"
                    })
                
                df_asientos = pd.DataFrame(asientos_data)
                
                st.dataframe(df_asientos, width="stretch", hide_index=True)

def reportes_ajustes(backend_url: str):
    """Generar reportes de partidas de ajuste"""
    
    st.subheader("📊 Reportes de Partidas de Ajuste")
    
    # Selector de tipo de reporte
    tipo_reporte = st.selectbox(
        "Tipo de reporte:",
        [
            "Resumen por período",
            "Análisis por tipo de ajuste", 
            "Evolución temporal",
            "Detalle completo"
        ]
    )
    
    # Filtros comunes
    col1, col2 = st.columns(2)
    
    with col1:
        try:
            response_periodos = requests.get(f"{backend_url}/api/periodos")
            periodos = response_periodos.json() if response_periodos.status_code == 200 else []
            
            if periodos:
                opciones_periodos = ["Todos los períodos"] + [
                    f"{p['descripcion']} ({p['fecha_inicio']} - {p['fecha_fin']})"
                    for p in periodos
                ]
                periodo_reporte = st.selectbox("Período:", opciones_periodos, key="reporte_periodo")
            else:
                periodo_reporte = "Todos los períodos"
                periodos = []
        except:
            periodo_reporte = "Todos los períodos"
            periodos = []
    
    with col2:
        fecha_desde_reporte = st.date_input(
            "Fecha desde:",
            value=None,
            help="Fecha inicial del reporte (opcional)"
        )
    
    fecha_hasta_reporte = st.date_input(
        "Fecha hasta:",
        value=datetime.now().date(),
        help="Incluir ajustes hasta esta fecha"
    )
    
    if st.button("📊 Generar Reporte", width="stretch"):
        generar_reporte_especifico(
            backend_url,
            tipo_reporte,
            periodo_reporte,
            periodos,
            fecha_desde_reporte,
            fecha_hasta_reporte
        )

def generar_reporte_especifico(
    backend_url: str,
    tipo_reporte: str,
    periodo_reporte: str,
    periodos: List[Dict],
    fecha_desde: date,
    fecha_hasta: date
):
    """Generar reporte específico según el tipo seleccionado"""
    
    try:
        # Por ahora, usar el endpoint de período para obtener datos
        # El backend no tiene endpoint /reporte implementado
        
        if periodo_reporte != "Todos los períodos":
            nombre_periodo = periodo_reporte.split(" (")[0]
            periodo_obj = next((p for p in periodos if p['descripcion'] == nombre_periodo), None)
            if not periodo_obj:
                st.error("❌ Error: Período no encontrado")
                return
            periodo_id = periodo_obj['id_periodo']
        else:
            if not periodos:
                st.warning("⚠️ No hay períodos disponibles")
                return
            periodo_id = periodos[0]['id_periodo']
        
        # Usar endpoint de período para obtener partidas
        response = requests.get(f"{backend_url}/api/partidas-ajuste/periodo/{periodo_id}")
        
        if response.status_code == 200:
            partidas = response.json()
            
            # Filtrar por fechas si están especificadas
            if fecha_desde or fecha_hasta:
                partidas_filtradas = []
                for p in partidas:
                    fecha_ajuste = datetime.fromisoformat(p['fecha_ajuste'].replace('Z', '+00:00')).date()
                    
                    incluir = True
                    if fecha_desde and fecha_ajuste < fecha_desde:
                        incluir = False
                    if fecha_hasta and fecha_ajuste > fecha_hasta:
                        incluir = False
                    
                    if incluir:
                        partidas_filtradas.append(p)
                partidas = partidas_filtradas
            
            if not partidas:
                st.info("📭 No hay partidas de ajuste en el rango de fechas especificado")
                return
            
            # Generar reporte según el tipo
            if tipo_reporte == "Resumen por período":
                mostrar_resumen_por_periodo(partidas, periodo_reporte)
            elif tipo_reporte == "Análisis por tipo de ajuste":
                mostrar_analisis_por_tipo(partidas)
            elif tipo_reporte == "Evolución temporal":
                mostrar_evolucion_temporal(partidas)
            elif tipo_reporte == "Detalle completo":
                mostrar_detalle_completo(partidas)
                
        else:
            st.error(f"Error al generar reporte: {response.status_code}")
            
    except Exception as e:
        st.error(f"Error al generar reporte: {e}")

def mostrar_resumen_por_periodo(partidas: List[Dict], periodo_nombre: str):
    """Mostrar resumen de ajustes por período"""
    
    st.markdown(f"### 📊 Resumen de Partidas de Ajuste - {periodo_nombre}")
    
    if not partidas:
        st.info("No hay partidas para mostrar")
        return
    
    # Calcular métricas
    total_partidas = len(partidas)
    
    # Sumar debe y haber de todos los asientos
    total_debe = 0
    total_haber = 0
    for partida in partidas:
        for asiento in partida.get('asientos_ajuste', []):
            total_debe += float(asiento.get('debe', 0))
            total_haber += float(asiento.get('haber', 0))
    
    # Contar por estado
    activas = sum(1 for p in partidas if p.get('estado') == 'ACTIVO')
    anuladas = sum(1 for p in partidas if p.get('estado') == 'ANULADO')
    pendientes = sum(1 for p in partidas if p.get('estado') == 'PENDIENTE')
    
    # Métricas generales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Partidas", total_partidas)
    
    with col2:
        st.metric("Total Debe", f"${total_debe:,.2f}")
    
    with col3:
        st.metric("Total Haber", f"${total_haber:,.2f}")
    
    with col4:
        st.metric("Activas", activas, delta=f"{anuladas} anuladas" if anuladas > 0 else None)
    
    # Mostrar tabla de partidas
    st.markdown("#### 📋 Listado de Partidas")
    mostrar_partidas_ajuste(partidas)

def mostrar_analisis_por_tipo(partidas: List[Dict]):
    """Mostrar análisis por tipo de ajuste"""
    
    st.markdown("### 📊 Análisis por Tipo de Ajuste")
    
    if not partidas:
        st.info("No hay partidas para analizar")
        return
    
    # Agrupar por tipo de ajuste
    from collections import defaultdict
    tipos_resumen = defaultdict(lambda: {'cantidad': 0, 'debe': 0, 'haber': 0})
    
    for partida in partidas:
        tipo = partida.get('tipo_ajuste', 'OTROS')
        tipos_resumen[tipo]['cantidad'] += 1
        
        for asiento in partida.get('asientos_ajuste', []):
            tipos_resumen[tipo]['debe'] += float(asiento.get('debe', 0))
            tipos_resumen[tipo]['haber'] += float(asiento.get('haber', 0))
    
    # Convertir a DataFrame
    datos_tabla = []
    for tipo, valores in tipos_resumen.items():
        datos_tabla.append({
            'Tipo': tipo,
            'Cantidad': valores['cantidad'],
            'Total Debe': f"${valores['debe']:,.2f}",
            'Total Haber': f"${valores['haber']:,.2f}"
        })
    
    df_tipos = pd.DataFrame(datos_tabla)
    st.dataframe(df_tipos, width="stretch", hide_index=True)

def mostrar_evolucion_temporal(partidas: List[Dict]):
    """Mostrar evolución temporal de ajustes"""
    
    st.markdown("### 📊 Evolución Temporal")
    
    if not partidas:
        st.info("No hay partidas para mostrar")
        return
    
    # Agrupar por mes
    from collections import defaultdict
    evolucion = defaultdict(lambda: {'cantidad': 0, 'debe': 0})
    
    for partida in partidas:
        fecha = partida.get('fecha_ajuste', '')[:7]  # YYYY-MM
        evolucion[fecha]['cantidad'] += 1
        
        for asiento in partida.get('asientos_ajuste', []):
            evolucion[fecha]['debe'] += float(asiento.get('debe', 0))
    
    # Convertir a tabla
    datos_tabla = []
    for mes, valores in sorted(evolucion.items()):
        datos_tabla.append({
            'Mes': mes,
            'Cantidad Partidas': valores['cantidad'],
            'Total Debe': f"${valores['debe']:,.2f}"
        })
    
    df_evolucion = pd.DataFrame(datos_tabla)
    st.dataframe(df_evolucion, width="stretch", hide_index=True)

def mostrar_detalle_completo(partidas: List[Dict]):
    """Mostrar detalle completo de partidas"""
    
    st.markdown("### 📄 Detalle Completo de Partidas")
    
    if not partidas:
        st.info("No hay partidas para mostrar")
        return
    
    mostrar_partidas_ajuste(partidas)
