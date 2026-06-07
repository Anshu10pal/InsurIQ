from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from services.agent.router import router as agent_router
from services.fraud.router import router as fraud_router
from services.ingestion.router import router as ingestion_router
from services.eval.router import router as eval_router
from services.dashboard.router import router as dashboard_router

app = FastAPI(
    title="InsurIQ API",
    description="AI-powered insurance fraud detection system",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Instrumentator().instrument(app).expose(app)

app.include_router(agent_router,     prefix="/api/v1/claims",    tags=["Claims"])
app.include_router(fraud_router,     prefix="/api/v1/fraud",     tags=["Fraud"])
app.include_router(ingestion_router, prefix="/api/v1/ingestion", tags=["Ingestion"])
app.include_router(eval_router,      prefix="/api/v1/eval",      tags=["Evaluation"])
app.include_router(dashboard_router, prefix="/api/v1/dashboard", tags=["Dashboard"])


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok", "service": "InsurIQ"}
