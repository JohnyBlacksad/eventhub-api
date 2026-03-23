"""Юнит-тесты для ActivationCodeService.

Модуль содержит тесты для бизнес-логики сервиса кодов активации:
создание, получение, удаление кодов.
"""

from datetime import datetime, timezone
from uuid import uuid4

import allure
import pytest
from bson import ObjectId
from fastapi import HTTPException, status

from app.schemas.activation_code import CodeFiltersResponse
from app.schemas.enums.user_enums.users_status import UserRoleEnum
from tests.core.const.mark_enums import (
    FeaturesActivationCodeMark,
    MarkTests,
    ModuleMarks,
    ServicesMark,
    tag,
)
from tests.core.event_data_factory.fake_event_data import event_faker


@tag(MarkTests.UNITS)
@tag(ModuleMarks.SERVICES)
@tag(ServicesMark.ACTIVATION_CODE)
@pytest.mark.asyncio
class TestActivationCodeService:
    """Тесты для ActivationCodeService."""

    @allure.title("Создание кода активации с автогенерацией")
    @tag(FeaturesActivationCodeMark.CREATE_CODE)
    async def test_create_code_with_auto_generation(
        self, code_service, subtests
    ):
        """Проверка создания кода с автоматически сгенерированным значением."""
        with allure.step("Создание кода с автогенерацией"):
            result = await code_service.create_code(
                role=UserRoleEnum.ORGANIZER, code=None
            )

        with allure.step("Проверка результата"):
            with subtests.test(msg="Проверка наличия ID"):
                assert result.id is not None

            with subtests.test(msg="Проверка роли"):
                assert result.role == UserRoleEnum.ORGANIZER

            with subtests.test(msg="Проверка наличия кода"):
                assert result.code is not None
                assert len(result.code) == 36  # UUID format

            with subtests.test(msg="Проверка is_used=False"):
                assert result.is_used is False

            with subtests.test(msg="Проверка created_at"):
                assert result.created_at is not None

    @allure.title("Создание кода активации с пользовательским значением")
    @tag(FeaturesActivationCodeMark.CREATE_CODE)
    async def test_create_code_with_custom_code(
        self, code_service, subtests
    ):
        """Проверка создания кода с заданным пользователем значением."""
        custom_code = str(uuid4())

        with allure.step("Создание кода с кастомным значением"):
            result = await code_service.create_code(
                role=UserRoleEnum.ADMIN, code=custom_code
            )

        with allure.step("Проверка результата"):
            with subtests.test(msg="Проверка ID"):
                assert result.id is not None

            with subtests.test(msg="Проверка роли"):
                assert result.role == UserRoleEnum.ADMIN

            with subtests.test(msg="Проверка кастомного кода"):
                assert result.code == custom_code

            with subtests.test(msg="Проверка is_used=False"):
                assert result.is_used is False

    @allure.title("Создание ORGANIZER кода по умолчанию")
    @tag(FeaturesActivationCodeMark.CREATE_CODE)
    async def test_create_code_default_role_organizer(
        self, code_service, subtests
    ):
        """Проверка что роль ORGANIZER используется по умолчанию."""
        with allure.step("Создание кода без указания роли"):
            result = await code_service.create_code()

        with allure.step("Проверка роли ORGANIZER"):
            with subtests.test(msg="Проверка роли"):
                assert result.role == UserRoleEnum.ORGANIZER

            with subtests.test(msg="Проверка наличия кода"):
                assert result.code is not None

    @allure.title("Получение кода активации по ID")
    @tag(FeaturesActivationCodeMark.GET_CODE)
    async def test_get_code_returns_code(
        self, code_service, activation_code_dao, code_factory_data, subtests
    ):
        """Проверка получения существующего кода."""
        code_data = code_factory_data()
        code_id = await activation_code_dao.create_code(code_data)

        with allure.step(f"Получение кода по ID: {code_id}"):
            result = await code_service.get_code(code_id)

        with allure.step("Проверка результата"):
            with subtests.test(msg="Проверка ID"):
                assert result.id == code_id

            with subtests.test(msg="Проверка кода"):
                assert result.code == code_data["code"]

            with subtests.test(msg="Проверка роли"):
                assert result.role == code_data["role"]

            with subtests.test(msg="Проверка is_used"):
                assert result.is_used is False

    @allure.title("Получение несуществующего кода вызывает 404")
    @tag(FeaturesActivationCodeMark.GET_CODE)
    async def test_get_code_raises_404_if_not_found(
        self, code_service
    ):
        """Проверка что получение несуществующего кода вызывает HTTPException 404."""
        fake_code_id = event_faker.generate_random_id()

        with allure.step(f"Попытка получения несуществующего кода: {fake_code_id}"):
            with pytest.raises(HTTPException) as exc_info:
                await code_service.get_code(fake_code_id)

        with allure.step("Проверка HTTPException 404"):
            assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
            assert exc_info.value.detail == "Code not found"

    @allure.title("Получение списка кодов без фильтров")
    @tag(FeaturesActivationCodeMark.GET_CODES)
    async def test_get_codes_returns_list(
        self, code_service, activation_codes_factory, subtests
    ):
        """Проверка получения списка кодов без фильтров."""
        codes_count = 5

        with allure.step(f"Создание {codes_count} кодов"):
            await activation_codes_factory(count=codes_count)

        with allure.step("Получение списка кодов"):
            result = await code_service.get_codes(skip=0, limit=100)

        with allure.step("Проверка результата"):
            with subtests.test(msg="Проверка количества кодов"):
                assert len(result.codes) == codes_count

            with subtests.test(msg="Проверка что все коды имеют required поля"):
                for code in result.codes:
                    assert code.id is not None
                    assert code.code is not None
                    assert code.role is not None
                    assert code.is_used is False
                    assert code.created_at is not None

    @allure.title("Получение списка кодов с пагинацией")
    @tag(FeaturesActivationCodeMark.GET_CODES)
    async def test_get_codes_with_pagination(
        self, code_service, activation_codes_factory, subtests
    ):
        """Проверка пагинации при получении списка кодов."""
        total_count = 10
        page_size = 3

        with allure.step(f"Создание {total_count} кодов"):
            await activation_codes_factory(count=total_count)

        with allure.step("Получение первой страницы"):
            page1 = await code_service.get_codes(skip=0, limit=page_size)

        with allure.step("Получение второй страницы"):
            page2 = await code_service.get_codes(skip=page_size, limit=page_size)

        with allure.step("Проверка пагинации"):
            with subtests.test(msg="Проверка размера страницы 1"):
                assert len(page1.codes) == page_size

            with subtests.test(msg="Проверка размера страницы 2"):
                assert len(page2.codes) == page_size

            with subtests.test(msg="Проверка что страницы не пересекаются"):
                page1_ids = {code.id for code in page1.codes}
                page2_ids = {code.id for code in page2.codes}
                assert page1_ids.isdisjoint(page2_ids)

    @allure.title("Получение списка кодов с фильтром is_used")
    @tag(FeaturesActivationCodeMark.FILTER_CODES)
    async def test_get_codes_filter_by_is_used(
        self, code_service, activation_code_dao, subtests
    ):
        """Проверка фильтрации кодов по флагу is_used."""
        with allure.step("Создание кодов с разными is_used"):
            code1_data = {"code": str(uuid4()), "role": UserRoleEnum.ORGANIZER}
            code2_data = {"code": str(uuid4()), "role": UserRoleEnum.ADMIN}
            code3_data = {"code": str(uuid4()), "role": UserRoleEnum.ORGANIZER}

            id1 = await activation_code_dao.create_code(code1_data)
            id2 = await activation_code_dao.create_code(code2_data)
            id3 = await activation_code_dao.create_code(code3_data)

            # Помечаем code1 и code3 как использованные
            await activation_code_dao.use_code(code1_data["code"], str(ObjectId()))
            await activation_code_dao.use_code(code3_data["code"], str(ObjectId()))

        with allure.step("Получение неиспользованных кодов (is_used=False)"):
            filter_obj = CodeFiltersResponse(is_used=False)  # type: ignore
            unused_result = await code_service.get_codes(filters=filter_obj)

        with allure.step("Получение использованных кодов (is_used=True)"):
            filter_obj_used = CodeFiltersResponse(is_used=True)  # type: ignore
            used_result = await code_service.get_codes(filters=filter_obj_used)

        with allure.step("Проверка фильтрации"):
            with subtests.test(msg="Проверка количества неиспользованных"):
                assert len(unused_result.codes) == 1
                assert unused_result.codes[0].id == id2

            with subtests.test(msg="Проверка количества использованных"):
                assert len(used_result.codes) == 2

    @allure.title("Получение списка кодов с фильтром role")
    @tag(FeaturesActivationCodeMark.FILTER_CODES)
    async def test_get_codes_filter_by_role(
        self, code_service, activation_code_dao, subtests
    ):
        """Проверка фильтрации кодов по роли."""
        with allure.step("Создание кодов с разными ролями"):
            organizer_code_data = {"code": str(uuid4()), "role": UserRoleEnum.ORGANIZER}
            admin_code_data = {"code": str(uuid4()), "role": UserRoleEnum.ADMIN}

            await activation_code_dao.create_code(organizer_code_data)
            await activation_code_dao.create_code(admin_code_data)

        with allure.step("Получение ORGANIZER кодов"):
            filter_obj = CodeFiltersResponse(role=UserRoleEnum.ORGANIZER)
            organizer_result = await code_service.get_codes(filters=filter_obj)

        with allure.step("Получение ADMIN кодов"):
            filter_obj_admin = CodeFiltersResponse(role=UserRoleEnum.ADMIN)
            admin_result = await code_service.get_codes(filters=filter_obj_admin)

        with allure.step("Проверка фильтрации по ролям"):
            with subtests.test(msg="Проверка ORGANIZER кодов"):
                assert len(organizer_result.codes) == 1
                assert organizer_result.codes[0].role == UserRoleEnum.ORGANIZER

            with subtests.test(msg="Проверка ADMIN кодов"):
                assert len(admin_result.codes) == 1
                assert admin_result.codes[0].role == UserRoleEnum.ADMIN

    @allure.title("Получение списка кодов с фильтром created_at")
    @tag(FeaturesActivationCodeMark.FILTER_CODES)
    async def test_get_codes_filter_by_created_at(
        self, code_service, activation_code_dao, subtests
    ):
        """Проверка фильтрации кодов по дате создания."""
        from datetime import timedelta

        with allure.step("Создание кодов с разными датами создания"):
            now = datetime.now(timezone.utc)
            past = now - timedelta(days=5)

            # Создаём код с датой в прошлом
            code1_data = {"code": str(uuid4()), "role": UserRoleEnum.ORGANIZER, "created_at": past}
            # Создаём код с текущей датой
            code2_data = {"code": str(uuid4()), "role": UserRoleEnum.ORGANIZER, "created_at": now}

            await activation_code_dao.create_code(code1_data)
            await activation_code_dao.create_code(code2_data)

        with allure.step("Получение всех кодов для проверки что они созданы"):
            all_codes = await code_service.get_codes()
            assert len(all_codes.codes) == 2

        with allure.step("Проверка что коды отсортированы по created_at DESC"):
            # Первый код должен быть новее (создан позже)
            with subtests.test(msg="Проверка сортировки"):
                assert all_codes.codes[0].created_at >= all_codes.codes[1].created_at

    @allure.title("Комбинированная фильтрация (is_used + role)")
    @tag(FeaturesActivationCodeMark.FILTER_CODES)
    async def test_get_codes_combined_filters(
        self, code_service, activation_code_dao, subtests
    ):
        """Проверка комбинированной фильтрации кодов."""
        with allure.step("Создание кодов с разными комбинациями"):
            # ORGANIZER, is_used=False
            code1_data = {"code": str(uuid4()), "role": UserRoleEnum.ORGANIZER}
            # ORGANIZER, is_used=True
            code2_data = {"code": str(uuid4()), "role": UserRoleEnum.ORGANIZER}
            # ADMIN, is_used=False
            code3_data = {"code": str(uuid4()), "role": UserRoleEnum.ADMIN}

            id1 = await activation_code_dao.create_code(code1_data)
            id2 = await activation_code_dao.create_code(code2_data)
            id3 = await activation_code_dao.create_code(code3_data)

            # Помечаем code2 как использованный
            await activation_code_dao.use_code(code2_data["code"], str(ObjectId()))

        with allure.step("Получение неиспользованных ORGANIZER кодов"):
            filter_obj = CodeFiltersResponse(
                is_used=False,  # type: ignore
                role=UserRoleEnum.ORGANIZER,
            )
            result = await code_service.get_codes(filters=filter_obj)

        with allure.step("Проверка комбинированной фильтрации"):
            with subtests.test(msg="Проверка количества"):
                assert len(result.codes) == 1

            with subtests.test(msg="Проверка ID"):
                assert result.codes[0].id == id1

            with subtests.test(msg="Проверка is_used"):
                assert result.codes[0].is_used is False

            with subtests.test(msg="Проверка role"):
                assert result.codes[0].role == UserRoleEnum.ORGANIZER

    @allure.title("Удаление существующего кода активации")
    @tag(FeaturesActivationCodeMark.DELETE_CODE)
    async def test_delete_code_returns_true(
        self, code_service, created_activation_code, subtests
    ):
        """Проверка удаления существующего кода."""
        code_id = str(created_activation_code["_id"])

        with allure.step(f"Удаление кода по ID: {code_id}"):
            result = await code_service.delete_code(code_id)

        with allure.step("Проверка результата"):
            with subtests.test(msg="Проверка что результат True"):
                assert result is True

        with allure.step("Проверка что код удалён из БД"):
            with pytest.raises(HTTPException) as exc_info:
                await code_service.get_code(code_id)
            assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    @allure.title("Удаление несуществующего кода вызывает 404")
    @tag(FeaturesActivationCodeMark.DELETE_CODE)
    async def test_delete_code_raises_404_if_not_found(
        self, code_service
    ):
        """Проверка что удаление несуществующего кода вызывает HTTPException 404."""
        fake_code_id = event_faker.generate_random_id()

        with allure.step(f"Попытка удаления несуществующего кода: {fake_code_id}"):
            with pytest.raises(HTTPException) as exc_info:
                await code_service.delete_code(fake_code_id)

        with allure.step("Проверка HTTPException 404"):
            assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
            assert exc_info.value.detail == "Code not found"

    @allure.title("Получение пустого списка кодов")
    @tag(FeaturesActivationCodeMark.GET_CODES)
    async def test_get_codes_empty_list(
        self, code_service, activation_code_dao, subtests
    ):
        """Проверка получения пустого списка кодов."""
        with allure.step("Очистка коллекции (если есть данные)"):
            await activation_code_dao.collection.delete_many({})

        with allure.step("Получение списка кодов"):
            result = await code_service.get_codes(skip=0, limit=100)

        with allure.step("Проверка пустого списка"):
            with subtests.test(msg="Проверка что список пуст"):
                assert len(result.codes) == 0

    @allure.title("Конвертация activated_by в строку")
    @tag(FeaturesActivationCodeMark.GET_CODE)
    async def test_get_code_converts_activated_by_to_string(
        self, code_service, activation_code_dao, subtests
    ):
        """Проверка что activated_by конвертируется в строку."""
        with allure.step("Создание и использование кода"):
            code_data = {"code": str(uuid4()), "role": UserRoleEnum.ORGANIZER}
            code_id = await activation_code_dao.create_code(code_data)
            user_id = event_faker.generate_random_id()

            await activation_code_dao.use_code(code_data["code"], user_id)

        with allure.step("Получение кода"):
            result = await code_service.get_code(code_id)

        with allure.step("Проверка activated_by"):
            with subtests.test(msg="Проверка что activated_by не None"):
                assert result.activated_by is not None

            with subtests.test(msg="Проверка что activated_by это строка"):
                assert isinstance(result.activated_by, str)

            with subtests.test(msg="Проверка что activated_by равен user_id"):
                assert result.activated_by == user_id

    @allure.title("Получение списка с использованными кодами показывает activated_at и activated_by")
    @tag(FeaturesActivationCodeMark.GET_CODES)
    async def test_get_codes_shows_activated_fields_for_used_codes(
        self, code_service, activation_code_dao, subtests
    ):
        """Проверка что использованные коды в списке имеют activated_at и activated_by."""
        user_id = event_faker.generate_random_id()

        with allure.step("Создание и использование кода"):
            code_data = {"code": str(uuid4()), "role": UserRoleEnum.ORGANIZER}
            await activation_code_dao.create_code(code_data)
            await activation_code_dao.use_code(code_data["code"], user_id)

        with allure.step("Получение списка использованных кодов"):
            filter_obj = CodeFiltersResponse(is_used=True)  # type: ignore
            result = await code_service.get_codes(filters=filter_obj)

        with allure.step("Проверка activated полей"):
            with subtests.test(msg="Проверка что activated_at установлен"):
                assert result.codes[0].activated_at is not None

            with subtests.test(msg="Проверка что activated_by установлен"):
                assert result.codes[0].activated_by is not None
                assert isinstance(result.codes[0].activated_by, str)
                assert result.codes[0].activated_by == user_id
