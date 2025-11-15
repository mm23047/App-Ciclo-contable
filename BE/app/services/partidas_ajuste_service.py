"""
Capa de servicios para operaciones de Partidas de Ajuste.
Maneja la lógica de negocio para crear y gestionar ajustes contables.
"""
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from app.models.partidas_ajuste import PartidaAjuste, AsientoAjuste
from app.models.catalogo_cuentas import CatalogoCuentas
from app.models.periodo import PeriodoContable
from app.schemas.partidas_ajuste import PartidaAjusteCreate, PartidaAjusteUpdate
from typing import List, Optional
from decimal import Decimal
from datetime import datetime

def validate_partida_ajuste_balance(asientos_ajuste: List[dict]) -> bool:
    """Validar que la partida de ajuste esté balanceada"""
    total_debe = sum(Decimal(str(asiento.get('debe', 0))) for asiento in asientos_ajuste)
    total_haber = sum(Decimal(str(asiento.get('haber', 0))) for asiento in asientos_ajuste)
    
    return abs(total_debe - total_haber) < Decimal("0.01")

def generate_numero_partida(db: Session) -> str:
    """Generar número automático para la partida de ajuste"""
    # Obtener el último número de partida
    last_partida = db.query(PartidaAjuste).order_by(PartidaAjuste.id_partida_ajuste.desc()).first()
    
    if last_partida and last_partida.numero_partida:
        try:
            # Extraer número de la partida (formato PAJ-XXXX)
            last_number = int(last_partida.numero_partida.split('-')[-1])
            new_number = last_number + 1
        except (ValueError, IndexError):
            new_number = 1
    else:
        new_number = 1
    
    return f"PAJ-{new_number:04d}"

def create_partida_ajuste(db: Session, partida_data: PartidaAjusteCreate) -> PartidaAjuste:
    """Crear una nueva partida de ajuste con sus asientos"""
    # Validar que el período existe
    periodo = db.query(PeriodoContable).filter(
        PeriodoContable.id_periodo == partida_data.id_periodo
    ).first()
    if not periodo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Período contable no encontrado"
        )
    
    # Validar que el período esté abierto
    if periodo.estado != 'ABIERTO':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se pueden crear ajustes en períodos cerrados"
        )
    
    # Validar balance de los asientos
    if not validate_partida_ajuste_balance([asiento.dict() for asiento in partida_data.asientos_ajuste]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La partida de ajuste no está balanceada. Total débitos debe igual total créditos"
        )
    
    # Validar que todas las cuentas existen
    for asiento_data in partida_data.asientos_ajuste:
        cuenta = db.query(CatalogoCuentas).filter(
            CatalogoCuentas.id_cuenta == asiento_data.id_cuenta
        ).first()
        if not cuenta:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cuenta con ID {asiento_data.id_cuenta} no encontrada"
            )
    
    # Generar número automático si no se proporciona
    if not partida_data.numero_partida.strip():
        numero_partida = generate_numero_partida(db)
    else:
        numero_partida = partida_data.numero_partida
    
    try:
        # Crear la partida de ajuste
        partida_dict = partida_data.dict(exclude={'asientos_ajuste'})
        partida_dict['numero_partida'] = numero_partida
        
        db_partida = PartidaAjuste(**partida_dict)
        db.add(db_partida)
        db.flush()  # Para obtener el ID sin hacer commit
        
        # Crear los asientos de ajuste
        for asiento_data in partida_data.asientos_ajuste:
            asiento_ajuste = AsientoAjuste(
                id_partida_ajuste=db_partida.id_partida_ajuste,
                **asiento_data.dict()
            )
            db.add(asiento_ajuste)
        
        db.commit()
        db.refresh(db_partida)
        return db_partida
        
    except IntegrityError as e:
        db.rollback()
        if "numero_partida" in str(e):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El número de partida ya existe"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Error al crear partida de ajuste"
            )

def get_partida_ajuste(db: Session, partida_id: int) -> Optional[PartidaAjuste]:
    """Obtener una partida de ajuste específica por ID"""
    partida = db.query(PartidaAjuste).filter(PartidaAjuste.id_partida_ajuste == partida_id).first()
    if not partida:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Partida de ajuste no encontrada"
        )
    return partida

def get_partidas_ajuste(
    db: Session,
    periodo_id: Optional[int] = None,
    tipo_ajuste: Optional[str] = None,
    estado: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
) -> List[PartidaAjuste]:
    """Obtener partidas de ajuste con filtros opcionales"""
    query = db.query(PartidaAjuste)
    
    if periodo_id:
        query = query.filter(PartidaAjuste.id_periodo == periodo_id)
    if tipo_ajuste:
        query = query.filter(PartidaAjuste.tipo_ajuste == tipo_ajuste)
    if estado:
        query = query.filter(PartidaAjuste.estado == estado)
    
    return query.order_by(PartidaAjuste.fecha_ajuste.desc()).offset(skip).limit(limit).all()

def update_partida_ajuste(db: Session, partida_id: int, partida_data: PartidaAjusteUpdate) -> PartidaAjuste:
    """Actualizar una partida de ajuste existente"""
    partida = get_partida_ajuste(db, partida_id)
    
    # Validar que no esté anulada
    if partida.estado == 'ANULADO':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se puede modificar una partida de ajuste anulada"
        )
    
    update_data = partida_data.dict(exclude_unset=True)
    
    try:
        for key, value in update_data.items():
            setattr(partida, key, value)
        db.commit()
        db.refresh(partida)
        return partida
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error al actualizar partida de ajuste"
        )

def anular_partida_ajuste(db: Session, partida_id: int, usuario_anulacion: str) -> PartidaAjuste:
    """Anular una partida de ajuste"""
    partida = get_partida_ajuste(db, partida_id)
    
    if partida.estado == 'ANULADO':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La partida de ajuste ya está anulada"
        )
    
    try:
        partida.estado = 'ANULADO'
        partida.usuario_aprobacion = usuario_anulacion
        partida.fecha_aprobacion = datetime.now()
        db.commit()
        db.refresh(partida)
        return partida
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error al anular partida de ajuste: {str(e)}"
        )

def aprobar_partida_ajuste(db: Session, partida_id: int, usuario_aprobacion: str) -> PartidaAjuste:
    """Aprobar una partida de ajuste"""
    partida = get_partida_ajuste(db, partida_id)
    
    if partida.estado == 'ANULADO':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se puede aprobar una partida anulada"
        )
    
    try:
        partida.usuario_aprobacion = usuario_aprobacion
        partida.fecha_aprobacion = datetime.now()
        db.commit()
        db.refresh(partida)
        return partida
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error al aprobar partida de ajuste: {str(e)}"
        )