"""Тесты на конкурентность для сервисов EventHub API.

Модуль содержит тесты для проверки корректной работы сервисов
при одновременном выполнении операций (race conditions).

Критичные сценарии:
- Использование одного кода активации несколькими пользователями
- Двойное использование кода одним пользователем

Note: Тесты на конкурентность для event registration и user registration
требуют уникальных индексов в MongoDB и не будут корректно работать
на mongomock. Эти сценарии должны быть покрыты integration тестами.
"""

import asyncio

import allure
import pytest

from app.schemas.enums.user_enums.users_status import UserRoleEnum
from tests.core.const.mark_enums import (
    FeaturesActivationCodeMark,
    MarkTests,
    ModuleMarks,
    ServicesMark,
    UnitTag,
    tag,
)
from tests.core.user_data_factory.fake_user_data import faker


@tag(MarkTests.UNITS)
@tag(ModuleMarks.SERVICES)
@tag(ServicesMark.ACTIVATION_CODE)
@tag(UnitTag.CONCURENCY)
@pytest.mark.asyncio
class TestActivationCodeConcurrency:
    """Тесты на конкурентность для ActivationCodeService."""

    @allure.title("Гонка: два пользователя пытаются использовать один код одновременно")
    @tag(FeaturesActivationCodeMark.USE_CODE)
    async def test_race_condition_use_code_by_multiple_users(
        self,
        activation_code_dao,
        user_service,
        subtests,
    ):
        """Проверка что только один пользователь может использовать код активации.

        Сценарий:
        1. Создаётся код активации для роли ORGANIZER
        2. Два пользователя одновременно пытаются активировать код
        3. Только один должен succeed, второй получает ошибку

        Это критичный сценарий — нельзя допустить чтобы один код
        дали двум разным пользователям.
        """
        # Создаём код активации
        code_data = {"code": "test-race-code", "role": UserRoleEnum.ORGANIZER}
        code_id = await activation_code_dao.create_code(code_data)
        code = await activation_code_dao.get_code(code_id)
        code_str = code["code"]

        # Создаём двух пользователей
        user1_data = faker.get_user_register_model()
        user2_data = faker.get_user_register_model()

        user1 = await user_service.register_user(user1_data)
        user2 = await user_service.register_user(user2_data)

        results = {"user1": None, "user2": None, "user1_error": None, "user2_error": None}

        async def try_upgrade_user1():
            try:
                result = await user_service.upgrade_role(str(user1.id), code_str)
                results["user1"] = result
            except Exception as e:
                results["user1_error"] = e

        async def try_upgrade_user2():
            try:
                result = await user_service.upgrade_role(str(user2.id), code_str)
                results["user2"] = result
            except Exception as e:
                results["user2_error"] = e

        with allure.step("Запуск конкурентных запросов на использование кода"):
            # Запускаем оба запроса "одновременно"
            await asyncio.gather(try_upgrade_user1(), try_upgrade_user2())

        with allure.step("Проверка результатов"):
            with subtests.test(msg="Только один пользователь успешно активировал код"):
                success_count = sum([
                    1 if results["user1"] is not None else 0,
                    1 if results["user2"] is not None else 0,
                ])
                assert success_count == 1, "Только один пользователь должен успешно использовать код"

            with subtests.test(msg="Второй пользователь получил ошибку"):
                error_count = sum([
                    1 if results["user1_error"] is not None else 0,
                    1 if results["user2_error"] is not None else 0,
                ])
                assert error_count == 1, "Второй пользователь должен получить ошибку"

            with subtests.test(msg="Код помечен как использованный"):
                updated_code = await activation_code_dao.get_code(code_id)
                assert updated_code["is_used"] is True
                assert updated_code["activated_by"] is not None

            with subtests.test(msg="activated_by установлен в победителя"):
                if results["user1"] is not None:
                    assert str(updated_code["activated_by"]) == str(user1.id)
                else:
                    assert str(updated_code["activated_by"]) == str(user2.id)

    @allure.title("Гонка: один пользователь дважды использует один код")
    @tag(FeaturesActivationCodeMark.USE_CODE)
    async def test_race_condition_same_user_double_use(
        self,
        activation_code_dao,
        user_service,
        subtests,
    ):
        """Проверка что пользователь не может дважды использовать один код.

        Сценарий:
        1. Создаётся код активации
        2. Один пользователь отправляет два запроса одновременно
        3. Только один должен succeed
        """
        # Создаём код активации
        code_data = {"code": "test-double-use-code", "role": UserRoleEnum.ORGANIZER}
        code_id = await activation_code_dao.create_code(code_data)
        code = await activation_code_dao.get_code(code_id)
        code_str = code["code"]

        # Создаём пользователя
        user_data = faker.get_user_register_model()
        user = await user_service.register_user(user_data)
        user_id = str(user.id)

        results = {"success": 0, "errors": []}

        async def try_upgrade():
            try:
                result = await user_service.upgrade_role(user_id, code_str)
                results["success"] += 1
                results["result"] = result
            except Exception as e:
                results["errors"].append(e)

        with allure.step("Запуск двух конкурентных запросов от одного пользователя"):
            # Запускаем два запроса "одновременно"
            await asyncio.gather(try_upgrade(), try_upgrade())

        with allure.step("Проверка результатов"):
            with subtests.test(msg="Только один запрос успешен"):
                assert results["success"] == 1, "Только один запрос должен быть успешным"

            with subtests.test(msg="Второй запрос получил ошибку"):
                assert len(results["errors"]) == 1, "Второй запрос должен вернуть ошибку"

            with subtests.test(msg="Код помечен как использованный"):
                updated_code = await activation_code_dao.get_code(code_id)
                assert updated_code["is_used"] is True
