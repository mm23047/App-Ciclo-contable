"""
Rutas FastAPI para Balanza de Comprobación.
Endpoints para generación y consulta de balanzas de comprobación.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
from app.db import get_db
from app.models.balanza_comprobacion import BalanzaComprobacion
from app.services.balanza_service import (
    generar_balanza_comprobacion, obtener_balanzas_periodo, obtener_balanza_por_id,
    validar_cuadre_periodo, obtener_analisis_cuentas_periodo
)

router = APIRouter(
    prefix="/api/balanza-comprobacion",
    tags=["Balanza de Comprobación"]
)

@router.post("/generar/{periodo_id}", response_model=dict)
def generar_balanza(
    periodo_id: int,
    fecha_hasta: Optional[date] = Query(None),
    db: Session = Depends(get_db)
):
    """Generar una nueva balanza de comprobación"""
    balanza = generar_balanza_comprobacion(db, periodo_id, fecha_hasta, "API_USER")
    return {
        "id_balanza": balanza.id_balanza,
        "estado_balanza": balanza.estado_balanza,
        "total_debe": balanza.total_debe,
        "total_haber": balanza.total_haber,
        "diferencia_saldos": balanza.diferencia_saldos,
        "message": "Balanza de comprobación generada exitosamente"
    }

@router.get("/periodo/{periodo_id}", response_model=List[BalanzaComprobacion])
def listar_balanzas_periodo(
    periodo_id: int,
    db: Session = Depends(get_db)
):
    """Obtener todas las balanzas de un período"""
    return obtener_balanzas_periodo(db, periodo_id)

@router.get("/{balanza_id}", response_model=BalanzaComprobacion)
def obtener_balanza(
    balanza_id: int,
    db: Session = Depends(get_db)
):
    """Obtener balanza específica por ID"""
    return obtener_balanza_por_id(db, balanza_id)

@router.get("/validar-cuadre/{periodo_id}")
def validar_cuadre(
    periodo_id: int,
    fecha_hasta: Optional[date] = Query(None),
    db: Session = Depends(get_db)
):
    """Validar cuadre contable de un período"""
    return validar_cuadre_periodo(db, periodo_id, fecha_hasta)

@router.get("/analisis/{periodo_id}")
def analisis_cuentas(
    periodo_id: int,
    tipo_cuenta: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Obtener análisis detallado de cuentas por período"""
    return obtener_analisis_cuentas_periodo(db, periodo_id, tipo_cuenta)