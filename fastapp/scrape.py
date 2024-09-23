
import asyncio
import traceback
from dataclasses import dataclass

import aiohttp
from sqlalchemy import select, create_engine
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session


from core import config
from sqlalchemyapp.models import Base, Collection, Product, Combination


def upsert(db: Session, model: Base, rows):
    table = model.__table__

    stmt = insert(table).values(rows)

    update_cols = [c.name for c in table.c
                   if c not in list(table.primary_key.columns)]

    on_conflict_stmt = stmt.on_conflict_do_update(
        index_elements=table.primary_key.columns,
        set_={k: getattr(stmt.excluded, k) for k in update_cols}
        )

    db.execute(on_conflict_stmt)

@dataclass
class Scraper:
    session: aiohttp.ClientSession
    max_tryings = 3
    error_sleep = 5

    async def get_items(self, url: str) -> list[dict]:
        items = []
        limit = 100
        offset = 0
        total = 1

        while offset < total:
            for i in range(self.max_tryings):
                try:
                    async with self.session.get(f"{url}&offset={offset}") as resp:
                        res = await resp.json()

                        limit = res["limit"]
                        offset = res["offset"]
                        total = res["total"]

                        offset +=  limit
                        items += res["items"]
                        break
                except Exception as e:
                    if i == self.max_tryings - 1: return items
                    await asyncio.sleep(self.error_sleep)

        return items

    async def get_collections(self) -> list[dict]:
        url = "https://app.ecwid.com/api/v3/10796017/categories?token=public_PrvdXNdRD3i2r9BVN2cVWwzugV6sStVL&parent=48485404"
        return await self.get_items(url)
    
    async def get_products(self) -> list[dict]:
        url = "https://app.ecwid.com/api/v3/10796017/products?token=public_PrvdXNdRD3i2r9BVN2cVWwzugV6sStVL&category=0&withSubcategories=false"
        return await self.get_items(url)


def validate_collection(collections: list[dict]) -> list[dict]:
    collection_list_of_dict: list[dict] = []

    for collection in collections:
        vsrap_id = collection["id"]
        vsrap_url = collection["url"]
        title = collection["name"]
        description = collection["description"] if collection["description"] != "" else None
        image_url = collection["imageUrl"] if "imageUrl" in collection and collection["imageUrl"] != "" else None

        collection_list_of_dict.append(dict(vsrap_id=vsrap_id, vsrap_url=vsrap_url, title=title, description=description, image_url=image_url))
    
    return collection_list_of_dict

def validate_products(products: list[dict]) -> list[dict]:
    products_info: list[dict] = []

    for product in products:
        product_info = {}

        if not product["enabled"]: continue

        vsrap_id = product["id"]
        vsrap_url = product["url"]
        title = product["name"]
        sub_title = product["subtitle"] if "subtitle" in product and product["subtitle"] != "" else None
        description = product["description"] if product["description"] != "" else None
        combinations = [{"vsrap_id": combination["id"],  "combination_number": combination["combinationNumber"], "size": combination["options"][0]["value"] if len(combination["options"]) > 0 else "", "price": combination["defaultDisplayedPrice"], "product_vsrap_id": vsrap_id} for combination in product["combinations"]] if len(product["combinations"]) > 0 else []
        image_url = product["imageUrl"] if "imageUrl" in product and product["imageUrl"] != "" else None
        categories = [category["id"] for category in product["categories"] if category["enabled"]]
        
        product_info["product"] = dict(vsrap_id=vsrap_id, vsrap_url=vsrap_url, title=title, sub_title=sub_title, description=description, image_url=image_url)
        product_info["categories"] = categories
        product_info["combinations"] = combinations

        products_info.append(product_info)
    
    return products_info

def update_data(collection_list_of_dict: list[dict], products_info: list[dict], engine) -> None:
    with Session(engine) as db:
        upsert(db, Collection, collection_list_of_dict)
        db.commit()

        # for product_info in products_info:
        #     nested = db.begin_nested()
        #     try:
        #         product_insert_stmt = insert(Product).values(product_info["product"])
        #         db.execute(product_insert_stmt)

        #         product: Product = db.scalars(select(Product).where(Product.vsrap_id==product_info["product"]["vsrap_id"])).one()

        #         combinations = product_info["combinations"]
        #         if len(combinations) > 0:
        #             combination_insert_return_stmt = insert(Combination).values(combinations).returning(Combination)
        #             db.execute(combination_insert_return_stmt)

        #         for collection_vsrap_id in product_info["categories"]:
        #             collection: Collection = db.scalars(select(Collection).where(Collection.vsrap_id==collection_vsrap_id)).one_or_none()
        #             if collection: collection.products.append(product)

        #         db.commit()
        #     except:
        #         traceback.print_exc()
        #         nested.rollback()

async def update_base(engine):
    async with aiohttp.ClientSession() as session:
        scraper = Scraper(session)

        collections = await scraper.get_collections()
        products = await scraper.get_products()

    collection_list_of_dict: list[dict] = validate_collection(collections)
    products_info: list[dict] = validate_products(products)

    update_data(collection_list_of_dict, products_info, engine)


if __name__ == "__main__":
    SQLALCHEMY_DATABASE_URL = f"postgresql+psycopg2://{config.POSTGRESQL_USER}:{config.POSTGRESQL_PASSWORD}@{config.POSTGRESQL_HOST}:{config.POSTGRESQL_PORT}/{config.POSTGRESQL_DATABASE}"
    engine = create_engine(SQLALCHEMY_DATABASE_URL)

    asyncio.run(update_base())