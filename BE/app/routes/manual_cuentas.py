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
    nuevo_manual = create_manual_cuenta(db, manual)
    
    # Convertir a diccionario con información de la cuenta
    return {
        'id_manual': nuevo_manual.id_manual,
        'id_cuenta': nuevo_manual.id_cuenta,
        'descripcion_detallada': nuevo_manual.descripcion_detallada,
        'naturaleza_cuenta': nuevo_manual.naturaleza_cuenta,
        'clasificacion': nuevo_manual.clasificacion,
        'instrucciones_uso': nuevo_manual.instrucciones_uso,
        'ejemplos_movimientos': nuevo_manual.ejemplos_movimientos,
        'cuentas_relacionadas': nuevo_manual.cuentas_relacionadas,
        'normativa_aplicable': nuevo_manual.normativa_aplicable,
        'fecha_creacion': nuevo_manual.fecha_creacion,
        'fecha_actualizacion': nuevo_manual.fecha_actualizacion,
        'usuario_actualizacion': nuevo_manual.usuario_actualizacion,
        'codigo_cuenta': nuevo_manual.cuenta.codigo_cuenta if nuevo_manual.cuenta else None,
        'nombre_cuenta': nuevo_manual.cuenta.nombre_cuenta if nuevo_manual.cuenta else None
    }

@router.get("/", response_model=List[ManualCuentasRead])
def listar_manuales(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    id_cuenta: Optional[int] = Query(None),
    texto_busqueda: Optional[str] = Query(None),
    naturaleza_cuenta: Optional[str] = Query(None),
    clasificacion: Optional[str] = Query(None),
    solo_con_ejemplos: Optional[bool] = Query(None),
    db: Session = Depends(get_db)
):
    """Listar manuales de cuentas con paginación y filtros de búsqueda"""
    if id_cuenta:
        manuales = get_manual_por_cuenta(db, id_cuenta)
        if manuales:
            manuales = [manuales]
        else:
            manuales = []
    else:
        manuales = get_manuales_cuentas(
            db, skip, limit, texto_busqueda, naturaleza_cuenta, 
            clasificacion, solo_con_ejemplos
        )
    
    # Convertir a lista de diccionarios con información de la cuenta
    resultado = []
    for manual in manuales:
        manual_dict = {
            'id_manual': manual.id_manual,
            'id_cuenta': manual.id_cuenta,
            'descripcion_detallada': manual.descripcion_detallada,
            'naturaleza_cuenta': manual.naturaleza_cuenta,
            'clasificacion': manual.clasificacion,
            'instrucciones_uso': manual.instrucciones_uso,
            'ejemplos_movimientos': manual.ejemplos_movimientos,
            'cuentas_relacionadas': manual.cuentas_relacionadas,
            'normativa_aplicable': manual.normativa_aplicable,
            'fecha_creacion': manual.fecha_creacion,
            'fecha_actualizacion': manual.fecha_actualizacion,
            'usuario_actualizacion': manual.usuario_actualizacion,
            'codigo_cuenta': manual.cuenta.codigo_cuenta if manual.cuenta else None,
            'nombre_cuenta': manual.cuenta.nombre_cuenta if manual.cuenta else None
        }
        resultado.append(manual_dict)
    
    return resultado

@router.get("/{manual_id}", response_model=ManualCuentasRead)
def obtener_manual(
    manual_id: int,
    db: Session = Depends(get_db)
):
    """Obtener manual específico por ID"""
    manual = get_manual_cuenta(db, manual_id)
    
    # Convertir a diccionario con información de la cuenta
    return {
        'id_manual': manual.id_manual,
        'id_cuenta': manual.id_cuenta,
        'descripcion_detallada': manual.descripcion_detallada,
        'naturaleza_cuenta': manual.naturaleza_cuenta,
        'clasificacion': manual.clasificacion,
        'instrucciones_uso': manual.instrucciones_uso,
        'ejemplos_movimientos': manual.ejemplos_movimientos,
        'cuentas_relacionadas': manual.cuentas_relacionadas,
        'normativa_aplicable': manual.normativa_aplicable,
        'fecha_creacion': manual.fecha_creacion,
        'fecha_actualizacion': manual.fecha_actualizacion,
        'usuario_actualizacion': manual.usuario_actualizacion,
        'codigo_cuenta': manual.cuenta.codigo_cuenta if manual.cuenta else None,
        'nombre_cuenta': manual.cuenta.nombre_cuenta if manual.cuenta else None
    }

@router.put("/{manual_id}", response_model=ManualCuentasRead)
def actualizar_manual(
    manual_id: int,
    manual_update: ManualCuentasUpdate,
    db: Session = Depends(get_db)
):
    """Actualizar manual existente"""
    manual_actualizado = update_manual_cuenta(db, manual_id, manual_update)
    
    # Convertir a diccionario con información de la cuenta
    return {
        'id_manual': manual_actualizado.id_manual,
        'id_cuenta': manual_actualizado.id_cuenta,
        'descripcion_detallada': manual_actualizado.descripcion_detallada,
        'naturaleza_cuenta': manual_actualizado.naturaleza_cuenta,
        'clasificacion': manual_actualizado.clasificacion,
        'instrucciones_uso': manual_actualizado.instrucciones_uso,
        'ejemplos_movimientos': manual_actualizado.ejemplos_movimientos,
        'cuentas_relacionadas': manual_actualizado.cuentas_relacionadas,
        'normativa_aplicable': manual_actualizado.normativa_aplicable,
        'fecha_creacion': manual_actualizado.fecha_creacion,
        'fecha_actualizacion': manual_actualizado.fecha_actualizacion,
        'usuario_actualizacion': manual_actualizado.usuario_actualizacion,
        'codigo_cuenta': manual_actualizado.cuenta.codigo_cuenta if manual_actualizado.cuenta else None,
        'nombre_cuenta': manual_actualizado.cuenta.nombre_cuenta if manual_actualizado.cuenta else None
    }

@router.delete("/{manual_id}")
def eliminar_manual(
    manual_id: int,
    db: Session = Depends(get_db)
):
    """Eliminar manual de cuenta"""
    delete_manual_cuenta(db, manual_id)
    return {"message": "Manual eliminado exitosamente"}