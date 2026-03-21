"""FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app import config
from app.routes.search import router as search_router
from app.routes.analyze import router as analyze_router
from app.routes.chat import router as chat_router


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

app.include_router(search_router, prefix="/api")
app.include_router(analyze_router, prefix="/api")
app.include_router(chat_router, prefix="/api")

app.mount("/", StaticFiles(directory="static", html=True), name="static")
