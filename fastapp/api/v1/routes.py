import traceback

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from fastapp.database import get_db
from fastapp import schemas, crud, helper
from sqlalchemyapp import models

router = APIRouter(prefix="/v1", tags=["v1"])


async def get_user_from_jwt(jwt: str, db: Session = Depends(get_db)) -> int:
    user_info = helper.decode_jwt(jwt)

    if not user_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid jwt"
        )
    
    user_id = user_info["user_id"]

    user: models.User | None = crud.get_user_by_id(db, user_id)

    return user


@router.get("/collection", response_model=list[schemas.Collection], status_code=status.HTTP_200_OK)
async def get_collections(db: Session = Depends(get_db)) -> list[schemas.Collection]:
    try:
        collections: list[models.Collection] = crud.get_collections(db)
        return collections
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/product", response_model=list[schemas.Product], status_code=status.HTTP_200_OK)
async def get_product(collection_id: int | None = None, db: Session = Depends(get_db)) -> list[schemas.Product]:
    try:
        products: list[models.Product]
        
        if collection_id:
            collection: models.Collection = crud.get_collection_by_id(db, collection_id)
            products = collection.products
        else:
            products = crud.get_products(db)

        return products
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    

@router.get("/user/combination", response_model=list[schemas.CombinationBase])
async def get_user_combinations(user: models.User = Depends(get_user_from_jwt), db: Session = Depends(get_db)) -> list[schemas.CombinationBase]:
    combinations: list[models.Combination] = user.combinations

    return combinations

@router.post("/user/combination", response_model=list[schemas.CombinationBase])
async def add_user_combinations(combination_id: int, user: models.User = Depends(get_user_from_jwt), db: Session = Depends(get_db)) -> list[schemas.CombinationBase]:    
    combination: models.Combination | None = crud.get_combination_by_id(db, combination_id)
    
    if not combination:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Combination not found"
        )

    user.combinations.append(combination)

    crud.update_user(db, user)

    return user.combinations

@router.delete("/user/combination/{combination_id}")
async def delete_user_combination(combination_id: int, user: models.User = Depends(get_user_from_jwt), db: Session = Depends(get_db)) -> JSONResponse:
    combination: models.Combination | None = crud.get_combination_by_id(db, combination_id)
    
    if not combination:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Combination not found"
        )

    user.combinations.remove(combination)

    crud.update_user(db, user)

    return JSONResponse({"status": "success"})

@router.get("/user/products", response_model=list[schemas.Product], status_code=status.HTTP_200_OK)
async def get_user_products(user: models.User = Depends(get_user_from_jwt), db: Session = Depends(get_db)) -> JSONResponse:
    combinations: list[models.Combination] = user.combinations

    products: list[models.Product] = crud.get_products_by_combinations(db, combinations)
    
    return products
