from datetime import datetime
from pydantic import BaseModel

from fastapp import models

# Base Models

class BaseConfigModel(BaseModel):
    class Config:
        arbitrary_types_allowed=True
        from_attributes = True

class BaseCustomModel(BaseConfigModel):
    id: int
    created_at: datetime
    updated_at: datetime | None = None

# User Models 

class UserBase(BaseConfigModel):
    password: str
    
class UserGet(BaseConfigModel):
    email: str | None = None
    phone_number: str | None = None

class UserCreate(UserGet, UserBase):
    pass

class User(UserBase, BaseModel):
    email: str | None = None
    phone_number: str | None = None
    password_hash: str

class UserLogin(UserBase):
    email: str

class UserVerify(UserGet):
    code: str

# Jwt & Token Models

class JwtTokenGet(BaseConfigModel):
    token: str
    expire: datetime

class JwtTokenCreate(JwtTokenGet):
    payload: dict

class JwtToken(JwtTokenCreate):
    pass

class TokenPair(BaseConfigModel):
    access: JwtToken
    refresh: JwtToken

# Collection Models

class CollectionBase(BaseConfigModel):
    vsrap_id: int
    vsrap_url: str
    title: str

class CollectionGet(CollectionBase):
    products: list["ProductBase"] = []

class CollectionCreate(CollectionBase):
    pass

class Collection(CollectionGet, BaseCustomModel):
    pass

# Product Models

class ProductBase(BaseConfigModel):
    vsrap_id: int
    vsrap_url: str
    title: str
    pre_order: bool = False
    limited: bool = False
    price: int
    image_url: str

class ProductGet(ProductBase):
    collections: list["CollectionBase"] = []
    combinations: list["CombinationCreate"] = []

class ProductCreate(ProductBase):
    pass

class Product(ProductGet, BaseCustomModel):
    pass

# Combination Models

class CombinationId(BaseModel):
    id: int

class CombinationBase(BaseConfigModel):
    vsrap_id: int
    combination_number: int
    size: str | None = None
    price: int
    product_vsrap_id: int

class CombinationCreate(CombinationBase):
    pass

class Combination(CombinationBase, BaseCustomModel):
    pass

# Collection & Product Model

class CollectionProductCombination(BaseConfigModel):
    collection: models.Collection | None = None
    products: list["ProductCreate"] = []
    combinations: list["CombinationCreate"] = []
    