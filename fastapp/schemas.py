from datetime import datetime
from pydantic import BaseModel


class BaseCustomModel(BaseModel):
    id: int
    created_at: datetime
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


class UserBase(BaseModel):
    password: str
    
class UserCreate(UserBase):
    email: str | None = None
    phone_number: str | None = None

class User(UserBase, BaseModel):
    email: str | None = None
    phone_number: str | None = None
    password_hash: str

class UserLogin(UserBase):
    email: str


class CollectionBase(BaseCustomModel):
    vsrap_id: int
    vsrap_url: str
    title: str
    description: str | None = None
    image_url: str | None = None

class CollectionCreate(CollectionBase):
    pass

class Collection(CollectionBase):
    products: list["ProductBase"] = []
    

class ProductBase(BaseCustomModel):
    vsrap_id: int
    vsrap_url: str
    title: str
    sub_title: str | None = None
    description: str | None = None
    image_url: str

class ProductCreate(ProductBase):
    pass

class Product(ProductBase):
    collections: list["CollectionBase"] = []
    combinations: list["CombinationBase"] = []


class CombinationId(BaseModel):
    id: int

class CombinationBase(BaseCustomModel):
    vsrap_id: int
    combination_number: int
    size: str | None = None
    price: int
    currency: str = "RUB"
    product_vsrap_id: int

class CombinationCreate(CombinationBase):
    pass

class Combination(CombinationBase):
    pass
