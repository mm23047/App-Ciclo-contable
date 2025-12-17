"""
Capa de servicios para Balance Inicial.
Maneja la lógica de negocio para configuración de balances iniciales por período.
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from fastapi import HTTPException, status
from app.models.balance_inicial import BalanceInicial
from app.models.catalogo_cuentas import CatalogoCuentas
from app.models.periodo import PeriodoContable
from app.schemas.balance_inicial import BalanceInicialCreate, BalanceInicialUpdate
from typing import Dict, List, Optional
from decimal import Decimal
from datetime import date

def crear_balance_inicial(db: Session, balance_data: BalanceInicialCreate, usuario: str) -> BalanceInicial:
    """
    Crear un nuevo balance inicial con validaciones de negocio
    """
    # Validar que la cuenta exista
    cuenta = db.query(CatalogoCuentas).filter(
        CatalogoCuentas.id_cuenta == balance_data.id_cuenta
    ).first()
    if not cuenta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cuenta no encontrada"
        )
    
    # Validar que el período exista
    periodo = db.query(PeriodoContable).filter(
        PeriodoContable.id_periodo == balance_data.id_periodo
    ).first()
    if not periodo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Período no encontrado"
        )
    
    # Verificar que no exista ya un balance inicial para esta cuenta y período
    balance_existente = db.query(BalanceInicial).filter(
        and_(
            BalanceInicial.id_cuenta == balance_data.id_cuenta,
            BalanceInicial.id_periodo == balance_data.id_periodo
        )
    ).first()
    
    if balance_existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ya existe un balance inicial para la cuenta {cuenta.codigo_cuenta} en el período {periodo.descripcion}"
        )
    
    # Validar que el saldo inicial tenga la naturaleza correcta según tipo de cuenta
    if cuenta.tipo_cuenta in ['Activo', 'Egreso'] and balance_data.saldo_inicial < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Las cuentas de tipo {cuenta.tipo_cuenta} no pueden tener saldo inicial negativo"
        )
    
    try:
        db_balance = BalanceInicial(
            **balance_data.dict(),
            fecha_registro=date.today(),
            fecha_creacion=date.today(),
            usuario_creacion=usuario,
            estado_balance='ACTIVO'
        )
        db.add(db_balance)
        db.commit()
        db.refresh(db_balance)
        return db_balance
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error al crear balance inicial: {str(e)}"
        )

def obtener_balances_por_periodo(db: Session, periodo_id: int) -> List[Dict]:
    """
    Obtener todos los balances iniciales de un período con información de las cuentas
    """
    balances = db.query(
        BalanceInicial,
        CatalogoCuentas.codigo_cuenta,
        CatalogoCuentas.nombre_cuenta,
        CatalogoCuentas.tipo_cuenta
    ).join(
        CatalogoCuentas, BalanceInicial.id_cuenta == CatalogoCuentas.id_cuenta
    ).filter(
        BalanceInicial.id_periodo == periodo_id,
        BalanceInicial.estado_balance == 'ACTIVO'
    ).order_by(CatalogoCuentas.codigo_cuenta).all()
    
    resultado = []
    for balance, codigo, nombre, tipo in balances:
        resultado.append({
            "id_balance_inicial": balance.id_balance_inicial,
            "id_cuenta": balance.id_cuenta,
            "codigo_cuenta": codigo,
            "nombre_cuenta": nombre,
            "tipo_cuenta": tipo,
            "saldo_inicial": float(balance.saldo_inicial),
            "naturaleza_saldo": balance.naturaleza_saldo,
            "fecha_creacion": balance.fecha_creacion,
            "usuario_creacion": balance.usuario_creacion,
            "observaciones": balance.observaciones,
            "estado_balance": balance.estado_balance
        })
    
    return resultado

def actualizar_balance_inicial(
    db: Session, 
    balance_id: int, 
    balance_data: BalanceInicialUpdate,
    usuario: str
) -> BalanceInicial:
    """
    Actualizar un balance inicial existente
    """
    balance = db.query(BalanceInicial).filter(BalanceInicial.id_balance_inicial == balance_id).first()
    if not balance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Balance inicial no encontrado"
        )
    
    # Obtener información de la cuenta para validaciones
    cuenta = db.query(CatalogoCuentas).filter(
        CatalogoCuentas.id_cuenta == balance.id_cuenta
    ).first()
    
    # Validar naturaleza del saldo si se está actualizando
    if balance_data.saldo_inicial is not None:
        if cuenta.tipo_cuenta in ['Activo', 'Egreso'] and balance_data.saldo_inicial < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Las cuentas de tipo {cuenta.tipo_cuenta} no pueden tener saldo inicial negativo"
            )
    
    try:
        # Actualizar campos modificables
        update_data = balance_data.dict(exclude_unset=True)
        update_data['fecha_modificacion'] = date.today()
        update_data['usuario_modificacion'] = usuario
        
        for field, value in update_data.items():
            setattr(balance, field, value)
        
        db.commit()
        db.refresh(balance)
        return balance
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error al actualizar balance inicial: {str(e)}"
        )

def eliminar_balance_inicial(db: Session, balance_id: int, usuario: str) -> bool:
    """
    Eliminar (desactivar) un balance inicial
    """
    balance = db.query(BalanceInicial).filter(BalanceInicial.id_balance_inicial == balance_id).first()
    if not balance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Balance inicial no encontrado"
        )
    
    try:
        # Marcar como inactivo en lugar de eliminar físicamente
        balance.estado_balance = 'INACTIVO'
        balance.fecha_modificacion = date.today()
        balance.usuario_modificacion = usuario
        
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error al eliminar balance inicial: {str(e)}"
        )

def eliminar_balances_periodo(db: Session, periodo_id: int, usuario: str) -> int:
    """
    Eliminar (desactivar) todos los balances iniciales de un período
    """
    try:
        balances = db.query(BalanceInicial).filter(
            BalanceInicial.id_periodo == periodo_id,
            BalanceInicial.estado_balance == 'ACTIVO'
        ).all()
        
        cantidad_eliminados = len(balances)
        
        for balance in balances:
            balance.estado_balance = 'INACTIVO'
            balance.fecha_modificacion = date.today()
            balance.usuario_modificacion = usuario
        
        db.commit()
        return cantidad_eliminados
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error al eliminar balances del período: {str(e)}"
        )


def generar_balances_desde_periodo_anterior(
    db: Session, 
    periodo_actual_id: int, 
    periodo_anterior_id: int, 
    usuario: str
) -> List[BalanceInicial]:
    """
    Generar balances iniciales del período actual basado en los saldos finales del período anterior
    """
    # Validar períodos
    periodo_actual = db.query(PeriodoContable).filter(
        PeriodoContable.id_periodo == periodo_actual_id
    ).first()
    periodo_anterior = db.query(PeriodoContable).filter(
        PeriodoContable.id_periodo == periodo_anterior_id
    ).first()
    
    if not periodo_actual or not periodo_anterior:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Uno o ambos períodos no encontrados"
        )
    
    # Verificar que no existan balances iniciales en el período actual
    balances_existentes = db.query(BalanceInicial).filter(
        BalanceInicial.id_periodo == periodo_actual_id,
        BalanceInicial.estado_balance == 'ACTIVO'
    ).count()
    
    if balances_existentes > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existen balances iniciales para el período actual"
        )
    
    # Calcular saldos finales del período anterior
    # Esto requeriría una consulta compleja que sume movimientos + balance inicial
    # Por simplicidad, implementamos una versión básica
    
    balances_anteriores = db.query(BalanceInicial).filter(
        BalanceInicial.id_periodo == periodo_anterior_id,
        BalanceInicial.estado_balance == 'ACTIVO'
    ).all()
    
    nuevos_balances = []
    
    try:
        for balance_anterior in balances_anteriores:
            # Para cuentas de balance (Activo, Pasivo, Capital) trasladar el saldo
            cuenta = db.query(CatalogoCuentas).filter(
                CatalogoCuentas.id_cuenta == balance_anterior.id_cuenta
            ).first()
            
            if cuenta.tipo_cuenta in ['Activo', 'Pasivo', 'Capital']:
                nuevo_balance = BalanceInicial(
                    id_cuenta=balance_anterior.id_cuenta,
                    id_periodo=periodo_actual_id,
                    saldo_inicial=balance_anterior.saldo_inicial,  # Simplificado
                    naturaleza_saldo=balance_anterior.naturaleza_saldo,
                    observaciones=f"Generado automáticamente desde período {periodo_anterior.descripcion}",
                    fecha_registro=date.today(),
                    usuario_creacion=usuario,
                    estado_balance='ACTIVO'
                )
                db.add(nuevo_balance)
                nuevos_balances.append(nuevo_balance)
        
        db.commit()
        
        # Refresh all objects
        for balance in nuevos_balances:
            db.refresh(balance)
        
        return nuevos_balances
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error al generar balances iniciales: {str(e)}"
        )

def obtener_resumen_balances_periodo(db: Session, periodo_id: int) -> Dict:
    """
    Obtener resumen de balances iniciales por tipo de cuenta
    """
    resumen = db.query(
        CatalogoCuentas.tipo_cuenta,
        func.count(BalanceInicial.id_balance_inicial).label('cantidad_cuentas'),
        func.sum(BalanceInicial.saldo_inicial).label('total_saldo')
    ).join(
        BalanceInicial, CatalogoCuentas.id_cuenta == BalanceInicial.id_cuenta
    ).filter(
        BalanceInicial.id_periodo == periodo_id,
        BalanceInicial.estado_balance == 'ACTIVO'
    ).group_by(CatalogoCuentas.tipo_cuenta).all()
    
    resultado = {
        "periodo_id": periodo_id,
        "resumen_por_tipo": {},
        "total_general": {
            "cantidad_cuentas": 0,
            "suma_debe": Decimal("0.00"),  # Activos y Egresos
            "suma_haber": Decimal("0.00")  # Pasivos, Capital e Ingresos
        }
    }
    
    for item in resumen:
        tipo_cuenta = item.tipo_cuenta
        cantidad = item.cantidad_cuentas
        total = item.total_saldo or Decimal("0.00")
        
        resultado["resumen_por_tipo"][tipo_cuenta] = {
            "cantidad_cuentas": cantidad,
            "total_saldo": float(total)
        }
        
        resultado["total_general"]["cantidad_cuentas"] += cantidad
        
        # Clasificar en debe o haber según naturaleza
        if tipo_cuenta in ['Activo', 'Egreso']:
            resultado["total_general"]["suma_debe"] += total
        else:  # Pasivo, Capital, Ingreso
            resultado["total_general"]["suma_haber"] += total
    
    # Convertir Decimals a float
    resultado["total_general"]["suma_debe"] = float(resultado["total_general"]["suma_debe"])
    resultado["total_general"]["suma_haber"] = float(resultado["total_general"]["suma_haber"])
    resultado["total_general"]["diferencia"] = (
        resultado["total_general"]["suma_debe"] - resultado["total_general"]["suma_haber"]
    )
    
    return resultado