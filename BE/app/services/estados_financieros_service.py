"""
Capa de servicios para Estados Financieros.
Maneja la lógica de negocio para generar Balance General y Estado de P&G.
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from fastapi import HTTPException, status
from app.models.catalogo_cuentas import CatalogoCuentas
from app.models.asiento import Asiento
from app.models.transaccion import Transaccion
from app.models.periodo import PeriodoContable
from app.models.balance_inicial import BalanceInicial
from app.models.estados_financieros import EstadosFinancierosHistorico, ConfiguracionEstadosFinancieros
from app.schemas.estados_financieros import EstadosFinancierosHistoricoCreate
from typing import Dict, Any, List
from decimal import Decimal
from datetime import date

def generar_balance_general(db: Session, periodo_id: int) -> Dict[str, Any]:
    """
    Generar Balance General para un período específico.
    Incluye Activos, Pasivos y Patrimonio con clasificación automática.
    """
    # Validar período
    periodo = db.query(PeriodoContable).filter(PeriodoContable.id_periodo == periodo_id).first()
    if not periodo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Período no encontrado"
        )
    
    # Obtener configuración de empresa
    config = db.query(ConfiguracionEstadosFinancieros).filter(
        ConfiguracionEstadosFinancieros.activa == True
    ).first()
    
    # Calcular saldos por cuenta
    saldos_query = db.query(
        CatalogoCuentas.id_cuenta,
        CatalogoCuentas.codigo_cuenta,
        CatalogoCuentas.nombre_cuenta,
        CatalogoCuentas.tipo_cuenta,
        func.sum(Asiento.debe).label('total_debe'),
        func.sum(Asiento.haber).label('total_haber')
    ).join(
        Asiento, CatalogoCuentas.id_cuenta == Asiento.id_cuenta
    ).join(
        Transaccion, Asiento.id_transaccion == Transaccion.id_transaccion
    ).filter(
        Transaccion.id_periodo == periodo_id
    ).group_by(
        CatalogoCuentas.id_cuenta,
        CatalogoCuentas.codigo_cuenta,
        CatalogoCuentas.nombre_cuenta,
        CatalogoCuentas.tipo_cuenta
    ).all()
    
    # Obtener balances iniciales
    balances_iniciales = db.query(BalanceInicial).filter(
        BalanceInicial.id_periodo == periodo_id,
        BalanceInicial.estado_balance == 'ACTIVO'
    ).all()
    
    balance_inicial_map = {bi.id_cuenta: bi.saldo_inicial for bi in balances_iniciales}
    
    # Organizar cuentas por tipo
    balance_general = {
        "empresa": {
            "nombre": config.nombre_empresa if config else "Empresa",
            "nit": config.nit_empresa if config else "",
            "direccion": config.direccion_empresa if config else "",
            "moneda": config.moneda_reporte if config else "USD"
        },
        "periodo": {
            "id": periodo_id,
            "fecha_inicio": periodo.fecha_inicio,
            "fecha_fin": periodo.fecha_fin,
            "tipo": periodo.tipo_periodo
        },
        "fecha_generacion": date.today(),
        "activos": {
            "corrientes": [],
            "no_corrientes": [],
            "total_activos": Decimal("0.00")
        },
        "pasivos": {
            "corrientes": [],
            "no_corrientes": [],
            "total_pasivos": Decimal("0.00")
        },
        "patrimonio": {
            "capital": [],
            "utilidades": [],
            "total_patrimonio": Decimal("0.00")
        },
        "total_pasivo_patrimonio": Decimal("0.00")
    }
    
    # Procesar cada cuenta
    for saldo in saldos_query:
        # Obtener saldo inicial
        saldo_inicial = balance_inicial_map.get(saldo.id_cuenta, Decimal("0.00"))
        
        # Calcular saldo final según naturaleza de la cuenta
        if saldo.tipo_cuenta in ['Activo']:
            saldo_final = saldo_inicial + (saldo.total_debe or 0) - (saldo.total_haber or 0)
        else:  # Pasivo, Capital
            saldo_final = saldo_inicial + (saldo.total_haber or 0) - (saldo.total_debe or 0)
        
        cuenta_data = {
            "id_cuenta": saldo.id_cuenta,
            "codigo": saldo.codigo_cuenta,
            "nombre": saldo.nombre_cuenta,
            "saldo_inicial": float(saldo_inicial),
            "movimientos_debe": float(saldo.total_debe or 0),
            "movimientos_haber": float(saldo.total_haber or 0),
            "saldo_final": float(saldo_final)
        }
        
        # Clasificar por tipo de cuenta
        if saldo.tipo_cuenta == 'Activo':
            # Clasificar activos (simplificado - se puede mejorar con campo clasificacion)
            if 'caja' in saldo.nombre_cuenta.lower() or 'banco' in saldo.nombre_cuenta.lower() or 'efectivo' in saldo.nombre_cuenta.lower():
                balance_general["activos"]["corrientes"].append(cuenta_data)
            else:
                balance_general["activos"]["no_corrientes"].append(cuenta_data)
            balance_general["activos"]["total_activos"] += Decimal(str(saldo_final))
        
        elif saldo.tipo_cuenta == 'Pasivo':
            # Clasificar pasivos
            if 'por pagar' in saldo.nombre_cuenta.lower() or 'acumulado' in saldo.nombre_cuenta.lower():
                balance_general["pasivos"]["corrientes"].append(cuenta_data)
            else:
                balance_general["pasivos"]["no_corrientes"].append(cuenta_data)
            balance_general["pasivos"]["total_pasivos"] += Decimal(str(saldo_final))
        
        elif saldo.tipo_cuenta == 'Capital':
            if 'utilidad' in saldo.nombre_cuenta.lower() or 'resultado' in saldo.nombre_cuenta.lower():
                balance_general["patrimonio"]["utilidades"].append(cuenta_data)
            else:
                balance_general["patrimonio"]["capital"].append(cuenta_data)
            balance_general["patrimonio"]["total_patrimonio"] += Decimal(str(saldo_final))
    
    # Calcular total pasivo + patrimonio
    balance_general["total_pasivo_patrimonio"] = (
        balance_general["pasivos"]["total_pasivos"] + 
        balance_general["patrimonio"]["total_patrimonio"]
    )
    
    # Convertir Decimals a float para JSON
    for key in ["total_activos", "total_pasivos", "total_patrimonio", "total_pasivo_patrimonio"]:
        if "activos" in key:
            balance_general["activos"][key.replace("total_", "")] = float(balance_general["activos"][key])
        elif "pasivos" in key:
            balance_general["pasivos"][key.replace("total_", "")] = float(balance_general["pasivos"][key])
        elif "patrimonio" in key:
            balance_general["patrimonio"][key.replace("total_", "")] = float(balance_general["patrimonio"][key])
        else:
            balance_general[key] = float(balance_general[key])
    
    return balance_general

def generar_estado_perdidas_ganancias(db: Session, periodo_id: int) -> Dict[str, Any]:
    """
    Generar Estado de Pérdidas y Ganancias para un período específico.
    """
    # Validar período
    periodo = db.query(PeriodoContable).filter(PeriodoContable.id_periodo == periodo_id).first()
    if not periodo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Período no encontrado"
        )
    
    # Obtener configuración de empresa
    config = db.query(ConfiguracionEstadosFinancieros).filter(
        ConfiguracionEstadosFinancieros.activa == True
    ).first()
    
    # Calcular ingresos y egresos por categoría
    ingresos_egresos = db.query(
        CatalogoCuentas.tipo_cuenta,
        Transaccion.categoria,
        func.sum(Asiento.debe).label('total_debe'),
        func.sum(Asiento.haber).label('total_haber')
    ).join(
        Asiento, CatalogoCuentas.id_cuenta == Asiento.id_cuenta
    ).join(
        Transaccion, Asiento.id_transaccion == Transaccion.id_transaccion
    ).filter(
        Transaccion.id_periodo == periodo_id,
        CatalogoCuentas.tipo_cuenta.in_(['Ingreso', 'Egreso'])
    ).group_by(
        CatalogoCuentas.tipo_cuenta,
        Transaccion.categoria
    ).all()
    
    estado_py = {
        "empresa": {
            "nombre": config.nombre_empresa if config else "Empresa",
            "nit": config.nit_empresa if config else "",
            "moneda": config.moneda_reporte if config else "USD"
        },
        "periodo": {
            "id": periodo_id,
            "fecha_inicio": periodo.fecha_inicio,
            "fecha_fin": periodo.fecha_fin,
            "tipo": periodo.tipo_periodo
        },
        "fecha_generacion": date.today(),
        "ingresos": {},
        "egresos": {},
        "resumen": {
            "total_ingresos": Decimal("0.00"),
            "total_egresos": Decimal("0.00"),
            "utilidad_bruta": Decimal("0.00"),
            "utilidad_neta": Decimal("0.00")
        }
    }
    
    # Procesar ingresos y egresos
    for item in ingresos_egresos:
        if item.tipo_cuenta == 'Ingreso':
            # Para ingresos, el saldo es haber - debe
            monto = (item.total_haber or 0) - (item.total_debe or 0)
            estado_py["ingresos"][item.categoria] = float(monto)
            estado_py["resumen"]["total_ingresos"] += Decimal(str(monto))
        
        elif item.tipo_cuenta == 'Egreso':
            # Para egresos, el saldo es debe - haber
            monto = (item.total_debe or 0) - (item.total_haber or 0)
            estado_py["egresos"][item.categoria] = float(monto)
            estado_py["resumen"]["total_egresos"] += Decimal(str(monto))
    
    # Calcular utilidades
    estado_py["resumen"]["utilidad_bruta"] = (
        estado_py["resumen"]["total_ingresos"] - estado_py["resumen"]["total_egresos"]
    )
    estado_py["resumen"]["utilidad_neta"] = estado_py["resumen"]["utilidad_bruta"]
    
    # Convertir a float para JSON
    for key, value in estado_py["resumen"].items():
        estado_py["resumen"][key] = float(value)
    
    return estado_py

def guardar_estado_financiero(
    db: Session, 
    tipo_estado: str, 
    contenido: Dict[str, Any], 
    usuario: str
) -> EstadosFinancierosHistorico:
    """Guardar un estado financiero generado en el histórico"""
    
    periodo_id = contenido["periodo"]["id"]
    
    # Extraer totales según el tipo de estado
    if tipo_estado == "BALANCE_GENERAL":
        total_activos = contenido.get("activos", {}).get("total_activos", 0)
        total_pasivos = contenido.get("pasivos", {}).get("total_pasivos", 0)
        patrimonio = contenido.get("patrimonio", {}).get("total_patrimonio", 0)
        utilidad_perdida = None
    else:  # ESTADO_PERDIDAS_GANANCIAS
        total_activos = None
        total_pasivos = None
        patrimonio = None
        utilidad_perdida = contenido.get("resumen", {}).get("utilidad_neta", 0)
    
    estado_data = EstadosFinancierosHistoricoCreate(
        id_periodo=periodo_id,
        tipo_estado=tipo_estado,
        fecha_generacion=date.today(),
        contenido_json=contenido,
        total_activos=total_activos,
        total_pasivos=total_pasivos,
        patrimonio=patrimonio,
        utilidad_perdida=utilidad_perdida,
        usuario_generacion=usuario
    )
    
    try:
        db_estado = EstadosFinancierosHistorico(**estado_data.dict())
        db.add(db_estado)
        db.commit()
        db.refresh(db_estado)
        return db_estado
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error al guardar estado financiero: {str(e)}"
        )