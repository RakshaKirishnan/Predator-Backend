"""Thin routes for Dashboard cards and usage logs."""

from __future__ import annotations

from fastapi import APIRouter, Request

from app.schemas.dashboard_schema import (
    DashboardCardsResponse,
    UsageLogsResponse,
)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def _services(request: Request):
    return request.app.state.auth_services


@router.get("/cards", response_model=DashboardCardsResponse)
def get_dashboard_cards(request: Request):
    """Retrieve 4 metric card stats (users, pending_invites, accepted_invites, total_invites)."""
    stats = _services(request).dashboard_cards.get_cards_stats()
    return {
        "success": True,
        "message": "Dashboard card metrics retrieved",
        "data": stats,
    }


@router.get("/usage-logs", response_model=UsageLogsResponse)
def get_usage_logs(request: Request, page: int = 1, limit: int = 10):
    """Retrieve paginated security audit logs."""
    data = _services(request).usage_logs_service.get_logs(page=page, limit=limit)
    return {
        "success": True,
        "message": "Usage logs retrieved",
        "data": data,
    }
