import pytest
import allure
import asyncio
from uuid import uuid4

from app.models.registration import RegistrationDAO
from app.models.activation_code import ActivationCodeDAO
from app.schemas.enums.user_enums.users_status import UserRoleEnum
from tests.core.const.mark_enums import (
    tag,
    MarkTests,
    ModuleMarks,
    ServicesMark,
    FeaturesRegistrationMark,
    FeaturesActivationCodeMark,
)


CONCURRENT_USERS_COUNT = 10
CONCURRENT_OPERATIONS_COUNT = 5


@tag(MarkTests.UNITS)
@tag(ModuleMarks.DAO)
@tag(ServicesMark.EVENT_REGISTRATION)
@pytest.mark.asyncio
class TestRegistrationDAOConcurrency:

    @allure.title('Конкурентная регистрация одного пользователя на одно событие')
    @tag(FeaturesRegistrationMark.ADD_REGISTRATION)
    async def test_concurrent_add_registration_prevents_duplicates(
        self,
        registration_dao: RegistrationDAO,
        setup_indexes_for_registration,
        created_user: dict,
        created_event: dict,
        subtests
    ):

        user_id = str(created_user['_id'])
        event_id = str(created_event['_id'])
        successful_registrations = 0
        failed_registrations = 0

        async def try_register():
            nonlocal successful_registrations, failed_registrations
            try:
                await registration_dao.add_registration(event_id, user_id)
                successful_registrations += 1
            except Exception:
                failed_registrations += 1

        with allure.step(f'Попытка создать {CONCURRENT_USERS_COUNT} регистраций одновременно'):
            tasks = [try_register() for _ in range(CONCURRENT_USERS_COUNT)]
            await asyncio.gather(*tasks, return_exceptions=True)

        with allure.step('Проверка результатов'):
            with subtests.test(msg='Только одна регистрация успешна'):
                assert successful_registrations == 1

            with subtests.test(msg='Остальные запросы отклонены'):
                assert failed_registrations == CONCURRENT_USERS_COUNT - 1

        with allure.step('Проверка что в БД только одна регистрация'):
            registrations = await registration_dao.get_event_registrations(event_id)
            assert len(registrations) == 1

    @allure.title('Конкурентная регистрация разных пользователей на одно событие')
    @tag(FeaturesRegistrationMark.ADD_REGISTRATION)
    async def test_concurrent_add_registration_different_users(
        self,
        registration_dao: RegistrationDAO,
        setup_indexes_for_registration,
        created_event: dict,
        user_factory,
        subtests
    ):

        event_id = str(created_event['_id'])
        user_ids = []

        with allure.step(f'Создание {CONCURRENT_USERS_COUNT} пользователей'):
            for _ in range(CONCURRENT_USERS_COUNT):
                user_id = await user_factory()
                user_ids.append(user_id)

        async def register_user(uid):
            await registration_dao.add_registration(event_id, uid)

        with allure.step(f'Одновременная регистрация {CONCURRENT_USERS_COUNT} пользователей'):
            tasks = [register_user(uid) for uid in user_ids]
            await asyncio.gather(*tasks)

        with allure.step('Проверка что все регистрации успешны'):
            registrations = await registration_dao.get_event_registrations(event_id)

            with subtests.test(msg='Все регистрации созданы'):
                assert len(registrations) == CONCURRENT_USERS_COUNT

            with subtests.test(msg='Все регистрации уникальны'):
                registration_user_ids = {str(reg['user_id']) for reg in registrations}
                assert len(registration_user_ids) == CONCURRENT_USERS_COUNT

    @allure.title('Конкурентное удаление всех регистраций на событие')
    @tag(FeaturesRegistrationMark.DELETE_ALL_REGISTRATIONS_FOR_EVENT)
    async def test_concurrent_delete_all_registrations(
        self,
        registration_dao: RegistrationDAO,
        created_event: dict,
        event_registrations_factory,
        subtests
    ):

        event_id = str(created_event['_id'])

        with allure.step(f'Создание {CONCURRENT_OPERATIONS_COUNT} регистраций'):
            await event_registrations_factory(event_id, count=CONCURRENT_OPERATIONS_COUNT)

        async def delete_all():
            return await registration_dao.delete_all_registrations_for_event(event_id)

        with allure.step(f'Одновременное выполнение {CONCURRENT_OPERATIONS_COUNT} удалений'):
            tasks = [delete_all() for _ in range(CONCURRENT_OPERATIONS_COUNT)]
            results = await asyncio.gather(*tasks)

        with allure.step('Проверка результатов'):
            with subtests.test(msg='Все операции завершены'):
                assert all(isinstance(r, bool) for r in results)

        with allure.step('Проверка что все регистрации удалены'):
            registrations = await registration_dao.get_event_registrations(event_id)
            assert len(registrations) == 0


@tag(MarkTests.UNITS)
@tag(ModuleMarks.DAO)
@tag(ServicesMark.ACTIVATION_CODE)
@pytest.mark.asyncio
class TestActivationCodeDAOConcurrency:

    @allure.title('Конкурентное использование одного кода активации')
    @tag(FeaturesActivationCodeMark.USE_CODE)
    async def test_concurrent_use_code_single_activation(
        self,
        activation_code_dao: ActivationCodeDAO,
        setup_indexes_for_activation_code,
        created_user: dict,
        activation_code_factory,
        subtests
    ):

        with allure.step('Создание кода активации'):
            code = await activation_code_factory()

        code_str = code['code']
        user_id = str(created_user['_id'])

        successful_activations = 0
        failed_activations = 0
        results = []

        async def try_activate():
            nonlocal successful_activations, failed_activations
            result = await activation_code_dao.use_code(code_str, user_id)
            results.append(result)
            if result is not None:
                successful_activations += 1
            else:
                failed_activations += 1

        with allure.step(f'Попытка активировать код {CONCURRENT_USERS_COUNT} раз одновременно'):
            tasks = [try_activate() for _ in range(CONCURRENT_USERS_COUNT)]
            await asyncio.gather(*tasks, return_exceptions=True)

        with allure.step('Проверка результатов'):
            with subtests.test(msg='Только одна активация успешна'):
                assert successful_activations == 1

            with subtests.test(msg='Остальные активации отклонены'):
                assert failed_activations == CONCURRENT_USERS_COUNT - 1

        with allure.step('Проверка что код использован в БД'):
            updated_code = await activation_code_dao.get_code(str(code['_id']))
            assert updated_code
            assert updated_code['is_used'] is True
            assert updated_code['activated_by'] is not None

    @allure.title('Конкурентное создание кодов с уникальными значениями')
    @tag(FeaturesActivationCodeMark.CREATE_CODE)
    async def test_concurrent_create_unique_codes(
        self,
        activation_code_dao: ActivationCodeDAO,
        setup_indexes_for_activation_code,
        subtests
    ):


        created_codes = []

        async def create_unique_code():
            code_data = {
                'role': UserRoleEnum.ORGANIZER,
                'code': str(uuid4())
            }
            code_id = await activation_code_dao.create_code(code_data)
            created_codes.append(code_id)

        with allure.step(f'Одновременное создание {CONCURRENT_USERS_COUNT} уникальных кодов'):
            tasks = [create_unique_code() for _ in range(CONCURRENT_USERS_COUNT)]
            await asyncio.gather(*tasks)

        with allure.step('Проверка что все коды созданы'):
            with subtests.test(msg='Все коды созданы'):
                assert len(created_codes) == CONCURRENT_USERS_COUNT

            with subtests.test(msg='Все коды уникальны'):
                assert len(set(created_codes)) == CONCURRENT_USERS_COUNT

        with allure.step('Проверка что все коды в БД'):
            codes = await activation_code_dao.get_codes(limit=CONCURRENT_USERS_COUNT)
            assert len(codes) == CONCURRENT_USERS_COUNT

    @allure.title('Конкурентное удаление разных кодов')
    @tag(FeaturesActivationCodeMark.DELETE_CODE)
    async def test_concurrent_delete_different_codes(
        self,
        activation_code_dao: ActivationCodeDAO,
        activation_codes_factory,
        subtests
    ):

        with allure.step(f'Создание {CONCURRENT_OPERATIONS_COUNT} кодов'):
            codes = await activation_codes_factory(count=CONCURRENT_OPERATIONS_COUNT)
            code_ids = [str(code['_id']) for code in codes]

        delete_code = lambda code_id: activation_code_dao.delete_code(code_id)

        with allure.step(f'Одновременное удаление {CONCURRENT_OPERATIONS_COUNT} кодов'):
            tasks = [delete_code(code_id) for code_id in code_ids]
            results = await asyncio.gather(*tasks)

        with allure.step('Проверка результатов'):
            with subtests.test(msg='Все удаления успешны'):
                assert all(results)

        with allure.step('Проверка что все коды удалены'):
            remaining_codes = await activation_code_dao.get_codes()
            assert len(remaining_codes) == 0

    @allure.title('Конкурентное чтение и запись кода')
    @tag(FeaturesActivationCodeMark.GET_CODE)
    @tag(FeaturesActivationCodeMark.USE_CODE)
    async def test_concurrent_read_write_code(
        self,
        activation_code_dao: ActivationCodeDAO,
        created_activation_code: dict,
        created_user: dict,
        subtests
    ):

        code_id = str(created_activation_code['_id'])
        code_str = created_activation_code['code']
        user_id = str(created_user['_id'])

        read_count = 0
        write_success = False

        async def read_code():
            nonlocal read_count
            result = await activation_code_dao.get_code(code_id)
            if result:
                read_count += 1

        async def use_code():
            nonlocal write_success
            result = await activation_code_dao.use_code(code_str, user_id)
            if result is not None:
                write_success = True

        with allure.step('Одновременное чтение и использование кода'):
            tasks = (
                [read_code() for _ in range(CONCURRENT_OPERATIONS_COUNT)] +
                [use_code()]
            )
            await asyncio.gather(*tasks, return_exceptions=True)

        with allure.step('Проверка результатов'):
            with subtests.test(msg='Чтения выполнены'):
                assert read_count > 0

            with subtests.test(msg='Использование кода успешно'):
                assert write_success is True

        with allure.step('Проверка что код использован'):
            updated_code = await activation_code_dao.get_code(code_id)
            assert updated_code
            assert updated_code['is_used'] is True
