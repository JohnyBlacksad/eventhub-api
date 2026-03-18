import pytest
import allure
from datetime import datetime, timezone, timedelta
from bson import ObjectId
from mongomock import DuplicateKeyError

from app.models.activation_code import ActivationCodeDAO
from app.schemas.activation_code import CodeFiltersResponse
from tests.core.event_data_factory.fake_event_data import event_faker
from app.schemas.enums.user_enums.users_status import UserRoleEnum
from tests.core.const.mark_enums import (
    tag,
    MarkTests,
    ModuleMarks,
    ServicesMark,
    FeaturesActivationCodeMark,
    DataBaseFunctionMark,
)


DEFAULT_PAGINATION_SKIP = 0
DEFAULT_PAGINATION_LIMIT = 10
DEFAULT_CODES_COUNT = 3
FUTURE_HOURS_OFFSET = 1
PAST_DAYS_OFFSET = 5


@tag(MarkTests.UNITS)
@tag(ModuleMarks.DAO)
@tag(ServicesMark.ACTIVATION_CODE)
@pytest.mark.asyncio
class TestActivationCodeDAO:

    @allure.title('Инициализация индексов для activation code коллекции')
    @tag(DataBaseFunctionMark.SETUP_INDEXES)
    async def test_setup_indexes_creates_all_indexes(
        self,
        activation_code_collection,
        subtests
    ):

        with allure.step('Инициализация индексов'):
            await ActivationCodeDAO.setup_indexes(activation_code_collection)
            indexes = await activation_code_collection.index_information()

        with allure.step('Проверка наличия всех индексов'):
            with subtests.test(msg='Проверка уникального индекса на code'):
                assert 'code_1' in indexes
                assert indexes['code_1']['unique'] is True

            with subtests.test(msg='Проверка индекса на activated_by'):
                assert 'activated_by_1' in indexes

    @allure.title('Уникальный индекс на code предотвращает дубликаты')
    @tag(DataBaseFunctionMark.SETUP_INDEXES)
    @tag(FeaturesActivationCodeMark.CREATE_CODE)
    async def test_setup_indexes_prevents_duplicate_codes(
        self,
        activation_code_collection,
        code_factory_data
    ):

        with allure.step('Инициализация индексов'):
            await ActivationCodeDAO.setup_indexes(activation_code_collection)
            dao = ActivationCodeDAO(activation_code_collection)

        with allure.step('Создание первого кода'):
            code_data = code_factory_data()
            await dao.create_code(code_data)

        with allure.step('Попытка создания дубликата должна вызвать ошибку'):

            with pytest.raises(DuplicateKeyError):
                await dao.create_code(code_data)

    @allure.title('Успешное создание кода активации')
    @tag(FeaturesActivationCodeMark.CREATE_CODE)
    async def test_create_code_returns_id(
        self,
        activation_code_dao: ActivationCodeDAO,
        code_factory_data,
        subtests
    ):

        with allure.step('Подготовка данных для кода'):
            code_data = code_factory_data()

        with allure.step('Создание кода активации'):
            code_id = await activation_code_dao.create_code(code_data)

        with allure.step('Проверка что код сохранён в БД'):
            created_code = await activation_code_dao.get_code(code_id)

            with subtests.test(msg='Проверка типа code_id'):
                assert isinstance(code_id, str)

            with subtests.test(msg='Проверка данных кода'):
                assert created_code is not None
                assert created_code['code'] == code_data['code']
                assert created_code['role'] == code_data['role']
                assert created_code['is_used'] is False
                assert 'created_at' in created_code

    @allure.title('Получение кода активации по ID')
    @tag(FeaturesActivationCodeMark.GET_CODE)
    async def test_get_code_returns_code(
        self,
        activation_code_dao: ActivationCodeDAO,
        created_activation_code: dict,
        subtests
    ):

        code_id = str(created_activation_code['_id'])

        with allure.step(f'Получение кода по ID: {code_id}'):
            code = await activation_code_dao.get_code(code_id)

        with allure.step('Проверка данных кода'):
            with subtests.test(msg='Проверка наличия кода'):
                assert code is not None

            with subtests.test(msg='Проверка ID'):
                assert code['_id'] == created_activation_code['_id']

            with subtests.test(msg='Проверка поля code'):
                assert code['code'] == created_activation_code['code']

            with subtests.test(msg='Проверка поля role'):
                assert code['role'] == created_activation_code['role']

    @allure.title('Получение несуществующего кода возвращает None')
    @tag(FeaturesActivationCodeMark.GET_CODE)
    async def test_get_code_returns_none_if_not_found(
        self,
        activation_code_dao: ActivationCodeDAO
    ):


        fake_code_id = event_faker.generate_random_id()

        with allure.step(f'Получение несуществующего кода по ID: {fake_code_id}'):
            code = await activation_code_dao.get_code(fake_code_id)

        with allure.step('Проверка что код не найден'):
            assert code is None

    @allure.title('Удаление кода активации')
    @tag(FeaturesActivationCodeMark.DELETE_CODE)
    async def test_delete_code_returns_true(
        self,
        activation_code_dao: ActivationCodeDAO,
        created_activation_code: dict
    ):

        code_id = str(created_activation_code['_id'])

        with allure.step(f'Удаление кода по ID: {code_id}'):
            result = await activation_code_dao.delete_code(code_id)

        with allure.step('Проверка что код удалён'):
            assert result is True

        with allure.step('Проверка что код не найден в БД'):
            deleted = await activation_code_dao.get_code(code_id)
            assert deleted is None

    @allure.title('Удаление несуществующего кода возвращает False')
    @tag(FeaturesActivationCodeMark.DELETE_CODE)
    async def test_delete_code_returns_false_if_not_found(
        self,
        activation_code_dao: ActivationCodeDAO
    ):

        fake_code_id = event_faker.generate_random_id()

        with allure.step(f'Удаление несуществующего кода по ID: {fake_code_id}'):
            result = await activation_code_dao.delete_code(fake_code_id)

        with allure.step('Проверка что результат False'):
            assert result is False

    @allure.title('Использование кода активации')
    @tag(FeaturesActivationCodeMark.USE_CODE)
    async def test_use_code_marks_code_as_used(
        self,
        activation_code_dao: ActivationCodeDAO,
        created_activation_code: dict,
        created_user: dict,
        subtests
    ):
        """Проверка что use_code помечает код как использованный."""

        code_str = created_activation_code['code']
        user_id = str(created_user['_id'])

        with allure.step(f'Использование кода: {code_str}'):
            result = await activation_code_dao.use_code(code_str, user_id)

        with allure.step('Проверка результата'):
            with subtests.test(msg='Проверка что код найден'):
                assert result is not None

            with subtests.test(msg='Проверка что is_used был False до обновления'):
                assert result['is_used'] is False

        with allure.step('Проверка что код обновлён в БД'):
            updated_code = await activation_code_dao.get_code(str(created_activation_code['_id']))

            with subtests.test(msg='Проверка is_used = True'):
                assert updated_code
                assert updated_code['is_used'] is True

            with subtests.test(msg='Проверка activated_at установлен'):
                assert 'activated_at' in updated_code
                assert updated_code['activated_at'] is not None

            with subtests.test(msg='Проверка activated_by установлен'):
                assert 'activated_by' in updated_code
                assert str(updated_code['activated_by']) == user_id

    @allure.title('Использование несуществующего кода возвращает None')
    @tag(FeaturesActivationCodeMark.USE_CODE)
    async def test_use_code_returns_none_for_nonexistent_code(
        self,
        activation_code_dao: ActivationCodeDAO,
        created_user: dict
    ):

        fake_code = event_faker.faker.text(max_nb_chars=12)
        user_id = str(created_user['_id'])

        with allure.step(f'Использование несуществующего кода: {fake_code}'):
            result = await activation_code_dao.use_code(fake_code, user_id)

        with allure.step('Проверка что результат None'):
            assert result is None

    @allure.title('Использование уже использованного кода возвращает None')
    @tag(FeaturesActivationCodeMark.USE_CODE)
    async def test_use_code_returns_none_for_already_used_code(
        self,
        activation_code_dao: ActivationCodeDAO,
        activation_code_factory,
        created_user: dict
    ):

        with allure.step('Создание уже использованного кода'):
            used_code = await activation_code_factory(is_used=True)

        user_id = str(created_user['_id'])
        code_str = used_code['code']

        with allure.step(f'Попытка использовать уже использованный код: {code_str}'):
            result = await activation_code_dao.use_code(code_str, user_id)

        with allure.step('Проверка что результат None'):
            assert result is None

    @allure.title('Получение списка кодов без фильтров')
    @tag(FeaturesActivationCodeMark.GET_CODES)
    async def test_get_codes_returns_list(
        self,
        activation_code_dao: ActivationCodeDAO,
        activation_codes_factory,
        subtests
    ):

        with allure.step(f'Создание {DEFAULT_CODES_COUNT} кодов'):
            await activation_codes_factory(count=DEFAULT_CODES_COUNT)

        with allure.step('Получение списка кодов'):
            codes = await activation_code_dao.get_codes(
                skip=DEFAULT_PAGINATION_SKIP,
                limit=DEFAULT_PAGINATION_LIMIT
            )

        with allure.step('Проверка списка кодов'):
            with subtests.test(msg='Проверка количества'):
                assert len(codes) == DEFAULT_CODES_COUNT

            with subtests.test(msg='Проверка что все кода имеют required поля'):
                for code in codes:
                    assert 'code' in code
                    assert 'role' in code
                    assert 'is_used' in code
                    assert 'created_at' in code

    @allure.title('Получение списка кодов с пагинацией')
    @tag(FeaturesActivationCodeMark.GET_CODES)
    async def test_get_codes_with_pagination(
        self,
        activation_code_dao: ActivationCodeDAO,
        activation_codes_factory,
        subtests
    ):

        total_count = 10
        page_size = 3

        with allure.step(f'Создание {total_count} кодов'):
            await activation_codes_factory(count=total_count)

        with allure.step('Получение первой страницы'):
            page1 = await activation_code_dao.get_codes(
                skip=0,
                limit=page_size
            )

        with allure.step('Получение второй страницы'):
            page2 = await activation_code_dao.get_codes(
                skip=page_size,
                limit=page_size
            )

        with allure.step('Проверка пагинации'):
            with subtests.test(msg='Проверка размера страницы 1'):
                assert len(page1) == page_size

            with subtests.test(msg='Проверка размера страницы 2'):
                assert len(page2) == page_size

            with subtests.test(msg='Проверка что страницы не пересекаются'):
                page1_ids = {str(code['_id']) for code in page1}
                page2_ids = {str(code['_id']) for code in page2}
                assert page1_ids.isdisjoint(page2_ids)

    @allure.title('Получение списка кодов отсортировано по created_at DESC')
    @tag(FeaturesActivationCodeMark.GET_CODES)
    async def test_get_codes_sorted_by_created_at_desc(
        self,
        activation_code_dao: ActivationCodeDAO,
        activation_codes_factory
    ):

        with allure.step('Создание кодов с разными временами создания'):
            base_time = datetime.now(timezone.utc)
            times = [
                base_time - timedelta(days=2),
                base_time - timedelta(days=1),
                base_time
            ]
            codes = await activation_codes_factory(
                count=len(times),
                created_at_list=times
            )

        with allure.step('Получение списка кодов'):
            result = await activation_code_dao.get_codes()

        with allure.step('Проверка сортировки по убыванию'):
            assert len(result) == len(times)
            for i in range(len(result) - 1):
                assert result[i]['created_at'] >= result[i + 1]['created_at']

    @allure.title('Фильтрация кодов по is_used')
    @tag(FeaturesActivationCodeMark.FILTER_CODES)
    async def test_get_codes_filter_by_is_used(
        self,
        activation_code_dao: ActivationCodeDAO,
        activation_codes_factory,
        subtests
    ):

        with allure.step('Создание кодов с разными is_used'):
            await activation_codes_factory(
                count=DEFAULT_CODES_COUNT,
                is_used_list=[True, False, True]
            )

        with allure.step('Получение неиспользованных кодов (is_used=False)'):
            filter_obj = CodeFiltersResponse(is_used=False) # type: ignore
            unused_codes = await activation_code_dao.get_codes(filters=filter_obj)

        with allure.step('Получение использованных кодов (is_used=True)'):
            filter_obj_used = CodeFiltersResponse(is_used=True) # type: ignore
            used_codes = await activation_code_dao.get_codes(filters=filter_obj_used)

        with allure.step('Проверка фильтрации'):
            with subtests.test(msg='Проверка количества неиспользованных'):
                assert len(unused_codes) == 1
                assert unused_codes[0]['is_used'] is False

            with subtests.test(msg='Проверка количества использованных'):
                assert len(used_codes) == 2
                for code in used_codes:
                    assert code['is_used'] is True

    @allure.title('Фильтрация кодов по role')
    @tag(FeaturesActivationCodeMark.FILTER_CODES)
    async def test_get_codes_filter_by_role(
        self,
        activation_code_dao: ActivationCodeDAO,
        activation_code_factory,
        subtests
    ):

        with allure.step('Создание кодов с разными ролями'):
            await activation_code_factory(role=UserRoleEnum.ORGANIZER)
            await activation_code_factory(role=UserRoleEnum.ADMIN)

        with allure.step('Получение кодов с ролью ORGANIZER'):
            filter_obj = CodeFiltersResponse(role=UserRoleEnum.ORGANIZER)
            organizer_codes = await activation_code_dao.get_codes(filters=filter_obj)

        with allure.step('Получение кодов с ролью ADMIN'):
            filter_obj_admin = CodeFiltersResponse(role=UserRoleEnum.ADMIN)
            admin_codes = await activation_code_dao.get_codes(filters=filter_obj_admin)

        with allure.step('Проверка фильтрации по ролям'):
            with subtests.test(msg='Проверка ORGANIZER кодов'):
                assert len(organizer_codes) == 1
                assert organizer_codes[0]['role'] == UserRoleEnum.ORGANIZER

            with subtests.test(msg='Проверка ADMIN кодов'):
                assert len(admin_codes) == 1
                assert admin_codes[0]['role'] == UserRoleEnum.ADMIN

    @allure.title('Фильтрация кодов по created_at (от даты)')
    @tag(FeaturesActivationCodeMark.FILTER_CODES)
    async def test_get_codes_filter_by_created_at_from(
        self,
        activation_code_dao: ActivationCodeDAO,
        activation_codes_factory
    ):

        with allure.step('Создание кодов с разными датами создания'):
            now = datetime.now(timezone.utc)
            past = now - timedelta(days=PAST_DAYS_OFFSET)
            middle = now - timedelta(seconds=1)
            future = now + timedelta(seconds=1)

            await activation_codes_factory(
                count=DEFAULT_CODES_COUNT,
                created_at_list=[past, middle, future]
            )

        with allure.step(f'Получение кодов созданных от {now}'):
            filter_obj = CodeFiltersResponse(created_at=now) # type: ignore
            recent_codes = await activation_code_dao.get_codes(filters=filter_obj)

        with allure.step('Проверка что найдены только недавние коды'):
            assert len(recent_codes) == 1

    @allure.title('Комбинированная фильтрация (is_used + role)')
    @tag(FeaturesActivationCodeMark.FILTER_CODES)
    async def test_get_codes_combined_filters(
        self,
        activation_code_dao: ActivationCodeDAO,
        activation_code_factory,
        subtests
    ):

        with allure.step('Создание кодов с разными комбинациями'):
            await activation_code_factory(role=UserRoleEnum.ORGANIZER, is_used=False)
            await activation_code_factory(role=UserRoleEnum.ORGANIZER, is_used=True)
            await activation_code_factory(role=UserRoleEnum.ADMIN, is_used=False)

        with allure.step('Получение неиспользованных ORGANIZER кодов'):
            filter_obj = CodeFiltersResponse(
                is_used=False, # type: ignore
                role=UserRoleEnum.ORGANIZER
            )
            codes = await activation_code_dao.get_codes(filters=filter_obj)

        with allure.step('Проверка комбинированной фильтрации'):
            with subtests.test(msg='Проверка количества'):
                assert len(codes) == 1

            with subtests.test(msg='Проверка is_used'):
                assert codes[0]['is_used'] is False

            with subtests.test(msg='Проверка role'):
                assert codes[0]['role'] == UserRoleEnum.ORGANIZER
