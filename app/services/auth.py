import jwt
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from fastapi import HTTPException, status
from app.config import settings

class AuthService:

    def __init__(self):
        self.pwd_context = CryptContext(schemes=[settings.auth_config.crypto_schemas], deprecated='auto')
        self.secret_key = settings.auth_config.secret_key.encode()
        self.algorithm = settings.auth_config.algorithm

    def hash_password(self, password: str) -> str:
        return self.pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return self.pwd_context.verify(plain_password, hashed_password)

    def create_access_token(self, data: dict):
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.auth_config.access_token_expire_time)
        to_encode.update({'exp': expire})
        token = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return token

    def create_refresh_token(self, data: dict):
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(days=settings.auth_config.refresh_token_expire_time)
        to_encode.update({'exp': expire})
        refresh_token = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return refresh_token

    def decode_token(self, token: str):
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Token expired')
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid token')