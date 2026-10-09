from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.api.routes_advisor import router as advisor_router
from app.api.routes_health import router as health_router
from app.api.routes_memory import router as memory_router
from app.repositories.database import init_db
from app.logging_config import logger
from mock_crm.main import app as mock_crm_app


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing Wealth Advisor Application...", extra={"event": "startup"})
    init_db()
    yield
    logger.info("Shutting down Wealth Advisor Application...", extra={"event": "shutdown"})


app = FastAPI(
    title="Mini Multi-Agent Wealth Advisor Assistant API",
    version="1.0.0",
    description="Production-quality multi-agent system for client financial data ingestion, anomaly detection, and advisory insights.",
    lifespan=lifespan
)

app.include_router(health_router)
app.include_router(advisor_router)
app.include_router(memory_router)

# Mount mock CRM service under /mock-crm if running combined app
app.mount("/mock-crm-service", mock_crm_app)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
