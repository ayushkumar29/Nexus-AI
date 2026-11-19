"""Aggregated API router for v1 endpoints."""

from fastapi import APIRouter
from app.api.routes import auth, health

api_router = APIRouter(prefix="/v1")
api_router.include_router(health.router)
api_router.include_router(auth.router)
