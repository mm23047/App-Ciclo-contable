"""
Main app minimal - solo catálogo de cuentas
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Solo importar catálogo de cuentas directamente
from app.routes.catalogo_cuentas import router as catalogo_router

app = FastAPI(
    title="Sistema Contable API",
    description="API para Sistema Contable - Versión Mínima",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Solo incluir catálogo de cuentas
app.include_router(catalogo_router, tags=["catalogo"])

@app.get("/")
async def root():
    return {"message": "Sistema Contable API - Funcionando", "status": "ok"}

@app.get("/health")
async def health():
    return {"status": "ok"}