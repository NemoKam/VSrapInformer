import uuid
import random
import string
import hashlib
from datetime import timedelta, datetime, timezone

import aiohttp
import jwt
from fastapi import Depends, HTTPException, Header, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from fastapp import exceptions
from core import config
from fastapp.database import get_db
from . import crud, models, schemas
from logger import get_logger

py_logger = get_logger("dependencies")


def generate_random_string(length: int = 128, only_digits: bool = False) -> str:
    chars = string.digits

    if not only_digits:
        chars += string.ascii_uppercase

    return ''.join(random.choice(chars) for _ in range(length))


def hash_password(password: str) -> str:
    password_bytes = password.encode('utf-8')
    hash_object = hashlib.sha256(password_bytes)

    return hash_object.hexdigest()


def _get_utc_now():
    current_utc_time = datetime.now(timezone.utc)

    return current_utc_time


def _create_access_token(payload: dict, minutes: int | None = None) -> schemas.JwtTokenCreate:
    expire = _get_utc_now() + timedelta(
        minutes=minutes or config.ACCESS_TOKEN_EXPIRES_MINUTES
    )

    payload[config.EXP] = expire

    token = schemas.JwtTokenCreate(
        token=jwt.encode(payload, config.JWT_SECRET,
                         algorithm=config.JWT_ALGORITHM),
        payload=payload,
        expire=expire,
    )

    return token


def _create_refresh_token(payload: dict) -> schemas.JwtTokenCreate:
    expire = _get_utc_now() + timedelta(minutes=config.REFRESH_TOKEN_EXPIRES_MINUTES)

    payload[config.EXP] = expire

    token = schemas.JwtTokenCreate(
        token=jwt.encode(payload, config.JWT_SECRET,
                         algorithm=config.JWT_ALGORITHM),
        expire=expire,
        payload=payload,
    )

    return token


def create_token_pair(user: models.User) -> schemas.TokenPair:
    payload = {config.SUB: str(user.id), config.JTI: str(
        uuid.uuid4()), config.IAT: _get_utc_now()}

    return schemas.TokenPair(
        access=_create_access_token(payload={**payload}),
        refresh=_create_refresh_token(payload={**payload}),
    )


def decode_access_token(token: str) -> dict:
    payload = jwt.decode(token, config.JWT_SECRET,
                         algorithms=[config.JWT_ALGORITHM])

    return payload


def refresh_token_state(token: str) -> schemas.JwtTokenGet:
    payload = jwt.decode(token, config.JWT_SECRET,
                         algorithms=[config.JWT_ALGORITHM])

    access_token = _create_access_token(payload=payload)

    return access_token


def add_refresh_token_cookie(response: Response, token: str):
    exp = _get_utc_now() + timedelta(minutes=config.REFRESH_TOKEN_EXPIRES_MINUTES)
    exp.replace(tzinfo=timezone.utc)

    response.set_cookie(
        key="refresh_token",
        value=token,
        expires=int(exp.timestamp()),
        httponly=True,
    )


def remove_refresh_token_from_cookie(response: Response):
    response.delete_cookie(
        key="refresh_token"
    )


async def get_user_from_access_token(authorization: str | None = Header(None), db: AsyncSession = Depends(get_db)) -> int:
    if not authorization:
        raise exceptions.AuthFailedException(
            detail="Authorization header missing")

    if not authorization.startswith("Bearer "):
        raise exceptions.AuthFailedException(
            detail="Invalid authorization header format")

    access_token = authorization.split(" ")[1]

    try:
        user_info = decode_access_token(access_token)
    except jwt.exceptions.DecodeError:
        raise exceptions.AuthFailedException(detail="Invalid access_token")

    user_id: uuid.UUID = user_info[config.SUB]

    user = await crud.get_user_by_id(db, user_id)

    if not user:
        raise exceptions.AuthFailedException(detail="Invalid access_token")

    return user


def get_ip_from_request(request: Request) -> str:
    return request.client.host


async def download_file(url: str, file_name: str, file_dir: str = "other") -> str | None:
    try:
        file_ext: str = url.split(".")[-1]
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    try:
                        file_path = f"{config.MEDIA_PATH}/{file_dir}/{file_name}.{file_ext}"
                        data = await response.read()

                        with open(file_path, 'wb') as f:
                            f.write(data)

                        return file_dir
                    except Exception as e:
                        print(f"Error while downloading {url}. Error: {e}")
                else:
                    print(
                        f"Error with response {url}. Response status: {response.status}")

    except Exception as e:
        print(f"Error while getting {url}. Error: {e}")
