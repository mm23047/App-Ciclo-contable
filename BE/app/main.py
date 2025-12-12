"""
Aplicación principal FastAPI para el sistema contable.
Configura la API, middleware y rutas.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
# Importar routers individualmente para evitar problemas de importación circular
from app.routes.catalogo_cuentas import router as catalogo_router
from app.routes.transacciones import router as transacciones_router
from app.routes.asientos import router as asientos_router
from app.routes.reportes import router as reportes_router
from app.routes.periodos import router as periodos_router

# Importar routers adicionales uno por uno para identificar problemas
try:
    from app.routes.manual_cuentas import router as manual_cuentas_router
    manual_cuentas_available = True
except ImportError as e:
    print(f"Manual cuentas no disponible: {e}")
    manual_cuentas_available = False

try:
    from app.routes.balance_inicial import router as balance_inicial_router
    balance_inicial_available = True
except ImportError as e:
    print(f"Balance inicial no disponible: {e}")
    balance_inicial_available = False

try:
    from app.routes.partidas_ajuste import router as partidas_ajuste_router
    partidas_ajuste_available = True
except ImportError as e:
    print(f"Partidas ajuste no disponible: {e}")
    partidas_ajuste_available = False

try:
    from app.routes.balanza import router as balanza_router
    balanza_available = True
except ImportError as e:
    print(f"Balanza no disponible: {e}")
    balanza_available = False

try:
    from app.routes.estados_financieros import router as estados_financieros_router
    estados_financieros_available = True
except ImportError as e:
    print(f"Estados financieros no disponible: {e}")
    estados_financieros_available = False

try:
    from app.routes.libro_mayor import router as libro_mayor_router
    libro_mayor_available = True
except ImportError as e:
    print(f"Libro mayor no disponible: {e}")
    libro_mayor_available = False

try:
    from app.routes.facturacion import router as facturacion_router
    facturacion_available = True
except ImportError as e:
    print(f"Facturación no disponible: {e}")
    facturacion_available = False

try:
    from app.routes.configuracion import router as configuracion_router
    configuracion_available = True
except ImportError as e:
    print(f"Configuración no disponible: {e}")
    configuracion_available = False

try:
    from app.routes.productos import router as productos_router
    productos_available = True
except ImportError as e:
    print(f"Productos no disponible: {e}")
    productos_available = False

try:
    from app.routes.clientes import router as clientes_router
    clientes_available = True
except ImportError as e:
    print(f"Clientes no disponible: {e}")
    clientes_available = False

try:
    from app.routes.auth import router as auth_router
    auth_available = True
except ImportError as e:
    print(f"Autenticación no disponible: {e}")
    auth_available = False

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

# Incluir rutas básicas de la API (siempre disponibles)
app.include_router(catalogo_router)
app.include_router(transacciones_router)
app.include_router(asientos_router)
app.include_router(reportes_router)
app.include_router(periodos_router)

# Incluir rutas adicionales solo si están disponibles
if manual_cuentas_available:
    app.include_router(manual_cuentas_router)

if balance_inicial_available:
    app.include_router(balance_inicial_router)

if partidas_ajuste_available:
    app.include_router(partidas_ajuste_router)

if balanza_available:
    app.include_router(balanza_router)

if estados_financieros_available:
    app.include_router(estados_financieros_router)

if libro_mayor_available:
    app.include_router(libro_mayor_router)

if facturacion_available:
    app.include_router(facturacion_router)

if configuracion_available:
    app.include_router(configuracion_router)

if productos_available:
    app.include_router(productos_router)

if clientes_available:
    app.include_router(clientes_router)

if auth_available:
    app.include_router(auth_router)

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