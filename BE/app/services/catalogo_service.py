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

def get_cuentas(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    tipo_cuenta: Optional[str] = None,
    estado: Optional[str] = None,
    codigo_like: Optional[str] = None,
    acepta_movimientos: Optional[bool] = None,
    nivel: Optional[int] = None
) -> List[CatalogoCuentas]:
    """
    Obtener todas las cuentas con filtros opcionales y paginación.
    
    Args:
        db: Sesión de base de datos
        skip: Número de registros a saltar (paginación)
        limit: Número máximo de registros a retornar
        tipo_cuenta: Filtrar por tipo de cuenta (Activo, Pasivo, etc.)
        estado: Filtrar por estado (ACTIVA, INACTIVA)
        codigo_like: Buscar por código O nombre de cuenta (búsqueda parcial)
        acepta_movimientos: Filtrar por si acepta movimientos
        nivel: Filtrar por nivel de cuenta en la jerarquía
        
    Returns:
        Lista de cuentas que cumplen con los filtros
    """
    query = db.query(CatalogoCuentas)
    
    # Aplicar filtros si están presentes
    if tipo_cuenta:
        query = query.filter(CatalogoCuentas.tipo_cuenta == tipo_cuenta)
    
    if estado:
        query = query.filter(CatalogoCuentas.estado == estado)
    
    if codigo_like:
        # Buscar tanto en código como en nombre de cuenta
        search_pattern = f"%{codigo_like}%"
        query = query.filter(
            (CatalogoCuentas.codigo_cuenta.like(search_pattern)) |
            (CatalogoCuentas.nombre_cuenta.ilike(search_pattern))
        )
    
    if acepta_movimientos is not None:
        query = query.filter(CatalogoCuentas.acepta_movimientos == acepta_movimientos)
    
    if nivel is not None:
        query = query.filter(CatalogoCuentas.nivel_cuenta == nivel)
    
    # Ordenar por código de cuenta para mantener jerarquía visual
    query = query.order_by(CatalogoCuentas.codigo_cuenta)
    
    # Aplicar paginación
    return query.offset(skip).limit(limit).all()

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