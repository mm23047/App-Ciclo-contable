"""
Rutas API para Clientes.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db import get_db
from app.schemas.cliente import ClienteCreate, ClienteUpdate, ClienteResponse
from app.services.cliente_service import ClienteService

router = APIRouter(prefix="/api/clientes", tags=["clientes"])


@router.post("", response_model=ClienteResponse, status_code=status.HTTP_201_CREATED)
def crear_cliente(
    cliente: ClienteCreate,
    db: Session = Depends(get_db)
):
    """
    Crear un nuevo cliente.
    """
    try:
        # Verificar si ya existe un cliente con ese código
        cliente_existente = ClienteService.obtener_por_codigo(db, cliente.codigo_cliente)
        if cliente_existente:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ya existe un cliente con el código '{cliente.codigo_cliente}'"
            )
        
        nuevo_cliente = ClienteService.crear_cliente(db, cliente)
        return nuevo_cliente
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear cliente: {str(e)}"
        )


@router.get("", response_model=List[ClienteResponse])
def listar_clientes(
    skip: int = Query(0, ge=0, description="Número de registros a omitir"),
    limit: int = Query(100, ge=1, le=1000, description="Número máximo de registros"),
    buscar: Optional[str] = Query(None, description="Término de búsqueda"),
    activo: Optional[bool] = Query(None, description="Filtrar por estado activo"),
    categoria: Optional[str] = Query(None, description="Filtrar por categoría"),
    tipo: Optional[str] = Query(None, description="Filtrar por tipo de cliente"),
    db: Session = Depends(get_db)
):
    """
    Listar clientes con filtros opcionales.
    """
    try:
        clientes = ClienteService.listar_clientes(
            db,
            skip=skip,
            limit=limit,
            buscar=buscar,
            activo=activo,
            categoria=categoria,
            tipo=tipo
        )
        return clientes
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al listar clientes: {str(e)}"
        )


@router.get("/analisis")
def obtener_analisis_clientes(db: Session = Depends(get_db)):
    """
    Obtener datos de análisis de clientes.
    """
    try:
        analisis = ClienteService.obtener_analisis_clientes(db)
        return analisis
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener análisis: {str(e)}"
        )


@router.get("/{id_cliente}", response_model=ClienteResponse)
def obtener_cliente(
    id_cliente: int,
    db: Session = Depends(get_db)
):
    """
    Obtener un cliente específico por ID.
    """
    cliente = ClienteService.obtener_cliente(db, id_cliente)
    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cliente con ID {id_cliente} no encontrado"
        )
    return cliente


@router.put("/{id_cliente}", response_model=ClienteResponse)
def actualizar_cliente(
    id_cliente: int,
    cliente_data: ClienteUpdate,
    db: Session = Depends(get_db)
):
    """
    Actualizar un cliente existente.
    """
    cliente = ClienteService.actualizar_cliente(db, id_cliente, cliente_data)
    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cliente con ID {id_cliente} no encontrado"
        )
    return cliente


@router.patch("/{id_cliente}/estado", response_model=ClienteResponse)
def cambiar_estado_cliente(
    id_cliente: int,
    activo: bool = Query(..., description="Nuevo estado del cliente"),
    db: Session = Depends(get_db)
):
    """
    Cambiar el estado activo/inactivo de un cliente.
    """
    cliente = ClienteService.cambiar_estado_cliente(db, id_cliente, activo)
    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cliente con ID {id_cliente} no encontrado"
        )
    return cliente


@router.delete("/{id_cliente}", status_code=status.HTTP_200_OK)
def eliminar_cliente(
    id_cliente: int,
    db: Session = Depends(get_db)
):
    """
    Eliminar un cliente (soft delete).
    """
    if not ClienteService.eliminar_cliente(db, id_cliente):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cliente con ID {id_cliente} no encontrado"
        )
    return {"message": "Cliente eliminado exitosamente"}
