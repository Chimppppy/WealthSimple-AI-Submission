from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from backend.routes.evaluate import router as evaluate_router
from backend.routes.explain import router as explain_router

load_dotenv()

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

app = FastAPI(
    title="Wealthsimple Pulse",
    version="0.4.0",
    description="AI-powered monthly financial decision engine",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(evaluate_router, prefix="/api")
app.include_router(explain_router, prefix="/api")

if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


@app.get("/")
def root():
    if (FRONTEND_DIR / "index.html").exists():
        return FileResponse(str(FRONTEND_DIR / "index.html"))
    return {
        "service": "Wealthsimple Pulse",
        "version": "0.4.0",
        "status": "running",
        "docs": "/docs",
    }
