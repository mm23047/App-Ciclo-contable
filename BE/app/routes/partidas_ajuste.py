"""
Rutas FastAPI para Partidas de Ajuste.
Endpoints para gestión de partidas de ajuste contable.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db import get_db
from app.schemas.partidas_ajuste import (
    PartidaAjusteCreate, PartidaAjusteUpdate, PartidaAjusteRead
)
from app.services.partidas_ajuste_service import (
    crear_partida_ajuste, obtener_partida_por_id, obtener_partidas_por_periodo,
    actualizar_partida_ajuste, aprobar_partida_ajuste, rechazar_partida_ajuste,
    aplicar_partida_ajuste, obtener_partidas_por_estado
)

router = APIRouter(
    prefix="/api/partidas-ajuste",
    tags=["Partidas de Ajuste"]
)

@router.post("/", response_model=PartidaAjusteRead)
def crear_partida(
    partida: PartidaAjusteCreate,
    db: Session = Depends(get_db)
):
    """Crear una nueva partida de ajuste"""
    return crear_partida_ajuste(db, partida, "API_USER")

@router.get("/periodo/{periodo_id}", response_model=List[PartidaAjusteRead])
def listar_partidas_periodo(
    periodo_id: int,
    estado: Optional[str] = Query(None),
    tipo_ajuste: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Listar partidas de ajuste por período"""
    if estado:
        return obtener_partidas_por_estado(db, periodo_id, estado)
    return obtener_partidas_por_periodo(db, periodo_id)

@router.get("/{partida_id}", response_model=PartidaAjusteRead)
def obtener_partida(
    partida_id: int,
    db: Session = Depends(get_db)
):
    """Obtener partida específica por ID"""
    return obtener_partida_por_id(db, partida_id)

@router.put("/{partida_id}", response_model=PartidaAjusteRead)
def actualizar_partida(
    partida_id: int,
    partida_update: PartidaAjusteUpdate,
    db: Session = Depends(get_db)
):
    """Actualizar partida de ajuste"""
    return actualizar_partida_ajuste(db, partida_id, partida_update, "API_USER")

@router.post("/{partida_id}/aprobar")
def aprobar_partida(
    partida_id: int,
    observaciones_aprobacion: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Aprobar partida de ajuste"""
    aprobar_partida_ajuste(db, partida_id, observaciones_aprobacion, "API_USER")
    return {"message": "Partida de ajuste aprobada exitosamente"}

@router.post("/{partida_id}/rechazar")
def rechazar_partida(
    partida_id: int,
    observaciones_rechazo: str,
    db: Session = Depends(get_db)
):
    """Rechazar partida de ajuste"""
    rechazar_partida_ajuste(db, partida_id, observaciones_rechazo, "API_USER")
    return {"message": "Partida de ajuste rechazada"}

@router.post("/{partida_id}/aplicar")
def aplicar_partida(
    partida_id: int,
    db: Session = Depends(get_db)
):
    """Aplicar partida de ajuste (generar asientos)"""
    aplicar_partida_ajuste(db, partida_id, "API_USER")
    return {"message": "Partida de ajuste aplicada exitosamente"}