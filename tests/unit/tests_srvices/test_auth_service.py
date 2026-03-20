import allure
import pytest
from fastapi import HTTPException
from passlib.exc import PasswordValueError, UnknownHashError

from app.config import settings
from app.config_models.auth_config import AuthConfig
from app.services.auth import AuthService
from tests.core.auth_data_factory.fake_auth_data import auth_faker
from tests.core.const.mark_enums import FeaturesAuthMark, MarkTests, ModuleMarks, ServicesMark, tag, UnitTag

@tag(UnitTag.FAST)
@tag(MarkTests.UNITS)
@tag(ModuleMarks.SERVICES)
@tag(ServicesMark.AUTH)
@pytest.mark.asyncio
class TestAuthService:

    @allure.title("Проверка возвращения строки в качестве хеша пароля")
    @tag(FeaturesAuthMark.HASH_PASSWORD)
    async def test_hash_password_returns_string(self, auth_service: AuthService):
        password = auth_faker.generate_valid_password()

        with allure.step("Запрос на хеширование пароля"):
            hashed_password = await auth_service.hash_password(password)

        with allure.step("Проверка возвращаемого значения на строчный объект"):
            assert hashed_password
            assert isinstance(hashed_password, str)

    @allure.title("Проверка добавления `соли` в хеш пароля")
    @tag(FeaturesAuthMark.HASH_PASSWORD)
    async def test_hash_password_different_salts(self, auth_service: AuthService):
        password = auth_faker.generate_valid_password()

        with allure.step(f"Запрос на хеширование двух одинаковых паролей {password}"):
            hash1 = await auth_service.hash_password(password)
            hash2 = await auth_service.hash_password(password)

        with allure.step("Проверка разных хешей при хешировании двух одинаковых паролей"):
            assert hash1 != hash2
            assert await auth_service.verify_password(password, hash1)
            assert await auth_service.verify_password(password, hash2)

    @allure.title("Проверка возникновения ошбки `passlib` при попытке хешиирования пароля с null символами")
    @tag(FeaturesAuthMark.HASH_PASSWORD)
    @pytest.mark.parametrize(
        "invalid_password",
        [
            "pass\x00word",
            "\x00password",
            "password\x00",
            "pass\x00wor\x00d",
            "\x00",
            "привет\x00мир",
            "null\x00in\x00the\x00middle",
        ],
        ids=[
            "null_middle",
            "null_start",
            "null_end",
            "multiple_null",
            "only_null",
            "unicode_with_null",
            "many_nulls",
        ],
    )
    async def test_hash_password_rejects_null_characters(self, auth_service: AuthService, invalid_password):
        with allure.step("Проверка возникновения ошибки при запросе на хеширование пароля"):
            with pytest.raises(PasswordValueError):
                await auth_service.hash_password(invalid_password)

    @allure.title("Проверка верификации пароля на соответсвие хэшу")
    @tag(FeaturesAuthMark.VERIFY_PASSWORD)
    async def test_hash_password_verifies_correctly(self, auth_service: AuthService):
        password = auth_faker.generate_valid_password()

        with allure.step("Запрос на хеширование пароля"):
            hash_password = await auth_service.hash_password(password)

        with allure.step("Проверка на соответсвие хэша паролю"):
            assert await auth_service.verify_password(password, hash_password)

    @allure.title("Проверка верификации несоответсвующего хешу пароля. Возвращает False")
    @tag(FeaturesAuthMark.VERIFY_PASSWORD)
    async def test_hash_password_verifies_wrong_password(self, auth_service: AuthService):
        password1 = auth_faker.generate_valid_password()
        password2 = auth_faker.generate_valid_password()

        with allure.step(f"Запрос на хеширование пароля {password1}"):
            hash_password = await auth_service.hash_password(password1)

        with allure.step(f"Проверка на несоответствие пароля {password2} хэшу пароля {password1}"):
            assert not await auth_service.verify_password(password2, hash_password)

    @allure.title("Проверка верификации с фейковым хэшем")
    @tag(FeaturesAuthMark.VERIFY_PASSWORD)
    async def test_verify_password_with_fake_hash(self, auth_service: AuthService):
        fake_hash = auth_faker.faker.text(max_nb_chars=15)
        password = auth_faker.generate_valid_password()

        with allure.step(f"Попытка верификации пароля по фейковому хешу {fake_hash}"):
            with pytest.raises(UnknownHashError):
                assert await auth_service.verify_password(password, fake_hash)

    @allure.title("Проверка хеширования и верификации пустой строки")
    @tag(FeaturesAuthMark.VERIFY_PASSWORD)
    @pytest.mark.parametrize(
        "empty_password",
        [
            "",
            " ",
            " " * 50,
        ],
        ids=[
            "empty_string",
            "one_space",
            "wery_long_spaces_string",
        ],
    )
    async def test_verify_password_empty(self, auth_service: AuthService, empty_password):
        with allure.step("Запрос на хеширование пустого пароля"):
            hash_password = await auth_service.hash_password(empty_password)

        with allure.step("Попытка верефикации хеша пустого пароля"):
            assert await auth_service.verify_password(empty_password, hash_password)

    @allure.title("Создание токена авторизации")
    @tag(FeaturesAuthMark.CREATE_TOKEN)
    async def test_create_access_token_returns_string(self, auth_service: AuthService, test_user_data):
        user_dict = {
            "user_id": auth_faker.faker.uuid4(),
            "email": test_user_data.get("email"),
        }

        with allure.step("Запрос на создание токена"):
            access_token = await auth_service.create_access_token(user_dict)

        with allure.step("Проверка вернувшегося значения"):
            assert access_token
            assert isinstance(access_token, str)

    @allure.title("Проверка наличия времени жизни у токена")
    @tag(FeaturesAuthMark.CREATE_TOKEN)
    @tag(FeaturesAuthMark.DECODE_TOKEN)
    async def test_access_token_has_expiration(self, auth_service: AuthService, test_user_data):
        with allure.step("Запрос на создание токена доступа"):
            access_token = await auth_service.create_access_token(test_user_data)

        with allure.step("Декодирование токена"):
            payload = await auth_service.decode_token(access_token)
            has_exp = payload.get("exp", None)

        with allure.step("Проверка наличия времени жизни у токена"):
            assert has_exp is not None
            assert isinstance(has_exp, int)

    @allure.title("Проверка истечения access токена")
    @tag(FeaturesAuthMark.CREATE_TOKEN)
    async def test_access_token_expires(self, auth_service, monkeypatch):
        original_config = settings.auth_config

        modified_config = AuthConfig.model_validate({**original_config.model_dump(), "access_token_expire_time": 0})

        monkeypatch.setattr(settings, "auth_config", modified_config)

        with allure.step("Запрос на создание токена"):
            token = await auth_service.create_access_token({"user_id": "123"})

        with allure.step("Проверка возникновения исключения об истечении срока жизни токена"):
            with pytest.raises(HTTPException) as exc_info:
                await auth_service.decode_token(token)
            assert exc_info.value.status_code == 401
            assert "Token expired" in exc_info.value.detail

    @allure.title("Создание refresh токена")
    @tag(FeaturesAuthMark.REFRESH_TOKEN)
    async def test_create_refresh_token(self, auth_service: AuthService, test_user_data):
        with allure.step("Запрос на создание refresh token"):
            refresh_token = await auth_service.create_refresh_token(test_user_data)

        with allure.step("Проверка вернувшегося значения токена"):
            assert refresh_token
            assert isinstance(refresh_token, str)

    @allure.title("Проверка наличия времени жизни у refresh токена")
    @tag(FeaturesAuthMark.REFRESH_TOKEN)
    @tag(FeaturesAuthMark.DECODE_TOKEN)
    async def test_refresh_token_has_expiration(self, auth_service: AuthService, test_user_data):
        with allure.step("Запрос на создание refresh токена"):
            refresh_token = await auth_service.create_refresh_token(test_user_data)

        with allure.step("Декодирование токена"):
            payload = await auth_service.decode_token(refresh_token)
            has_exp = payload.get("exp", None)

        with allure.step("Проверка наличия времени жизни у токена"):
            assert has_exp is not None
            assert isinstance(has_exp, int)

    @allure.title("Проверка истечения access токена")
    @tag(FeaturesAuthMark.REFRESH_TOKEN)
    async def test_refresh_token_expires(self, auth_service: AuthService, monkeypatch, test_user_data):
        original_config = settings.auth_config

        modified_config = AuthConfig.model_validate({**original_config.model_dump(), "refresh_token_expire_time": 0})

        monkeypatch.setattr(settings, "auth_config", modified_config)

        with allure.step("Запрос на создание refresh токена"):
            token = await auth_service.create_refresh_token(test_user_data)

        with allure.step("Проверка возникновения исключения об истечении срока жизни refresh токена"):
            with pytest.raises(HTTPException) as exc_info:
                await auth_service.decode_token(token)
            assert exc_info.value.status_code == 401
            assert "Token expired" in exc_info.value.detail

    @allure.title("Проверка валидности данных access token после декодирования")
    @tag(FeaturesAuthMark.DECODE_TOKEN)
    @tag(FeaturesAuthMark.CREATE_TOKEN)
    async def test_decode_access_token_valid(self, auth_service: AuthService, test_user_data):
        data_user = {"user_id": auth_faker.faker.uuid4(), "email": test_user_data.get("email")}

        with allure.step("Запрос на создание access token"):
            token = await auth_service.create_access_token(data_user)

        with allure.step("Запрос на декодирование access token"):
            payload = await auth_service.decode_token(token)

        with allure.step("Проверка данных токна"):
            assert payload
            assert payload["user_id"] == data_user["user_id"]
            assert payload["email"] == data_user["email"]

    @allure.title("Проверка валидности данных refresh token после декодирования")
    @tag(FeaturesAuthMark.DECODE_TOKEN)
    @tag(FeaturesAuthMark.CREATE_TOKEN)
    async def test_decode_refresh_token_valid(self, auth_service: AuthService, test_user_data):
        data_user = {"user_id": auth_faker.faker.uuid4(), "email": test_user_data.get("email")}

        with allure.step("Запрос на создание access token"):
            token = await auth_service.create_refresh_token(data_user)

        with allure.step("Запрос на декодирование access token"):
            payload = await auth_service.decode_token(token)

        with allure.step("Проверка данных токна"):
            assert payload
            assert payload["user_id"] == data_user["user_id"]
            assert payload["email"] == data_user["email"]

    @allure.title("Попытка декадирования фейкового токена")
    @tag(FeaturesAuthMark.DECODE_TOKEN)
    async def test_decode_fake_token(self, auth_service: AuthService):
        fake_token = auth_faker.faker.uuid4()

        with allure.step("Попытка декодирования фейкового токена"):
            with pytest.raises(HTTPException) as exc_info:
                await auth_service.decode_token(fake_token)
            assert exc_info.value.status_code == 401
            assert "Invalid token" in exc_info.value.detail

    @allure.title("Попытка декодирования токена с неверным sekret-key")
    @tag(FeaturesAuthMark.REFRESH_TOKEN)
    async def test_refresh_invalid_signature(self, auth_service: AuthService, monkeypatch, test_user_data):
        with allure.step("Запрос на создание refresh токена"):
            token = await auth_service.create_refresh_token(test_user_data)

        with allure.step("Подмена ключа доступа на фейковый"):
            original_config = settings.auth_config
            modified_config = AuthConfig.model_validate(
                {**original_config.model_dump(), "secret_key": auth_faker.faker.text(max_nb_chars=20)}
            )

            monkeypatch.setattr(settings, "auth_config", modified_config)

            new_auth_service = AuthService()

        with allure.step("Проверка возникновения исключения при подмене подписи"):
            with pytest.raises(HTTPException) as exc_info:
                await new_auth_service.decode_token(token)
            assert exc_info.value.status_code == 401
            assert "Invalid token" in exc_info.value.detail
