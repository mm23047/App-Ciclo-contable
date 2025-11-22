"""
Servicio de gestión de productos.
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from typing import List, Optional, Dict, Any
from app.models.facturacion import Producto
from app.schemas.producto import ProductoCreate, ProductoUpdate

class ProductoService:
    """Servicio para gestión de productos"""

    @staticmethod
    def crear_producto(db: Session, producto_data: ProductoCreate) -> Producto:
        """Crear nuevo producto"""
        # Verificar que el código no exista
        existe = db.query(Producto).filter(
            Producto.codigo_producto == producto_data.codigo_producto
        ).first()
        
        if existe:
            raise ValueError(f"Ya existe un producto con el código {producto_data.codigo_producto}")
        
        # Crear producto
        nuevo_producto = Producto(**producto_data.model_dump())
        db.add(nuevo_producto)
        db.commit()
        db.refresh(nuevo_producto)
        
        return nuevo_producto

    @staticmethod
    def obtener_producto(db: Session, id_producto: int) -> Optional[Producto]:
        """Obtener producto por ID"""
        return db.query(Producto).filter(Producto.id_producto == id_producto).first()

    @staticmethod
    def obtener_producto_por_codigo(db: Session, codigo: str) -> Optional[Producto]:
        """Obtener producto por código"""
        return db.query(Producto).filter(Producto.codigo_producto == codigo).first()

    @staticmethod
    def listar_productos(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        buscar: Optional[str] = None,
        tipo: Optional[str] = None,
        activo: Optional[bool] = None,
        categoria: Optional[str] = None
    ) -> List[Producto]:
        """Listar productos con filtros opcionales"""
        query = db.query(Producto)
        
        # Filtro de búsqueda por nombre o código
        if buscar:
            query = query.filter(
                or_(
                    Producto.nombre.ilike(f"%{buscar}%"),
                    Producto.codigo_producto.ilike(f"%{buscar}%"),
                    Producto.descripcion.ilike(f"%{buscar}%")
                )
            )
        
        # Filtro por tipo
        if tipo:
            query = query.filter(Producto.tipo_producto == tipo)
        
        # Filtro por estado (activo = ACTIVO, inactivo = INACTIVO)
        if activo is not None:
            estado = "ACTIVO" if activo else "INACTIVO"
            query = query.filter(Producto.estado_producto == estado)
        
        # Filtro por categoría
        if categoria:
            query = query.filter(Producto.categoria_producto == categoria)
        
        return query.offset(skip).limit(limit).all()

    @staticmethod
    def actualizar_producto(
        db: Session,
        id_producto: int,
        producto_data: ProductoUpdate
    ) -> Optional[Producto]:
        """Actualizar producto existente"""
        producto = db.query(Producto).filter(Producto.id_producto == id_producto).first()
        
        if not producto:
            return None
        
        # Actualizar solo campos proporcionados
        update_data = producto_data.model_dump(exclude_unset=True)
        
        # Si se actualiza el código, verificar que no exista
        if 'codigo_producto' in update_data:
            existe = db.query(Producto).filter(
                Producto.codigo_producto == update_data['codigo_producto'],
                Producto.id_producto != id_producto
            ).first()
            
            if existe:
                raise ValueError(f"Ya existe otro producto con el código {update_data['codigo_producto']}")
        
        for key, value in update_data.items():
            setattr(producto, key, value)
        
        db.commit()
        db.refresh(producto)
        
        return producto

    @staticmethod
    def eliminar_producto(db: Session, id_producto: int) -> bool:
        """Eliminar producto"""
        producto = db.query(Producto).filter(Producto.id_producto == id_producto).first()
        
        if not producto:
            return False
        
        db.delete(producto)
        db.commit()
        
        return True

    @staticmethod
    def cambiar_estado_producto(db: Session, id_producto: int, activo: bool) -> Optional[Producto]:
        """Cambiar estado activo/inactivo del producto"""
        producto = db.query(Producto).filter(Producto.id_producto == id_producto).first()
        
        if not producto:
            return None
        
        producto.estado_producto = "ACTIVO" if activo else "INACTIVO"
        db.commit()
        db.refresh(producto)
        
        return producto

    @staticmethod
    def obtener_analisis_productos(db: Session) -> Dict[str, Any]:
        """Obtener análisis y estadísticas de productos"""
        total_productos = db.query(func.count(Producto.id_producto)).scalar()
        productos_activos = db.query(func.count(Producto.id_producto)).filter(
            Producto.estado_producto == "ACTIVO"
        ).scalar()
        
        # Categorías únicas
        total_categorias = db.query(func.count(func.distinct(Producto.categoria_producto))).scalar()
        
        # Precio promedio
        precio_promedio = db.query(func.avg(Producto.precio_venta)).scalar() or 0
        
        # Distribución por tipo
        distribucion_tipos = db.query(
            Producto.tipo_producto,
            func.count(Producto.id_producto)
        ).group_by(Producto.tipo_producto).all()
        
        tipos_dict = {tipo: count for tipo, count in distribucion_tipos}
        
        # Productos con stock bajo
        productos_stock_bajo = db.query(func.count(Producto.id_producto)).filter(
            Producto.stock_actual <= Producto.stock_minimo,
            Producto.stock_minimo > 0,
            Producto.maneja_inventario == True
        ).scalar()
        
        return {
            "total_productos": total_productos,
            "productos_activos": productos_activos,
            "total_categorias": total_categorias,
            "precio_promedio": float(precio_promedio),
            "distribucion_tipos": tipos_dict,
            "productos_stock_bajo": productos_stock_bajo
        }

    @staticmethod
    def actualizar_stock(
        db: Session,
        id_producto: int,
        cantidad: int,
        tipo_movimiento: str = "ajuste"
    ) -> Optional[Producto]:
        """
        Actualizar stock de producto
        tipo_movimiento: 'ajuste', 'entrada', 'salida'
        """
        producto = db.query(Producto).filter(Producto.id_producto == id_producto).first()
        
        if not producto:
            return None
        
        if tipo_movimiento == "ajuste":
            producto.stock_actual = cantidad
        elif tipo_movimiento == "entrada":
            producto.stock_actual += cantidad
        elif tipo_movimiento == "salida":
            if producto.stock_actual < cantidad:
                raise ValueError("Stock insuficiente")
            producto.stock_actual -= cantidad
        
        db.commit()
        db.refresh(producto)
        
        return producto
