"""
Capa de servicios para Balanza de Comprobación.
Maneja la lógica de negocio para generar balanzas de comprobación.
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from fastapi import HTTPException, status
from app.models.balanza_comprobacion import BalanzaComprobacion
from app.models.catalogo_cuentas import CatalogoCuentas
from app.models.asiento import Asiento
from app.models.transaccion import Transaccion
from app.models.periodo import PeriodoContable
from app.models.balance_inicial import BalanceInicial
from app.schemas.balanza_comprobacion import BalanzaComprobacionCreate
from typing import Dict, List
from decimal import Decimal
from datetime import date, datetime

def generar_balanza_comprobacion(
    db: Session, 
    periodo_id: int, 
    fecha_hasta: date = None,
    usuario: str = "Sistema"
) -> BalanzaComprobacion:
    """
    Generar una nueva balanza de comprobación para un período específico
    """
    # Validar que el período exista
    periodo = db.query(PeriodoContable).filter(
        PeriodoContable.id_periodo == periodo_id
    ).first()
    
    if not periodo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Período no encontrado"
        )
    
    # Si no se especifica fecha_hasta, usar la fecha fin del período
    if not fecha_hasta:
        fecha_hasta = periodo.fecha_fin
    
    # Validar que la fecha esté dentro del período
    if fecha_hasta < periodo.fecha_inicio or fecha_hasta > periodo.fecha_fin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La fecha debe estar dentro del rango del período"
        )
    
    # Obtener todas las cuentas que tienen movimientos en el período o balance inicial
    cuentas_con_movimientos = db.query(
        CatalogoCuentas.id_cuenta,
        CatalogoCuentas.codigo_cuenta,
        CatalogoCuentas.nombre_cuenta,
        CatalogoCuentas.tipo_cuenta,
        func.coalesce(func.sum(Asiento.debe), 0).label('total_debe'),
        func.coalesce(func.sum(Asiento.haber), 0).label('total_haber')
    ).outerjoin(
        Asiento, CatalogoCuentas.id_cuenta == Asiento.id_cuenta
    ).outerjoin(
        Transaccion, and_(
            Asiento.id_transaccion == Transaccion.id_transaccion,
            Transaccion.id_periodo == periodo_id,
            Transaccion.fecha_transaccion <= fecha_hasta
        )
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
    
    # Construir datos de la balanza
    detalle_cuentas = []
    totales = {
        'total_debe': Decimal('0.00'),
        'total_haber': Decimal('0.00'),
        'total_saldo_debe': Decimal('0.00'),
        'total_saldo_haber': Decimal('0.00')
    }
    
    for cuenta in cuentas_con_movimientos:
        saldo_inicial = balance_inicial_map.get(cuenta.id_cuenta, Decimal('0.00'))
        movimiento_debe = Decimal(str(cuenta.total_debe))
        movimiento_haber = Decimal(str(cuenta.total_haber))
        
        # Calcular saldo final según naturaleza de la cuenta
        if cuenta.tipo_cuenta in ['Activo', 'Egreso']:
            # Naturaleza deudora
            saldo_final = saldo_inicial + movimiento_debe - movimiento_haber
            saldo_debe = saldo_final if saldo_final >= 0 else Decimal('0.00')
            saldo_haber = abs(saldo_final) if saldo_final < 0 else Decimal('0.00')
        else:
            # Naturaleza acreedora (Pasivo, Capital, Ingreso)
            saldo_final = saldo_inicial + movimiento_haber - movimiento_debe
            saldo_haber = saldo_final if saldo_final >= 0 else Decimal('0.00')
            saldo_debe = abs(saldo_final) if saldo_final < 0 else Decimal('0.00')
        
        # Solo incluir cuentas con movimientos o saldo inicial
        if saldo_inicial != 0 or movimiento_debe != 0 or movimiento_haber != 0:
            detalle_cuenta = {
                "id_cuenta": cuenta.id_cuenta,
                "codigo_cuenta": cuenta.codigo_cuenta,
                "nombre_cuenta": cuenta.nombre_cuenta,
                "tipo_cuenta": cuenta.tipo_cuenta,
                "saldo_inicial": float(saldo_inicial),
                "movimiento_debe": float(movimiento_debe),
                "movimiento_haber": float(movimiento_haber),
                "saldo_debe": float(saldo_debe),
                "saldo_haber": float(saldo_haber)
            }
            
            detalle_cuentas.append(detalle_cuenta)
            
            # Acumular totales
            totales['total_debe'] += movimiento_debe
            totales['total_haber'] += movimiento_haber
            totales['total_saldo_debe'] += saldo_debe
            totales['total_saldo_haber'] += saldo_haber
    
    # Verificar cuadre de la balanza
    diferencia_movimientos = totales['total_debe'] - totales['total_haber']
    diferencia_saldos = totales['total_saldo_debe'] - totales['total_saldo_haber']
    
    estado_balanza = 'CUADRADA'
    if abs(diferencia_movimientos) > Decimal('0.01') or abs(diferencia_saldos) > Decimal('0.01'):
        estado_balanza = 'DESCUADRADA'
    
    # Crear registro de balanza
    balanza_data = {
        "id_periodo": periodo_id,
        "fecha_generacion": date.today(),
        "fecha_hasta": fecha_hasta,
        "estado_balanza": estado_balanza,
        "total_debe": float(totales['total_debe']),
        "total_haber": float(totales['total_haber']),
        "total_saldo_debe": float(totales['total_saldo_debe']),
        "total_saldo_haber": float(totales['total_saldo_haber']),
        "diferencia_movimientos": float(diferencia_movimientos),
        "diferencia_saldos": float(diferencia_saldos),
        "detalle_cuentas": detalle_cuentas,
        "usuario_generacion": usuario
    }
    
    try:
        balanza_create = BalanzaComprobacionCreate(**balanza_data)
        db_balanza = BalanzaComprobacion(**balanza_create.dict())
        db.add(db_balanza)
        db.commit()
        db.refresh(db_balanza)
        return db_balanza
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error al generar balanza de comprobación: {str(e)}"
        )

def obtener_balanzas_periodo(db: Session, periodo_id: int) -> List[BalanzaComprobacion]:
    """
    Obtener todas las balanzas de comprobación de un período
    """
    return db.query(BalanzaComprobacion).filter(
        BalanzaComprobacion.id_periodo == periodo_id
    ).order_by(BalanzaComprobacion.fecha_generacion.desc()).all()

def obtener_balanza_por_id(db: Session, balanza_id: int) -> BalanzaComprobacion:
    """
    Obtener una balanza específica por ID
    """
    balanza = db.query(BalanzaComprobacion).filter(
        BalanzaComprobacion.id_balanza == balanza_id
    ).first()
    
    if not balanza:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Balanza de comprobación no encontrada"
        )
    
    return balanza

def validar_cuadre_periodo(db: Session, periodo_id: int, fecha_hasta: date = None) -> Dict:
    """
    Validar el cuadre contable de un período sin generar balanza
    """
    periodo = db.query(PeriodoContable).filter(
        PeriodoContable.id_periodo == periodo_id
    ).first()
    
    if not periodo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Período no encontrado"
        )
    
    if not fecha_hasta:
        fecha_hasta = periodo.fecha_fin
    
    # Calcular totales de asientos
    totales_asientos = db.query(
        func.sum(Asiento.debe).label('total_debe'),
        func.sum(Asiento.haber).label('total_haber')
    ).join(
        Transaccion, Asiento.id_transaccion == Transaccion.id_transaccion
    ).filter(
        Transaccion.id_periodo == periodo_id,
        Transaccion.fecha_transaccion <= fecha_hasta
    ).first()
    
    total_debe = totales_asientos.total_debe or Decimal('0.00')
    total_haber = totales_asientos.total_haber or Decimal('0.00')
    diferencia = total_debe - total_haber
    
    # Contar transacciones descuadradas
    transacciones_descuadradas = db.query(
        Transaccion.id_transaccion,
        Transaccion.descripcion,
        func.sum(Asiento.debe).label('debe'),
        func.sum(Asiento.haber).label('haber')
    ).join(
        Asiento, Transaccion.id_transaccion == Asiento.id_transaccion
    ).filter(
        Transaccion.id_periodo == periodo_id,
        Transaccion.fecha_transaccion <= fecha_hasta
    ).group_by(
        Transaccion.id_transaccion,
        Transaccion.descripcion
    ).having(
        func.sum(Asiento.debe) != func.sum(Asiento.haber)
    ).all()
    
    estado_validacion = "CUADRADO" if abs(diferencia) <= Decimal('0.01') else "DESCUADRADO"
    
    resultado = {
        "periodo_id": periodo_id,
        "fecha_validacion": fecha_hasta,
        "estado": estado_validacion,
        "total_debe": float(total_debe),
        "total_haber": float(total_haber),
        "diferencia": float(diferencia),
        "cantidad_transacciones_descuadradas": len(transacciones_descuadradas),
        "transacciones_descuadradas": [
            {
                "id_transaccion": t.id_transaccion,
                "descripcion": t.descripcion,
                "debe": float(t.debe),
                "haber": float(t.haber),
                "diferencia": float(t.debe - t.haber)
            }
            for t in transacciones_descuadradas
        ]
    }
    
    return resultado

def obtener_analisis_cuentas_periodo(
    db: Session, 
    periodo_id: int, 
    tipo_cuenta: str = None
) -> List[Dict]:
    """
    Obtener análisis detallado de cuentas por período
    """
    query = db.query(
        CatalogoCuentas.id_cuenta,
        CatalogoCuentas.codigo_cuenta,
        CatalogoCuentas.nombre_cuenta,
        CatalogoCuentas.tipo_cuenta,
        func.count(Asiento.id_asiento).label('cantidad_movimientos'),
        func.coalesce(func.sum(Asiento.debe), 0).label('total_debe'),
        func.coalesce(func.sum(Asiento.haber), 0).label('total_haber')
    ).outerjoin(
        Asiento, CatalogoCuentas.id_cuenta == Asiento.id_cuenta
    ).outerjoin(
        Transaccion, and_(
            Asiento.id_transaccion == Transaccion.id_transaccion,
            Transaccion.id_periodo == periodo_id
        )
    )
    
    if tipo_cuenta:
        query = query.filter(CatalogoCuentas.tipo_cuenta == tipo_cuenta)
    
    cuentas = query.group_by(
        CatalogoCuentas.id_cuenta,
        CatalogoCuentas.codigo_cuenta,
        CatalogoCuentas.nombre_cuenta,
        CatalogoCuentas.tipo_cuenta
    ).order_by(CatalogoCuentas.codigo_cuenta).all()
    
    # Obtener balances iniciales
    balances_iniciales = db.query(BalanceInicial).filter(
        BalanceInicial.id_periodo == periodo_id,
        BalanceInicial.estado_balance == 'ACTIVO'
    ).all()
    
    balance_inicial_map = {bi.id_cuenta: bi.saldo_inicial for bi in balances_iniciales}
    
    resultado = []
    for cuenta in cuentas:
        saldo_inicial = balance_inicial_map.get(cuenta.id_cuenta, Decimal('0.00'))
        total_debe = Decimal(str(cuenta.total_debe))
        total_haber = Decimal(str(cuenta.total_haber))
        
        # Calcular saldo final
        if cuenta.tipo_cuenta in ['Activo', 'Egreso']:
            saldo_final = saldo_inicial + total_debe - total_haber
        else:
            saldo_final = saldo_inicial + total_haber - total_debe
        
        resultado.append({
            "id_cuenta": cuenta.id_cuenta,
            "codigo_cuenta": cuenta.codigo_cuenta,
            "nombre_cuenta": cuenta.nombre_cuenta,
            "tipo_cuenta": cuenta.tipo_cuenta,
            "saldo_inicial": float(saldo_inicial),
            "cantidad_movimientos": cuenta.cantidad_movimientos,
            "total_debe": float(total_debe),
            "total_haber": float(total_haber),
            "saldo_final": float(saldo_final),
            "porcentaje_actividad": 0 if total_debe + total_haber == 0 else float(
                (total_debe + total_haber) / (total_debe + total_haber) * 100
            )
        })
    
    return resultado