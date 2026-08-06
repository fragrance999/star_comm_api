from pydantic import BaseModel, Field, model_validator


class RegisterRequest(BaseModel):
    account: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=8, max_length=128)
    nickname: str = Field(min_length=2, max_length=20)
    birth_year: int = Field(ge=1900, le=2100)
    avatar_url: str | None = None
    invite_code: str | None = Field(default=None, max_length=64)
    accepted_terms: bool

    @model_validator(mode="after")
    def validate_account(self) -> "RegisterRequest":
        if "@" in self.account and "." not in self.account.rsplit("@", maxsplit=1)[-1]:
            raise ValueError("Invalid email account")
        return self


class LoginRequest(BaseModel):
    account: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=8, max_length=128)


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=10)


class LogoutRequest(BaseModel):
    refresh_token: str = Field(min_length=10)


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
