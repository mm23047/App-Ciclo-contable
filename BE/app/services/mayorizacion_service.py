"""
Capa de servicios para operaciones de Mayorización (Libro Mayor).
Maneja la lógica de negocio para generar el libro mayor automáticamente.
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, String, literal_column
from fastapi import HTTPException, status
from app.models.libro_mayor import LibroMayor
from app.models.asiento import Asiento
from app.models.transaccion import Transaccion
from app.models.catalogo_cuentas import CatalogoCuentas
from app.models.periodo import PeriodoContable
from app.models.partidas_ajuste import AsientoAjuste, PartidaAjuste
from typing import List, Optional, Dict, Any
from decimal import Decimal
from datetime import date

def generar_libro_mayor_cuenta(
    db: Session, 
    cuenta_id: int, 
    periodo_id: Optional[int] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None
) -> List[Dict[str, Any]]:
    """
    Generar el libro mayor para una cuenta específica.
    Calcula saldos acumulados por cada movimiento.
    """
    # Validar que la cuenta existe
    cuenta = db.query(CatalogoCuentas).filter(CatalogoCuentas.id_cuenta == cuenta_id).first()
    if not cuenta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cuenta no encontrada"
        )
    
    # Query para asientos normales
    query_asientos = db.query(
        Asiento.id_asiento.label('id'),
        Asiento.debe,
        Asiento.haber,
        Asiento.descripcion_asiento.label('descripcion'),
        Transaccion.fecha_transaccion.label('fecha'),
        Transaccion.numero_referencia.label('referencia'),
        literal_column("'ASIENTO'").label('tipo')
    ).join(
        Transaccion, Asiento.id_transaccion == Transaccion.id_transaccion
    ).filter(
        Asiento.id_cuenta == cuenta_id
    )
    
    # Aplicar filtros a asientos
    if periodo_id:
        query_asientos = query_asientos.filter(Transaccion.id_periodo == periodo_id)
    if fecha_desde:
        query_asientos = query_asientos.filter(Transaccion.fecha_transaccion >= fecha_desde)
    if fecha_hasta:
        query_asientos = query_asientos.filter(Transaccion.fecha_transaccion <= fecha_hasta)
    
    # Query para asientos de ajuste
    query_ajustes = db.query(
        AsientoAjuste.id_asiento_ajuste.label('id'),
        AsientoAjuste.debe,
        AsientoAjuste.haber,
        AsientoAjuste.descripcion_detalle.label('descripcion'),
        PartidaAjuste.fecha_ajuste.label('fecha'),
        PartidaAjuste.numero_partida.label('referencia'),
        literal_column("'AJUSTE'").label('tipo')
    ).join(
        PartidaAjuste, AsientoAjuste.id_partida_ajuste == PartidaAjuste.id_partida_ajuste
    ).filter(
        AsientoAjuste.id_cuenta == cuenta_id,
        PartidaAjuste.estado == 'ACTIVO'
    )
    
    # Aplicar filtros a ajustes
    if periodo_id:
        query_ajustes = query_ajustes.filter(PartidaAjuste.id_periodo == periodo_id)
    if fecha_desde:
        query_ajustes = query_ajustes.filter(PartidaAjuste.fecha_ajuste >= fecha_desde)
    if fecha_hasta:
        query_ajustes = query_ajustes.filter(PartidaAjuste.fecha_ajuste <= fecha_hasta)
    
    # Unir ambas queries y ordenar por fecha
    movimientos = query_asientos.union_all(query_ajustes).order_by('fecha', 'id').all()
    
    # Calcular saldos acumulados
    libro_mayor = []
    saldo_acumulado = Decimal("0.00")
    
    for movimiento in movimientos:
        # Determinar movimiento según naturaleza de la cuenta
        if cuenta.tipo_cuenta in ['Activo', 'Egreso']:
            # Cuentas de naturaleza deudora
            cambio = float(movimiento.debe) - float(movimiento.haber)
        else:
            # Cuentas de naturaleza acreedora (Pasivo, Capital, Ingreso)
            cambio = float(movimiento.haber) - float(movimiento.debe)
        
        saldo_anterior = saldo_acumulado
        saldo_acumulado += Decimal(str(cambio))
        
        # Determinar tipo de saldo
        tipo_saldo = "DEUDOR" if saldo_acumulado >= 0 else "ACREEDOR"
        if cuenta.tipo_cuenta in ['Pasivo', 'Capital', 'Ingreso']:
            tipo_saldo = "ACREEDOR" if saldo_acumulado >= 0 else "DEUDOR"
        
        # Convertir fecha si es datetime
        fecha_mov = movimiento.fecha.date() if hasattr(movimiento.fecha, 'date') else movimiento.fecha
        
        libro_mayor.append({
            "id": movimiento.id,
            "tipo": movimiento.tipo,
            "fecha_movimiento": fecha_mov,
            "descripcion": movimiento.descripcion or "Sin descripción",
            "referencia": movimiento.referencia or f"{movimiento.tipo}-{movimiento.id}",
            "debe": float(movimiento.debe),
            "haber": float(movimiento.haber),
            "saldo_anterior": float(saldo_anterior),
            "saldo_actual": float(saldo_acumulado),
            "tipo_saldo": tipo_saldo,
            "cuenta_codigo": cuenta.codigo_cuenta,
            "cuenta_nombre": cuenta.nombre_cuenta,
            "cuenta_tipo": cuenta.tipo_cuenta
        })
    
    return libro_mayor

def generar_libro_mayor_completo(db: Session, periodo_id: int) -> Dict[str, Any]:
    """
    Generar libro mayor completo para todas las cuentas con movimientos en un período.
    """
    # Validar que el período existe
    periodo = db.query(PeriodoContable).filter(PeriodoContable.id_periodo == periodo_id).first()
    if not periodo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Período no encontrado"
        )
    
    # Obtener IDs de cuentas con movimientos de asientos normales
    ids_asientos = db.query(
        Asiento.id_cuenta
    ).join(
        Transaccion, Asiento.id_transaccion == Transaccion.id_transaccion
    ).filter(
        Transaccion.id_periodo == periodo_id
    ).distinct().all()
    
    # Obtener IDs de cuentas con movimientos de ajuste
    ids_ajustes = db.query(
        AsientoAjuste.id_cuenta
    ).join(
        PartidaAjuste, AsientoAjuste.id_partida_ajuste == PartidaAjuste.id_partida_ajuste
    ).filter(
        PartidaAjuste.id_periodo == periodo_id,
        PartidaAjuste.estado == 'ACTIVO'
    ).distinct().all()
    
    # Combinar ambos conjuntos de IDs (usar set para eliminar duplicados)
    ids_asientos_set = {r[0] for r in ids_asientos}
    ids_ajustes_set = {r[0] for r in ids_ajustes}
    ids_lista = list(ids_asientos_set.union(ids_ajustes_set))
    
    # Obtener detalles de las cuentas si hay IDs
    if not ids_lista:
        cuentas_con_movimientos = []
    else:
        cuentas_con_movimientos = db.query(
            CatalogoCuentas.id_cuenta,
            CatalogoCuentas.codigo_cuenta,
            CatalogoCuentas.nombre_cuenta,
            CatalogoCuentas.tipo_cuenta
        ).filter(
            CatalogoCuentas.id_cuenta.in_(ids_lista)
        ).order_by(CatalogoCuentas.codigo_cuenta).all()
    
    libro_mayor_completo = {
        "periodo_id": periodo_id,
        "fecha_inicio": periodo.fecha_inicio,
        "fecha_fin": periodo.fecha_fin,
        "tipo_periodo": periodo.tipo_periodo,
        "cuentas": {}
    }
    
    for cuenta in cuentas_con_movimientos:
        movimientos = generar_libro_mayor_cuenta(
            db=db,
            cuenta_id=cuenta.id_cuenta,
            periodo_id=periodo_id
        )
        
        libro_mayor_completo["cuentas"][cuenta.codigo_cuenta] = {
            "id_cuenta": cuenta.id_cuenta,
            "nombre_cuenta": cuenta.nombre_cuenta,
            "tipo_cuenta": cuenta.tipo_cuenta,
            "movimientos": movimientos,
            "saldo_final": movimientos[-1]["saldo_actual"] if movimientos else 0.00
        }
    
    return libro_mayor_completo

def actualizar_libro_mayor_automatico(db: Session, asiento_id: int) -> LibroMayor:
    """
    Actualizar automáticamente el libro mayor cuando se crea/modifica un asiento.
    Esta función se llamaría desde triggers o servicios de asientos.
    """
    # Obtener el asiento
    asiento = db.query(Asiento).filter(Asiento.id_asiento == asiento_id).first()
    if not asiento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asiento no encontrado"
        )
    
    # Obtener saldo anterior para la cuenta
    saldo_anterior = db.query(LibroMayor).filter(
        and_(
            LibroMayor.id_cuenta == asiento.id_cuenta,
            LibroMayor.fecha_movimiento <= asiento.transaccion.fecha_transaccion.date()
        )
    ).order_by(LibroMayor.fecha_movimiento.desc()).first()
    
    saldo_anterior_valor = Decimal(str(saldo_anterior.saldo_actual)) if saldo_anterior else Decimal("0.00")
    
    # Calcular nuevo saldo
    cuenta = asiento.cuenta
    if cuenta.tipo_cuenta in ['Activo', 'Egreso']:
        movimiento = asiento.debe - asiento.haber
    else:
        movimiento = asiento.haber - asiento.debe
    
    saldo_actual = saldo_anterior_valor + movimiento
    tipo_saldo = "DEUDOR" if saldo_actual >= 0 else "ACREEDOR"
    
    # Crear registro en libro mayor
    libro_mayor_entry = LibroMayor(
        id_cuenta=asiento.id_cuenta,
        fecha_movimiento=asiento.transaccion.fecha_transaccion.date(),
        descripcion=asiento.descripcion_asiento or asiento.transaccion.descripcion,
        referencia=asiento.transaccion.numero_referencia or f"ASI-{asiento.id_asiento}",
        debe=asiento.debe,
        haber=asiento.haber,
        saldo_anterior=saldo_anterior_valor,
        saldo_actual=saldo_actual,
        id_asiento=asiento.id_asiento,
        id_periodo=asiento.transaccion.id_periodo,
        tipo_saldo=tipo_saldo
    )
    
    try:
        db.add(libro_mayor_entry)
        db.commit()
        db.refresh(libro_mayor_entry)
        return libro_mayor_entry
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error al actualizar libro mayor: {str(e)}"
        )