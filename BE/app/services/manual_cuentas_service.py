"""
Capa de servicios para operaciones del Manual de Cuentas.
Maneja la lógica de negocio y operaciones de base de datos para el manual de cuentas.
"""
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from app.models.manual_cuentas import ManualCuentas
from app.models.catalogo_cuentas import CatalogoCuentas
from app.schemas.manual_cuentas import ManualCuentasCreate, ManualCuentasUpdate
from typing import List, Optional

def create_manual_cuenta(db: Session, manual_data: ManualCuentasCreate) -> ManualCuentas:
    """Crear un nuevo manual de cuenta"""
    from sqlalchemy.orm import joinedload
    
    # Validar que la cuenta existe
    cuenta = db.query(CatalogoCuentas).filter(
        CatalogoCuentas.id_cuenta == manual_data.id_cuenta
    ).first()
    if not cuenta:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La cuenta especificada no existe"
        )
    
    # Validar que no existe ya un manual para esta cuenta
    existing_manual = db.query(ManualCuentas).filter(
        ManualCuentas.id_cuenta == manual_data.id_cuenta
    ).first()
    if existing_manual:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe un manual para esta cuenta"
        )
    
    try:
        db_manual = ManualCuentas(**manual_data.dict())
        db.add(db_manual)
        db.commit()
        db.refresh(db_manual)
        
        # Recargar con la relación
        db_manual = db.query(ManualCuentas).options(
            joinedload(ManualCuentas.cuenta)
        ).filter(ManualCuentas.id_manual == db_manual.id_manual).first()
        
        return db_manual
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error al crear manual de cuenta"
        )

def get_manual_cuenta(db: Session, manual_id: int) -> Optional[ManualCuentas]:
    """Obtener un manual de cuenta específico por ID"""
    from sqlalchemy.orm import joinedload
    
    manual = db.query(ManualCuentas).options(
        joinedload(ManualCuentas.cuenta)
    ).filter(ManualCuentas.id_manual == manual_id).first()
    if not manual:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Manual de cuenta no encontrado"
        )
    return manual

def get_manual_por_cuenta(db: Session, cuenta_id: int) -> Optional[ManualCuentas]:
    """Obtener manual por ID de cuenta"""
    from sqlalchemy.orm import joinedload
    
    return db.query(ManualCuentas).options(
        joinedload(ManualCuentas.cuenta)
    ).filter(ManualCuentas.id_cuenta == cuenta_id).first()

def get_manuales_cuentas(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    texto_busqueda: Optional[str] = None,
    naturaleza_cuenta: Optional[str] = None,
    clasificacion: Optional[str] = None,
    solo_con_ejemplos: Optional[bool] = None
) -> List[ManualCuentas]:
    """Obtener todos los manuales con paginación y filtros"""
    from sqlalchemy.orm import joinedload
    
    query = db.query(ManualCuentas).options(joinedload(ManualCuentas.cuenta))
    
    # Aplicar filtros
    if texto_busqueda:
        # Búsqueda en múltiples campos de texto
        search_pattern = f"%{texto_busqueda}%"
        query = query.filter(
            (ManualCuentas.descripcion_detallada.ilike(search_pattern)) |
            (ManualCuentas.instrucciones_uso.ilike(search_pattern)) |
            (ManualCuentas.ejemplos_movimientos.ilike(search_pattern)) |
            (ManualCuentas.normativa_aplicable.ilike(search_pattern)) |
            (ManualCuentas.cuentas_relacionadas.ilike(search_pattern))
        )
    
    if naturaleza_cuenta:
        query = query.filter(ManualCuentas.naturaleza_cuenta == naturaleza_cuenta)
    
    if clasificacion:
        query = query.filter(ManualCuentas.clasificacion.ilike(f"%{clasificacion}%"))
    
    if solo_con_ejemplos:
        query = query.filter(ManualCuentas.ejemplos_movimientos.isnot(None))
        query = query.filter(ManualCuentas.ejemplos_movimientos != '')
    
    # Ordenar por ID de cuenta para mantener consistencia
    query = query.order_by(ManualCuentas.id_cuenta)
    
    return query.offset(skip).limit(limit).all()

def update_manual_cuenta(db: Session, manual_id: int, manual_data: ManualCuentasUpdate) -> ManualCuentas:
    """Actualizar un manual de cuenta existente"""
    manual = get_manual_cuenta(db, manual_id)
    update_data = manual_data.dict(exclude_unset=True)
    
    try:
        for key, value in update_data.items():
            setattr(manual, key, value)
        db.commit()
        db.refresh(manual)
        return manual
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error al actualizar manual de cuenta"
        )

def delete_manual_cuenta(db: Session, manual_id: int) -> bool:
    """Eliminar un manual de cuenta"""
    manual = get_manual_cuenta(db, manual_id)
    db.delete(manual)
    db.commit()
    return True