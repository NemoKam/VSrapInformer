import traceback

from fastapi import APIRouter, Query, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from fastapp.core import config
from fastapp.database import get_db
from fastapp import dependencies, exceptions, schemas, crud
from fastapp import models

router = APIRouter(prefix="/v1", tags=["v1"])


@router.get("/collection", response_model=list[schemas.CollectionGet], status_code=status.HTTP_200_OK)
async def get_collections(db: Session = Depends(get_db)) -> list[schemas.CollectionGet]:
    try:
        collections: list[models.Collection] = crud.get_collections(db)
        return collections
    except Exception as e:
        raise exceptions.BadRequestException(detail=e)

@router.get("/product", response_model=list[schemas.ProductGet], status_code=status.HTTP_200_OK)
async def get_product(collection_vsrap_ids: list[int] | None = Query(default=None), search_text: str | None = None, page: int = 0, page_size: int = config.MAX_OBJECTS_PER_PAGE, db: Session = Depends(get_db)) -> list[schemas.Product]:
    try:
        if page_size > config.MAX_OBJECTS_PER_PAGE:
            raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Max page_size is {config.MAX_OBJECTS_PER_PAGE}"
        )

        products: list[models.Product]
        
        if collection_vsrap_ids:
            products: models.Product = crud.get_products_by_collection_vsrap_id(db, collection_vsrap_ids, page, page_size, search_text)
        else:
            products = crud.get_products(db, page=page, page_size=page_size, search_text=search_text)

        return products
    except Exception as e:
        traceback.print_exc()
        raise exceptions.BadRequestException(detail=e)
    
@router.get("/user/combination", response_model=list[schemas.CombinationBase], status_code=status.HTTP_200_OK)
async def get_user_combinations(user: models.User = Depends(dependencies.get_user_from_access_token), db: Session = Depends(get_db)) -> list[schemas.CombinationBase]:
    combinations: list[models.Combination] = user.combinations

    return combinations

@router.post("/user/combination", response_model=list[schemas.CombinationBase], status_code=status.HTTP_200_OK)
async def add_user_combinations(combination_id: int, user: models.User = Depends(dependencies.get_user_from_access_token), db: Session = Depends(get_db)) -> list[schemas.CombinationBase]:    
    combination: models.Combination | None = crud.get_combination_by_id(db, combination_id)
    
    if not combination:
        raise exceptions.NotFoundException(detail="Combination not found")

    user.combinations.append(combination)

    crud.update_user(db, user)

    return user.combinations

@router.delete("/user/combination/{combination_id}", status_code=status.HTTP_200_OK)
async def delete_user_combination(combination_id: int, user: models.User = Depends(dependencies.get_user_from_access_token), db: Session = Depends(get_db)) -> JSONResponse:
    combination: models.Combination | None = crud.get_combination_by_id(db, combination_id)
    
    if not combination:
        raise exceptions.NotFoundException(detail="Combination not found")

    user.combinations.remove(combination)

    crud.update_user(db, user)

    return JSONResponse({"status": "success"})

@router.get("/user/products", response_model=list[schemas.Product], status_code=status.HTTP_200_OK)
async def get_user_products(user: models.User = Depends(dependencies.get_user_from_access_token), db: Session = Depends(get_db)) -> JSONResponse:
    combinations: list[models.Combination] = user.combinations

    products: list[models.Product] = crud.get_products_by_combinations(db, combinations)
    
    return products
