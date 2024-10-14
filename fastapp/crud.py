import datetime
import uuid

from sqlalchemy import insert, select, delete, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.sql._typing import _ColumnExpressionArgument

from fastapp import models
from core import config
from . import dependencies, schemas


async def upsert(db: AsyncSession, model: models.Base, rows, index_elements: list[str] = ["vsrap_id"], need_return: bool = False):
    table = model.__table__

    stmt = pg_insert(table).values(rows)

    update_cols = [c.name for c in table.c
                   if c not in list(table.primary_key.columns)]

    on_conflict_stmt = stmt.on_conflict_do_update(
        index_elements=index_elements,
        set_={k: getattr(stmt.excluded, k) for k in update_cols}
    )

    if need_return:
        on_conflict_stmt = on_conflict_stmt.returning(table.c.id)

    return_model = await db.execute(on_conflict_stmt)

    if need_return:
        return await return_model.fetchall()

    return None


# Collection

async def get_collections(db: AsyncSession, whereclause: _ColumnExpressionArgument[bool] | None = None) -> list[models.Collection]:
    select_collections_stmt = select(models.Collection)

    if whereclause is not None:
        select_collections_stmt = select_collections_stmt.where(whereclause)

    collections: list[models.Collection] = (await db.scalars(select_collections_stmt)).all()

    return collections


async def get_collection_by_id(db: AsyncSession, collection_id: int) -> models.Collection | None:
    select_collection_stmt = select(models.Collection).where(
        models.Collection.id == collection_id)
    collection: models.Collection | None = (await db.scalars(select_collection_stmt)).one_or_none()

    return collection


async def get_collections_by_id(db: AsyncSession, collections_ids: list[int]) -> list[models.Product]:
    whereclause = (
        models.Collection.id.in_(collections_ids)
    )

    return await get_collections(db, whereclause)


async def upsert_collections(db: AsyncSession, collections_json: list[dict], need_return: bool = False) -> list[models.Collection] | None:
    collections = await upsert(db, models.Collection, collections_json, need_return=need_return)

    return collections


# Product

async def get_products(db: AsyncSession, whereclause: _ColumnExpressionArgument[bool] | None = None, page: int = 0, page_size: int | None = None, search_text: str | None = None, join_collection: bool = False) -> list[models.Product]:
    select_products_stmt = select(models.Product)

    if join_collection:
        select_products_stmt = select_products_stmt.join(
            models.Product.collections).distinct()

    if whereclause is not None:
        select_products_stmt = select_products_stmt.where(whereclause)

    if search_text is not None:
        select_products_stmt = select_products_stmt.where(
            models.Product.title.contains(search_text))

    if page_size:
        select_products_stmt = select_products_stmt.offset(
            page_size * page).limit(page_size)

    products: list[models.Product] = (await db.scalars(select_products_stmt)).all()

    return products


async def get_products_by_collection_vsrap_id(db: AsyncSession, collection_vsrap_ids: list[int], page: int = 0, page_size: int | None = None, search_text: str | None = None) -> list[models.Product]:
    whereclause = (
        models.Collection.vsrap_id.in_(collection_vsrap_ids)
    )

    return await get_products(db, whereclause, page, page_size, search_text, join_collection=True)


async def get_products_by_combinations(db: AsyncSession, combinations: list[models.Combination], page: int = 0, page_size: int | None = None) -> list[models.Product]:
    product_vsrap_ids: list[int] = [
        combination.product_vsrap_id for combination in combinations]

    whereclause = (
        models.Product.vsrap_id.in_(product_vsrap_ids)
    )

    return await get_products(db, whereclause, page, page_size)


async def get_products_by_id(db: AsyncSession, products_ids: list[int], page: int = 0, page_size: int | None = None) -> list[models.Product]:
    whereclause = (
        models.Product.id.in_(products_ids)
    )

    return await get_products(db, whereclause, page, page_size)


async def upsert_products(db: AsyncSession, products_json: list[dict], need_return: bool = False) -> list[models.Product] | None:
    products: list[models.Product] = await upsert(db, models.Product, products_json, need_return=need_return)

    return products


# Combination

async def get_combination(db: AsyncSession, whereclause: _ColumnExpressionArgument[bool] | None = None) -> models.Combination | None:
    select_combination_stmt = select(models.Combination).where(whereclause)
    combination: models.Combination | None = (await db.scalars(select_combination_stmt)).one_or_none()

    return combination


async def get_combination_by_id(db: AsyncSession, combination_id: int) -> models.Combination | None:
    whereclause = (models.Combination.id == combination_id)

    return await get_combination(db, whereclause)


async def upsert_combinations(db: AsyncSession, combinations_json: list[dict], need_return: bool = False) -> list[models.Combination] | None:
    combinations: list[models.Combination] = await upsert(db, models.Combination, combinations_json, need_return=need_return)

    return combinations

# User Combination

async def add_combination_to_user(db: AsyncSession, combination_id: uuid.UUID, user_id: uuid.UUID) -> None:
    add_combination_to_user_stmt = insert(models.user_combination_table).values(user_id=user_id, combination_id=combination_id)

    await db.execute(add_combination_to_user_stmt)

async def remove_combination_from_user(db: AsyncSession, combination_id: uuid.UUID, user_id: uuid.UUID) -> None:
    remove_combination_from_user = delete(models.user_combination_table).where(user_id=user_id, combination_id=combination_id)

    await db.execute(remove_combination_from_user)
    
# User

async def create_user(db: AsyncSession, user: schemas.UserCreate) -> models.User:
    password_hash = dependencies.hash_password(user.password)

    new_user = models.User(
        email=user.email, phone_number=user.phone_number, password_hash=password_hash)
    await db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return new_user


async def get_users(db: AsyncSession, user_id: int | None = None) -> list[models.User]:
    select_user_stmt = select(models.User).where(
        id == user_id) if user_id else select(models.Product)
    users: list[models.User] = (await db.scalars(select_user_stmt)).all()

    return users


async def get_user(db: AsyncSession, whereclause: _ColumnExpressionArgument[bool]) -> models.User | None:
    select_user_stmt = select(models.User).where(whereclause)
    user: models.User = (await db.scalars(select_user_stmt)).one_or_none()

    return user


async def get_user_by_id(db: AsyncSession, user_id: int) -> models.User | None:
    whereclause = (models.User.id == user_id)

    return await get_user(db, whereclause)


async def get_user_by_email_or_by_phone_number(db: AsyncSession, email: str | None = None, phone_number: str | None = None) -> models.User | None:
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

    return await get_user(db, whereclause)


async def get_user_by_email_and_password_hash(db: AsyncSession, email: str, password_hash: str, is_verified: bool = False) -> models.User | None:
    whereclause = and_(
        models.User.email == email,
        models.User.is_verified_email == is_verified,
        models.User.password_hash == password_hash
    )

    return await get_user(db, whereclause)


async def update_user(db: AsyncSession, user: models.User) -> models.User:
    await db.commit()
    await db.refresh(user)


async def update_user_email(db: AsyncSession, user: models.User, email: str) -> models.User:
    user.email = email
    await update_user(db, user)


async def update_user_phone_number(db: AsyncSession, user: models.User, phone_number: str) -> models.User:
    user.phone_number = phone_number
    await update_user(db, user)


async def delete_user(db: AsyncSession, whereclause: _ColumnExpressionArgument[bool]) -> None:
    delete_users_stmt = delete(models.User).where(whereclause)
    await db.execute(delete_users_stmt)
    await db.commit()


async def delete_user_by_email(db: AsyncSession, email: str, is_verified: bool = False) -> None:
    whereclause = and_(
        models.User.email == email,
        models.User.is_verified_email == is_verified,
        models.User.is_verified_phone_number == False
    )

    return await delete_user(db, whereclause)


async def delete_user_by_phone_number(db: AsyncSession, phone_number: str, is_verified: bool = False) -> None:
    whereclause = and_(
        models.User.phone_number == phone_number,
        models.User.is_verified_phone_number == is_verified,
        models.User.is_verified_email == False
    )

    return await delete_user(db, whereclause)


async def delete_expired_users(db: AsyncSession) -> None:
    whereclause = and_(
        models.User.expire_datetime < datetime.datetime.now(),
        models.User.is_verified_email == False,
        models.User.is_verified_phone_number == False,
    )

    return await delete_user(db, whereclause)


# Code

async def get_code(db: AsyncSession, whereclause: _ColumnExpressionArgument[bool], join_user: bool = False) -> models.Code | None:
    get_code_stmt = select(models.Code)

    if join_user:
        get_code_stmt = get_code_stmt.join(models.User)

    get_code_stmt = get_code_stmt.where(whereclause)

    code: models.Code | None = (await db.scalars(get_code_stmt)).one_or_none()

    return code


async def get_code_by_user_email(db: AsyncSession, code: str, email: str) -> models.Code | None:
    whereclause = and_(
        models.Code.code == code,
        models.User.email == email
    )

    return await get_code(db, whereclause, True)


async def get_code_by_phone_number(db: AsyncSession, code: str, phone_number: str) -> models.Code | None:
    whereclause = and_(
        models.Code.code == code,
        models.User.phone_number == phone_number
    )

    return await get_code(db, whereclause)


async def create_code(db: AsyncSession, user: models.User, code_type: str) -> str:
    code = dependencies.generate_random_string(
        config.VERIFICATION_CODE_LENGTH, config.VERIFICATION_CODE_ONLY_DIGITS)
    expire_datetime = datetime.datetime.now(
    ) + datetime.timedelta(minutes=config.VERIFICATION_CODE_EXPIRES_MINUTES)
    create_code_stmt = insert(models.Code).values(
        user_id=user.id, type=code_type, code=code, expire_datetime=expire_datetime)

    await db.execute(create_code_stmt)
    await db.commit()

    return code


async def delete_code(db: AsyncSession, whereclause: _ColumnExpressionArgument[bool]) -> None:
    delete_users_stmt = delete(models.Code).where(whereclause)

    await db.execute(delete_users_stmt)
    await db.commit()
