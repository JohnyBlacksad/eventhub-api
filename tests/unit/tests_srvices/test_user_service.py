"""Тесты на UserService — бизнес-логика пользователей.

Модуль содержит тесты для покрытия всех методов UserService:
- register_user() — регистрация
- authenticate_user() — аутентификация
- get_user_by_id() — получение по ID
- get_users() — список пользователей с фильтрами
- update_user() — обновление профиля
- delete_user() — удаление аккаунта
- upgrade_role() — повышение роли по коду
- set_ban_user() — бан/разбан
- change_user_role() — смена роли админом
"""

import allure
from fastapi import HTTPException
import pytest

from app.schemas.users import UserFilterModel
from app.schemas.activation_code import ActivationCodeModelResponse
from app.schemas.enums.user_enums.users_status import UserRoleEnum
from app.schemas.users import GetUsersResponseModel, UserResponseModel
from app.services.event import EventService
from app.services.user import UserService
from tests.core.user_data_factory.fake_user_data import faker
from tests.core.const.mark_enums import (
    FeaturesUserMark,
    ModuleMarks,
    ServicesMark,
    tag,
    MarkTests,
    )


@tag(MarkTests.UNITS)
@tag(ModuleMarks.SERVICES)
@tag(ServicesMark.USERS)
@pytest.mark.asyncio
class TestUserService:

    @allure.title('Регистрация пользователя')
    @tag(FeaturesUserMark.CREATE_USER)
    async def test_register_user_creates_user(
        self,
        user_service: UserService
    ):

        user = faker.get_user_register_model()

        with allure.step(f'Запрос на регистрацию пользователя'):
            registered_user = await user_service.register_user(user)

        with allure.step('Проверка данных созданного пользователя'):
            assert isinstance(registered_user, UserResponseModel)
            assert registered_user.id is not None
            assert registered_user.email == user.email
            assert registered_user.first_name == user.first_name
            assert registered_user.last_name == user.last_name
            assert registered_user.phone_number == user.phone_number
            assert registered_user.created_at
            assert not registered_user.is_banned
            assert registered_user.role == UserRoleEnum.USER

    @allure.title('Попытка регистрации уже зарегистрированного пользователя')
    @tag(FeaturesUserMark.CREATE_USER)
    async def test_register_duplicate_user(self, user_service: UserService, created_user):

        user, *_ = created_user

        with allure.step('Проверка возбуждения ошибки при попытке регистрации дубликата'):
            with pytest.raises(HTTPException) as err:
                await user_service.register_user(user)

            assert err.value.status_code == 400
            assert 'already exists' in err.value.detail

    @allure.title('Авторизация пользователя')
    @tag(FeaturesUserMark.AUTH_USER)
    async def test_authorization_user(self, user_service: UserService, created_user):

        user, password = created_user
        user_email = user.email

        with allure.step('Запрос на авторизацию пользователя'):
            auth_user = await user_service.authenticate_user(
                email=user_email,
                password=password
            )

        with allure.step('Проверка вернувшегося документа пользователя'):
            assert auth_user
            assert str(auth_user['_id']) == user.id
            assert auth_user['email'] == user.email
            assert auth_user['first_name'] == user.first_name
            assert auth_user['last_name'] == user.last_name

    @allure.title('Попытка авторизации несуществующего пользователя')
    @tag(FeaturesUserMark.AUTH_USER)
    async def test_authorization_fake_user(self, user_service: UserService):

        email = faker.faker.email()
        password = faker.faker.uuid4()

        with allure.step('Проверка возбуждения ошибки несуществующего пользователя'):
            with pytest.raises(HTTPException) as err:
                await user_service.authenticate_user(email=email, password=password)

            assert err.value.status_code == 404
            assert 'not exist' in err.value.detail

    @allure.title('Проверка авторизации с некорректным паролем')
    @tag(FeaturesUserMark.AUTH_USER)
    async def test_authorizate_wrong_password(self, user_service: UserService, created_user):
        user, *_ = created_user
        email = user.email
        password = faker.faker.uuid4()

        with allure.step('Проверка возбуждения ошибки при вводе некорректного пароля'):
            with pytest.raises(HTTPException) as err:
                await user_service.authenticate_user(email=email, password=password)

            assert err.value.status_code == 400
            assert 'password is incorrect' in err.value.detail

    @allure.title('Проверка попытки авторизации забаненого пользователя')
    @tag(FeaturesUserMark.AUTH_USER)
    async def test_authorizate_banned_user(self, user_service: UserService, banned_user):
        user, password = banned_user

        with allure.step('Проверка возбуждения ошибки авторизации забанненого пользователя'):
            with pytest.raises(HTTPException) as err:
                await user_service.authenticate_user(user.email, password)

            assert err.value.status_code == 403
            assert 'User is banned' in err.value.detail

    @allure.title('Получение пользователя по существующему id')
    @tag(FeaturesUserMark.GET_USER)
    async def test_get_user_by_id(self, user_service: UserService, created_user):
        user, *_ = created_user
        user_id = user.id

        with allure.step('Запрос на получение пользователя по id'):
            return_user = await user_service.get_user_by_id(user_id)

        with allure.step('Проверка вернувшихся данных пользователя'):

            assert isinstance(return_user, UserResponseModel)
            assert return_user.id == user_id
            assert return_user.first_name == user.first_name
            assert return_user.last_name == user.last_name
            assert return_user.phone_number == user.phone_number
            assert return_user.role == user.role
            assert not return_user.is_banned

    @allure.title('Проверка получения пользователя по несуществуюшему id')
    @tag(FeaturesUserMark.GET_USER)
    async def test_get_user_by_fake_id(self, user_service: UserService):

        user_id = faker.generate_user_id()

        with allure.step('Проверка возбуждения ошибки несуществующего пользователя'):
            with pytest.raises(HTTPException) as err:
                await user_service.get_user_by_id(user_id)

            assert err.value.status_code == 404
            assert 'id is incorrect' in err.value.detail

    @allure.title('Обновление данных существующего пользователя')
    @tag(FeaturesUserMark.UPDATE_USER)
    async def test_update_user_data(self, user_service: UserService, created_user):
        user, *_ = created_user
        updated_data = faker.get_update_user_model()

        with allure.step('Запрос на обновление данных существующего пользователя'):
            updated_user = await user_service.update_user(user.id, updated_data)

        with allure.step('Проверка вернувшихся обновленных данных пользователя'):

            assert isinstance(updated_user, UserResponseModel)
            assert updated_user.id == user.id
            assert updated_user.first_name == updated_data.first_name
            assert updated_user.last_name == updated_data.last_name
            assert updated_user.phone_number == updated_data.phone_number
            assert updated_user.email == updated_data.email
            assert updated_user.role == user.role
            assert updated_user.is_banned == user.is_banned

    @allure.title('Попытка обновления данных несуществующего пользователя')
    @tag(FeaturesUserMark.UPDATE_USER)
    async def test_update_data_for_nonexistent_user(self, user_service: UserService):
        user_id = faker.generate_user_id()
        updated_data = faker.get_update_user_model()

        with allure.step('Проверка возбуждения ошибки при попытке обновления несуществующего пользователя'):
            with pytest.raises(HTTPException) as err:
                await user_service.update_user(user_id, updated_data)

            assert err.value.status_code == 404
            assert 'not found' in err.value.detail

    @allure.title('Удаление пользователя без активных событий')
    @tag(FeaturesUserMark.DELETE_USER)
    async def test_delete_user_without_event(self, user_service: UserService, created_user):

        user, *_ = created_user

        with allure.step('Запрос на удаление пользователя'):
            is_deleted = await user_service.delete_user(user.id)

        with allure.step('Проверка статуса удаления'):
            assert is_deleted

    @allure.title('Удаление пользователя с активными событиями')
    @tag(FeaturesUserMark.DELETE_USER)
    async def test_delete_user_with_event(self, user_service: UserService, created_user_with_event):

        user, *_ = created_user_with_event

        with allure.step('Проверка возбуждения ошибки при попытке удаления пользователя с активным евентом'):
            with pytest.raises(HTTPException) as err:
                await user_service.delete_user(user.id)

            assert err.value.status_code == 400
            assert 'not delete' in err.value.detail

    @allure.title('Удаление несуществующего пользователя')
    @tag(FeaturesUserMark.DELETE_USER)
    async def test_delete_fake_user(self, user_service: UserService):

        user_id = faker.generate_user_id()

        with allure.step('Проверка возбуждения ошибки при попытке удаления фейк пользователя'):
            with pytest.raises(HTTPException) as err:
                await user_service.delete_user(user_id)

            assert err.value.status_code == 404
            assert 'not found' in err.value.detail

    @allure.title('Обновление роли пользователя до организатора с помощью кода активации')
    @tag(FeaturesUserMark.UPDATE_ROLE)
    async def test_upgrade_role_to_organizer(
        self,
        user_service: UserService,
        created_user,
        organizer_code: ActivationCodeModelResponse
    ):
        user, *_ = created_user
        code = organizer_code.code

        with allure.step('Запрос на обновление роли пользователя с помощью кода активации'):
            updated_user = await user_service.upgrade_role(user.id, code)

        with allure.step('Проверка обновленных данных пользователя'):
            assert updated_user.id == user.id
            assert updated_user.role != user.role
            assert updated_user.role == UserRoleEnum.ORGANIZER

    @allure.title('Обновление роли пользователя до администратора с помощью кода активации')
    @tag(FeaturesUserMark.UPDATE_ROLE)
    async def test_upgrade_role_to_admin(
        self,
        user_service: UserService,
        created_user,
        admin_code: ActivationCodeModelResponse
    ):
        user, *_ = created_user
        code = admin_code.code

        with allure.step('Запрос на обновление роли пользователя с помощью кода активации'):
            updated_user = await user_service.upgrade_role(user.id, code)

        with allure.step('Проверка обновленных данных пользователя'):
            assert updated_user.id == user.id
            assert updated_user.role != user.role
            assert updated_user.role == UserRoleEnum.ADMIN

    @allure.title('Попытка обновления роли пользователя с помощью использованного кода активации')
    @tag(FeaturesUserMark.UPDATE_ROLE)
    async def test_upgrade_role_with_code_deactivated(
        self,
        user_service: UserService,
        created_user,
        admin_code: ActivationCodeModelResponse,
        organizer_code: ActivationCodeModelResponse
    ):
        user, *_ = created_user
        org_code = organizer_code.code
        adm_code = admin_code.code
        await user_service.upgrade_role(user.id, org_code)
        await user_service.upgrade_role(user.id, adm_code)

        with allure.step('Проверка возбуждения ошибки использованного кода'):
            with pytest.raises(HTTPException) as err:
                await user_service.upgrade_role(user_id=user.id, code_str=org_code)

            assert err.value.status_code == 403
            assert 'Invalid or expired activation code' in err.value.detail

    @allure.title('Попытка обновления роли пользователя с помощью фейкового кода активации')
    @tag(FeaturesUserMark.UPDATE_ROLE)
    async def test_upgrade_role_with_fake_code(
        self,
        user_service: UserService,
        created_user,
    ):
        user, *_ = created_user
        code = faker.faker.uuid4()

        with allure.step('Проверка возбуждения ошибки невалидного кода'):
            with pytest.raises(HTTPException) as err:
                await user_service.upgrade_role(user_id=user.id, code_str=code)

            assert err.value.status_code == 403
            assert 'Invalid or expired activation code' in err.value.detail

    @allure.title('Попытка обновления роли несуществующего пользователя с помощью кода активации')
    @tag(FeaturesUserMark.UPDATE_ROLE)
    async def test_upgrade_role_with_code_for_fake_user(
        self,
        user_service: UserService,
        organizer_code: ActivationCodeModelResponse,
    ):
        user_id = faker.generate_user_id()
        code = organizer_code.code

        with allure.step('Проверка возбуждения ошибки невалидного кода'):
            with pytest.raises(HTTPException) as err:
                await user_service.upgrade_role(user_id, code)

            assert err.value.status_code == 404
            assert 'User not found' in err.value.detail

    @allure.title('Установка статуса "забанен" у существующего пользователя')
    @tag(FeaturesUserMark.BAN_USER)
    async def test_set_ban_created_user(self, user_service: UserService, created_user):
        user, *_ = created_user

        with allure.step('Запрос на обновление статуса "забанен" пользователя'):
            updated_user = await user_service.set_ban_user(user.id, True)

        with allure.step('Проверка возвращенных данных пользователя'):
            assert updated_user
            assert updated_user.id == user.id
            assert updated_user.is_banned != user.is_banned

    @allure.title('Установка статуса "забанен" у существующего пользователя')
    @tag(FeaturesUserMark.BAN_USER)
    async def test_set_ban_fake_user(self, user_service: UserService):
        user_id = faker.generate_user_id()

        with allure.step('Проверка возбуждения ошибки при попытке передачи несуществующего id'):
            with pytest.raises(HTTPException) as err:
                await user_service.set_ban_user(user_id, True)

            assert err.value.status_code == 404
            assert 'not found' in err.value.detail

    @allure.title('Обновление роли на организатора существующего пользователя с помощью "админ" метода')
    @tag(FeaturesUserMark.UPDATE_ROLE)
    async def test_update_role_user_with_admin_method(self, user_service: UserService, created_user):
        user, *_ = created_user

        with allure.step('Запрос на обвновление роли пользователя на организатора'):
            updated_user = await user_service.change_user_role(user.id, UserRoleEnum.ORGANIZER)

        with allure.step('Проверка вернувшихся данных пользователя'):

            assert updated_user.id == user.id
            assert updated_user.role != user.role
            assert updated_user.role == UserRoleEnum.ORGANIZER

    @allure.title('Обновление роли на админа существующего пользователя с помощью "админ" метода')
    @tag(FeaturesUserMark.UPDATE_ROLE)
    async def test_update_role_admin_user_with_admin_method(self, user_service: UserService, created_user):
        user, *_ = created_user

        with allure.step('Запрос на обвновление роли пользователя на админа'):
            updated_user = await user_service.change_user_role(user.id, UserRoleEnum.ADMIN)

        with allure.step('Проверка вернувшихся данных пользователя'):

            assert updated_user.id == user.id
            assert updated_user.role != user.role
            assert updated_user.role == UserRoleEnum.ADMIN

    @allure.title('Обновление роли несуществующего пользователя с помощью "админ" метода')
    @tag(FeaturesUserMark.UPDATE_ROLE)
    async def test_update_role_existing_user_with_admin_method(self, user_service: UserService):
        user_id = faker.generate_user_id()

        with allure.step('Проверка возбуждения ошибки при попытке передать несуществующий ID пользователя'):
            with pytest.raises(HTTPException) as err:
                await user_service.change_user_role(user_id, UserRoleEnum.ORGANIZER)

            assert err.value.status_code == 404
            assert 'not found' in err.value.detail

    @allure.title('Удаление пользователя с помощью "админ" метода')
    @tag(FeaturesUserMark.DELETE_USER)
    async def test_delete_user_with_admin_method(self, user_service: UserService, created_user):

        user, *_ = created_user

        with allure.step('Запрос на удаление пользователя'):
            is_deleted = await user_service.delete_user_by_admin(user.id)

        with allure.step('Проверка вернувшегося статуса'):
            assert is_deleted

            with pytest.raises(HTTPException) as err:
                await user_service.get_user_by_id(user.id)

            assert err.value.status_code == 404
            assert 'id is incorrect' in err.value.detail

    @allure.title('Удаление пользователя c активными ивентами с помощью "админ" метода')
    @tag(FeaturesUserMark.DELETE_USER)
    async def test_delete_user_with_publish_event_admin_method(self, user_service: UserService, created_user_with_event):

        user, *_ = created_user_with_event

        with allure.step('Запрос на удаление пользователя'):
            is_deleted = await user_service.delete_user_by_admin(user.id)

        with allure.step('Проверка вернувшегося статуса'):
            assert is_deleted

            with pytest.raises(HTTPException) as err:
                await user_service.get_user_by_id(user.id)

            assert err.value.status_code == 404
            assert 'id is incorrect' in err.value.detail

    @allure.title('Удаление фейкового пользователя с помощью "админ" метода')
    @tag(FeaturesUserMark.DELETE_USER)
    async def test_fake_delete_user_admin_method(self, user_service: UserService):

        user_id = faker.generate_user_id()

        with allure.step('Запрос на удаление пользователя'):

            with pytest.raises(HTTPException) as err:
                await user_service.delete_user_by_admin(user_id)

            assert err.value.status_code == 404
            assert 'User not found' in err.value.detail

    @allure.title("Получение списка пользователей без фильтров")
    @tag(FeaturesUserMark.GET_USERS)
    async def test_get_users_no_filters(
        self,
        user_service: UserService,
        created_user
    ):
        with allure.step('Запрос на получение списка пользователей'):
            result = await user_service.get_users(skip=0, limit=10)

        with allure.step('Проверка списка пользователей'):
            assert isinstance(result, GetUsersResponseModel)
            assert len(result.users) >= 1
            assert isinstance(result.users[0], UserResponseModel)


    @allure.title("Получение списка пользователей с пагинацией")
    @tag(FeaturesUserMark.GET_USERS)
    async def test_get_users_with_pagination(
        self,
        user_service: UserService,
        multiple_users
    ):

        with allure.step('Запрос на получение списка пользователей с пагинацией'):
            result_page1 = await user_service.get_users(skip=0, limit=5)
            result_page2 = await user_service.get_users(skip=5, limit=5)

        with allure.step('Проверка пагинации'):
            assert len(result_page1.users) == 5
            assert len(result_page2.users) == 5
            assert result_page1.users[0].id != result_page2.users[0].id

    @allure.title("Получение пользователей с фильтром по роли 'Организатор'")
    @tag(FeaturesUserMark.GET_USERS)
    async def test_get_users_filter_by_role(
        self,
        user_service: UserService,
        created_user,
        organizer_user: UserResponseModel,
        admin_user: UserResponseModel
    ):

        filter_obj = UserFilterModel(role=UserRoleEnum.ORGANIZER)

        with allure.step('Запрос на получение списка пользователей с фильтром по роли "Организатор"'):
            result = await user_service.get_users(skip=0, limit=10, filter_obj=filter_obj) # type: ignore

        with allure.step('Проверка фильтрации по роли "Организатор"'):
            assert len(result.users) >= 1
            for user in result.users:
                assert user.role == UserRoleEnum.ORGANIZER

    @allure.title("Получение пользователей с фильтром по статусу бана")
    @tag(FeaturesUserMark.GET_USERS)
    async def test_get_users_filter_by_banned(
        self,
        user_service: UserService,
        created_user,
        banned_user
    ):

        filter_obj = {"is_banned": True}

        with allure.step('Запрос на получение списка пользователей с фильтром по cтатусу is_banned'):
            result = await user_service.get_users(skip=0, limit=10, filter_obj=filter_obj)

        with allure.step('Проверка фильтрации по cтатусу is_banned'):
            assert len(result.users) >= 1
            assert all(user.is_banned is True for user in result.users)

    @allure.title("Получение пустого списка пользователей")
    @tag(FeaturesUserMark.GET_USERS)
    async def test_get_users_empty_list(
        self,
        user_service: UserService
    ):

        with allure.step('Запрос на получение списка пользователей в пустую БД без фильтров'):
            result = await user_service.get_users(skip=0, limit=10)

        with allure.step('Проверка возвращения пустого списка пользователей'):
            assert isinstance(result, GetUsersResponseModel)
            assert len(result.users) == 0