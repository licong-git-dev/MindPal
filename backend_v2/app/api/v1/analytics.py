"""
MindPal Backend V2 - Analytics API Routes
最小埋点能力，确保前端埋点接口可用。
"""

from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.schemas import APIResponse

router = APIRouter()


class TrackEventRequest(BaseModel):
    eventName: str = Field(..., min_length=1, max_length=100)
    metadata: dict[str, Any] = Field(default_factory=dict)
    userId: Optional[int] = None
    sessionId: Optional[str] = None


class BatchTrackRequest(BaseModel):
    events: list[TrackEventRequest] = Field(default_factory=list)


@router.post("/track", response_model=APIResponse)
async def track_event(request: TrackEventRequest):
    return APIResponse(
        code=0,
        message="success",
        data={
            "accepted": True,
            "eventName": request.eventName,
            "receivedAt": datetime.utcnow().isoformat(),
        },
    )


@router.post("/batch", response_model=APIResponse)
async def track_batch(request: BatchTrackRequest):
    return APIResponse(
        code=0,
        message="success",
        data={
            "accepted": True,
            "count": len(request.events),
            "receivedAt": datetime.utcnow().isoformat(),
        },
    )


@router.get("/dashboard", response_model=APIResponse)
async def get_dashboard(range: int = 7):
    return APIResponse(
        code=0,
        message="success",
        data={
            "summary": {
                "totalUsers": 0,
                "newUsers": 0,
                "dau": 0,
                "totalMessages": 0,
                "todayMessages": 0,
                "wacu": 0,
            },
            "dailyStats": [],
            "eventStats": {},
            "range": range,
        },
    )


@router.get("/events", response_model=APIResponse)
async def get_events(event: Optional[str] = None, limit: int = 100, offset: int = 0):
    return APIResponse(
        code=0,
        message="success",
        data={
            "events": [],
            "total": 0,
            "limit": limit,
            "offset": offset,
            "event": event,
        },
    )


@router.get("/funnel", response_model=APIResponse)
async def get_funnel(range: int = 30):
    return APIResponse(
        code=0,
        message="success",
        data={
            "steps": [],
            "range": range,
        },
    )
