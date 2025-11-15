"""
Rutas FastAPI para Configuración del Sistema.
Endpoints para gestión de configuraciones generales.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from app.db import get_db
from app.services.configuracion_service import (
    obtener_configuracion_empresa, actualizar_configuracion_empresa,
    obtener_configuraciones_categoria, crear_configuracion_categoria,
    actualizar_configuracion_categoria, configurar_cuentas_contables_default,
    configurar_parametros_facturacion, obtener_configuracion_por_categoria,
    obtener_valor_configuracion, establecer_valor_configuracion,
    validar_configuracion_sistema, exportar_configuraciones
)

router = APIRouter(
    prefix="/api/configuracion",
    tags=["Configuración del Sistema"]
)

# Configuración de Empresa
@router.get("/empresa")
def obtener_config_empresa(db: Session = Depends(get_db)):
    """Obtener configuración actual de la empresa"""
    return obtener_configuracion_empresa(db)

@router.put("/empresa")
def actualizar_config_empresa(
    nombre_empresa: str = None,
    nit_empresa: str = None,
    direccion_empresa: str = None,
    telefono_empresa: str = None,
    email_empresa: str = None,
    moneda_reporte: str = None,
    db: Session = Depends(get_db)
):
    """Actualizar configuración de la empresa"""
    return actualizar_configuracion_empresa(
        db, nombre_empresa, nit_empresa, direccion_empresa,
        telefono_empresa, email_empresa, moneda_reporte, "API_USER"
    )

# Configuraciones por Categoría
@router.get("/categorias")
def listar_configuraciones_categoria(db: Session = Depends(get_db)):
    """Listar todas las configuraciones por categoría"""
    return obtener_configuraciones_categoria(db)

@router.post("/categorias")
def crear_config_categoria(
    categoria: str,
    descripcion: str,
    configuracion_json: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Crear nueva configuración de categoría"""
    return crear_configuracion_categoria(
        db, categoria, descripcion, configuracion_json, "API_USER"
    )

@router.get("/categorias/{categoria}")
def obtener_config_categoria(
    categoria: str,
    db: Session = Depends(get_db)
):
    """Obtener configuración específica por categoría"""
    config = obtener_configuracion_por_categoria(db, categoria)
    if not config:
        raise HTTPException(
            status_code=404,
            detail=f"No se encontró configuración para la categoría: {categoria}"
        )
    return config

@router.put("/categorias/{categoria_id}")
def actualizar_config_categoria(
    categoria_id: int,
    descripcion: str = None,
    configuracion_json: Dict[str, Any] = None,
    db: Session = Depends(get_db)
):
    """Actualizar configuración de categoría existente"""
    return actualizar_configuracion_categoria(
        db, categoria_id, descripcion, configuracion_json, "API_USER"
    )

# Configuraciones Específicas
@router.post("/cuentas-contables/inicializar")
def inicializar_cuentas_contables(db: Session = Depends(get_db)):
    """Configurar cuentas contables por defecto"""
    return configurar_cuentas_contables_default(db, "API_USER")

@router.post("/facturacion/inicializar")
def inicializar_parametros_facturacion(db: Session = Depends(get_db)):
    """Configurar parámetros de facturación por defecto"""
    return configurar_parametros_facturacion(db, "API_USER")

# Gestión de Valores Específicos
@router.get("/valor/{categoria}/{clave}")
def obtener_valor_config(
    categoria: str,
    clave: str,
    valor_por_defecto: str = None,
    db: Session = Depends(get_db)
):
    """Obtener un valor específico de configuración"""
    valor = obtener_valor_configuracion(db, categoria, clave, valor_por_defecto)
    return {"categoria": categoria, "clave": clave, "valor": valor}

@router.put("/valor/{categoria}/{clave}")
def establecer_valor_config(
    categoria: str,
    clave: str,
    valor: Any,
    db: Session = Depends(get_db)
):
    """Establecer un valor específico de configuración"""
    exito = establecer_valor_configuracion(db, categoria, clave, valor, "API_USER")
    return {
        "success": exito,
        "message": f"Valor actualizado para {categoria}.{clave}",
        "categoria": categoria,
        "clave": clave,
        "nuevo_valor": valor
    }

# Validación y Diagnóstico
@router.get("/validar-sistema")
def validar_sistema(db: Session = Depends(get_db)):
    """Validar que el sistema esté correctamente configurado"""
    return validar_configuracion_sistema(db)

@router.get("/exportar")
def exportar_todas_configuraciones(db: Session = Depends(get_db)):
    """Exportar todas las configuraciones del sistema"""
    return exportar_configuraciones(db)

# Endpoints de utilidad
@router.get("/estado")
def obtener_estado_configuracion(db: Session = Depends(get_db)):
    """Obtener estado general de la configuración"""
    validacion = validar_configuracion_sistema(db)
    empresa = obtener_configuracion_empresa(db)
    
    return {
        "sistema_configurado": validacion["sistema_listo"],
        "empresa_configurada": empresa.nombre_empresa != "Mi Empresa S.A.",
        "total_errores": validacion["total_errores"],
        "total_advertencias": validacion["total_advertencias"],
        "empresa": {
            "nombre": empresa.nombre_empresa,
            "nit": empresa.nit_empresa,
            "moneda": empresa.moneda_reporte
        },
        "recomendaciones": validacion["recomendaciones"][:3]  # Top 3 recomendaciones
    }