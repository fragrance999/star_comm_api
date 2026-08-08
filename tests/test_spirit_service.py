import asyncio
import json

import pytest
from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db.base import Base
from app.models.spirit import UserMemory
from app.models.user import User
from app.schemas.spirit import SpiritCreate, SpiritMessageRequest, SpiritUpdate
from app.services.spirit import CONFIRMED, SpiritService
from app.services.spirit_ai import LocalSpiritAiProvider


def test_onboarding_creates_and_confirms_a_candidate_memory(monkeypatch: pytest.MonkeyPatch) -> None:
    async def scenario() -> None:
        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        session_factory = async_sessionmaker(engine, expire_on_commit=False)

        async with session_factory() as db:
            user = User(
                account="spirit-test@example.com",
                password_hash="not-used",
                nickname="测试用户",
                birth_year=1998,
                accepted_terms=True,
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)

            service = SpiritService(db)
            state = await service.create(user, SpiritCreate())
            assert state["spirit"] is not None
            assert state["spirit"].name == "星灵"
            assert state["onboarding_completed"] is False

            for answer in ("有共同爱好的搭子", "自然随意地聊", "看书听歌"):
                events = [event async for event in service.stream_message(user, SpiritMessageRequest(content=answer), onboarding=True)]
                assert events[0].startswith("event: message.start")
                delta_events = [event for event in events if event.startswith("event: message.delta")]
                assert len(delta_events) > 1
                assert events[-2].startswith("event: message.complete") or events[-1].startswith("event: message.complete")

            candidate_event = next(event for event in events if event.startswith("event: memory.candidate"))
            candidate_data = json.loads(next(line[6:] for line in candidate_event.splitlines() if line.startswith("data: ")))
            memory = await service.confirm_memory(user, int(candidate_data["id"]))
            assert memory.confirmation_status == CONFIRMED
            assert (await service.state(user))["onboarding_completed"] is True

        await engine.dispose()

    monkeypatch.setattr("app.services.spirit.get_spirit_ai_provider", lambda: LocalSpiritAiProvider())
    asyncio.run(scenario())


def test_spirit_name_can_be_created_and_updated() -> None:
    async def scenario() -> None:
        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        session_factory = async_sessionmaker(engine, expire_on_commit=False)

        async with session_factory() as db:
            user = User(account="name@example.com", password_hash="x", nickname="命名用户", birth_year=1994, accepted_terms=True)
            db.add(user)
            await db.commit()
            await db.refresh(user)

            service = SpiritService(db)
            state = await service.create(user, SpiritCreate(name="  小星  "))
            assert state["spirit"] is not None
            assert state["spirit"].name == "小星"

            spirit = await service.update(user, SpiritUpdate(name="夜航星"))
            assert spirit.name == "夜航星"

            other = User(account="other-name@example.com", password_hash="x", nickname="其他用户", birth_year=1993, accepted_terms=True)
            db.add(other)
            await db.commit()
            await db.refresh(other)
            with pytest.raises(HTTPException) as error:
                await service.update(other, SpiritUpdate(name="无权修改"))
            assert error.value.status_code == 404

        await engine.dispose()

    asyncio.run(scenario())


def test_spirit_name_rejects_blank_and_too_long_values() -> None:
    with pytest.raises(ValidationError):
        SpiritCreate(name="   ")
    with pytest.raises(ValidationError):
        SpiritUpdate(name="星" * 17)


def test_sse_response_disables_proxy_transforms() -> None:
    from app.api.v1.spirit import _stream_response

    async def stream():
        yield "event: message.start\\ndata: {}\\n\\n"

    response = _stream_response(stream())
    assert response.headers["cache-control"] == "no-cache, no-transform"
    assert response.headers["x-accel-buffering"] == "no"


def test_pending_memory_cannot_be_read_or_changed_by_another_user() -> None:
    async def scenario() -> None:
        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        session_factory = async_sessionmaker(engine, expire_on_commit=False)

        async with session_factory() as db:
            owner = User(account="owner@example.com", password_hash="x", nickname="拥有者", birth_year=1997, accepted_terms=True)
            other = User(account="other@example.com", password_hash="x", nickname="其他人", birth_year=1996, accepted_terms=True)
            db.add_all([owner, other])
            await db.commit()
            await db.refresh(owner)
            await db.refresh(other)
            service = SpiritService(db)
            await service.create(owner, SpiritCreate())
            spirit = (await service.state(owner))["spirit"]
            assert spirit is not None
            memory = UserMemory(user_id=owner.id, spirit_id=spirit.id, category="SOCIAL_GOAL", content="仅归属拥有者")
            db.add(memory)
            await db.commit()
            await db.refresh(memory)

            with pytest.raises(HTTPException) as error:
                await service.confirm_memory(other, memory.id)
            assert error.value.status_code == 404

        await engine.dispose()

    asyncio.run(scenario())


def test_risky_message_returns_safe_stream_without_memory(monkeypatch: pytest.MonkeyPatch) -> None:
    async def scenario() -> None:
        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        session_factory = async_sessionmaker(engine, expire_on_commit=False)

        async with session_factory() as db:
            user = User(account="safe@example.com", password_hash="x", nickname="安全用户", birth_year=1995, accepted_terms=True)
            db.add(user)
            await db.commit()
            await db.refresh(user)
            service = SpiritService(db)
            await service.create(user, SpiritCreate())
            events = [
                event
                async for event in service.stream_message(user, SpiritMessageRequest(content="我不想活了"), onboarding=True)
            ]
            assert any(event.startswith("event: error") for event in events)
            assert not any(event.startswith("event: memory.candidate") for event in events)

        await engine.dispose()

    monkeypatch.setattr("app.services.spirit.get_spirit_ai_provider", lambda: LocalSpiritAiProvider())
    asyncio.run(scenario())
