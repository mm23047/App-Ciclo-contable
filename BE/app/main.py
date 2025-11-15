"""
Aplicación principal FastAPI para el sistema contable.
Configura la API, middleware y rutas.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import (
    catalogo_cuentas, transacciones, asientos, reportes, periodos,
    manual_cuentas, balance_inicial, partidas_ajuste, balanza,
    estados_financieros, facturacion, configuracion
)
from app.db import create_tables
import os

# Inicializar aplicación FastAPI
app = FastAPI(
    title="Sistema Contable Empresarial API",
    description="API completa para sistema de contabilidad con 9 módulos integrados",
    version="2.0.0",
)

# Configurar CORS - Permite todos los orígenes para desarrollo
# TODO: Configurar orígenes específicos para producción
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir rutas básicas de la API
app.include_router(catalogo_cuentas.router)
app.include_router(transacciones.router)
app.include_router(asientos.router)
app.include_router(reportes.router)
app.include_router(periodos.router)

# Incluir nuevas rutas de los 9 módulos
app.include_router(manual_cuentas.router)
app.include_router(balance_inicial.router)
app.include_router(partidas_ajuste.router)
app.include_router(balanza.router)
app.include_router(estados_financieros.router)
app.include_router(facturacion.router)
app.include_router(configuracion.router)

@app.on_event("startup")
def startup_event():
    """Inicializar tablas de la base de datos al arrancar"""
    create_tables()

@app.get("/")
def read_root():
    """Endpoint raíz con información de la API"""
    return {
        "message": "Sistema Contable Empresarial API",
        "version": "2.0.0",
        "modulos": [
            "Catálogo de Cuentas",
            "Manual de Cuentas", 
            "Libro Diario (Asientos)",
            "Libro Mayor",
            "Partidas de Ajuste",
            "Balanza de Comprobación",
            "Balance Inicial",
            "Estados Financieros",
            "Facturación Digital"
        ],
        "docs_url": "/docs",
        "endpoints": {
            "catalogo_cuentas": "/api/catalogo-cuentas",
            "transacciones": "/api/transacciones", 
            "asientos": "/api/asientos",
            "reportes": "/api/reportes",
            "periodos": "/api/periodos"
        }
    }

@app.get("/health")
def health_check():
    """Endpoint de verificación de salud"""
    return {"status": "healthy"}

# Para ejecutar en desarrollo local:
# Leer PORT_BE desde .env usando python-dotenv
# uvicorn app.main:app --host 0.0.0.0 --port ${PORT_BE} --reload

# En producción, el Dockerfile especificará el comando CMD
# TODO: Usar gunicorn/uvicorn workers en producción para mejor rendimiento