from datetime import datetime, timedelta

from sqlalchemy import Column, Table, ForeignKey
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from core import config

class Base(DeclarativeBase):
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now())
    updated_at: Mapped[datetime] = mapped_column(onupdate=datetime.now(), nullable=True)

collection_product_table = Table(
    "collection_product_table",
    Base.metadata,
    Column("left_id", ForeignKey("collection_table.id", ondelete="CASCADE")),
    Column("right_id", ForeignKey("product_table.id", ondelete="CASCADE")),
    extend_existing=True
)

user_combination_table = Table(
    "user_combination_table",
    Base.metadata,
    Column("left_id", ForeignKey("user_table.id", ondelete="CASCADE")),
    Column("right_id", ForeignKey("combination_table.id", ondelete="CASCADE")),
)

class Code(Base):
    __tablename__ = "code_table"

    user_id: Mapped[int] = mapped_column(ForeignKey("user_table.id", ondelete="CASCADE"))
    user: Mapped["User"] = relationship(back_populates="codes")
    type: Mapped[str] = mapped_column(ENUM("email", "phone_number", name="code_type_enum", create_type=False))
    code: Mapped[str]
    expire_datetime: Mapped[datetime]

class User(Base):
    __tablename__ = "user_table"

    email: Mapped[str] = mapped_column(nullable=True)
    is_verified_email: Mapped[bool] = mapped_column(default=False)
    phone_number: Mapped[str] = mapped_column(nullable=True)
    is_verified_phone_number: Mapped[bool] = mapped_column(default=False)
    password_hash: Mapped[str]
    combinations: Mapped[list["Combination"]] = relationship(secondary=user_combination_table, back_populates="users")
    codes: Mapped[list["Code"]] = relationship(back_populates="user")
    expire_datetime: Mapped[datetime] = mapped_column(default=datetime.now() + timedelta(seconds=config.UNVERIFIED_USER_TIME_LIVE), nullable=True)

class Collection(Base):
    __tablename__ = "collection_table"

    vsrap_id: Mapped[int] = mapped_column(unique=True)
    vsrap_url: Mapped[str]
    title: Mapped[str]
    description: Mapped[str] = mapped_column(nullable=True)
    image_url: Mapped[str] = mapped_column(nullable=True)
    products: Mapped[list["Product"]] = relationship(secondary=collection_product_table, back_populates="collections")
    

class Product(Base):
    __tablename__ = "product_table"

    vsrap_id: Mapped[int] = mapped_column(unique=True)
    vsrap_url: Mapped[str]
    title: Mapped[str]
    sub_title: Mapped[str] = mapped_column(nullable=True)
    description: Mapped[str] = mapped_column(nullable=True)
    image_url: Mapped[str]
    collections: Mapped[list["Collection"]] = relationship(secondary=collection_product_table, back_populates="products")
    combinations: Mapped[list["Combination"]] = relationship(back_populates="product")


class Combination(Base):
    __tablename__ = "combination_table"
    
    vsrap_id: Mapped[int] = mapped_column(unique=True)
    combination_number: Mapped[int]
    size: Mapped[str] = mapped_column(nullable=True)
    price: Mapped[int] # currency: RUB
    product_vsrap_id: Mapped[int] = mapped_column(ForeignKey("product_table.vsrap_id", ondelete="CASCADE"))
    product: Mapped["Product"] = relationship(back_populates="combinations")
    users: Mapped[list["User"]] = relationship(secondary=user_combination_table, back_populates="combinations")

