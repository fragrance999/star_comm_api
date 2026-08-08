from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

AppearanceType = Literal["STARLIGHT", "FOX", "OTTER", "ROBOT"]
PersonaType = Literal["WARM_LISTENER", "FUN_COMPANION", "SOCIAL_ADVISOR", "DIRECT_FRIEND"]
InitiativeLevel = Literal["PASSIVE", "OCCASIONAL", "IMPORTANT_EVENTS"]


class SpiritCreate(BaseModel):
    name: str = Field(default="星灵", min_length=1, max_length=16)
    appearance_type: AppearanceType = "STARLIGHT"
    persona_type: PersonaType = "WARM_LISTENER"
    initiative_level: InitiativeLevel = "IMPORTANT_EVENTS"

    @field_validator("name", mode="before")
    @classmethod
    def normalize_name(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value


class SpiritUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=16)
    persona_type: PersonaType | None = None
    initiative_level: InitiativeLevel | None = None

    @field_validator("name", mode="before")
    @classmethod
    def normalize_name(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value

    @model_validator(mode="after")
    def requires_change(self) -> "SpiritUpdate":
        if self.name is None and self.persona_type is None and self.initiative_level is None:
            raise ValueError("At least one setting is required")
        return self


class SpiritRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    appearance_type: AppearanceType
    persona_type: PersonaType
    initiative_level: InitiativeLevel
    status: str
    created_at: datetime


class SessionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    session_type: str
    status: str
    user_turn_count: int
    created_at: datetime


class SpiritStateRead(BaseModel):
    spirit: SpiritRead | None
    onboarding_session: SessionRead | None
    chat_session: SessionRead | None
    onboarding_completed: bool
    pending_memory: "MemoryRead | None" = None


class MessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    role: str
    content: str
    created_at: datetime


class MessageListRead(BaseModel):
    session: SessionRead
    messages: list[MessageRead]


class SpiritMessageRequest(BaseModel):
    content: str = Field(min_length=1, max_length=1000)


class MemoryUpdate(BaseModel):
    content: str = Field(min_length=2, max_length=240)


class MemoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    category: str
    content: str
    confidence: float
    confirmation_status: str
    created_at: datetime
