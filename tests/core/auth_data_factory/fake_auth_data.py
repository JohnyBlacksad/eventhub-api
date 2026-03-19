import random

from faker import Faker


class FakeAuthData:
    def __init__(self, faker: Faker):
        self.faker = faker
        self.emoji_set = [
            "😀",
            "😂",
            "😍",
            "🥳",
            "😎",
            "😭",
            "😡",
            "👍",
            "👎",
            "👌",
            "🎉",
            "🔥",
            "✨",
            "⭐",
            "💀",
            "☠️",
            "❤️",
            "🧡",
            "💛",
            "💚",
            "💙",
            "💜",
            "🖤",
            "🤍",
            "🤎",
            "💔",
            "❣️",
            "💕",
            "💞",
            "💓",
            "💗",
            "💖",
            "💘",
            "💝",
            "💟",
            "☮️",
            "✝️",
            "☪️",
            "🕉️",
            "☸️",
            "✡️",
            "🔯",
            "🕎",
            "☯️",
            "☦️",
            "🛐",
            "⛎",
            "♈",
            "♉",
            "♊",
            "♋",
            "♌",
            "♍",
            "♎",
            "♏",
            "♐",
            "♑",
            "♒",
            "♓",
            "⛎",
            "🇺🇸",
            "🇬🇧",
            "🇨🇦",
            "🇦🇺",
            "🇯🇵",
            "🇨🇳",
            "🇮🇳",
            "🇧🇷",
            "🇫🇷",
            "🇩🇪",
            "🇮🇹",
            "🇪🇸",
            "🇲🇽",
            "🇰🇷",
            "🇷🇺",
            "🇿🇦",
            "🇳🇬",
            "🇸🇦",
            "🇹🇷",
            "🇻🇳",
            "🐶",
            "🐱",
            "🐭",
            "🐹",
            "🐰",
            "🦊",
            "🐻",
            "🐼",
            "🐨",
            "🦁",
            "🐮",
            "🐸",
            "🐙",
            "🦑",
            "🦐",
            "🦞",
            "🐠",
            "🐟",
            "🐡",
            "🐬",
        ]

    def generate_auth_config_dict(self, **kwargs):
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
        if count > 1:
            return random.choices(self.emoji_set, k=count)
        return random.choice(self.emoji_set)

    def generate_valid_password(
        self, length=None, special_chars=True, digits=True, upper_case=True, lower_case=True, emoji_count=0
    ):
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
