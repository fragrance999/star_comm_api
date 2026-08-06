from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    account: str
    nickname: str
    birth_year: int
    avatar_url: str | None
    invite_code: str | None
    status: str
    created_at: datetime
