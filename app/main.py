"""FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app import config
from app.routes.search import router as search_router
from app.routes.analyze import router as analyze_router
from app.routes.chat import router as chat_router
from app.routes import admin as admin_module
from app.routes.admin import router as admin_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    config.validate()
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Jinja2 templates (admin portal) ──────────────────────────────────────────
_templates = Jinja2Templates(directory="app/templates")
admin_module.templates = _templates

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(search_router, prefix="/api")
app.include_router(analyze_router, prefix="/api")
app.include_router(chat_router, prefix="/api")
app.include_router(admin_router)  # prefix="/admin" set on the router itself

# ── Static files (built frontend) — must be last ─────────────────────────────
app.mount("/", StaticFiles(directory="static", html=True), name="static")
