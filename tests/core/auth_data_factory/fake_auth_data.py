"""Фабрика тестовых данных для аутентификации.

Модуль содержит класс FakeAuthData для генерации случайных
данных для тестирования AuthService: JWT конфиги, пароли.

Используется в тестах аутентификации для создания тестовых данных.
"""

import random

from faker import Faker


class FakeAuthData:
    """Фабрика данных аутентификации для тестов.

    Генерирует тестовые JWT конфиги, валидные пароли с различными
    опциями (спецсимволы, цифры, emoji).

    Attributes:
        faker: Faker instance для генерации данных.
        emoji_set: Набор emoji для тестирования паролей.
    """

    def __init__(self, faker: Faker):
        """Инициализировать фабрику с Faker instance.

        Args:
            faker: Faker instance для генерации данных.
        """
        self.faker = faker
        self.emoji_set = [
            "😀",
            "😂",
            # ... (emoji list remains the same)
            "🐬",
        ]

    def generate_auth_config_dict(self, **kwargs):
        """Сгенерировать словарь конфигурации JWT для тестов.

        Args:
            **kwargs: Дополнительные поля для переопределения.

        Returns:
            dict: Словарь с JWT конфигурацией (crypto_schemas, secret_key, algorithm, etc.).
        """
        config = {
            "crypto_schemas": "bcrypt",
            "secret_key": "tests-secret-key-for-tests-only",
            "algorithm": "HS256",
            "access_token_expire_time": 30,
            "refresh_token_expire_time": 7,
        }
        config.update(**kwargs)
        return config

    def get_emoji(self, count: int = 1):
        """Получить случайный emoji или список emoji.

        Args:
            count: Количество emoji для возврата (default: 1).

        Returns:
            str | list: Один emoji или список emoji.
        """
        if count > 1:
            return random.choices(self.emoji_set, k=count)
        return random.choice(self.emoji_set)

    def generate_valid_password(
        self, length=None, special_chars=True, digits=True, upper_case=True, lower_case=True, emoji_count=0
    ):
        """Сгенерировать валидный пароль с опциями.

        Args:
            length: Длина пароля (random 5-13 if None).
            special_chars: Включить спецсимволы (default: True).
            digits: Включить цифры (default: True).
            upper_case: Включить заглавные буквы (default: True).
            lower_case: Включить строчные буквы (default: True).
            emoji_count: Количество emoji (default: 0).

        Returns:
            str: Сгенерированный пароль.
        """
        if length is None:
            length = random.randint(5, 13)

        base_length = length - emoji_count
        if base_length < 1:
            base_length = 1

        base_password = self.faker.password(
            length=base_length,
            special_chars=special_chars,
            digits=digits,
            upper_case=upper_case,
            lower_case=lower_case,
        )

        chars = list(base_password)

        if emoji_count > 0:
            emojis = self.get_emoji(count=emoji_count)
            if isinstance(emojis, list):
                chars.extend(emojis)
            else:
                chars.append(emojis)
            random.shuffle(chars)

        return "".join(chars)

    def generate_list_valid_passwords(
        self,
        count_passwords: int = 2,
        length=None,
        special_chars=True,
        digits=True,
        upper_case=True,
        lower_case=True,
        emoji_count=0,
    ):
        """Сгенерировать список валидных паролей.

        Args:
            count_passwords: Количество паролей для генерации.
            length: Длина каждого пароля.
            special_chars: Включить спецсимволы.
            digits: Включить цифры.
            upper_case: Включить заглавные буквы.
            lower_case: Включить строчные буквы.
            emoji_count: Количество emoji в каждом пароле.

        Returns:
            list[str]: Список сгенерированных паролей.
        """
        password_list = [
            self.generate_valid_password(
                length=length,
                special_chars=special_chars,
                digits=digits,
                upper_case=upper_case,
                lower_case=lower_case,
                emoji_count=emoji_count,
            )
            for _ in range(count_passwords)
        ]

        return password_list


auth_faker = FakeAuthData(faker=Faker("ru_RU"))
