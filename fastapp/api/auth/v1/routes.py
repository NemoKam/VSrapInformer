import traceback
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Response, Cookie
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from fastapp import dependencies, models, schemas, crud, exceptions
from fastapp.core import config
from fastapp.database import get_db
from fastapp.tasks import celery_tasks

router = APIRouter(prefix="/v1", tags=["v1"])

oauth2_schema = OAuth2PasswordBearer(tokenUrl="login")


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def create_user(user_schema: schemas.UserCreate, db: Session = Depends(get_db)) -> JSONResponse:
    if not user_schema.email and not user_schema.phone_number:
        raise exceptions.AuthFailedException(
            detail="Email or phone number must be written"
        )
    
    another_user = crud.get_user_by_email_or_by_phone_number(db, user_schema.email, user_schema.phone_number)
    
    if another_user:
        raise exceptions.AuthFailedException(
            detail="This credentials are already used"
        )
    
    user_model: models.User = crud.create_user(db, user_schema)

    message_title = f"Verifying on {config.PROJECT_TITLE}"
    if user_model.email:
        code = crud.create_code(db, user_model, "email")
        message_body = f"Activation Code:\n{code}"
        celery_tasks.send_mail.delay(user_model.email, message_title, message_body)
        
    if user_model.phone_number:
        code = crud.create_code(db, user_model, "phone_number")
        message_body = f"Activation Code:\n{code}"
        celery_tasks.send_phone_message.delay(user_model.phone_number, message_title, message_body)
        
    return JSONResponse({"status": "success"})
    
@router.get("/user", status_code=status.HTTP_200_OK, response_model=schemas.UserGet)
async def get_user(user: models.User = Depends(dependencies.get_user_from_access_token)) -> None:
    return user

@router.post("/verify")
async def verify(user_verify: schemas.UserVerify, db: Session = Depends(get_db)) -> JSONResponse:
    try:
        if not user_verify.email and not user_verify.phone_number:
            raise HTTPException(
                status_code=status.HTTP_406_NOT_ACCEPTABLE,
                detail="Email or phone number must be written"
            )
        
        code_info: models.Code | None = crud.get_code_by_user_email(db, user_verify.code, user_verify.email) if user_verify.email else crud.get_code_by_phone_number(db, user_verify.code, user_verify.phone_number)
        
        if not code_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Incorrect code"
            )
        
        user: models.User = code_info.user

        if user.expire_datetime < datetime.now():
            raise exceptions.AuthFailedException(detail="User activation timeout")

        user.expire_datetime = None

        if user_verify.email:
            user.is_verified_email = True
            crud.update_user(db, user)
            crud.delete_user_by_email(db, user_verify.email, is_verified=False)
        else:
            user.is_verified_phone_number = True
            crud.update_user(db, user)
            crud.delete_user_by_phone_number(db, user_verify.phone_number, is_verified=False)
        
        return JSONResponse({"status": "success"})
    except Exception as e:
        raise exceptions.BadRequestException(detail=e)

@router.post("/login", response_model=schemas.JwtTokenGet)
async def login(response: Response, user_login: schemas.UserLogin, db: Session = Depends(get_db)) -> JSONResponse:
    password_hash = dependencies.hash_password(user_login.password)

    user: models.User | None = crud.get_user_by_email_and_password_hash(db, user_login.email, password_hash, is_verified=True)

    if not user:
        raise exceptions.AuthFailedException("Invalid credentials")

    token_pair = dependencies.create_token_pair(user=user)

    dependencies.add_refresh_token_cookie(response=response, token=token_pair.refresh.token)

    return token_pair.access
    

@router.post("/refresh_token", response_model=schemas.JwtTokenGet)
async def refresh_token(refresh_token: str | None = Cookie()):
    if not refresh_token:
        raise exceptions.BadRequestException(detail="refresh token required")
    
    return dependencies.refresh_token_state(token=refresh_token)

@router.post("/logout")
async def logout(response: Response) -> JSONResponse:
    dependencies.remove_refresh_token_from_cookie(response)
