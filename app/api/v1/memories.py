from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.spirit import MemoryRead, MemoryUpdate
from app.services.spirit import SpiritService

router = APIRouter()


@router.patch("/{memory_id}", response_model=MemoryRead)
async def update_memory(
    memory_id: int,
    payload: MemoryUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> object:
    return await SpiritService(db).update_memory(current_user, memory_id, payload)


@router.post("/{memory_id}/confirm", response_model=MemoryRead)
async def confirm_memory(
    memory_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> object:
    return await SpiritService(db).confirm_memory(current_user, memory_id)


@router.post("/{memory_id}/discard", response_model=MemoryRead)
async def discard_memory(
    memory_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> object:
    return await SpiritService(db).discard_memory(current_user, memory_id)
