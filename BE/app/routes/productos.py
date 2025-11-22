"""
Rutas de API para gestión de productos.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db import get_db
from app.schemas.producto import ProductoCreate, ProductoUpdate, ProductoResponse
from app.services.producto_service import ProductoService

router = APIRouter(
    prefix="/api/productos",
    tags=["productos"]
)

@router.post("", response_model=ProductoResponse, status_code=status.HTTP_201_CREATED)
def crear_producto(
    producto: ProductoCreate,
    db: Session = Depends(get_db)
):
    """Crear nuevo producto"""
    try:
        nuevo_producto = ProductoService.crear_producto(db, producto)
        return nuevo_producto
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al crear producto: {str(e)}")

@router.get("", response_model=List[ProductoResponse])
def listar_productos(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    buscar: Optional[str] = Query(None),
    tipo: Optional[str] = Query(None),
    activo: Optional[bool] = Query(None),
    categoria: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Listar productos con filtros opcionales"""
    try:
        productos = ProductoService.listar_productos(
            db,
            skip=skip,
            limit=limit,
            buscar=buscar,
            tipo=tipo,
            activo=activo,
            categoria=categoria
        )
        return productos
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al listar productos: {str(e)}")

@router.get("/analisis")
def obtener_analisis_productos(db: Session = Depends(get_db)):
    """Obtener análisis y estadísticas de productos"""
    try:
        analisis = ProductoService.obtener_analisis_productos(db)
        return analisis
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener análisis: {str(e)}")

@router.get("/{id_producto}", response_model=ProductoResponse)
def obtener_producto(
    id_producto: int,
    db: Session = Depends(get_db)
):
    """Obtener producto por ID"""
    producto = ProductoService.obtener_producto(db, id_producto)
    
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    return producto

@router.get("/codigo/{codigo_producto}", response_model=ProductoResponse)
def obtener_producto_por_codigo(
    codigo_producto: str,
    db: Session = Depends(get_db)
):
    """Obtener producto por código"""
    producto = ProductoService.obtener_producto_por_codigo(db, codigo_producto)
    
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    return producto

@router.put("/{id_producto}", response_model=ProductoResponse)
def actualizar_producto(
    id_producto: int,
    producto: ProductoUpdate,
    db: Session = Depends(get_db)
):
    """Actualizar producto existente"""
    try:
        producto_actualizado = ProductoService.actualizar_producto(db, id_producto, producto)
        
        if not producto_actualizado:
            raise HTTPException(status_code=404, detail="Producto no encontrado")
        
        return producto_actualizado
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al actualizar producto: {str(e)}")

@router.patch("/{id_producto}/estado")
def cambiar_estado_producto(
    id_producto: int,
    activo: bool,
    db: Session = Depends(get_db)
):
    """Cambiar estado activo/inactivo del producto"""
    try:
        producto = ProductoService.cambiar_estado_producto(db, id_producto, activo)
        
        if not producto:
            raise HTTPException(status_code=404, detail="Producto no encontrado")
        
        return {"mensaje": "Estado actualizado exitosamente", "producto": producto}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al cambiar estado: {str(e)}")

@router.patch("/{id_producto}/stock")
def actualizar_stock_producto(
    id_producto: int,
    cantidad: int,
    tipo_movimiento: str = Query("ajuste", regex="^(ajuste|entrada|salida)$"),
    db: Session = Depends(get_db)
):
    """Actualizar stock de producto"""
    try:
        producto = ProductoService.actualizar_stock(db, id_producto, cantidad, tipo_movimiento)
        
        if not producto:
            raise HTTPException(status_code=404, detail="Producto no encontrado")
        
        return {"mensaje": "Stock actualizado exitosamente", "producto": producto}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al actualizar stock: {str(e)}")

@router.delete("/{id_producto}")
def eliminar_producto(
    id_producto: int,
    db: Session = Depends(get_db)
):
    """Eliminar producto"""
    try:
        eliminado = ProductoService.eliminar_producto(db, id_producto)
        
        if not eliminado:
            raise HTTPException(status_code=404, detail="Producto no encontrado")
        
        return {"mensaje": "Producto eliminado exitosamente"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al eliminar producto: {str(e)}")
