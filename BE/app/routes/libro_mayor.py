"""
Rutas FastAPI para Libro Mayor.
Endpoints para consultar movimientos mayorizados por cuenta.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db import get_db
from app.services.mayorizacion_service import (
    generar_libro_mayor_cuenta,
    generar_libro_mayor_completo
)

router = APIRouter(
    prefix="/api/libro-mayor",
    tags=["Libro Mayor"]
)

@router.get("/cuenta/{cuenta_id}/periodo/{periodo_id}")
def obtener_libro_mayor_cuenta(
    cuenta_id: int,
    periodo_id: int,
    db: Session = Depends(get_db)
):
    """Obtener libro mayor para una cuenta específica en un período"""
    try:
        movimientos = generar_libro_mayor_cuenta(
            db=db,
            cuenta_id=cuenta_id,
            periodo_id=periodo_id
        )
        
        if not movimientos:
            return {
                "id_cuenta": cuenta_id,
                "codigo_cuenta": "N/A",
                "nombre_cuenta": "N/A",
                "tipo_cuenta": "N/A",
                "saldo_inicial": 0.00,
                "saldo_final": 0.00,
                "movimientos": []
            }
        
        # Obtener información de la cuenta del primer movimiento
        primer_mov = movimientos[0]
        ultimo_mov = movimientos[-1]
        
        return {
            "id_cuenta": cuenta_id,
            "codigo_cuenta": primer_mov["cuenta_codigo"],
            "nombre_cuenta": primer_mov["cuenta_nombre"],
            "tipo_cuenta": primer_mov["cuenta_tipo"],
            "saldo_inicial": 0.00,  # TODO: Obtener del balance inicial
            "saldo_final": ultimo_mov["saldo_actual"],
            "total_debe": sum(m["debe"] for m in movimientos),
            "total_haber": sum(m["haber"] for m in movimientos),
            "cantidad_movimientos": len(movimientos),
            "movimientos": [{
                "fecha_movimiento": str(m["fecha_movimiento"]),
                "descripcion": m["descripcion"],
                "referencia": m["referencia"],
                "debe": m["debe"],
                "haber": m["haber"],
                "saldo_acumulado": m["saldo_actual"]
            } for m in movimientos]
        }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al generar libro mayor: {str(e)}"
        )

@router.get("/periodo/{periodo_id}")
def obtener_libro_mayor_completo(
    periodo_id: int,
    solo_con_movimientos: bool = Query(True, description="Solo cuentas con movimientos"),
    db: Session = Depends(get_db)
):
    """Obtener libro mayor completo para todas las cuentas en un período"""
    try:
        libro_mayor = generar_libro_mayor_completo(
            db=db,
            periodo_id=periodo_id
        )
        
        # Formatear respuesta para el frontend
        cuentas_resumen = []
        
        for codigo_cuenta, datos_cuenta in libro_mayor["cuentas"].items():
            movimientos = datos_cuenta["movimientos"]
            
            # Calcular totales
            total_debe = sum(m["debe"] for m in movimientos)
            total_haber = sum(m["haber"] for m in movimientos)
            
            cuenta_info = {
                "id_cuenta": datos_cuenta["id_cuenta"],
                "codigo_cuenta": codigo_cuenta,
                "nombre_cuenta": datos_cuenta["nombre_cuenta"],
                "tipo_cuenta": datos_cuenta["tipo_cuenta"],
                "saldo_inicial": 0.00,  # TODO: Obtener del balance inicial
                "total_debe": total_debe,
                "total_haber": total_haber,
                "saldo_final": datos_cuenta["saldo_final"],
                "cantidad_movimientos": len(movimientos),
                "movimientos": [{
                    "fecha_movimiento": str(m["fecha_movimiento"]),
                    "descripcion": m["descripcion"],
                    "referencia": m["referencia"],
                    "debe": m["debe"],
                    "haber": m["haber"],
                    "saldo_acumulado": m["saldo_actual"]
                } for m in movimientos]
            }
            
            if solo_con_movimientos and len(movimientos) > 0:
                cuentas_resumen.append(cuenta_info)
            elif not solo_con_movimientos:
                cuentas_resumen.append(cuenta_info)
        
        return cuentas_resumen
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al generar libro mayor completo: {str(e)}"
        )
