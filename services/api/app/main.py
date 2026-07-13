from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import api_router
from app.core.config import settings
from app.services import queue, storage


@asynccontextmanager
async def lifespan(app: FastAPI):
    storage.ensure_bucket()
    await queue.connect()
    yield
    await queue.disconnect()


app = FastAPI(
    title="Sınav Otomasyonu API",
    description="Yapay Zeka Destekli Akademik Değerlendirme ve Sınav Otomasyonu Platformu",
    version="0.1.0",
    lifespan=lifespan,
)

# SRS §4: CORS kısıtlı tutulur — joker (*) kullanılmaz.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/health", tags=["system"])
async def health() -> dict[str, str]:
    return {"status": "ok"}
