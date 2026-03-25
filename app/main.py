from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api import whatsapp, telegram, rest, test
import traceback

app = FastAPI(
    title="DeggBi AI",
    description="Détection de deepfakes et vérification de contenus — La Vérité en Wolof",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(whatsapp.router, prefix="/api/v1/whatsapp", tags=["WhatsApp"])
app.include_router(telegram.router, prefix="/api/v1/telegram", tags=["Telegram"])
app.include_router(rest.router, prefix="/api/v1", tags=["REST API"])
app.include_router(test.router, prefix="/api/v1/test", tags=["Test Sync"])


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    tb = traceback.format_exc()
    print(f"ERROR: {exc}\n{tb}")
    return JSONResponse(status_code=500, content={"detail": str(exc), "traceback": tb})


@app.get("/health")
async def health():
    return {"status": "ok", "service": "deggbi-ai"}
