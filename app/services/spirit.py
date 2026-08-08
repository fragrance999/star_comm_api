import json
from collections.abc import AsyncIterator

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.spirit import AiSpirit, AiSpiritMessage, AiSpiritSession, UserMemory
from app.models.user import User
from app.schemas.spirit import MemoryUpdate, SpiritCreate, SpiritMessageRequest, SpiritUpdate
from app.services.onboarding import create_candidate_memory
from app.services.spirit_ai import contains_safety_risk, get_spirit_ai_provider, safe_reply

ONBOARDING = "ONBOARDING"
CHAT = "CHAT"
ACTIVE = "ACTIVE"
COMPLETED = "COMPLETED"
PENDING = "PENDING"
CONFIRMED = "CONFIRMED"
DISCARDED = "DISCARDED"


class SpiritService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def state(self, user: User) -> dict[str, object]:
        spirit = await self._get_spirit_or_none(user.id)
        if spirit is None:
            return {
                "spirit": None,
                "onboarding_session": None,
                "chat_session": None,
                "onboarding_completed": False,
                "pending_memory": None,
            }

        session = await self._latest_session(spirit.id, user.id, ONBOARDING)
        chat_session = await self._latest_session(spirit.id, user.id, CHAT)
        pending_memory = await self._pending_memory(user.id, spirit.id)
        return {
            "spirit": spirit,
            "onboarding_session": session,
            "chat_session": chat_session,
            "onboarding_completed": session is not None and session.status == COMPLETED,
            "pending_memory": pending_memory,
        }

    async def create(self, user: User, payload: SpiritCreate) -> dict[str, object]:
        if await self._get_spirit_or_none(user.id) is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Spirit already exists")

        spirit = AiSpirit(
            user_id=user.id,
            name=payload.name,
            appearance_type=payload.appearance_type,
            persona_type=payload.persona_type,
            initiative_level=payload.initiative_level,
        )
        self.db.add(spirit)
        await self.db.flush()
        self.db.add(AiSpiritSession(user_id=user.id, spirit_id=spirit.id, session_type=ONBOARDING))
        await self.db.commit()
        return await self.state(user)

    async def update(self, user: User, payload: SpiritUpdate) -> AiSpirit:
        spirit = await self._require_spirit(user.id)
        if payload.name is not None:
            spirit.name = payload.name
        if payload.persona_type is not None:
            spirit.persona_type = payload.persona_type
        if payload.initiative_level is not None:
            spirit.initiative_level = payload.initiative_level
        await self.db.commit()
        await self.db.refresh(spirit)
        return spirit

    async def messages(self, user: User, session_id: int) -> dict[str, object]:
        session = await self._require_session(user.id, session_id)
        result = await self.db.execute(
            select(AiSpiritMessage).where(AiSpiritMessage.session_id == session.id).order_by(AiSpiritMessage.id)
        )
        return {"session": session, "messages": list(result.scalars())}

    async def stream_message(
        self,
        user: User,
        payload: SpiritMessageRequest,
        *,
        onboarding: bool,
    ) -> AsyncIterator[str]:
        spirit = await self._require_spirit(user.id)
        session = await self._conversation_session(user.id, spirit.id, ONBOARDING if onboarding else CHAT)
        if onboarding and session.status == COMPLETED:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Onboarding already completed")

        user_message = AiSpiritMessage(session_id=session.id, role="USER", content=payload.content.strip())
        self.db.add(user_message)
        if onboarding:
            session.user_turn_count += 1
        await self.db.commit()
        await self.db.refresh(session)

        yield _sse("message.start", {"session_id": session.id})
        reply_parts: list[str] = []
        is_risk = contains_safety_risk(payload.content)
        if is_risk:
            reply_parts = [safe_reply()]
            yield _sse("error", {"code": "SAFETY_RISK", "message": "已切换至安全回应"})
        else:
            history = await self._history(session.id)
            provider = get_spirit_ai_provider()
            try:
                async for chunk in provider.stream_reply(
                    persona_type=spirit.persona_type,
                    messages=history,
                    onboarding_turn=session.user_turn_count if onboarding else None,
                ):
                    reply_parts.append(chunk)
                    yield _sse("message.delta", {"content": chunk})
            except Exception:
                reply_parts = ["刚才的信号有些不稳定，但我还在。你愿意再说一次吗？"]
                yield _sse("error", {"code": "MODEL_UNAVAILABLE", "message": "模型暂时不可用，已使用本地回复"})

        if is_risk:
            for part in reply_parts:
                yield _sse("message.delta", {"content": part})

        reply = "".join(reply_parts)
        self.db.add(AiSpiritMessage(session_id=session.id, role="ASSISTANT", content=reply))
        await self.db.commit()
        yield _sse("message.complete", {"content": reply})

        if onboarding and not is_risk and session.user_turn_count >= 3:
            candidate = await self._pending_memory(user.id, spirit.id)
            if candidate is None:
                answers = await self._onboarding_answers(session.id)
                candidate = UserMemory(
                    user_id=user.id,
                    spirit_id=spirit.id,
                    category="SOCIAL_GOAL",
                    content=create_candidate_memory(answers),
                    confidence=0.72,
                )
                self.db.add(candidate)
                await self.db.commit()
                await self.db.refresh(candidate)
            yield _sse(
                "memory.candidate",
                {
                    "id": candidate.id,
                    "category": candidate.category,
                    "content": candidate.content,
                    "confidence": candidate.confidence,
                },
            )

    async def update_memory(self, user: User, memory_id: int, payload: MemoryUpdate) -> UserMemory:
        memory = await self._require_pending_memory(user.id, memory_id)
        memory.content = payload.content.strip()
        await self.db.commit()
        await self.db.refresh(memory)
        return memory

    async def confirm_memory(self, user: User, memory_id: int) -> UserMemory:
        memory = await self._require_pending_memory(user.id, memory_id)
        memory.confirmation_status = CONFIRMED
        memory.is_enabled = True
        await self._complete_onboarding(user.id, memory.spirit_id)
        await self.db.commit()
        await self.db.refresh(memory)
        return memory

    async def discard_memory(self, user: User, memory_id: int) -> UserMemory:
        memory = await self._require_pending_memory(user.id, memory_id)
        memory.confirmation_status = DISCARDED
        await self._complete_onboarding(user.id, memory.spirit_id)
        await self.db.commit()
        await self.db.refresh(memory)
        return memory

    async def _get_spirit_or_none(self, user_id: int) -> AiSpirit | None:
        result = await self.db.execute(select(AiSpirit).where(AiSpirit.user_id == user_id))
        return result.scalar_one_or_none()

    async def _require_spirit(self, user_id: int) -> AiSpirit:
        spirit = await self._get_spirit_or_none(user_id)
        if spirit is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Spirit not found")
        return spirit

    async def _latest_session(self, spirit_id: int, user_id: int, session_type: str) -> AiSpiritSession | None:
        result = await self.db.execute(
            select(AiSpiritSession)
            .where(AiSpiritSession.spirit_id == spirit_id)
            .where(AiSpiritSession.user_id == user_id)
            .where(AiSpiritSession.session_type == session_type)
            .order_by(AiSpiritSession.id.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def _conversation_session(self, user_id: int, spirit_id: int, session_type: str) -> AiSpiritSession:
        session = await self._latest_session(spirit_id, user_id, session_type)
        if session is not None:
            return session
        session = AiSpiritSession(user_id=user_id, spirit_id=spirit_id, session_type=session_type)
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def _require_session(self, user_id: int, session_id: int) -> AiSpiritSession:
        result = await self.db.execute(
            select(AiSpiritSession).where(AiSpiritSession.id == session_id).where(AiSpiritSession.user_id == user_id)
        )
        session = result.scalar_one_or_none()
        if session is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
        return session

    async def _history(self, session_id: int) -> list[dict[str, str]]:
        result = await self.db.execute(
            select(AiSpiritMessage).where(AiSpiritMessage.session_id == session_id).order_by(AiSpiritMessage.id.desc()).limit(12)
        )
        messages = list(reversed(result.scalars().all()))
        return [{"role": message.role, "content": message.content} for message in messages]

    async def _onboarding_answers(self, session_id: int) -> list[str]:
        result = await self.db.execute(
            select(AiSpiritMessage)
            .where(AiSpiritMessage.session_id == session_id)
            .where(AiSpiritMessage.role == "USER")
            .order_by(AiSpiritMessage.id)
        )
        return [message.content for message in result.scalars()]

    async def _pending_memory(self, user_id: int, spirit_id: int) -> UserMemory | None:
        result = await self.db.execute(
            select(UserMemory)
            .where(UserMemory.user_id == user_id)
            .where(UserMemory.spirit_id == spirit_id)
            .where(UserMemory.confirmation_status == PENDING)
            .order_by(UserMemory.id.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def _require_pending_memory(self, user_id: int, memory_id: int) -> UserMemory:
        result = await self.db.execute(
            select(UserMemory)
            .where(UserMemory.id == memory_id)
            .where(UserMemory.user_id == user_id)
            .where(UserMemory.confirmation_status == PENDING)
        )
        memory = result.scalar_one_or_none()
        if memory is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pending memory not found")
        return memory

    async def _complete_onboarding(self, user_id: int, spirit_id: int) -> None:
        session = await self._latest_session(spirit_id, user_id, ONBOARDING)
        if session is not None:
            session.status = COMPLETED


def _sse(event: str, data: dict[str, object]) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
