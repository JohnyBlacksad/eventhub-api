import pytest
from mongomock import DuplicateKeyError
from mongomock_motor import AsyncMongoMockCollection
from datetime import timedelta
import allure

from app.models.user import UserDAO
from app.schemas.users import UserFilterModel
from tests.core.user_data_factory.fake_user_data import faker
from app.schemas.enums.user_enums.users_status import UserRoleEnum
from tests.core.const.mark_enums import (
    MarkTests,
    ModuleMarks,
    ServicesMark,
    FeaturesUserMark,
    DataBaseFunctionMark,
    tag
)

@allure.epic("Core Modules")
@allure.feature("User Management")
@allure.story("User DAO Operations")
@tag(MarkTests.UNITS)
@tag(ModuleMarks.DAO)
@tag(ServicesMark.USERS)
@pytest.mark.asyncio
class TestUserDAO:

    @allure.title('Успешное создание пользователя и проверка контракта')
    @tag(FeaturesUserMark.CREATE_USER)
    async def test_create_user_returns_id(
        self,
        mock_user_dao: UserDAO,
        subtests
    ):
        user_data = faker.get_user_register_data_dict()

        with allure.step("Создание пользователя через DAO"):
            user_id = await mock_user_dao.create_user(user_data)

        with allure.step(f"Получение пользователя {user_id} из БД и проверка типов"):
            db_user = await mock_user_dao.get_user_by_id(user_id)

            with subtests.test(msg='Проверка данных'):
                assert isinstance(user_id, str)
                assert db_user is not None
                assert isinstance(db_user, dict)
                assert db_user['firstName'] == user_data['firstName']
                assert db_user['email'] == user_data['email']
                assert db_user['lastName'] == user_data['lastName']
                assert db_user['phoneNumber'] == user_data['phoneNumber']

    @allure.title("Ошибка при создании дубликата пользователя")
    @tag(FeaturesUserMark.CREATE_USER)
    async def test_create_user_with_duplicate_id_raises_error(self, mock_user_dao: UserDAO, created_user: dict):

        with allure.step("Попытка повторного создания пользователя с тем же ID"):
            with pytest.raises(DuplicateKeyError):
                await mock_user_dao.create_user(created_user)

    @allure.title("Поиск пользователя по ID")
    @tag(FeaturesUserMark.GET_USER)
    async def test_get_user_by_id_returns_user(
        self,
        mock_user_dao: UserDAO,
        created_user: dict,
        subtests
    ):
        user_id = created_user['_id']

        with allure.step(f'Запрос пользователя по ID: {user_id}'):
            get_user = await mock_user_dao.get_user_by_id(user_id)

        with allure.step('Проверка соответствия данных'):
            with subtests.test(msg=f'Проверка данных'):
                assert get_user is not None
                assert user_id == get_user['_id']
                assert created_user['email'] == get_user['email']
                assert created_user['firstName'] == get_user['firstName']
                assert created_user['lastName'] == get_user['lastName']
                assert created_user['phoneNumber'] == get_user['phoneNumber']

    @allure.title("Поиск несуществующего пользователя по ID возвращает None")
    @tag(FeaturesUserMark.GET_USER)
    async def test_get_user_by_id_returns_none_if_not_found(self, mock_user_dao: UserDAO):
        random_id = faker.generate_user_id()

        with allure.step(f"Запрос рандомного ID {random_id}"):
            user = await mock_user_dao.get_user_by_id(random_id)
            assert user is None

    @allure.title("Поиск существующего пользователя по Email возвращает данные пользователя")
    @tag(FeaturesUserMark.GET_USER)
    async def test_get_user_by_email_returns_user(
        self,
        mock_user_dao: UserDAO,
        created_user: dict,
        subtests,
    ):

        user_email = created_user['email']

        with allure.step(f"Запрос данных по email {user_email}"):
            db_user = await mock_user_dao.get_user_by_email(user_email)

        with subtests.test(msg='Проверка данных'):
            assert db_user is not None
            assert db_user['email'] == user_email
            assert db_user['firstName'] == created_user['firstName']
            assert db_user['lastName'] == created_user['lastName']
            assert db_user['phoneNumber'] == created_user['phoneNumber']

    @allure.title("Поиск несуществующего пользователя по Email возвращает None")
    @tag(FeaturesUserMark.GET_USER)
    async def test_get_user_by_email_returns_none_if_not_found(self, mock_user_dao: UserDAO):
        not_existing_user = faker.get_user_register_data_dict()
        not_existing_email = not_existing_user['email']

        with allure.step(f"Запрос рандомного email {not_existing_email}"):
            db_user = await mock_user_dao.get_user_by_email(not_existing_email)

        assert db_user is None

    @allure.title("Обновление данных пользователя")
    @tag(FeaturesUserMark.UPDATE_USER)
    async def test_update_user_updates_fields(
        self,
        mock_user_dao: UserDAO,
        created_user: dict,
        subtests
    ):
        created_user_id = created_user['_id']
        update_data = faker.get_user_register_data_dict()

        with allure.step(f"Вызов обновления данных пользователя {created_user_id} в DAO"):
            updated_user = await mock_user_dao.update_user(created_user_id, update_data)

        with allure.step("Проверка измененных данных"):
            with subtests.test(msg='Проверка данных'):
                assert updated_user is not None
                assert updated_user['_id'] == created_user['_id']
                assert updated_user['email'] == update_data['email']
                assert updated_user['firstName'] == update_data['firstName']
                assert updated_user['lastName'] == update_data['lastName']
                assert updated_user['phoneNumber'] == update_data['phoneNumber']

    @allure.title("Обновление данных несуществующего пользователя")
    @tag(FeaturesUserMark.UPDATE_USER)
    async def test_update_user_returns_none_if_not_found(self, mock_user_dao: UserDAO):
        user_id = faker.generate_user_id()
        update_data = faker.get_user_register_data_dict()

        with allure.step(f"Вызов обновления данных по сгенерированному ID {user_id} в DAO"):
            updated_user = await mock_user_dao.update_user(user_id, update_data)

        with allure.step("Проверка отсусвтия вернувшихся данных"):
            assert updated_user is None

    @allure.title("Удаление пользователя")
    @tag(FeaturesUserMark.DELETE_USER)
    async def test_delete_user_returns_true(self, mock_user_dao: UserDAO, created_user: dict):
        user_id = created_user['_id']

        with allure.step(f"Удаление существующего пользователя {user_id}"):
            assert await mock_user_dao.delete_user(user_id)

    @allure.title("Удаление несуществующего пользователя")
    @tag(FeaturesUserMark.DELETE_USER)
    async def test_delete_user_returns_false_if_not_found(self, mock_user_dao: UserDAO):
        not_exsiting_id = faker.generate_user_id()

        with allure.step(f"Удаление несуществующего пользователя {not_exsiting_id}"):
            assert not await mock_user_dao.delete_user(not_exsiting_id)

    @allure.title("Изменение роли у существующего пользователя")
    @tag(FeaturesUserMark.UPDATE_ROLE)
    async def test_update_user_role_updates_role(self, mock_user_dao: UserDAO, created_user: dict):
        role = faker.get_role()
        user_id = created_user['_id']

        with allure.step(f"Обновление роли у существующего пользователя {user_id} на {role}"):
            updated_user = await mock_user_dao.update_user_role(user_id, role)

        with allure.step("Проверка роли пользователя"):
            assert updated_user is not None
            assert updated_user['role'] == role

    @allure.title("Изменение роли у несуществующего пользователя")
    @tag(FeaturesUserMark.UPDATE_ROLE)
    async def test_update_user_role_raises_for_non_existing_user(self, mock_user_dao: UserDAO):
        not_existing_user = faker.generate_user_id()
        role = faker.get_role()

        with allure.step(f"Обновление роли у несуществующего пользователя {not_existing_user} на {role}"):
            updated_user = await mock_user_dao.update_user_role(not_existing_user, role)

        with allure.step("Проверка отсусвтия вернувшихся данных"):
            assert updated_user is None

    @allure.title("Изменение статуса бана у существующего пользователя")
    @tag(FeaturesUserMark.BAN_USER)
    async def test_set_ban_user_updates_is_banned(self, mock_user_dao: UserDAO, created_user):
        user_id = created_user['_id']

        with allure.step(f"Обновление роли у существующего пользователя {user_id} на is_banned = True"):
            updated_user = await mock_user_dao.set_ban_user(user_id, True)

        with allure.step("Проверка статуса бана у обновленного пользователя"):
            assert updated_user is not None
            assert updated_user['is_banned']

    @allure.title("Получение списка пользователей без фильтрации")
    @tag(FeaturesUserMark.GET_USERS)
    async def test_get_users_returns_list(
        self,
        base_users: UserDAO,
        subtests
    ):

        with allure.step('Запрос на получение списка пользователей без фильтрации'):
            user_list = await base_users.get_users()
            assert user_list

        with allure.step('Проверка данных списка пользователей'):
            for user in user_list:
                for k, _ in user.items():
                    with subtests.test(msg=f'Проверка поля {k}'):
                        assert user[k]

    @allure.title("Фильтрация пользователей по роли")
    @tag(FeaturesUserMark.GET_USERS)
    async def test_get_users_with_filter_role(self, base_users: UserDAO, created_user: dict):

        with allure.step("Смена роли пользователю"):
            await base_users.update_user_role(
            user_id=created_user['_id'],
            new_role=UserRoleEnum.ORGANIZER
            )

            with allure.step("Запрос списка с фильтром по роли ORGANIZER"):
                filter_obj = UserFilterModel(role=UserRoleEnum.ORGANIZER)
                users_list = await base_users.get_users(filter_obj=filter_obj)

            assert users_list

            for user in users_list:
                assert user['role'] == UserRoleEnum.ORGANIZER

    @allure.title("Получение списка всех пользователей доступных в БД")
    @tag(FeaturesUserMark.GET_USERS)
    async def test_get_users_specific_quantity(
        self,
        mock_user_dao: UserDAO,
        subtests
    ):

        raw_user_list = [faker.get_user_register_data_dict() for _ in range(5)]

        with allure.step(f"Запрос на создание {len(raw_user_list)} пользователей"):
            for user in raw_user_list:
                await mock_user_dao.create_user(user)

        with allure.step("Получение списка пользователей"):
            user_list = await mock_user_dao.get_users()

        with allure.step("Проверка списка пользователей"):
            assert len(user_list) == 5

            for user in user_list:
                for k, _ in user.items():
                    with subtests.test(msg=f'Проверка поля {k}'):
                        assert user[k]

    @allure.title("Фильтрация пользователей по статусу is_banned")
    @tag(FeaturesUserMark.GET_USERS)
    async def test_get_users_with_filter_is_banned(self, base_users: UserDAO, created_user: dict):
        user_id = created_user['_id']

        with allure.step(f"Смена статуса is_banned пользователю {user_id}"):
            await base_users.set_ban_user(user_id, True)

        with allure.step("Запрос списка с фильтром по статусу is_banned = True"):
            filter_obj = UserFilterModel(isBanned=True)

            users_list = await base_users.get_users(filter_obj=filter_obj)

            assert users_list

            for user in users_list:
                assert user['is_banned']


    @allure.title("Фильтрация пользователей ОТ указанной даты")
    @tag(FeaturesUserMark.GET_USERS)
    async def test_get_users_with_filter_created_at_from(
        self,
        mock_user_dao: UserDAO,
        users_with_different_dates: dict
    ):

        dao = mock_user_dao
        now = users_with_different_dates['now']

        with allure.step(f"Запрос списка с фильтром от указанной даты {now}"):
            filter_obj = UserFilterModel(created_at=now)  # type: ignore

            users = await dao.get_users(filter_obj=filter_obj)

            assert len(users) == 7

    @allure.title("Фильтрация пользователей ДО указанной даты")
    @tag(FeaturesUserMark.GET_USERS)
    async def test_get_users_with_filter_created_at_to(
        self,
        mock_user_dao: UserDAO,
        users_with_different_dates: dict
    ):
        dao = mock_user_dao
        now = users_with_different_dates['now']

        with allure.step(f"Запрос списка с фильтром до указанной даты {now}"):
            filter_obj = UserFilterModel(created_at_to=now)  # type: ignore

            users = await dao.get_users(filter_obj=filter_obj)

            assert len(users) == 8


    @allure.title("Фильтрация пользователей в диапазоне указанных дат")
    @tag(FeaturesUserMark.GET_USERS)
    async def test_get_users_with_filter_date_range(
        self,
        mock_user_dao: UserDAO,
        users_with_different_dates: dict
    ):
        dao = mock_user_dao
        now = users_with_different_dates['now']
        to = now + timedelta(seconds=5)

        filter_obj = UserFilterModel(
            created_at=now,           # type: ignore
            created_at_to=to  # type: ignore
        )
        with allure.step(f"Запрос списка с фильтром в диапазоне от {now} до {to}"):
            users = await dao.get_users(filter_obj=filter_obj)

            assert len(users) == 5

    @allure.title("Инициализация уникальных индексов для Email")
    @tag(DataBaseFunctionMark.SETUP_INDEXES)
    @tag(FeaturesUserMark.CREATE_USER)
    async def test_setup_indexes_creates_unique_email_index(self, user_collections: AsyncMongoMockCollection):

        await UserDAO.setup_indexes(user_collections)

        with allure.step("Проверка наличия уникального индекса в коллекции"):
            indexes = await user_collections.index_information()

            assert 'email_1' in indexes
            assert indexes['email_1']['unique'] is True

    @allure.title("Попытка создания дубликата пользователя по email после создания индекса")
    @tag(DataBaseFunctionMark.SETUP_INDEXES)
    @tag(FeaturesUserMark.CREATE_USER)
    async def test_create_user_with_duplicate_email_raises_error_after_setup_indexes(
        self,
        user_collections: AsyncMongoMockCollection
    ):

        await UserDAO.setup_indexes(user_collections)
        dao = UserDAO(user_collections)

        user_data = faker.get_user_register_data_dict()

        with allure.step("Попытка создания дубликата и проверка возникновении ошибки"):
            await dao.create_user(user_data)


            with pytest.raises(DuplicateKeyError):
                await dao.create_user(user_data)