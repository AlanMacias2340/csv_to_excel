from fastapi import FastAPI
from app.api.v1.routes import router as v1_router
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup tasks here (e.g., DB, caches)
    yield
    # shutdown tasks here

app = FastAPI(title="CSV to Excel API", version="0.1.0", lifespan=lifespan)

app.include_router(v1_router, prefix="/api/v1")

@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok"}
