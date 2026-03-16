from faker import Faker
from bson import ObjectId
from app.schemas.users import UserRegisterModel, UserResponseModel
from app.schemas.enums.user_enums.users_status import UserRoleEnum
import random

faker = Faker('ru_RU')

class FakeUserData:
    def __init__(self, faker: Faker):
        self.faker = faker

    def get_user_register_data_dict(self, **kwargs) -> dict:
        user_data = {
            "email": self.faker.email(domain='@test.com'),
            "firstName": self.faker.first_name(),
            'lastName': self.faker.last_name(),
            'phoneNumber': self.faker.phone_number(),
            'password': self.faker.password(length=12)
        }

        user_data.update(**kwargs)

        return user_data

    def get_user_register_model(self) -> UserRegisterModel:
        user_reg = self.get_user_register_data_dict()
        return UserRegisterModel.model_validate(user_reg, from_attributes=True)

    def generate_user_id(self) -> str:
        random_id = str(ObjectId())
        return random_id

    def get_role(self) -> str:
        roles = [UserRoleEnum.ADMIN, UserRoleEnum.ORGANIZER]
        return random.choice(roles)


faker = FakeUserData(Faker('ru_RU'))