import traceback
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from core import config
from sqlalchemyapp import models
from fastapp import schemas, crud, helper
from fastapp.database import get_db
from fastapp.tasks import celery_tasks

router = APIRouter(prefix="/v1", tags=["v1"])


@router.post("/user", status_code=status.HTTP_201_CREATED)
async def create_user(user_schema: schemas.UserCreate, db: Session = Depends(get_db)) -> JSONResponse:
    try:
        if not user_schema.email and not user_schema.phone_number:
            raise HTTPException(
                status_code=status.HTTP_406_NOT_ACCEPTABLE,
                detail="Email or phone number must be written"
            )
        
        another_user = crud.get_user_by_email_or_by_phone_number(db, user_schema.email, user_schema.phone_number)
        
        if another_user:
            raise HTTPException(
                status_code=status.HTTP_406_NOT_ACCEPTABLE,
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
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    

@router.get("/verify")
async def verify(code: str, email: str | None = None, phone_number: str | None = None, db: Session = Depends(get_db)) -> JSONResponse:
    try:
        if not email and not phone_number:
            raise HTTPException(
                status_code=status.HTTP_406_NOT_ACCEPTABLE,
                detail="Email or phone number must be written"
            )
        
        code_info: models.Code | None = crud.get_code_by_user_email(db, code, email) if email else crud.get_code_by_phone_number(db, code, phone_number)
        
        if not code_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Incorrect code"
            )
        
        user: models.User = code_info.user

        if user.expire_datetime > datetime.now():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User activation timeout"
            )

        user.expire_datetime = None

        if email:
            user.is_verified_email = True
            crud.update_user(db, user)
            crud.delete_user_by_email(db, email, is_verified=False)
        else:
            user.is_verified_phone_number = True
            crud.update_user(db, user)
            crud.delete_user_by_phone_number(db, phone_number, is_verified=False)
        
        return JSONResponse({"status": "success"})
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/login")
async def login(user: schemas.UserLogin, db: Session = Depends(get_db)) -> JSONResponse:
    try:
        password_hash = helper.hash_password(user.password)
        user: models.User | None = crud.get_user_by_email_and_password_hash(db, user.email, password_hash, is_verified=True)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        jwt_payload = {"user_id": user.id}
        jwt_token = helper.generate_jwt(jwt_payload)

        return jwt_token
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

