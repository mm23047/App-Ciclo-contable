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
        return db_manual
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error al crear manual de cuenta"
        )

def get_manual_cuenta(db: Session, manual_id: int) -> Optional[ManualCuentas]:
    """Obtener un manual de cuenta específico por ID"""
    manual = db.query(ManualCuentas).filter(ManualCuentas.id_manual == manual_id).first()
    if not manual:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Manual de cuenta no encontrado"
        )
    return manual

def get_manual_por_cuenta(db: Session, cuenta_id: int) -> Optional[ManualCuentas]:
    """Obtener manual por ID de cuenta"""
    return db.query(ManualCuentas).filter(ManualCuentas.id_cuenta == cuenta_id).first()

def get_manuales_cuentas(db: Session, skip: int = 0, limit: int = 100) -> List[ManualCuentas]:
    """Obtener todos los manuales con paginación"""
    return db.query(ManualCuentas).offset(skip).limit(limit).all()

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