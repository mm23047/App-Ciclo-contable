"""
Rutas FastAPI para Estados Financieros.
Endpoints para generación de Balance General y Estado de P&G.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any
from app.db import get_db
from app.models.estados_financieros import EstadosFinancierosHistorico
from app.services.estados_financieros_service import (
    generar_balance_general, generar_estado_perdidas_ganancias, guardar_estado_financiero
)

router = APIRouter(
    prefix="/api/estados-financieros",
    tags=["Estados Financieros"]
)

@router.get("/balance-general/{periodo_id}")
def obtener_balance_general(
    periodo_id: int,
    guardar: bool = False,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Generar Balance General para un período"""
    balance = generar_balance_general(db, periodo_id)
    
    if guardar:
        guardar_estado_financiero(
            db, "BALANCE_GENERAL", balance, "API_USER"
        )
    
    return balance

@router.get("/estado-pyg/{periodo_id}")
def obtener_estado_perdidas_ganancias(
    periodo_id: int,
    guardar: bool = False,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Generar Estado de Pérdidas y Ganancias"""
    estado_py = generar_estado_perdidas_ganancias(db, periodo_id)
    
    if guardar:
        guardar_estado_financiero(
            db, "ESTADO_PERDIDAS_GANANCIAS", estado_py, "API_USER"
        )
    
    return estado_py

@router.post("/guardar")
def guardar_estado(
    tipo_estado: str,
    periodo_id: int,
    db: Session = Depends(get_db)
):
    """Guardar estado financiero en el histórico"""
    if tipo_estado == "BALANCE_GENERAL":
        contenido = generar_balance_general(db, periodo_id)
    elif tipo_estado == "ESTADO_PERDIDAS_GANANCIAS":
        contenido = generar_estado_perdidas_ganancias(db, periodo_id)
    else:
        raise HTTPException(
            status_code=400,
            detail="Tipo de estado no válido. Use: BALANCE_GENERAL o ESTADO_PERDIDAS_GANANCIAS"
        )
    
    estado_guardado = guardar_estado_financiero(db, tipo_estado, contenido, "API_USER")
    
    return {
        "message": "Estado financiero guardado exitosamente",
        "id_estado": estado_guardado.id_estado,
        "tipo_estado": estado_guardado.tipo_estado,
        "fecha_generacion": estado_guardado.fecha_generacion
    }

@router.get("/historico/{periodo_id}")
def obtener_historico_periodo(
    periodo_id: int,
    tipo_estado: str = None,
    db: Session = Depends(get_db)
):
    """Obtener histórico de estados financieros de un período"""
    query = db.query(EstadosFinancierosHistorico).filter(
        EstadosFinancierosHistorico.id_periodo == periodo_id
    )
    
    if tipo_estado:
        query = query.filter(EstadosFinancierosHistorico.tipo_estado == tipo_estado)
    
    estados = query.order_by(EstadosFinancierosHistorico.fecha_generacion.desc()).all()
    
    return [
        {
            "id_estado": estado.id_estado,
            "tipo_estado": estado.tipo_estado,
            "fecha_generacion": estado.fecha_generacion,
            "total_activos": estado.total_activos,
            "total_pasivos": estado.total_pasivos,
            "patrimonio": estado.patrimonio,
            "utilidad_perdida": estado.utilidad_perdida,
            "usuario_generacion": estado.usuario_generacion
        }
        for estado in estados
    ]