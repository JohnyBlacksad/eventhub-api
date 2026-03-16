from mongomock import DuplicateKeyError
from mongomock_motor import AsyncMongoMockCollection
import pytest
from app.schemas.users import UserFilterModel
from tests.core.user_data_factory.fake_user_data import faker
from app.models.user import UserDAO
from app.schemas.enums.user_enums.users_status import UserRoleEnum
from datetime import datetime, timezone, timedelta
import asyncio


@pytest.mark.units
@pytest.mark.DAO
@pytest.mark.users
@pytest.mark.asyncio
class TestUserDAO:

    @pytest.mark.create_user
    async def test_create_user_returns_id(self, mock_user_dao: UserDAO):
        user_data = faker.get_user_register_data_dict()

        user_id = await mock_user_dao.create_user(user_data)
        db_user = await mock_user_dao.get_user_by_id(user_id)

        assert isinstance(user_id, str)
        assert db_user is not None
        assert isinstance(db_user, dict)
        assert db_user['firstName'] == user_data['firstName']
        assert db_user['email'] == user_data['email']

    @pytest.mark.create_user
    async def test_create_user_with_duplicate_email_raises_error(self, mock_user_dao: UserDAO, created_user: dict):

        with pytest.raises(DuplicateKeyError):
            await mock_user_dao.create_user(created_user)

    @pytest.mark.get_user
    async def test_get_user_by_id_returns_user(self, mock_user_dao: UserDAO, created_user: dict):
        user_id = created_user['_id']

        get_user = await mock_user_dao.get_user_by_id(user_id)

        assert get_user is not None
        assert user_id == get_user['_id']
        assert created_user['email'] == get_user['email']

    @pytest.mark.get_user
    async def test_get_user_by_id_returns_none_if_not_found(self, mock_user_dao: UserDAO):
        random_id = faker.generate_user_id()

        user = await mock_user_dao.get_user_by_id(random_id)

        assert user is None

    @pytest.mark.get_user
    async def test_get_user_by_email_returns_user(self, mock_user_dao: UserDAO, created_user: dict):
        user_email = created_user['email']

        db_user = await mock_user_dao.get_user_by_email(user_email)

        assert db_user is not None
        assert db_user['email'] == user_email

    @pytest.mark.get_user
    async def test_get_user_by_email_returns_none_if_not_found(self, mock_user_dao: UserDAO):
        not_existing_user = faker.get_user_register_data_dict()
        db_user = await mock_user_dao.get_user_by_email(not_existing_user['email'])

        assert db_user is None

    @pytest.mark.update_user
    async def test_update_user_updates_fields(self, mock_user_dao: UserDAO, created_user: dict):
        created_user_id = created_user['_id']
        update_data = faker.get_user_register_data_dict()

        updated_user = await mock_user_dao.update_user(created_user_id, update_data)

        assert updated_user is not None
        assert updated_user['email'] == update_data['email']

    @pytest.mark.update_user
    async def test_update_user_returns_none_if_not_found(self, mock_user_dao: UserDAO):
        user_id = faker.generate_user_id()
        update_data = faker.get_user_register_data_dict()

        updated_user = await mock_user_dao.update_user(user_id, update_data)

        assert updated_user is None

    @pytest.mark.delete_user
    async def test_delete_user_returns_true(self, mock_user_dao: UserDAO, created_user: dict):
        user_id = created_user['_id']

        assert await mock_user_dao.delete_user(user_id)

    @pytest.mark.delete_user
    async def test_delete_user_returns_false_if_not_found(self, mock_user_dao: UserDAO):
        not_exsiting_id = faker.generate_user_id()

        assert not await mock_user_dao.delete_user(not_exsiting_id)

    @pytest.mark.update_role
    async def test_update_user_role_updates_role(self, mock_user_dao: UserDAO, created_user: dict):
        role = faker.get_role()
        user_id = created_user['_id']
        updated_user = await mock_user_dao.update_user_role(user_id, role)

        assert updated_user is not None
        assert updated_user['role'] == role

    @pytest.mark.update_role
    async def test_update_user_role_raises_for_non_existing_user(self, mock_user_dao: UserDAO):
        not_existing_user = faker.generate_user_id()
        role = faker.get_role()

        updated_user = await mock_user_dao.update_user_role(not_existing_user, role)

        assert updated_user is None

    @pytest.mark.ban_user
    async def test_set_ban_user_updates_is_banned(self, mock_user_dao: UserDAO, created_user):
        user_id = created_user['_id']

        updated_user = await mock_user_dao.set_ban_user(user_id, True)

        assert updated_user is not None
        assert updated_user['is_banned']

    @pytest.mark.get_users
    async def test_get_users_returns_list(self, base_users: UserDAO):
        user_list = await base_users.get_users()

        assert user_list

        for user in user_list:
            assert user['_id']
            assert user['email']

    @pytest.mark.get_users
    async def test_get_users_with_filter_role(self, base_users: UserDAO, created_user: dict):
        await base_users.update_user_role(
           user_id=created_user['_id'],
           new_role=UserRoleEnum.ORGANIZER
        )

        filter_obj = UserFilterModel(role=UserRoleEnum.ORGANIZER)

        users_list = await base_users.get_users(filter_obj=filter_obj)

        assert users_list

        for user in users_list:
            assert user['role'] == UserRoleEnum.ORGANIZER

    @pytest.mark.get_users
    async def test_get_users_specific_quantity(self, mock_user_dao: UserDAO):
        raw_user_list = [faker.get_user_register_data_dict() for _ in range(5)]

        for user in raw_user_list:
            await mock_user_dao.create_user(user)

        user_list = await mock_user_dao.get_users()

        assert len(user_list) == 5

        for user in user_list:
            assert user['_id']
            assert user['email']

    @pytest.mark.get_users
    async def test_get_users_with_filter_is_banned(self, base_users: UserDAO, created_user: dict):
        await base_users.set_ban_user(created_user['_id'], True)

        filter_obj = UserFilterModel(isBanned=True)

        users_list = await base_users.get_users(filter_obj=filter_obj)

        assert users_list

        for user in users_list:
            assert user['is_banned']

    @pytest.mark.get_users
    async def test_get_users_with_filter_created_at_from(
        self,
        mock_user_dao: UserDAO,
        users_with_different_dates: dict
    ):
        """Пользователи созданные ОТ указанной даты."""
        dao = mock_user_dao
        now = users_with_different_dates['now']

        filter_obj = UserFilterModel(created_at=now)  # type: ignore

        users = await dao.get_users(filter_obj=filter_obj)

        assert len(users) == 7


    @pytest.mark.get_users
    async def test_get_users_with_filter_created_at_to(
        self,
        mock_user_dao: UserDAO,
        users_with_different_dates: dict
    ):
        """Пользователи созданные ДО указанной даты."""
        dao = mock_user_dao
        now = users_with_different_dates['now']

        filter_obj = UserFilterModel(created_at_to=now)  # type: ignore

        users = await dao.get_users(filter_obj=filter_obj)

        assert len(users) == 8


    @pytest.mark.get_users
    async def test_get_users_with_filter_date_range(
        self,
        mock_user_dao: UserDAO,
        users_with_different_dates: dict
    ):
        """Пользователи созданные В ДИАПАЗОНЕ дат."""
        dao = mock_user_dao
        now = users_with_different_dates['now']

        filter_obj = UserFilterModel(
            created_at=now,           # type: ignore
            created_at_to=now + timedelta(seconds=5)  # type: ignore
        )

        users = await dao.get_users(filter_obj=filter_obj)

        assert len(users) == 5

    @pytest.mark.asyncio
    async def test_setup_indexes_creates_unique_email_index(self, user_collections: AsyncMongoMockCollection):

        await UserDAO.setup_indexes(user_collections)

        indexes = await user_collections.index_information()

        assert 'email_1' in indexes
        assert indexes['email_1']['unique'] is True


    @pytest.mark.create_user
    @pytest.mark.asyncio
    async def test_create_user_with_duplicate_email_raises_error_after_setup_indexes(
        self,
        user_collections: AsyncMongoMockCollection
    ):

        await UserDAO.setup_indexes(user_collections)
        dao = UserDAO(user_collections)

        user_data = faker.get_user_register_data_dict()
        await dao.create_user(user_data)


        with pytest.raises(DuplicateKeyError):
            await dao.create_user(user_data)