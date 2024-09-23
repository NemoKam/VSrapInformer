import random
import string
import hashlib
from datetime import timedelta, datetime, timezone

import jwt

from core.config import JWT_SECRET, JWT_ALGORITHM, JWT_TIME_LIVE


def generate_random_string(length: int = 128, only_digits: bool = False) -> str:
    chars = string.digits

    if not only_digits: chars += string.ascii_uppercase 

    return ''.join(random.choice(chars) for _ in range(length))

def hash_password(password: str) -> str:
    password_bytes = password.encode('utf-8')
    hash_object = hashlib.sha256(password_bytes)

    return hash_object.hexdigest()

def generate_jwt(payload: dict, exp: int = JWT_TIME_LIVE) -> str:
    payload["exp"] = datetime.now(timezone.utc) + timedelta(seconds=exp)

    token = jwt.encode(payload, JWT_SECRET, JWT_ALGORITHM)

    return token

def decode_jwt(token: str) -> dict | None:
    try:
        decoded_jwt =jwt.decode(token, JWT_SECRET, JWT_ALGORITHM)

        return decoded_jwt
    except:
        return None