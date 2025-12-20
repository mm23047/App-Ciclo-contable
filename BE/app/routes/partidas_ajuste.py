"""
Rutas FastAPI para Partidas de Ajuste.
Endpoints para gestión de partidas de ajuste contable.
"""
from fastapi import APIRouter, Depends, Query, Body
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

@router.get("/", response_model=List[PartidaAjusteRead])
def listar_todas_partidas(
    estado: Optional[str] = Query(None),
    tipo_ajuste: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Listar todas las partidas de ajuste (sin filtro de período)"""
    return get_partidas_ajuste(db, periodo_id=None, estado=estado, tipo_ajuste=tipo_ajuste)

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

@router.post("/{partida_id}/aprobar", response_model=PartidaAjusteRead)
def aprobar_partida(
    partida_id: int,
    usuario_aprobacion: str = Body(..., embed=True),
    db: Session = Depends(get_db)
):
    """Aprobar partida de ajuste"""
    return aprobar_partida_ajuste(db, partida_id, usuario_aprobacion)

@router.post("/{partida_id}/anular", response_model=PartidaAjusteRead)
def anular_partida(
    partida_id: int,
    usuario_anulacion: str = Body(..., embed=True),
    db: Session = Depends(get_db)
):
    """Anular partida de ajuste"""
    return anular_partida_ajuste(db, partida_id, usuario_anulacion)