"""
Rutas FastAPI para Balance Inicial.
Endpoints para gestión de balances iniciales por período.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db import get_db
from app.schemas.balance_inicial import (
    BalanceInicialCreate, BalanceInicialUpdate, BalanceInicialResponse,
    ResumenBalancesPeriodo, GenerarBalanceRequest
)
from app.services.balance_inicial_service import (
    crear_balance_inicial, obtener_balances_por_periodo, actualizar_balance_inicial,
    eliminar_balance_inicial, generar_balances_desde_periodo_anterior,
    obtener_resumen_balances_periodo
)

router = APIRouter(
    prefix="/api/balance-inicial",
    tags=["Balance Inicial"]
)

@router.post("/", response_model=BalanceInicialResponse, status_code=status.HTTP_201_CREATED)
def crear_balance(
    balance: BalanceInicialCreate,
    db: Session = Depends(get_db)
):
    """Crear un nuevo balance inicial"""
    return crear_balance_inicial(db, balance, "API_USER")

@router.get("/periodo/{periodo_id}", response_model=List[dict])
def listar_balances_periodo(
    periodo_id: int,
    db: Session = Depends(get_db)
):
    """Obtener todos los balances iniciales de un período"""
    return obtener_balances_por_periodo(db, periodo_id)

@router.put("/{balance_id}", response_model=BalanceInicialResponse)
def actualizar_balance(
    balance_id: int,
    balance_update: BalanceInicialUpdate,
    db: Session = Depends(get_db)
):
    """Actualizar balance inicial existente"""
    return actualizar_balance_inicial(db, balance_id, balance_update, "API_USER")

@router.delete("/{balance_id}")
def eliminar_balance(
    balance_id: int,
    db: Session = Depends(get_db)
):
    """Eliminar (desactivar) balance inicial"""
    eliminar_balance_inicial(db, balance_id, "API_USER")
    return {"message": "Balance inicial eliminado exitosamente"}

@router.delete("/periodo/{periodo_id}")
def eliminar_balances_periodo(
    periodo_id: int,
    db: Session = Depends(get_db)
):
    """Eliminar todos los balances iniciales de un período"""
    from app.services.balance_inicial_service import eliminar_balances_periodo
    cantidad_eliminados = eliminar_balances_periodo(db, periodo_id, "API_USER")
    return {
        "message": "Balances iniciales eliminados exitosamente",
        "cantidad_eliminados": cantidad_eliminados
    }

@router.post("/generar-desde-anterior")
def generar_balances_automaticos(
    request: GenerarBalanceRequest,
    db: Session = Depends(get_db)
):
    """Generar balances iniciales desde período anterior"""
    balances = generar_balances_desde_periodo_anterior(
        db, request.periodo_actual_id, request.periodo_anterior_id, "API_USER"
    )
    return {
        "message": "Balances iniciales generados exitosamente",
        "cantidad_balances": len(balances)
    }

@router.get("/resumen/{periodo_id}", response_model=ResumenBalancesPeriodo)
def obtener_resumen_periodo(
    periodo_id: int,
    db: Session = Depends(get_db)
):
    """Obtener resumen de balances iniciales por período"""
    return obtener_resumen_balances_periodo(db, periodo_id)