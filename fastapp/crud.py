import datetime
from sqlalchemy import insert, select, delete, or_, and_
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.sql._typing import _ColumnExpressionArgument

from fastapp import models
from fastapp.core import config
from . import dependencies, schemas

def upsert(db: Session, model: models.Base, rows, index_elements: list[str] = ["vsrap_id"], need_return: bool = False):
    table = model.__table__
    
    stmt = pg_insert(table).values(rows)

    update_cols = [c.name for c in table.c
                   if c not in list(table.primary_key.columns)]

    on_conflict_stmt = stmt.on_conflict_do_update(
        index_elements=index_elements,
        set_={k: getattr(stmt.excluded, k) for k in update_cols}
    )
    
    if need_return: on_conflict_stmt = on_conflict_stmt.returning(table.c.id)

    return_model = db.execute(on_conflict_stmt)

    if need_return: return return_model.fetchall()

    return None

# Collection

def get_collections(db: Session, whereclause: _ColumnExpressionArgument[bool] | None = None) -> list[models.Collection]:
    select_collections_stmt = select(models.Collection)
    
    if whereclause is not None:
        select_collections_stmt = select_collections_stmt.where(whereclause)

    collections: list[models.Collection] = db.scalars(select_collections_stmt).all()
    
    return collections

def get_collection_by_id(db: Session, collection_id: int) -> models.Collection | None:
    select_collection_stmt = select(models.Collection).where(models.Collection.id == collection_id)
    collection: models.Collection | None = db.scalars(select_collection_stmt).one_or_none()
    
    return collection

def get_collections_by_id(db: Session, collections_ids: list[int]) -> list[models.Product]:
    whereclause = (
        models.Collection.id.in_(collections_ids)
    )

    return get_collections(db, whereclause)

def upsert_collections(db: Session, collections_json: list[dict], need_return: bool = False) -> list[models.Collection] | None:
    collections = upsert(db, models.Collection, collections_json, need_return=need_return)

    return collections

# Product

def get_products(db: Session, whereclause: _ColumnExpressionArgument[bool] | None = None, page: int = 0, page_size: int | None = None, search_text: str | None = None, join_collection: bool = False) -> list[models.Product]:
    select_products_stmt = select(models.Product)

    if join_collection:
        select_products_stmt = select_products_stmt.join(models.Product.collections).distinct()

    if whereclause is not None:
        select_products_stmt = select_products_stmt.where(whereclause)

    if search_text is not None:
        select_products_stmt = select_products_stmt.where(models.Product.title.contains(search_text))

    if page_size:
        select_products_stmt = select_products_stmt.offset(page_size * page).limit(page_size)

    products: list[models.Product] = db.scalars(select_products_stmt).all()

    return products

def get_products_by_collection_vsrap_id(db: Session, collection_vsrap_ids: list[int], page: int = 0, page_size: int | None = None, search_text: str | None = None) -> list[models.Product]:
    whereclause = (
        models.Collection.vsrap_id.in_(collection_vsrap_ids)
    )

    return get_products(db, whereclause, page, page_size, search_text, join_collection=True)

def get_products_by_combinations(db: Session, combinations: list[models.Combination], page: int = 0, page_size: int | None = None) -> list[models.Product]:
    product_vsrap_ids: list[int] = [combination.product_vsrap_id for combination in combinations]
    
    whereclause = (
        models.Product.vsrap_id.in_(product_vsrap_ids)
    )

    return get_products(db, whereclause, page, page_size)

def get_products_by_id(db: Session, products_ids: list[int], page: int = 0, page_size: int | None = None) -> list[models.Product]:
    whereclause = (
        models.Product.id.in_(products_ids)
    )

    return get_products(db, whereclause, page, page_size)

def upsert_products(db: Session, products_json: list[dict], need_return: bool = False) -> list[models.Product] | None:
    products: list[models.Product] = upsert(db, models.Product, products_json, need_return=need_return)

    return products

# Combination

def get_combination(db: Session, whereclause: _ColumnExpressionArgument[bool] | None = None) -> models.Combination | None:
    select_combination_stmt = select(models.Combination).where(whereclause)
    combination: models.Combination | None = db.scalars(select_combination_stmt).one_or_none()

    return combination


def get_combination_by_id(db: Session, combination_id: int) -> models.Combination | None:
    whereclause = (models.Combination.id == combination_id)

    return get_combination(db, whereclause)

def upsert_combinations(db: Session, combinations_json: list[dict], need_return: bool = False) -> list[models.Combination] | None:
    combinations: list[models.Combination] = upsert(db, models.Combination, combinations_json, need_return=need_return)
    
    return combinations

# User

def create_user(db: Session, user: schemas.UserCreate) -> models.User:
    password_hash = dependencies.hash_password(user.password)

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

def delete_expired_users(db: Session) -> None:
    whereclause = and_(
        models.User.expire_datetime < datetime.datetime.now(),
        models.User.is_verified_email == False,
        models.User.is_verified_phone_number == False,
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
    code = dependencies.generate_random_string(config.VERIFICATION_CODE_LENGTH, config.VERIFICATION_CODE_ONLY_DIGITS)
    expire_datetime = datetime.datetime.now() + datetime.timedelta(minutes=config.VERIFICATION_CODE_EXPIRES_MINUTES)
    create_code_stmt = insert(models.Code).values(user_id=user.id, type=code_type, code=code, expire_datetime=expire_datetime)
    
    db.execute(create_code_stmt)
    db.commit()

    return code

def delete_code(db: Session, whereclause: _ColumnExpressionArgument[bool]) -> None:
    delete_users_stmt = delete(models.Code).where(whereclause)

    db.execute(delete_users_stmt)
    db.commit()
