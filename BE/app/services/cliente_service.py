"""
Servicio de lógica de negocio para Clientes.
"""
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from typing import List, Optional
from decimal import Decimal

from app.models.facturacion import Cliente
from app.schemas.cliente import ClienteCreate, ClienteUpdate


class ClienteService:
    """Servicio para operaciones de Cliente"""
    
    @staticmethod
    def crear_cliente(db: Session, cliente_data: ClienteCreate) -> Cliente:
        """Crear un nuevo cliente"""
        
        # Convertir activo a estado_cliente
        estado = "ACTIVO" if cliente_data.activo else "INACTIVO"
        
        # Preparar datos del cliente
        cliente_dict = cliente_data.model_dump(exclude={'activo'}, exclude_unset=True, by_alias=False)
        cliente_dict['estado_cliente'] = estado
        
        # Asegurar que usuario_creacion tenga un valor
        if 'usuario_creacion' not in cliente_dict or not cliente_dict['usuario_creacion']:
            cliente_dict['usuario_creacion'] = 'sistema'
        
        # Mapear alias a nombres de columna
        if 'telefono' in cliente_dict:
            cliente_dict['telefono_principal'] = cliente_dict.pop('telefono')
        if 'celular' in cliente_dict:
            cliente_dict['telefono_secundario'] = cliente_dict.pop('celular')
        if 'descuento_comercial' in cliente_dict:
            cliente_dict['descuento_habitual'] = cliente_dict.pop('descuento_comercial')
        
        nuevo_cliente = Cliente(**cliente_dict)
        
        db.add(nuevo_cliente)
        db.commit()
        db.refresh(nuevo_cliente)
        
        return nuevo_cliente
    
    @staticmethod
    def listar_clientes(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        buscar: Optional[str] = None,
        activo: Optional[bool] = None,
        categoria: Optional[str] = None,
        tipo: Optional[str] = None
    ) -> List[Cliente]:
        """Listar clientes con filtros opcionales"""
        
        query = db.query(Cliente)
        
        # Filtro de búsqueda general
        if buscar:
            query = query.filter(
                or_(
                    Cliente.nombre.ilike(f"%{buscar}%"),
                    Cliente.codigo_cliente.ilike(f"%{buscar}%"),
                    Cliente.nit.ilike(f"%{buscar}%"),
                    Cliente.email.ilike(f"%{buscar}%")
                )
            )
        
        # Filtro por estado activo
        if activo is not None:
            estado = "ACTIVO" if activo else "INACTIVO"
            query = query.filter(Cliente.estado_cliente == estado)
        
        # Filtro por categoría
        if categoria:
            query = query.filter(Cliente.categoria_cliente == categoria)
        
        # Filtro por tipo
        if tipo:
            query = query.filter(Cliente.tipo_cliente == tipo)
        
        return query.offset(skip).limit(limit).all()
    
    @staticmethod
    def obtener_cliente(db: Session, id_cliente: int) -> Optional[Cliente]:
        """Obtener un cliente por ID"""
        return db.query(Cliente).filter(Cliente.id_cliente == id_cliente).first()
    
    @staticmethod
    def obtener_por_codigo(db: Session, codigo_cliente: str) -> Optional[Cliente]:
        """Obtener cliente por código"""
        return db.query(Cliente).filter(Cliente.codigo_cliente == codigo_cliente).first()
    
    @staticmethod
    def actualizar_cliente(db: Session, id_cliente: int, cliente_data: ClienteUpdate) -> Optional[Cliente]:
        """Actualizar un cliente existente"""
        
        cliente = ClienteService.obtener_cliente(db, id_cliente)
        if not cliente:
            return None
        
        # Preparar datos de actualización
        update_data = cliente_data.model_dump(exclude_unset=True, by_alias=False)
        
        # Mapear activo a estado_cliente
        if 'activo' in update_data:
            activo = update_data.pop('activo')
            update_data['estado_cliente'] = "ACTIVO" if activo else "INACTIVO"
        
        # Mapear alias a nombres de columna
        if 'telefono' in update_data:
            update_data['telefono_principal'] = update_data.pop('telefono')
        if 'celular' in update_data:
            update_data['telefono_secundario'] = update_data.pop('celular')
        if 'descuento_comercial' in update_data:
            update_data['descuento_habitual'] = update_data.pop('descuento_comercial')
        
        # Actualizar campos
        for campo, valor in update_data.items():
            setattr(cliente, campo, valor)
        
        db.commit()
        db.refresh(cliente)
        
        return cliente
    
    @staticmethod
    def cambiar_estado_cliente(db: Session, id_cliente: int, activo: bool) -> Optional[Cliente]:
        """Cambiar estado activo/inactivo del cliente"""
        
        cliente = ClienteService.obtener_cliente(db, id_cliente)
        if not cliente:
            return None
        
        cliente.estado_cliente = "ACTIVO" if activo else "INACTIVO"
        
        db.commit()
        db.refresh(cliente)
        
        return cliente
    
    @staticmethod
    def eliminar_cliente(db: Session, id_cliente: int) -> bool:
        """Eliminar un cliente permanentemente de la base de datos"""
        
        cliente = ClienteService.obtener_cliente(db, id_cliente)
        if not cliente:
            return False
        
        # Eliminación real (hard delete)
        db.delete(cliente)
        db.commit()
        
        return True
    
    @staticmethod
    def obtener_analisis_clientes(db: Session) -> dict:
        """Obtener datos de análisis de clientes"""
        
        from sqlalchemy import func, extract
        from datetime import datetime
        
        total_clientes = db.query(Cliente).count()
        clientes_activos = db.query(Cliente).filter(Cliente.estado_cliente == "ACTIVO").count()
        clientes_inactivos = db.query(Cliente).filter(Cliente.estado_cliente == "INACTIVO").count()
        
        # Clientes nuevos del mes actual
        mes_actual = datetime.now().month
        anio_actual = datetime.now().year
        
        nuevos_mes = db.query(Cliente).filter(
            extract('month', Cliente.fecha_creacion) == mes_actual,
            extract('year', Cliente.fecha_creacion) == anio_actual
        ).count()
        
        # Análisis por categoría
        categorias = {}
        clientes_con_categoria = db.query(Cliente.categoria_cliente).filter(Cliente.categoria_cliente.isnot(None)).all()
        for (categoria,) in clientes_con_categoria:
            categorias[categoria] = categorias.get(categoria, 0) + 1
        
        # Análisis por tipo
        tipos = {}
        clientes_con_tipo = db.query(Cliente.tipo_cliente).all()
        for (tipo,) in clientes_con_tipo:
            tipos[tipo] = tipos.get(tipo, 0) + 1
        
        # Límite de crédito total
        limite_total = db.query(func.sum(Cliente.limite_credito)).scalar() or Decimal("0.00")
        
        return {
            "total_clientes": total_clientes,
            "clientes_activos": clientes_activos,
            "clientes_inactivos": clientes_inactivos,
            "nuevos_mes": nuevos_mes,
            "distribucion_categorias": categorias,
            "distribucion_tipos": tipos,
            "limite_credito_total": float(limite_total)
        }
