import asyncio
from collections.abc import AsyncIterator

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.core.config import settings

RISK_KEYWORDS = (
    "自杀",
    "自残",
    "杀人",
    "伤害他人",
    "炸弹",
    "勒索",
    "诈骗",
    "未成年",
    "不想活",
)

PERSONA_INSTRUCTIONS = {
    "WARM_LISTENER": "语气温暖、耐心，先理解再轻柔追问。",
    "FUN_COMPANION": "语气轻松、有一点俏皮，但不油腻也不冒犯。",
    "SOCIAL_ADVISOR": "语气理性、清晰，帮助用户看见可执行的社交方向。",
    "DIRECT_FRIEND": "语气温和但直接，用简短的表达给出诚实反馈。",
}


def contains_safety_risk(content: str) -> bool:
    normalized = content.lower().replace(" ", "")
    return any(keyword in normalized for keyword in RISK_KEYWORDS)


def safe_reply() -> str:
    return "我很在意你现在的安全。请先联系你信任的家人、朋友，或当地紧急援助服务；如果你正处于紧急危险中，请立即拨打当地紧急电话。现在不需要独自承受。"


class SpiritAiProvider:
    async def stream_reply(
        self,
        *,
        persona_type: str,
        messages: list[dict[str, str]],
        onboarding_turn: int | None,
    ) -> AsyncIterator[str]:
        raise NotImplementedError


class LocalSpiritAiProvider(SpiritAiProvider):
    async def stream_reply(
        self,
        *,
        persona_type: str,
        messages: list[dict[str, str]],
        onboarding_turn: int | None,
    ) -> AsyncIterator[str]:
        if onboarding_turn == 1:
            reply = "听起来你已经有一点想靠近的人和关系了。相处时，你更喜欢对方用什么方式和你聊天？"
        elif onboarding_turn == 2:
            reply = "我记下了这种感觉。最后一个轻问题：最近有没有一件让你觉得放松或有能量的小事？"
        elif onboarding_turn and onboarding_turn >= 3:
            reply = "谢谢你愿意告诉我这些。我已经开始了解你想要怎样的连接了。"
        else:
            reply = "我在。你可以从今天最想聊的一件小事开始，也可以告诉我你现在更需要陪伴、梳理，还是一个社交方向。"

        for chunk in _chunks(reply):
            await asyncio.sleep(0)
            yield chunk


class DashScopeSpiritAiProvider(SpiritAiProvider):
    def __init__(self) -> None:
        self.model = ChatOpenAI(
            model=settings.dashscope_model,
            api_key=settings.dashscope_api_key,
            base_url=settings.dashscope_base_url,
            temperature=0.7,
            streaming=True,
        )

    async def stream_reply(
        self,
        *,
        persona_type: str,
        messages: list[dict[str, str]],
        onboarding_turn: int | None,
    ) -> AsyncIterator[str]:
        phase_hint = (
            f"这是首次访谈的第 {onboarding_turn} 轮用户回答。"
            "第 1、2 轮在共情后各追问一个简短、开放的问题；第 3 轮后简短收束，不要自行声称记住任何事实。"
            if onboarding_turn
            else "这是日常对话，回复应简短自然。"
        )
        system = SystemMessage(
            content=(
                "你是星邻社中的星灵，目标是帮助用户逐步建立真实人际连接。"
                f"{PERSONA_INSTRUCTIONS[persona_type]}{phase_hint}"
                "不得鼓励用户只依赖你，不得声称拥有真实意识或现实身份，不得给出医疗诊断。"
            )
        )
        history = [
            HumanMessage(content=item["content"]) if item["role"] == "USER" else AIMessage(content=item["content"])
            for item in messages
        ]
        async for chunk in self.model.astream([system, *history[-8:]]):
            content = _content_to_text(chunk.content)
            if content:
                yield content


def get_spirit_ai_provider() -> SpiritAiProvider:
    if settings.dashscope_api_key:
        return DashScopeSpiritAiProvider()
    return LocalSpiritAiProvider()


def _content_to_text(content: object) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(part.get("text", "") for part in content if isinstance(part, dict))
    return ""


def _chunks(content: str) -> list[str]:
    return [content[index : index + 12] for index in range(0, len(content), 12)]
