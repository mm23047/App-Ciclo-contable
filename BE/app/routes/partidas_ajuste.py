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
    create_partida_ajuste, get_partida_ajuste, get_partidas_ajuste,
    update_partida_ajuste, aprobar_partida_ajuste, anular_partida_ajuste
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
    return create_partida_ajuste(db, partida)

@router.get("/periodo/{periodo_id}", response_model=List[PartidaAjusteRead])
def listar_partidas_periodo(
    periodo_id: int,
    estado: Optional[str] = Query(None),
    tipo_ajuste: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Listar partidas de ajuste por período"""
    return get_partidas_ajuste(db, periodo_id=periodo_id, estado=estado)

@router.get("/{partida_id}", response_model=PartidaAjusteRead)
def obtener_partida(
    partida_id: int,
    db: Session = Depends(get_db)
):
    """Obtener partida específica por ID"""
    return get_partida_ajuste(db, partida_id)

@router.put("/{partida_id}", response_model=PartidaAjusteRead)
def actualizar_partida(
    partida_id: int,
    partida_update: PartidaAjusteUpdate,
    db: Session = Depends(get_db)
):
    """Actualizar partida de ajuste"""
    return update_partida_ajuste(db, partida_id, partida_update)

@router.post("/{partida_id}/aprobar")
def aprobar_partida(
    partida_id: int,
    db: Session = Depends(get_db)
):
    """Aprobar partida de ajuste"""
    partida = aprobar_partida_ajuste(db, partida_id, "API_USER")
    return {"message": "Partida de ajuste aprobada exitosamente"}

@router.post("/{partida_id}/anular")
def anular_partida(
    partida_id: int,
    db: Session = Depends(get_db)
):
    """Anular partida de ajuste"""
    partida = anular_partida_ajuste(db, partida_id, "API_USER")
    return {"message": "Partida de ajuste anulada"}