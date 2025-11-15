"""
Rutas FastAPI para Manual de Cuentas.
Endpoints para gestión de manuales contables.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db import get_db
from app.schemas.manual_cuentas import (
    ManualCuentasCreate, ManualCuentasUpdate, ManualCuentasRead
)
from app.services.manual_cuentas_service import (
    create_manual_cuenta, get_manual_cuenta, get_manuales_cuentas,
    update_manual_cuenta, delete_manual_cuenta, get_manual_por_cuenta
)

router = APIRouter(
    prefix="/api/manual-cuentas",
    tags=["Manual de Cuentas"]
)

@router.post("/", response_model=ManualCuentasRead)
def crear_manual(
    manual: ManualCuentasCreate,
    db: Session = Depends(get_db)
):
    """Crear un nuevo manual de cuenta"""
    return create_manual_cuenta(db, manual)

@router.get("/", response_model=List[ManualCuentasRead])
def listar_manuales(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    id_cuenta: Optional[int] = Query(None),
    id_periodo: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """Listar manuales de cuentas con paginación"""
    if id_cuenta:
        return get_manual_por_cuenta(db, id_cuenta)
    return get_manuales_cuentas(db, skip, limit)

@router.get("/{manual_id}", response_model=ManualCuentasRead)
def obtener_manual(
    manual_id: int,
    db: Session = Depends(get_db)
):
    """Obtener manual específico por ID"""
    return get_manual_cuenta(db, manual_id)

@router.put("/{manual_id}", response_model=ManualCuentasRead)
def actualizar_manual(
    manual_id: int,
    manual_update: ManualCuentasUpdate,
    db: Session = Depends(get_db)
):
    """Actualizar manual existente"""
    return update_manual_cuenta(db, manual_id, manual_update)

@router.delete("/{manual_id}")
def eliminar_manual(
    manual_id: int,
    db: Session = Depends(get_db)
):
    """Eliminar manual de cuenta"""
    delete_manual_cuenta(db, manual_id)
    return {"message": "Manual eliminado exitosamente"}