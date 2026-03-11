from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.users import UserRegisterModel, UserLoginModel
from app.schemas.token import TokenModel, RefreshTokenModel
from app.depency_container.users_deps import get_auth_service, get_user_service
from app.services.auth import AuthService
from app.services.user import UserService

auth_router = APIRouter(tags=['Auth'])

@auth_router.post('/register', response_model=TokenModel)
async def register(
    user_data: UserRegisterModel,
    user_service: UserService = Depends(get_user_service),
    auth_service: AuthService = Depends(get_auth_service)
):
    user = await user_service.register_user(user_data)
    token_data = {'user_id': user.id, 'email': user.email}

    access_token = await auth_service.create_access_token(token_data)
    refresh_token = await auth_service.create_refresh_token(token_data)

    return TokenModel(
        accessToken=access_token,
        refreshToken=refresh_token
    )

@auth_router.post('/login', response_model=TokenModel)
async def login(
    login_data: UserLoginModel,
    user_service: UserService = Depends(get_user_service),
    auth_service: AuthService = Depends(get_auth_service)
):
    user = await user_service.authenticate_user(
        email=login_data.email,
        password=login_data.password.get_secret_value()
    )

    token_data = {'user_id': str(user['_id']), 'email': user['email']}
    access_token = await auth_service.create_access_token(token_data)
    refresh_token = await auth_service.create_refresh_token(token_data)

    return TokenModel(
        accessToken=access_token,
        refreshToken=refresh_token
    )

@auth_router.post('/refresh', response_model=TokenModel)
async def refresh_token(
    refresh_token: RefreshTokenModel,
    auth_service: AuthService = Depends(get_auth_service)
):
    payload = await auth_service.decode_token(refresh_token.refresh_token)
    new_access = await auth_service.create_access_token(payload)
    new_refresh = await auth_service.create_refresh_token(payload)

    return TokenModel(
        accessToken=new_access,
        refreshToken=new_refresh
    )