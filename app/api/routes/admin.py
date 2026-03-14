from fastapi import APIRouter, Depends, Query, status
from app.api.deps import require_admin
from app.schemas.users import UserResponseModel
from app.dependency_container.users_deps import get_user_service
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