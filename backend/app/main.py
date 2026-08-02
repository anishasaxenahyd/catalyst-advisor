import logging
import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()  # loads backend/.env if present; real env vars still take precedence

from app.api.knowledge_routes import router as knowledge_router
from app.api.prompt_optimizer_routes import router as prompt_optimizer_router
from app.api.routes import router

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

app = FastAPI(
    title="Catalyst AI Solution Advisor",
    description="POC — deterministic recommendation engine behind a vendor-agnostic LLMProvider.",
    version="0.1.0",
)

_origins = os.getenv("FRONTEND_ORIGIN", "*")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _origins.split(",")],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")
app.include_router(knowledge_router, prefix="/api/knowledge")
app.include_router(prompt_optimizer_router, prefix="/api")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
