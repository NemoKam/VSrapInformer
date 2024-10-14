import traceback
from datetime import datetime

from aiohttp import request
from fastapi import APIRouter, Depends, HTTPException, status, Response, Cookie, Request
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from core import config
from fastapp import dependencies, models, schemas, crud, exceptions
from fastapp.database import get_db
from fastapp.tasks import celery_tasks
from logger import get_logger

py_logger = get_logger("auth/v1/routes.py")

py_logger.debug("Starting APIRouter")
router = APIRouter(prefix="/v1", tags=["v1"])

py_logger.debug("Starting OAuth2PasswordBearer")
oauth2_schema = OAuth2PasswordBearer(tokenUrl="login")


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def create_user(user_schema: schemas.UserCreate, user_ip: str = Depends(dependencies.get_ip_from_request), db: AsyncSession = Depends(get_db)) -> JSONResponse:
    py_logger.debug(f"POST auth/v1/register. IP: {user_ip}")
    if not user_schema.email and not user_schema.phone_number:
        py_logger.debug(f"Email and phone number are empty. IP: {user_ip}")
        raise exceptions.AuthFailedException(
            detail="Email or phone number must be written"
        )

    another_user = await crud.get_user_by_email_or_by_phone_number(db, user_schema.email, user_schema.phone_number)

    if another_user:
        py_logger.debug(f"Credentials are already used. IP: {user_ip}")
        raise exceptions.AuthFailedException(
            detail="This credentials are already used"
        )

    user_model: models.User = await crud.create_user(db, user_schema)
    py_logger.debug(f"User created. IP: {user_ip}")

    message_title = f"Verifying on {config.PROJECT_TITLE}"
    if user_model.email:
        py_logger.debug(f"Creating code for email. IP: {user_ip}")
        code = await crud.create_code(db, user_model, "email")
        message_body = f"Activation Code:\n{code}"
        py_logger.debug(f"Sending code to email. IP: {user_ip}")
        celery_tasks.send_mail.delay(
            user_model.email, message_title, message_body)

    if user_model.phone_number:
        py_logger.debug(f"Creating code for phone. IP: {user_ip}")
        code = await crud.create_code(db, user_model, "phone_number")
        message_body = f"Activation Code:\n{code}"
        py_logger.debug(f"Sending code to phone. IP: {user_ip}")
        celery_tasks.send_phone_message.delay(
            user_model.phone_number, message_title, message_body)

    return JSONResponse({"status": "success"})


@router.get("/user", status_code=status.HTTP_200_OK, response_model=schemas.UserGet)
async def get_user(user: models.User = Depends(dependencies.get_user_from_access_token), user_ip: str = Depends(dependencies.get_ip_from_request)) -> None:
    py_logger.debug("GET: /auth/v1/user")
    return user


@router.post("/verify")
async def verify(user_verify: schemas.UserVerify, user_ip: str = Depends(dependencies.get_ip_from_request), db: AsyncSession = Depends(get_db)) -> JSONResponse:
    try:
        py_logger.debug(f"Verifying user. IP: {user_ip}")
        if not user_verify.email and not user_verify.phone_number:
            py_logger.debug(f"Email or phone must be written. IP: {user_ip}")
            raise HTTPException(
                status_code=status.HTTP_406_NOT_ACCEPTABLE,
                detail="Email or phone number must be written"
            )

        code_info: models.Code | None = await crud.get_code_by_user_email(db, user_verify.code, user_verify.email) if user_verify.email else crud.get_code_by_phone_number(db, user_verify.code, user_verify.phone_number)

        if not code_info:
            py_logger.debug(f"Incorrect code. IP: {user_ip}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Incorrect code"
            )

        user: models.User = code_info.user

        if user.expire_datetime < datetime.now():
            py_logger.debug(f"User activation timeout. IP: {user_ip}")
            raise exceptions.AuthFailedException(
                detail="User activation timeout")

        user.expire_datetime = None

        if user_verify.email:
            py_logger.debug(f"Updating email verifying status. IP: {user_ip}")
            user.is_verified_email = True
            await crud.update_user(db, user)
            await crud.delete_user_by_email(db, user_verify.email, is_verified=False)
            py_logger.debug(f"Email verified. IP: {user_ip}")
        else:
            py_logger.debug(f"Updating phone verifying status. IP: {user_ip}")
            user.is_verified_phone_number = True
            await crud.update_user(db, user)
            await crud.delete_user_by_phone_number(db, user_verify.phone_number, is_verified=False)
            py_logger.debug(f"Phone verified. IP: {user_ip}")
        return JSONResponse({"status": "success"})
    except Exception as e:
        py_logger.error(f"Unexpected error. IP: {user_ip}", exc_info=True)
        raise exceptions.BadRequestException(detail=e)


@router.post("/login", response_model=schemas.JwtTokenGet)
async def login(response: Response, user_login: schemas.UserLogin, user_ip: str = Depends(dependencies.get_ip_from_request), db: AsyncSession = Depends(get_db)) -> JSONResponse:
    py_logger.debug(f"Logging. IP: {user_ip}")
    password_hash = dependencies.hash_password(user_login.password)

    user: models.User | None = await crud.get_user_by_email_and_password_hash(db, user_login.email, password_hash, is_verified=True)

    if not user:
        py_logger.debug(f"Invalid credentials. IP: {user_ip}")
        raise exceptions.AuthFailedException("Invalid credentials")

    py_logger.debug(f"Creating token pair. IP: {user_ip}")
    token_pair = dependencies.create_token_pair(user=user)

    py_logger.debug(f"Addint refresh_token to cookie. IP: {user_ip}")
    dependencies.add_refresh_token_cookie(
        response=response, token=token_pair.refresh.token)

    return token_pair.access


@router.post("/refresh_token", response_model=schemas.JwtTokenGet)
async def refresh_token(refresh_token: str | None = Cookie(), user_ip: str = Depends(dependencies.get_ip_from_request)):
    py_logger.debug(f"Updating refresh_token. IP: {user_ip}")
    if not refresh_token:
        py_logger.debug(f"Refresh_token required. IP: {user_ip}")
        raise exceptions.BadRequestException(detail="refresh token required")

    py_logger.debug(f"Refreshing token. IP: {user_ip}")
    jwt_token: schemas.JwtTokenGet = dependencies.refresh_token_state(
        token=refresh_token)

    return jwt_token


@router.post("/logout")
async def logout(response: Response, user_ip: str = Depends(dependencies.get_ip_from_request)) -> JSONResponse:
    py_logger.debug(f"Loging out. IP: {user_ip}")
    dependencies.remove_refresh_token_from_cookie(response)
    py_logger.debug(f"Refresh token removed from cookies. IP: {user_ip}")
