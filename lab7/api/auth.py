from fastapi import APIRouter, Depends, HTTPException, status

from api.dependencies import get_auth_service, get_current_user
from models.user import User
from schemas.auth import RefreshRequest, TokenPair, UserCreate, UserLogin, UserResponse
from services.auth_service import (
    AuthError,
    AuthService,
    CredentialsError,
    UserAlreadyExistsError,
)

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Зареєструвати нового користувача",
)
async def register(
    data: UserCreate,
    service: AuthService = Depends(get_auth_service),
) -> UserResponse:
    try:
        user = await service.register(data)
    except UserAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    return UserResponse.model_validate(user)


@router.post(
    "/login",
    response_model=TokenPair,
    status_code=status.HTTP_200_OK,
    summary="Отримати пару (access + refresh) за username/password",
)
async def login(
    data: UserLogin,
    service: AuthService = Depends(get_auth_service),
) -> TokenPair:
    try:
        access, refresh = await service.login(data)
    except CredentialsError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        )
    return TokenPair(access_token=access, refresh_token=refresh)


@router.post(
    "/refresh",
    response_model=TokenPair,
    status_code=status.HTTP_200_OK,
    summary="Обміняти refresh-токен на нову пару (refresh token rotation)",
)
async def refresh_tokens(
    body: RefreshRequest,
    service: AuthService = Depends(get_auth_service),
) -> TokenPair:
    try:
        access, refresh = await service.refresh(body.refresh_token)
    except AuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        )
    return TokenPair(access_token=access, refresh_token=refresh)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Відкликати refresh-токен (logout з цього пристрою)",
)
async def logout(
    body: RefreshRequest,
    service: AuthService = Depends(get_auth_service),
) -> None:
    await service.logout(body.refresh_token)
    return None


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Інформація про поточного користувача (потрібен access-токен)",
)
async def get_me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse.model_validate(current_user)
