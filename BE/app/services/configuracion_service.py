"""
Capa de servicios para Configuraciones del Sistema.
Maneja la configuración general de la empresa y parámetros del sistema contable.
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from fastapi import HTTPException, status
from app.models.estados_financieros import ConfiguracionEstadosFinancieros
from app.models.configuracion_categoria import ConfiguracionContableCategoria
from app.models.periodo import PeriodoContable
from typing import Dict, List, Optional, Any
from decimal import Decimal
from datetime import date, datetime
import json

def obtener_configuracion_empresa(db: Session) -> ConfiguracionEstadosFinancieros:
    """Obtener la configuración activa de la empresa"""
    
    config = db.query(ConfiguracionEstadosFinancieros).filter(
        ConfiguracionEstadosFinancieros.activa == True
    ).first()
    
    if not config:
        # Crear configuración por defecto si no existe
        config = crear_configuracion_empresa_default(db)
    
    return config

def crear_configuracion_empresa_default(db: Session) -> ConfiguracionEstadosFinancieros:
    """Crear configuración de empresa por defecto"""
    
    try:
        # Desactivar cualquier configuración existente
        db.query(ConfiguracionEstadosFinancieros).update({"activa": False})
        
        config_default = ConfiguracionEstadosFinancieros(
            nombre_empresa="Mi Empresa S.A.",
            nit_empresa="0000000000000",
            direccion_empresa="Dirección no configurada",
            telefono_empresa="0000-0000",
            email_empresa="contacto@empresa.com",
            moneda_reporte="USD",
            activa=True,
            fecha_creacion=date.today(),
            usuario_creacion="Sistema"
        )
        
        db.add(config_default)
        db.commit()
        db.refresh(config_default)
        return config_default
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error al crear configuración por defecto: {str(e)}"
        )

def actualizar_configuracion_empresa(
    db: Session,
    nombre_empresa: str = None,
    nit_empresa: str = None,
    direccion_empresa: str = None,
    telefono_empresa: str = None,
    email_empresa: str = None,
    moneda_reporte: str = None,
    usuario: str = "Sistema"
) -> ConfiguracionEstadosFinancieros:
    """Actualizar configuración de la empresa"""
    
    config = obtener_configuracion_empresa(db)
    
    try:
        # Actualizar campos proporcionados
        if nombre_empresa is not None:
            config.nombre_empresa = nombre_empresa
        if nit_empresa is not None:
            config.nit_empresa = nit_empresa
        if direccion_empresa is not None:
            config.direccion_empresa = direccion_empresa
        if telefono_empresa is not None:
            config.telefono_empresa = telefono_empresa
        if email_empresa is not None:
            config.email_empresa = email_empresa
        if moneda_reporte is not None:
            config.moneda_reporte = moneda_reporte
        
        config.fecha_modificacion = date.today()
        config.usuario_modificacion = usuario
        
        db.commit()
        db.refresh(config)
        return config
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error al actualizar configuración: {str(e)}"
        )

def obtener_configuraciones_categoria(db: Session) -> List[ConfiguracionContableCategoria]:
    """Obtener todas las configuraciones de categorías"""
    
    return db.query(ConfiguracionContableCategoria).filter(
        ConfiguracionContableCategoria.activa == True
    ).order_by(ConfiguracionContableCategoria.categoria).all()

def crear_configuracion_categoria(
    db: Session,
    categoria: str,
    descripcion: str,
    configuracion_json: Dict[str, Any],
    usuario: str
) -> ConfiguracionContableCategoria:
    """Crear nueva configuración de categoría"""
    
    # Verificar que no exista una configuración activa para esta categoría
    config_existente = db.query(ConfiguracionContableCategoria).filter(
        ConfiguracionContableCategoria.categoria == categoria,
        ConfiguracionContableCategoria.activa == True
    ).first()
    
    if config_existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ya existe una configuración activa para la categoría: {categoria}"
        )
    
    try:
        config = ConfiguracionContableCategoria(
            categoria=categoria,
            descripcion=descripcion,
            configuracion_json=configuracion_json,
            fecha_creacion=date.today(),
            usuario_creacion=usuario,
            activa=True
        )
        
        db.add(config)
        db.commit()
        db.refresh(config)
        return config
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error al crear configuración de categoría: {str(e)}"
        )

def actualizar_configuracion_categoria(
    db: Session,
    categoria_id: int,
    descripcion: str = None,
    configuracion_json: Dict[str, Any] = None,
    usuario: str = "Sistema"
) -> ConfiguracionContableCategoria:
    """Actualizar configuración de categoría existente"""
    
    config = db.query(ConfiguracionContableCategoria).filter(
        ConfiguracionContableCategoria.id_configuracion == categoria_id
    ).first()
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuración de categoría no encontrada"
        )
    
    try:
        if descripcion is not None:
            config.descripcion = descripcion
        if configuracion_json is not None:
            config.configuracion_json = configuracion_json
        
        config.fecha_modificacion = date.today()
        config.usuario_modificacion = usuario
        
        db.commit()
        db.refresh(config)
        return config
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error al actualizar configuración: {str(e)}"
        )

def configurar_cuentas_contables_default(db: Session, usuario: str = "Sistema") -> Dict[str, Any]:
    """Configurar cuentas contables por defecto para el sistema"""
    
    configuracion_cuentas = {
        "cuentas_ventas": {
            "codigo_base": "4101",
            "descripcion": "Cuenta base para ventas"
        },
        "cuentas_clientes": {
            "codigo_base": "1103",
            "descripcion": "Cuenta base para cuentas por cobrar clientes"
        },
        "iva_debito_fiscal": {
            "codigo_base": "2104",
            "descripcion": "Cuenta para IVA débito fiscal"
        },
        "iva_credito_fiscal": {
            "codigo_base": "1108",
            "descripcion": "Cuenta para IVA crédito fiscal"
        },
        "caja_general": {
            "codigo_base": "1101",
            "descripcion": "Cuenta principal de caja"
        },
        "bancos": {
            "codigo_base": "1102",
            "descripcion": "Cuentas bancarias"
        },
        "compras": {
            "codigo_base": "5101",
            "descripcion": "Cuenta base para compras"
        },
        "proveedores": {
            "codigo_base": "2101",
            "descripcion": "Cuenta base para cuentas por pagar proveedores"
        }
    }
    
    try:
        # Crear o actualizar configuración de cuentas contables
        config = db.query(ConfiguracionContableCategoria).filter(
            ConfiguracionContableCategoria.categoria == "CUENTAS_CONTABLES",
            ConfiguracionContableCategoria.activa == True
        ).first()
        
        if config:
            config.configuracion_json = configuracion_cuentas
            config.fecha_modificacion = date.today()
            config.usuario_modificacion = usuario
        else:
            config = ConfiguracionContableCategoria(
                categoria="CUENTAS_CONTABLES",
                descripcion="Configuración de cuentas contables por defecto del sistema",
                configuracion_json=configuracion_cuentas,
                fecha_creacion=date.today(),
                usuario_creacion=usuario,
                activa=True
            )
            db.add(config)
        
        db.commit()
        db.refresh(config)
        
        return {
            "configuracion_id": config.id_configuracion,
            "cuentas_configuradas": configuracion_cuentas
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error al configurar cuentas contables: {str(e)}"
        )

def configurar_parametros_facturacion(db: Session, usuario: str = "Sistema") -> Dict[str, Any]:
    """Configurar parámetros de facturación por defecto"""
    
    parametros_facturacion = {
        "numeracion": {
            "formato": "FAC-{año}-{numero:06d}",
            "reiniciar_anual": True,
            "numero_inicial": 1
        },
        "impuestos": {
            "iva_porcentaje": 13.0,
            "aplicar_iva_por_defecto": True,
            "cuenta_iva_ventas": "2104001",
            "cuenta_iva_compras": "1108001"
        },
        "validaciones": {
            "permitir_precio_cero": False,
            "requerir_cliente": True,
            "validar_stock": False
        },
        "integracion_contable": {
            "generar_asientos_automaticos": True,
            "cuenta_ventas_default": "4101001",
            "cuenta_clientes_default": "1103001"
        }
    }
    
    try:
        config = db.query(ConfiguracionContableCategoria).filter(
            ConfiguracionContableCategoria.categoria == "FACTURACION",
            ConfiguracionContableCategoria.activa == True
        ).first()
        
        if config:
            config.configuracion_json = parametros_facturacion
            config.fecha_modificacion = date.today()
            config.usuario_modificacion = usuario
        else:
            config = ConfiguracionContableCategoria(
                categoria="FACTURACION",
                descripcion="Configuración de parámetros de facturación",
                configuracion_json=parametros_facturacion,
                fecha_creacion=date.today(),
                usuario_creacion=usuario,
                activa=True
            )
            db.add(config)
        
        db.commit()
        db.refresh(config)
        
        return {
            "configuracion_id": config.id_configuracion,
            "parametros": parametros_facturacion
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error al configurar parámetros de facturación: {str(e)}"
        )

def obtener_configuracion_por_categoria(db: Session, categoria: str) -> Optional[ConfiguracionContableCategoria]:
    """Obtener configuración específica por categoría"""
    
    return db.query(ConfiguracionContableCategoria).filter(
        ConfiguracionContableCategoria.categoria == categoria,
        ConfiguracionContableCategoria.activa == True
    ).first()

def obtener_valor_configuracion(
    db: Session, 
    categoria: str, 
    clave: str, 
    valor_por_defecto: Any = None
) -> Any:
    """Obtener un valor específico de configuración"""
    
    config = obtener_configuracion_por_categoria(db, categoria)
    
    if not config or not config.configuracion_json:
        return valor_por_defecto
    
    # Navegar por la estructura JSON usando la clave (puede ser anidada con puntos)
    claves = clave.split('.')
    valor = config.configuracion_json
    
    try:
        for k in claves:
            valor = valor[k]
        return valor
    except (KeyError, TypeError):
        return valor_por_defecto

def establecer_valor_configuracion(
    db: Session,
    categoria: str,
    clave: str,
    valor: Any,
    usuario: str = "Sistema"
) -> bool:
    """Establecer un valor específico de configuración"""
    
    config = obtener_configuracion_por_categoria(db, categoria)
    
    if not config:
        # Crear nueva configuración si no existe
        config = ConfiguracionContableCategoria(
            categoria=categoria,
            descripcion=f"Configuración automática para {categoria}",
            configuracion_json={},
            fecha_creacion=date.today(),
            usuario_creacion=usuario,
            activa=True
        )
        db.add(config)
    
    try:
        # Asegurar que existe la estructura JSON
        if not config.configuracion_json:
            config.configuracion_json = {}
        
        # Navegar y establecer el valor (puede ser anidado)
        claves = clave.split('.')
        diccionario = config.configuracion_json
        
        for k in claves[:-1]:
            if k not in diccionario:
                diccionario[k] = {}
            diccionario = diccionario[k]
        
        diccionario[claves[-1]] = valor
        
        config.fecha_modificacion = date.today()
        config.usuario_modificacion = usuario
        
        db.commit()
        return True
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error al establecer configuración: {str(e)}"
        )

def validar_configuracion_sistema(db: Session) -> Dict[str, Any]:
    """Validar que el sistema esté correctamente configurado"""
    
    validaciones = {
        "configuracion_empresa": {
            "configurada": False,
            "errores": [],
            "advertencias": []
        },
        "cuentas_contables": {
            "configurada": False,
            "errores": [],
            "advertencias": []
        },
        "periodo_activo": {
            "configurado": False,
            "errores": [],
            "advertencias": []
        },
        "facturacion": {
            "configurada": False,
            "errores": [],
            "advertencias": []
        }
    }
    
    # Validar configuración de empresa
    try:
        config_empresa = obtener_configuracion_empresa(db)
        if config_empresa.nombre_empresa == "Mi Empresa S.A.":
            validaciones["configuracion_empresa"]["advertencias"].append(
                "La empresa aún tiene el nombre por defecto"
            )
        if config_empresa.nit_empresa == "0000000000000":
            validaciones["configuracion_empresa"]["advertencias"].append(
                "El NIT de la empresa no ha sido configurado"
            )
        validaciones["configuracion_empresa"]["configurada"] = True
    except Exception as e:
        validaciones["configuracion_empresa"]["errores"].append(str(e))
    
    # Validar configuración de cuentas
    try:
        config_cuentas = obtener_configuracion_por_categoria(db, "CUENTAS_CONTABLES")
        if config_cuentas:
            validaciones["cuentas_contables"]["configurada"] = True
        else:
            validaciones["cuentas_contables"]["errores"].append(
                "No hay configuración de cuentas contables"
            )
    except Exception as e:
        validaciones["cuentas_contables"]["errores"].append(str(e))
    
    # Validar período activo
    try:
        periodo_activo = db.query(PeriodoContable).filter(
            PeriodoContable.estado == 'ABIERTO'
        ).first()
        if periodo_activo:
            validaciones["periodo_activo"]["configurado"] = True
        else:
            validaciones["periodo_activo"]["errores"].append(
                "No hay período contable activo"
            )
    except Exception as e:
        validaciones["periodo_activo"]["errores"].append(str(e))
    
    # Validar configuración de facturación
    try:
        config_facturacion = obtener_configuracion_por_categoria(db, "FACTURACION")
        if config_facturacion:
            validaciones["facturacion"]["configurada"] = True
        else:
            validaciones["facturacion"]["advertencias"].append(
                "No hay configuración específica de facturación"
            )
    except Exception as e:
        validaciones["facturacion"]["errores"].append(str(e))
    
    # Resumen general
    total_errores = sum(len(v["errores"]) for v in validaciones.values())
    total_advertencias = sum(len(v["advertencias"]) for v in validaciones.values())
    configurado_completamente = all(
        v["configurada"] or v["configurado"] for v in validaciones.values()
    ) and total_errores == 0
    
    return {
        "sistema_listo": configurado_completamente,
        "total_errores": total_errores,
        "total_advertencias": total_advertencias,
        "validaciones": validaciones,
        "fecha_validacion": datetime.now(),
        "recomendaciones": _generar_recomendaciones_configuracion(validaciones)
    }

def _generar_recomendaciones_configuracion(validaciones: Dict) -> List[str]:
    """Generar recomendaciones basadas en las validaciones"""
    
    recomendaciones = []
    
    if not validaciones["configuracion_empresa"]["configurada"]:
        recomendaciones.append("Configure la información de la empresa")
    
    if validaciones["configuracion_empresa"]["advertencias"]:
        recomendaciones.append("Complete la información de la empresa (nombre, NIT)")
    
    if not validaciones["cuentas_contables"]["configurada"]:
        recomendaciones.append("Configure las cuentas contables por defecto del sistema")
    
    if not validaciones["periodo_activo"]["configurado"]:
        recomendaciones.append("Cree y active un período contable")
    
    if not validaciones["facturacion"]["configurada"]:
        recomendaciones.append("Configure los parámetros de facturación")
    
    if not recomendaciones:
        recomendaciones.append("El sistema está correctamente configurado")
    
    return recomendaciones

def exportar_configuraciones(db: Session) -> Dict[str, Any]:
    """Exportar todas las configuraciones del sistema"""
    
    # Configuración de empresa
    config_empresa = obtener_configuracion_empresa(db)
    
    # Configuraciones de categorías
    configs_categoria = obtener_configuraciones_categoria(db)
    
    return {
        "fecha_exportacion": datetime.now().isoformat(),
        "configuracion_empresa": {
            "nombre_empresa": config_empresa.nombre_empresa,
            "nit_empresa": config_empresa.nit_empresa,
            "direccion_empresa": config_empresa.direccion_empresa,
            "telefono_empresa": config_empresa.telefono_empresa,
            "email_empresa": config_empresa.email_empresa,
            "moneda_reporte": config_empresa.moneda_reporte
        } if config_empresa else None,
        "configuraciones_categoria": [
            {
                "categoria": config.categoria,
                "descripcion": config.descripcion,
                "configuracion_json": config.configuracion_json
            }
            for config in configs_categoria
        ]
    }
