from fastapi import APIRouter, Depends, Query, status
from app.api.deps import require_admin
from app.dependency_container.activation_code_deps import get_activation_code_service
from app.schemas.activation_code import ActivationCodeCreateModel, ActivationCodeModelResponse, CodeFiltersResponse, GetActivationCodesResponseModel
from app.schemas.users import GetUsersResponseModel, UserFilterModel, UserResponseModel
from app.dependency_container.users_deps import get_user_service
from app.services.activation_code import ActivationCodeService
from app.services.user import UserService

admin_route = APIRouter(tags=['Admins'])

@admin_route.put('/users/{user_id}/ban', response_model=UserResponseModel, status_code=status.HTTP_200_OK)
async def ban_user(
    user_id: str,
    current_user: UserResponseModel = Depends(require_admin),
    user_service: UserService = Depends(get_user_service)
):
    return await user_service.set_ban_user(user_id=user_id, is_banned=True)

@admin_route.put('/users/{user_id}/unban', response_model=UserResponseModel, status_code=status.HTTP_200_OK)
async def unban_user(
    user_id: str,
    current_user: UserResponseModel = Depends(require_admin),
    user_service: UserService = Depends(get_user_service)
):
    return await user_service.set_ban_user(user_id=user_id, is_banned=False)

@admin_route.post('/activation-code', response_model=ActivationCodeModelResponse, status_code=status.HTTP_201_CREATED)
async def create_activation_code(
    request: ActivationCodeCreateModel,
    current_user: UserResponseModel = Depends(require_admin),
    service: ActivationCodeService = Depends(get_activation_code_service)
):

    return await service.create_code(role=request.role, code=request.code)

@admin_route.get('/activation-code', response_model=GetActivationCodesResponseModel, status_code=status.HTTP_200_OK)
async def get_activation_codes(
    filters: CodeFiltersResponse = Depends(),
    skip: int = 0,
    limit: int = 100,
    current_user: UserResponseModel = Depends(require_admin),
    service: ActivationCodeService = Depends(get_activation_code_service)
):
    return await service.get_codes(
        skip=skip,
        limit=limit,
        filters=filters
    )

@admin_route.delete('/activation-code/{code_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_activation_code(
    code_id: str,
    current_user: UserResponseModel = Depends(require_admin),
    service: ActivationCodeService = Depends(get_activation_code_service)
):
    await service.delete_code(code_id=code_id)

@admin_route.get('/users', response_model=GetUsersResponseModel)
async def get_all_users(
    skip: int = 0,
    limit: int = 100,
    filters: UserFilterModel = Depends(),
    current_user: UserResponseModel = Depends(require_admin),
    service: UserService = Depends(get_user_service)
):
    return await service.get_users(
        skip=skip,
        limit=limit,
        filter_obj=filters.model_dump()
    )