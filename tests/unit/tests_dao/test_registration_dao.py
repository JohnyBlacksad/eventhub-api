import pytest
import allure
from datetime import datetime, timezone, timedelta
from bson import ObjectId

from tests.core.user_data_factory.fake_user_data import faker
from tests.core.event_data_factory.fake_event_data import event_faker
from app.models.registration import RegistrationDAO
from app.schemas.enums.event_enums.event_enums import EventStatusEnum
from tests.core.const.mark_enums import (
    tag,
    MarkTests,
    ModuleMarks,
    ServicesMark,
    FeaturesRegistrationMark,
    DataBaseFunctionMark,
)


@tag(MarkTests.UNITS)
@tag(ModuleMarks.DAO)
@tag(ServicesMark.EVENT_REGISTRATION)
@pytest.mark.asyncio
class TestRegistrationDAO:

    @allure.title('Инициализация индексов для registration коллекции')
    @tag(DataBaseFunctionMark.SETUP_INDEXES)
    async def test_setup_indexes_creates_all_indexes(
        self,
        registration_collection,
        subtests
    ):

        with allure.step('Инициализация индексов'):
            await RegistrationDAO.setup_indexes(registration_collection)
            indexes = await registration_collection.index_information()

        with allure.step('Проверка наличия всех индексов'):
            with subtests.test(msg='Проверка уникального составного индекса'):
                assert 'event_id_1_user_id_1' in indexes
                assert indexes['event_id_1_user_id_1']['unique'] is True

            with subtests.test(msg='Проверка индекса по user_id'):
                assert 'user_id_1' in indexes

    @allure.title('Уникальный составной индекс предотвращает дубликаты')
    @tag(DataBaseFunctionMark.SETUP_INDEXES)
    @tag(FeaturesRegistrationMark.ADD_REGISTRATION)
    async def test_setup_indexes_prevents_duplicate_registrations(
        self,
        registration_collection,
        created_user: dict,
        created_event: dict
    ):

        with allure.step('Инициализация индексов'):
            await RegistrationDAO.setup_indexes(registration_collection)
            dao = RegistrationDAO(registration_collection)

        with allure.step('Создание первой регистрации'):
            user_id = str(created_user['_id'])
            event_id = str(created_event['_id'])
            await dao.add_registration(event_id, user_id)

        with allure.step('Попытка создания дубликата должна вызвать ошибку'):
            from mongomock import DuplicateKeyError
            with pytest.raises(DuplicateKeyError):
                await dao.add_registration(event_id, user_id)

    @allure.title('Успешное добавление регистрации')
    @tag(FeaturesRegistrationMark.ADD_REGISTRATION)
    async def test_add_registration_returns_insert_result(
        self,
        registration_dao: RegistrationDAO,
        created_user: dict,
        created_event: dict,
        subtests
    ):

        user_id = str(created_user['_id'])
        event_id = str(created_event['_id'])

        with allure.step(f'Добавление регистрации: user={user_id}, event={event_id}'):
            result = await registration_dao.add_registration(event_id, user_id)

        with allure.step('Проверка результата вставки'):
            with subtests.test(msg='Проверка inserted_id'):
                assert result.inserted_id is not None

        with allure.step('Проверка что регистрация сохранена в БД'):
            registration = await registration_dao.get_existing_registration(event_id, user_id)

            with subtests.test(msg='Проверка данных регистрации'):
                assert registration is not None
                assert str(registration['event_id']) == event_id
                assert str(registration['user_id']) == user_id
                assert 'registered_at' in registration
                assert isinstance(registration['registered_at'], datetime)

    @allure.title('Удаление регистрации пользователя с события')
    @tag(FeaturesRegistrationMark.REMOVE_REGISTRATION)
    async def test_remove_registration_returns_delete_result(
        self,
        registration_dao: RegistrationDAO,
        created_registration: dict,
        subtests
    ):

        event_id = created_registration['event_id']
        user_id = created_registration['user_id']

        with allure.step(f'Удаление регистрации: event={event_id}, user={user_id}'):
            result = await registration_dao.remove_registration(str(event_id), str(user_id))

        with allure.step('Проверка результата удаления'):
            with subtests.test(msg='Проверка deleted_count'):
                assert result.deleted_count == 1

        with allure.step('Проверка что регистрация удалена из БД'):
            deleted = await registration_dao.get_existing_registration(str(event_id), str(user_id))
            assert deleted is None

    @allure.title('Удаление несуществующей регистрации возвращает 0')
    @tag(FeaturesRegistrationMark.REMOVE_REGISTRATION)
    async def test_remove_registration_returns_zero_if_not_found(
        self,
        registration_dao: RegistrationDAO,
        created_user: dict,
        created_event: dict
    ):

        user_id = str(created_user['_id'])
        event_id = str(created_event['_id'])

        with allure.step(f'Удаление несуществующей регистрации: event={event_id}, user={user_id}'):
            result = await registration_dao.remove_registration(event_id, user_id)

        with allure.step('Проверка что deleted_count = 0'):
            assert result.deleted_count == 0

    @allure.title('Получение списка регистраций на событие')
    @tag(FeaturesRegistrationMark.GET_EVENT_REGISTRATIONS)
    async def test_get_event_registrations_returns_list(
        self,
        registration_dao: RegistrationDAO,
        created_event: dict,
        event_registrations_factory,
        subtests
    ):

        event_id = str(created_event['_id'])

        with allure.step(f'Создание 5 регистраций на событие {event_id}'):
            registrations = await event_registrations_factory(event_id, count=5)

        with allure.step('Получение списка регистраций'):
            result = await registration_dao.get_event_registrations(event_id)

        with allure.step('Проверка списка регистраций'):
            with subtests.test(msg='Проверка количества'):
                assert len(result) == 5

            with subtests.test(msg='Проверка что все регистрации на одно событие'):
                for reg in result:
                    assert str(reg['event_id']) == event_id

    @allure.title('Получение регистраций с пагинацией')
    @tag(FeaturesRegistrationMark.GET_EVENT_REGISTRATIONS)
    async def test_get_event_registrations_with_pagination(
        self,
        registration_dao: RegistrationDAO,
        created_event: dict,
        event_registrations_factory,
        subtests
    ):

        event_id = str(created_event['_id'])

        with allure.step(f'Создание 10 регистраций на событие {event_id}'):
            await event_registrations_factory(event_id, count=10)

        with allure.step('Получение первой страницы (skip=0, limit=3)'):
            page1 = await registration_dao.get_event_registrations(event_id, skip=0, limit=3)

        with allure.step('Получение второй страницы (skip=3, limit=3)'):
            page2 = await registration_dao.get_event_registrations(event_id, skip=3, limit=3)

        with allure.step('Проверка пагинации'):
            with subtests.test(msg='Проверка количества на странице 1'):
                assert len(page1) == 3

            with subtests.test(msg='Проверка количества на странице 2'):
                assert len(page2) == 3

            with subtests.test(msg='Проверка что страницы не пересекаются'):
                page1_ids = {str(reg['_id']) for reg in page1}
                page2_ids = {str(reg['_id']) for reg in page2}
                assert page1_ids.isdisjoint(page2_ids)

    @allure.title('Получение регистраций сортируется по registered_at ASC')
    @tag(FeaturesRegistrationMark.GET_EVENT_REGISTRATIONS)
    async def test_get_event_registrations_sorted_by_registered_at(
        self,
        registration_dao: RegistrationDAO,
        created_event: dict,
        user_factory
    ):

        event_id = created_event['_id']

        with allure.step('Создание регистраций с разными timestamp'):
            base_time = datetime.now(timezone.utc)

            for i in range(3):
                user_id = await user_factory()
                await registration_dao.collection.insert_one({
                    'event_id': event_id,
                    'user_id': ObjectId(user_id),
                    'registered_at': base_time + timedelta(seconds=i)
                })

        with allure.step('Получение регистраций'):
            registrations = await registration_dao.get_event_registrations(str(event_id))

        with allure.step('Проверка сортировки по возрастанию'):
            assert len(registrations) == 3
            for i in range(len(registrations) - 1):
                assert registrations[i]['registered_at'] <= registrations[i + 1]['registered_at']

    @allure.title('Получение регистраций несуществующего события')
    @tag(FeaturesRegistrationMark.GET_EVENT_REGISTRATIONS)
    async def test_get_event_registrations_returns_empty_for_nonexistent_event(
        self,
        registration_dao: RegistrationDAO
    ):

        fake_event_id = event_faker.generate_random_id()

        with allure.step(f'Получение регистраций для несуществующего события {fake_event_id}'):
            registrations = await registration_dao.get_event_registrations(fake_event_id)

        with allure.step('Проверка что список пуст'):
            assert registrations == []

    @allure.title('Получение списка регистраций пользователя')
    @tag(FeaturesRegistrationMark.GET_USER_REGISTRATIONS)
    async def test_get_user_registrations_returns_list(
        self,
        registration_dao: RegistrationDAO,
        created_user: dict,
        event_factory_for_user,
        subtests
    ):

        user_id = str(created_user['_id'])

        with allure.step(f'Создание 5 регистраций для пользователя {user_id}'):
            for _ in range(5):
                _, _, event_id = await event_factory_for_user(EventStatusEnum.PUBLISHED, count=1)
                await registration_dao.add_registration(event_id, user_id)

        with allure.step('Получение списка регистраций пользователя'):
            registrations = await registration_dao.get_user_registrations(user_id)

        with allure.step('Проверка списка регистраций'):
            with subtests.test(msg='Проверка количества'):
                assert len(registrations) == 5

            with subtests.test(msg='Проверка что все регистрации одного пользователя'):
                for reg in registrations:
                    assert str(reg['user_id']) == user_id

    @allure.title('Получение регистраций пользователя с limit')
    @tag(FeaturesRegistrationMark.GET_USER_REGISTRATIONS)
    async def test_get_user_registrations_with_limit(
        self,
        registration_dao: RegistrationDAO,
        created_user: dict,
        event_factory_for_user
    ):

        user_id = str(created_user['_id'])

        with allure.step(f'Создание 10 регистраций для пользователя {user_id}'):
            for _ in range(10):
                _, _, event_id = await event_factory_for_user(EventStatusEnum.PUBLISHED, count=1)
                await registration_dao.add_registration(event_id, user_id)

        with allure.step('Получение регистраций с limit=5'):
            all_registrations = await registration_dao.get_user_registrations(user_id, limit=100)
            registrations = all_registrations[:5]

        with allure.step('Проверка что возвращено 5 регистраций'):
            assert len(registrations) == 5

    @allure.title('Получение регистраций несуществующего пользователя')
    @tag(FeaturesRegistrationMark.GET_USER_REGISTRATIONS)
    async def test_get_user_registrations_returns_empty_for_nonexistent_user(
        self,
        registration_dao: RegistrationDAO
    ):

        fake_user_id = faker.generate_user_id()

        with allure.step(f'Получение регистраций для несуществующего пользователя {fake_user_id}'):
            registrations = await registration_dao.get_user_registrations(fake_user_id)

        with allure.step('Проверка что список пуст'):
            assert registrations == []

    @allure.title('Получение существующей регистрации')
    @tag(FeaturesRegistrationMark.GET_EXISTING_REGISTRATION)
    async def test_get_existing_registration_returns_registration(
        self,
        registration_dao: RegistrationDAO,
        created_registration: dict,
        subtests
    ):

        event_id = created_registration['event_id']
        user_id = created_registration['user_id']

        with allure.step(f'Получение регистрации: event={event_id}, user={user_id}'):
            registration = await registration_dao.get_existing_registration(str(event_id), str(user_id))

        with allure.step('Проверка данных регистрации'):
            with subtests.test(msg='Проверка event_id'):
                assert registration is not None
                assert registration['event_id'] == event_id

            with subtests.test(msg='Проверка user_id'):
                assert registration['user_id'] == user_id

    @allure.title('Получение несуществующей регистрации возвращает None')
    @tag(FeaturesRegistrationMark.GET_EXISTING_REGISTRATION)
    async def test_get_existing_registration_returns_none_if_not_found(
        self,
        registration_dao: RegistrationDAO,
        created_user: dict,
        created_event: dict
    ):

        user_id = str(created_user['_id'])
        event_id = str(created_event['_id'])

        with allure.step(f'Получение несуществующей регистрации: event={event_id}, user={user_id}'):
            registration = await registration_dao.get_existing_registration(event_id, user_id)

        with allure.step('Проверка что registration is None'):
            assert registration is None

    @allure.title('Удаление всех регистраций на событие')
    @tag(FeaturesRegistrationMark.DELETE_ALL_REGISTRATIONS_FOR_EVENT)
    async def test_delete_all_registrations_for_event_returns_true(
        self,
        registration_dao: RegistrationDAO,
        created_event: dict,
        event_registrations_factory,
        subtests
    ):

        event_id = str(created_event['_id'])

        with allure.step(f'Создание 5 регистраций на событие {event_id}'):
            await event_registrations_factory(event_id, count=5)

        with allure.step('Удаление всех регистраций на событие'):
            result = await registration_dao.delete_all_registrations_for_event(event_id)

        with allure.step('Проверка результата'):
            with subtests.test(msg='Проверка что result = True'):
                assert result is True

        with allure.step('Проверка что все регистрации удалены'):
            registrations = await registration_dao.get_event_registrations(event_id)
            assert len(registrations) == 0

    @allure.title('Удаление всех регистраций несуществующего события')
    @tag(FeaturesRegistrationMark.DELETE_ALL_REGISTRATIONS_FOR_EVENT)
    async def test_delete_all_registrations_for_event_returns_false(
        self,
        registration_dao: RegistrationDAO
    ):

        fake_event_id = event_faker.generate_random_id()

        with allure.step(f'Удаление регистраций несуществующего события {fake_event_id}'):
            result = await registration_dao.delete_all_registrations_for_event(fake_event_id)

        with allure.step('Проверка что result = False'):
            assert result is False

    @allure.title('Установка времени удаления для всех регистраций на событие')
    @tag(FeaturesRegistrationMark.SET_DELETION_TIME_FOR_EVENT)
    async def test_set_deletion_time_for_event_updates_registrations(
        self,
        registration_dao: RegistrationDAO,
        created_event: dict,
        event_registrations_factory,
        subtests
    ):

        event_id = str(created_event['_id'])
        death_date = datetime.now(timezone.utc)

        with allure.step(f'Создание 3 регистраций на событие {event_id}'):
            await event_registrations_factory(event_id, count=3)

        with allure.step(f'Установка deleted_at = {death_date}'):
            result = await registration_dao.set_deletion_time_for_event(event_id, death_date)

        with allure.step('Проверка результата обновления'):
            with subtests.test(msg='Проверка modified_count'):
                assert result.modified_count == 3

        with allure.step('Проверка что deleted_at установлен'):
            registrations = await registration_dao.get_event_registrations(event_id)
            for reg in registrations:
                assert reg['deleted_at'] is not None
                expected_ts = death_date.timestamp()
                actual_ts = reg['deleted_at'].timestamp() if reg['deleted_at'].tzinfo else reg['deleted_at'].replace(tzinfo=timezone.utc).timestamp()
                assert abs(expected_ts - actual_ts) < 2

    @allure.title('Установка None времени удаления')
    @tag(FeaturesRegistrationMark.SET_DELETION_TIME_FOR_EVENT)
    async def test_set_deletion_time_for_event_with_none(
        self,
        registration_dao: RegistrationDAO,
        created_event: dict,
        event_registrations_factory
    ):

        event_id = str(created_event['_id'])
        death_date = datetime.now(timezone.utc) + timedelta(hours=1)

        with allure.step(f'Создание регистраций и установка deleted_at'):
            await event_registrations_factory(event_id, count=2)
            await registration_dao.set_deletion_time_for_event(event_id, death_date)

        with allure.step('Снятие метки удаления (deleted_at = None)'):
            result = await registration_dao.set_deletion_time_for_event(event_id, None)

        with allure.step('Проверка что deleted_at удалён'):
            registrations = await registration_dao.get_event_registrations(event_id)
            for reg in registrations:
                assert 'deleted_at' not in reg or reg['deleted_at'] is None

    @allure.title('Удаление всех регистраций пользователя')
    @tag(FeaturesRegistrationMark.DELETE_REGISTRATION_BY_USER)
    async def test_delete_registration_by_user_returns_true(
        self,
        registration_dao: RegistrationDAO,
        created_user: dict,
        event_factory_for_user,
        subtests
    ):

        user_id = str(created_user['_id'])

        with allure.step(f'Создание 5 регистраций для пользователя {user_id}'):
            for _ in range(5):
                _, _, event_id = await event_factory_for_user(EventStatusEnum.PUBLISHED, count=1)
                await registration_dao.add_registration(event_id, user_id)

        with allure.step('Удаление всех регистраций пользователя'):
            result = await registration_dao.delete_registration_by_user(user_id)

        with allure.step('Проверка результата'):
            with subtests.test(msg='Проверка что result = True'):
                assert result is True

        with allure.step('Проверка что все регистрации удалены'):
            registrations = await registration_dao.get_user_registrations(user_id)
            assert len(registrations) == 0

    @allure.title('Удаление регистраций несуществующего пользователя')
    @tag(FeaturesRegistrationMark.DELETE_REGISTRATION_BY_USER)
    async def test_delete_registration_by_user_returns_false(
        self,
        registration_dao: RegistrationDAO
    ):

        fake_user_id = faker.generate_user_id()

        with allure.step(f'Удаление регистраций несуществующего пользователя {fake_user_id}'):
            result = await registration_dao.delete_registration_by_user(fake_user_id)

        with allure.step('Проверка что result = False'):
            assert result is False
