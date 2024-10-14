import traceback

from fastapi import APIRouter, Query, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from core import config
from fastapp.database import get_db
from fastapp import dependencies, exceptions, schemas, crud
from fastapp import models
from logger import get_logger

py_logger = get_logger("v1/routes.py")

router = APIRouter(prefix="/v1", tags=["v1"])


@router.get("/collection", response_model=list[schemas.CollectionGet], status_code=status.HTTP_200_OK)
async def get_collections(user_ip: str = Depends(dependencies.get_ip_from_request), db: AsyncSession = Depends(get_db)) -> list[schemas.CollectionGet]:
    try:
        py_logger.debug(f"Getting collections. IP: {user_ip}")
        collections: list[models.Collection] = await crud.get_collections(db)

        return collections
    except Exception as e:
        py_logger.error(f"Unexpected error. IP: {user_ip}", exc_info=True)
        raise exceptions.BadRequestException(detail=e)


@router.get("/product", response_model=list[schemas.ProductGet], status_code=status.HTTP_200_OK)
async def get_product(collection_vsrap_ids: list[int] | None = Query(default=None), search_text: str | None = None, page: int = 0, page_size: int = config.MAX_OBJECTS_PER_PAGE, user_ip: str = Depends(dependencies.get_ip_from_request), db: AsyncSession = Depends(get_db)) -> list[schemas.Product]:
    try:
        py_logger.debug(
            f"Getting products ({page}, {page_size}). IP: {user_ip}")
        if page_size > config.MAX_OBJECTS_PER_PAGE:
            py_logger.debug(
                f"Page size is bigger than Max Objects Per Page. IP: {user_ip}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Max page_size is {config.MAX_OBJECTS_PER_PAGE}"
            )

        products: list[models.Product]

        if collection_vsrap_ids:
            products: models.Product = await crud.get_products_by_collection_vsrap_id(db, collection_vsrap_ids, page, page_size, search_text)
        else:
            products = await crud.get_products(db, page=page, page_size=page_size, search_text=search_text)

        return products
    except Exception as e:
        py_logger.error(f"Unexpected error. IP: {user_ip}", exc_info=True)
        raise exceptions.BadRequestException(detail=e)


@router.get("/user/combination", response_model=list[schemas.CombinationBase], status_code=status.HTTP_200_OK)
async def get_user_combinations(user: models.User = Depends(dependencies.get_user_from_access_token), user_ip: str = Depends(dependencies.get_ip_from_request), db: AsyncSession = Depends(get_db)) -> list[schemas.CombinationBase]:
    py_logger.debug(f"Getting user_combinations. IP: {user_ip}")
    combinations: list[models.Combination] = user.combinations

    return combinations


@router.post("/user/combination", response_model=list[schemas.CombinationBase], status_code=status.HTTP_200_OK)
async def add_user_combinations(combination_id: int, user: models.User = Depends(dependencies.get_user_from_access_token), user_ip: str = Depends(dependencies.get_ip_from_request), db: AsyncSession = Depends(get_db)) -> list[schemas.CombinationBase]:
    py_logger.debug(f"Adding user_combination. IP: {user_ip}")
    combination: models.Combination | None = await crud.get_combination_by_id(db, combination_id)

    if not combination:
        py_logger.debug(f"Combination not found. IP: {user_ip}")
        raise exceptions.NotFoundException(detail="Combination not found")

    
    await crud.add_combination_to_user(db, combination.id, user.id)
    await crud.update_user(db, user)

    return user.combinations


@router.delete("/user/combination/{combination_id}", status_code=status.HTTP_200_OK)
async def delete_user_combination(combination_id: int, user: models.User = Depends(dependencies.get_user_from_access_token), user_ip: str = Depends(dependencies.get_ip_from_request), db: AsyncSession = Depends(get_db)) -> JSONResponse:
    py_logger.debug(f"Removing user_combination. IP: {user_ip}")
    combination: models.Combination | None = await crud.get_combination_by_id(db, combination_id)

    if not combination:
        py_logger.debug(f"Combination notfound. IP: {user_ip}")
        raise exceptions.NotFoundException(detail="Combination not found")

    await crud.remove_combination_from_user(db, combination.id, user.id)
    await crud.update_user(db, user)

    return JSONResponse({"status": "success"})


@router.get("/user/products", response_model=list[schemas.Product], status_code=status.HTTP_200_OK)
async def get_user_products(user: models.User = Depends(dependencies.get_user_from_access_token), user_ip: str = Depends(dependencies.get_ip_from_request), db: AsyncSession = Depends(get_db)) -> JSONResponse:
    py_logger.debug(f"Getting user_combination. IP: {user_ip}")
    combinations: list[models.Combination] = user.combinations

    products: list[models.Product] = await crud.get_products_by_combinations(db, combinations)

    return products
