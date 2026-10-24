"""
Passwordless face authentication API.

Only endpoints:
  POST /auth/signup
  POST /auth/face-login
  POST /auth/invite
  POST /auth/accept-invite
  GET  /auth/health

Run:
  cd face-auth/backend
  pip install -r requirements.txt
  uvicorn app.main:app --reload --port 8090
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_config
from app.core.error_handlers import register_exception_handlers
from app.db.mongo import get_mongo, reset_mongo
from app.routers.auth_routes import router as auth_router
from app.routers.dashboard_routes import router as dashboard_router
from app.routers.members_routes import router as members_router
from app.routers.settings_routes import router as settings_router
from app.services.auth.container import build_auth_services
from app.services.engine import InsightFaceEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("face-auth")


@asynccontextmanager
async def lifespan(app: FastAPI):
    config = get_config()
    mongo = get_mongo(config)
    engine = InsightFaceEngine.get(config)
    auth_services = build_auth_services(config=config, mongo=mongo, engine=engine)

    app.state.face_auth_config = config
    app.state.mongo = mongo
    app.state.face_engine = engine
    app.state.auth_services = auth_services

    try:
        engine.load()
    except Exception:
        logger.exception(
            "InsightFace failed to load at startup; endpoints will retry on demand"
        )

    yield

    reset_mongo()


app = FastAPI(
    title="Face Auth",
    description=(
        "Passwordless face authentication: signup, face-login, invite (SMTP), "
        "accept-invite. Backend generates InsightFace embeddings — clients send images only."
    ),
    version="2.0.0",
    lifespan=lifespan,
)

from app.middleware.client_metadata import ClientMetadataMiddleware
from app.middleware.auth_middleware import AuthMiddleware

register_exception_handlers(app)

app.add_middleware(AuthMiddleware)
app.add_middleware(ClientMetadataMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8090",
        "http://127.0.0.1:8090",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth_router)
app.include_router(dashboard_router)
app.include_router(members_router)
app.include_router(settings_router)



@app.get("/")
async def root():
    return {
        "name": "face-auth",
        "version": "2.0.0",
        "engine": "insightface",
        "docs": "/docs",
    }


if __name__ == "__main__":
    
    import uvicorn

    config = get_config()
    uvicorn.run("main:app", host=config.host, port=config.port, reload=True)


