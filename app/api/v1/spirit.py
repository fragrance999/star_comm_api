from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.spirit import (
    MemoryRead,
    MemoryUpdate,
    MessageListRead,
    SpiritCreate,
    SpiritMessageRequest,
    SpiritRead,
    SpiritStateRead,
    SpiritUpdate,
)
from app.services.spirit import SpiritService

router = APIRouter()


@router.get("", response_model=SpiritStateRead)
async def get_spirit(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> dict[str, object]:
    return await SpiritService(db).state(current_user)


@router.post("", response_model=SpiritStateRead, status_code=status.HTTP_201_CREATED)
async def create_spirit(
    payload: SpiritCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, object]:
    return await SpiritService(db).create(current_user, payload)


@router.patch("", response_model=SpiritRead)
async def update_spirit(
    payload: SpiritUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> object:
    return await SpiritService(db).update(current_user, payload)


@router.get("/sessions/{session_id}/messages", response_model=MessageListRead)
async def get_messages(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, object]:
    return await SpiritService(db).messages(current_user, session_id)


@router.post("/onboarding/messages/stream")
async def stream_onboarding_message(
    payload: SpiritMessageRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    stream = SpiritService(db).stream_message(current_user, payload, onboarding=True)
    return _stream_response(stream)


@router.post("/chat/stream")
async def stream_chat_message(
    payload: SpiritMessageRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    stream = SpiritService(db).stream_message(current_user, payload, onboarding=False)
    return _stream_response(stream)


def _stream_response(stream: AsyncIterator[str]) -> StreamingResponse:
    return StreamingResponse(
        stream,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
