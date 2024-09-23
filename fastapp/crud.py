import datetime
from sqlalchemy import create_engine, insert, select, delete, or_, and_
from sqlalchemy.orm import Session
from sqlalchemy.sql._typing import _ColumnExpressionArgument

from sqlalchemyapp import models
from . import schemas, helper
from core import config

# Collection

def get_collections(db: Session) -> list[models.Collection]:
    select_collections_stmt = select(models.Collection)
    collections: list[models.Collection] = db.scalars(select_collections_stmt).all()
    
    return collections

def get_collection_by_id(db: Session, collection_id: int) -> models.Collection | None:
    select_collection_stmt = select(models.Collection).where(models.Collection.id == collection_id)
    collection: models.Collection | None = db.scalars(select_collection_stmt).one_or_none()
    
    return collection


# Product

def get_products(db: Session, whereclause: _ColumnExpressionArgument[bool] | None = None) -> list[models.Product]:
    select_products_stmt = select(models.Product)

    if type(whereclause) is not None: select_products_stmt = select_products_stmt.where(whereclause) 

    products: list[models.Product] = db.scalars(select_products_stmt).all()

    return products

def get_products_by_combinations(db: Session, combinations: list[models.Combination]) -> list[models.Product]:
    product_vsrap_ids: list[int] = [combination.product_vsrap_id for combination in combinations]
    
    whereclause = (
        models.Product.vsrap_id.in_(product_vsrap_ids)
    )

    return get_products(db, whereclause)


# User

def create_user(db: Session, user: schemas.UserCreate) -> models.User:
    password_hash = helper.hash_password(user.password)

    new_user = models.User(email=user.email, phone_number=user.phone_number, password_hash=password_hash)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user

def get_users(db: Session, user_id: int | None = None) -> list[models.User]:
    select_user_stmt = select(models.User).where(id == user_id) if user_id else select(models.Product)
    users: list[models.User] = db.scalars(select_user_stmt).all()

    return users

def get_user(db: Session, whereclause: _ColumnExpressionArgument[bool]) -> models.User | None:
    select_user_stmt = select(models.User).where(whereclause)
    user: models.User = db.scalars(select_user_stmt).one_or_none()

    return user

def get_user_by_id(db: Session, user_id: int) -> models.User | None:
    whereclause = (models.User.id == user_id)

    return get_user(db, whereclause)

def get_user_by_email_or_by_phone_number(db: Session, email: str | None = None, phone_number: str | None = None) -> models.User | None:
    whereclause = or_(
        and_(
            models.User.email == email,
            models.User.is_verified_email == True
        ),
        and_(
            models.User.phone_number == phone_number,
            models.User.is_verified_phone_number == True
        )
    )

    return get_user(db, whereclause)


def get_user_by_email_and_password_hash(db: Session, email: str, password_hash: str, is_verified: bool = False) -> models.User | None:
    whereclause = and_(
        models.User.email == email,
        models.User.is_verified_email == is_verified,
        models.User.password_hash == password_hash
    )

    return get_user(db, whereclause)

def update_user(db: Session, user: models.User) -> models.User:
    db.commit()
    db.refresh(user)

def update_user_email(db: Session, user: models.User, email: str) -> models.User:
    user.email = email
    update_user(db, user)

def update_user_phone_number(db: Session, user: models.User, phone_number: str) -> models.User:
    user.phone_number = phone_number
    update_user(db, user)

def delete_user(db: Session, whereclause: _ColumnExpressionArgument[bool]) -> None:
    delete_users_stmt = delete(models.User).where(whereclause)
    db.execute(delete_users_stmt)
    db.commit()

def delete_user_by_email(db: Session, email: str, is_verified: bool = False) -> None:
    whereclause = and_(
        models.User.email == email,
        models.User.is_verified_email == is_verified,
        models.User.is_verified_phone_number == False
    )

    return delete_user(db, whereclause)

def delete_user_by_phone_number(db: Session, phone_number: str, is_verified: bool = False) -> None:
    whereclause = and_(
        models.User.phone_number == phone_number,
        models.User.is_verified_phone_number == is_verified,
        models.User.is_verified_email == False
    )

    return delete_user(db, whereclause)

# Code

def get_code(db: Session, whereclause: _ColumnExpressionArgument[bool], join_user: bool = False) -> models.Code | None:
    get_code_stmt = select(models.Code)

    if join_user: get_code_stmt = get_code_stmt.join(models.User)

    get_code_stmt = get_code_stmt.where(whereclause)

    code: models.Code | None = db.scalars(get_code_stmt).one_or_none()

    return code

def get_code_by_user_email(db: Session, code: str, email: str) -> models.Code | None:
    whereclause = and_(
        models.Code.code == code,
        models.User.email == email
    )

    return get_code(db, whereclause, True)

def get_code_by_phone_number(db: Session, code: str, phone_number: str) -> models.Code | None:
    whereclause = and_(
        models.Code.code == code,
        models.User.phone_number == phone_number
    )

    return get_code(db, whereclause)

def create_code(db: Session, user: models.User, code_type: str) -> str:
    code = helper.generate_random_string(config.VERIFICATION_CODE_LENGTH, config.VERIFICATION_CODE_ONLY_DIGITS)
    expire_datetime = datetime.datetime.now() + datetime.timedelta(seconds=config.VERIFICATION_CODE_TIME_LIVE)
    create_code_stmt = insert(models.Code).values(user_id=user.id, type=code_type, code=code, expire_datetime=expire_datetime)
    db.execute(create_code_stmt)
    db.commit()

    return code

def delete_code(db: Session, whereclause: _ColumnExpressionArgument[bool]) -> None:
    delete_users_stmt = delete(models.Code).where(whereclause)

    db.execute(delete_users_stmt)
    db.commit()

# Combination

def get_combination_by_id(db: Session, combination_id: int) -> models.Combination | None:
    select_combination_stmt = select(models.Combination).where(models.Combination.id == combination_id)
    combination: models.Combination | None = db.scalars(select_combination_stmt).one_or_none()

    return combination

