from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    """Тіло запиту POST /auth/register."""
    username: str = Field(..., min_length=3, max_length=50, description="Унікальне ім'я користувача")
    password: str = Field(..., min_length=6, max_length=128, description="Пароль (мінімум 6 символів)")


class UserLogin(BaseModel):
    """Тіло запиту POST /auth/login."""
    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=1, max_length=128)


class UserResponse(BaseModel):
    """Безпечне представлення користувача у відповідях."""
    id: str
    username: str
    is_active: bool

    model_config = {"from_attributes": True}


class TokenPair(BaseModel):
    """
    Відповідь /auth/login та /auth/refresh — пара токенів.
    """
    access_token: str = Field(..., description="Короткоживучий JWT для доступу до API")
    refresh_token: str = Field(..., description="Довгоживучий JWT для отримання нової пари токенів")
    token_type: str = Field("bearer", description="Тип схеми автентифікації")


class RefreshRequest(BaseModel):
    """Тіло запиту POST /auth/refresh."""
    refresh_token: str = Field(..., min_length=10)
