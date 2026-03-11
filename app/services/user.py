from fastapi import HTTPException, status
from app.models.user import UserDAO
from app.services.auth import AuthService
from app.schemas.users import UserRegisterModel, UserResponseModel, UserUpdateModel

class UserService:
    def __init__(self, user_dao: UserDAO, auth_service: AuthService):
        self.user_dao = user_dao
        self.auth_service = auth_service

    async def register_user(self, user_data: UserRegisterModel) -> UserResponseModel:
        existing_user = await self.user_dao.get_user_by_email(user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='The users email address already exists.'
            )

        hashed_password = await self.auth_service.hash_password(
            user_data.password.get_secret_value()
        )

        user_dict = user_data.model_dump(exclude={'password'})
        user_dict['hashed_password'] = hashed_password

        user_id = await self.user_dao.create_user(user_dict)
        new_user = await self.user_dao.get_user_by_id(user_id)

        return UserResponseModel.model_validate(new_user, from_attributes=True)

    async def authenticate_user(self, email: str, password: str):
        user = await self.user_dao.get_user_by_email(email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='User does not exist'
            )

        is_valid = await self.auth_service.verify_password(password, user.get('hashed_password'))

        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Email or password is incorrect'
            )

        return user

    async def get_user_by_id(self, user_id: str):
        user = await self.user_dao.get_user_by_id(user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='The id is incorrect'
            )

        return UserResponseModel.model_validate(user, from_attributes=True)

    async def update_user(self, user_id: str, user_data: UserUpdateModel):
        data_dict = user_data.model_dump(exclude_none=True)

        if 'password' in data_dict:
            if user_data.password is not None:
                raw_password = user_data.password.get_secret_value()
                data_dict['hashed_password'] = await self.auth_service.hash_password(raw_password)
            del data_dict['password']

        updated_user = await self.user_dao.update_user(user_id, data_dict)

        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='User not found'
            )

        return UserResponseModel.model_validate(updated_user, from_attributes=True)

    async def delete_user(self, user_id: str) -> bool:
        return await self.user_dao.delete_user(user_id)