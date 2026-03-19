import pytest

from app.config_models.auth_config import AuthConfig
from app.services.auth import AuthService
from tests.core.auth_data_factory.fake_auth_data import auth_faker
from tests.core.user_data_factory.fake_user_data import faker


@pytest.fixture
def mock_auth_settings():
    auth_config = auth_faker.generate_auth_config_dict()
    return AuthConfig.model_validate(auth_config)


@pytest.fixture
def auth_service(mock_auth_settings: AuthConfig):
    return AuthService()


@pytest.fixture
def test_user_data():
    fake_user = faker.get_user_register_data_dict()
    return fake_user


@pytest.fixture
async def valid_token(auth_service: AuthService, test_user_data: dict):
    return await auth_service.create_access_token(test_user_data)
