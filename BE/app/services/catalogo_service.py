"""
Capa de servicios para operaciones del Catálogo de Cuentas.
Maneja la lógica de negocio y operaciones de base de datos para cuentas.
"""
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from app.models.catalogo_cuentas import CatalogoCuentas
from app.schemas.catalogo_cuentas import CatalogoCuentaCreate, CatalogoCuentaUpdate
from typing import List, Optional

def create_cuenta(db: Session, cuenta_data: CatalogoCuentaCreate) -> CatalogoCuentas:
    """Crear una nueva cuenta en el catálogo de cuentas"""
    try:
        # Calcular el nivel automáticamente basado en la cuenta padre
        nivel_cuenta = 1  # Nivel por defecto para cuentas raíz
        
        if cuenta_data.cuenta_padre:
            cuenta_padre = db.query(CatalogoCuentas).filter(
                CatalogoCuentas.id_cuenta == cuenta_data.cuenta_padre
            ).first()
            
            if cuenta_padre:
                nivel_cuenta = cuenta_padre.nivel_cuenta + 1
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="La cuenta padre especificada no existe"
                )
        
        # Crear el diccionario de datos y actualizar el nivel
        cuenta_dict = cuenta_data.dict()
        cuenta_dict['nivel_cuenta'] = nivel_cuenta
        
        db_cuenta = CatalogoCuentas(**cuenta_dict)
        db.add(db_cuenta)
        db.commit()
        db.refresh(db_cuenta)
        return db_cuenta
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El código de cuenta ya existe"
        )

def get_cuenta(db: Session, cuenta_id: int) -> Optional[CatalogoCuentas]:
    """Obtener una cuenta específica por ID"""
    cuenta = db.query(CatalogoCuentas).filter(CatalogoCuentas.id_cuenta == cuenta_id).first()
    if not cuenta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cuenta no encontrada"
        )
    return cuenta

def get_cuentas(db: Session, skip: int = 0, limit: int = 100) -> List[CatalogoCuentas]:
    """Obtener todas las cuentas con paginación"""
    return db.query(CatalogoCuentas).offset(skip).limit(limit).all()

def update_cuenta(db: Session, cuenta_id: int, cuenta_data: CatalogoCuentaUpdate) -> CatalogoCuentas:
    """Actualizar una cuenta existente"""
    cuenta = get_cuenta(db, cuenta_id)
    update_data = cuenta_data.dict(exclude_unset=True)
    
    try:
        for key, value in update_data.items():
            setattr(cuenta, key, value)
        db.commit()
        db.refresh(cuenta)
        return cuenta
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El código de cuenta ya existe"
        )

def delete_cuenta(db: Session, cuenta_id: int) -> bool:
    """Eliminar una cuenta"""
    cuenta = get_cuenta(db, cuenta_id)
    
    # TODO: Verificar si la cuenta se usa en asientos antes de eliminar
    # Por ahora, permitimos la eliminación
    
    db.delete(cuenta)
    db.commit()
    return True