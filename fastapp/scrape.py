
import asyncio
import traceback
from dataclasses import dataclass

import aiohttp
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session

from fastapp import models
from fastapp.core import config
from . import dependencies, schemas, crud


SHOP_BASE_URL = config.SHOP_BASE_URL


@dataclass
class Scraper:
    session: aiohttp.ClientSession

    async def validate_collection(self, soup: BeautifulSoup) -> list[schemas.CollectionCreate]:
        collections: list[schemas.CollectionCreate] = []

        soup_collections: list[BeautifulSoup] = soup.findAll("div", {"class": "grid-list__item"})

        for collection in soup_collections:
            try:
                vsrap_id: int = int(collection["id"].split("_")[2])
                vsrap_url: str = SHOP_BASE_URL + collection.find("a", {"class": "ui-card__link"})["href"]
                title: str = collection.find("div", {"class": "brands-list__image-wrapper"}).text.replace("	", "").replace("\n", "")
                
                collection = schemas.CollectionCreate(vsrap_id=vsrap_id, vsrap_url=vsrap_url, title=title)

                collections.append(collection)
            except Exception as e:
                traceback.print_exc()

        return collections

    async def get_collections(self) -> list[schemas.CollectionCreate]:
        url = f"{SHOP_BASE_URL}/brands/"
        for i in range(config.SCRAPER_PAGE_LOAD_MAX_TRYINGS):
            try:
                async with self.session.get(url) as resp:
                    res = await resp.text()
                    soup = BeautifulSoup(res, 'html.parser')

                    collections = await self.validate_collection(soup)
                    return collections
                
            except Exception as e:
                traceback.print_exc()
                await asyncio.sleep(config.SCRAPER_SLEEP_ON_ERROR)
        return []
    
    async def validate_products_combinations(self, soup: BeautifulSoup) -> schemas.CollectionProductCombination:
        products: list[schemas.ProductCreate] = []
        combinations: list[schemas.CombinationCreate] = []

        soup_products: list[BeautifulSoup] = soup.findAll("div", {"class": "catalog-block__inner"})

        for product_info in soup_products:
            vsrap_id = int(product_info.find("div", {"class": "catalog-block__info"})["data-id"])
            vsrap_url: str = SHOP_BASE_URL + product_info.find("a")["href"]
            title: str = product_info.find("div", {"class": "catalog-block__info-title"}).find("span").text
            try:
                price = int(product_info.find("meta", {"itemprop": "price"})["content"])
            except TypeError:
                product_soup = await self.get_product_page_soup(vsrap_url)
                price = int(product_soup.find("meta", {"itemprop": "price"})["content"])

            pre_order: bool = True if product_info.find("div", {"class": "sticker__item--preorder"}) != None else False
            limited: bool = True if product_info.find("div", {"class": "sticker__item--limited"}) != None else False
            image_url: str = ""
            try:
                image_download_url = SHOP_BASE_URL + product_info.find("img", {"class": "img-responsive"})["data-src"]
                image_url = await dependencies.download_file(image_download_url, str(vsrap_id), "product")
            except (TypeError, KeyError):
                pass
            except Exception as e:
                traceback.print_exc()
            
            combinations_info: BeautifulSoup | None = product_info.find("div", {"class": "sku-props"})
            if combinations_info:
                data_item_id = int(combinations_info["data-item-id"])
                vsrap_id = data_item_id
                for i, combination_info in enumerate(combinations_info.findAll("div", {"class": "sku-props__value"})):
                    combination_vsrap_id = data_item_id + i + 1
                    combination_number = i + 1
                    combination_size: str = combination_info["data-title"]
                    
                    combination = schemas.CombinationCreate(vsrap_id=combination_vsrap_id, combination_number=combination_number, size=combination_size, price=price, product_vsrap_id=vsrap_id)
                    combinations.append(combination)

            product = schemas.ProductCreate(vsrap_id=vsrap_id, vsrap_url=vsrap_url, title=title, pre_order=pre_order, limited=limited, price=price, image_url=image_url)
            products.append(product)
    
        return schemas.CollectionProductCombination(products=products, combinations=combinations)    
    
    async def get_products_combinations(self, collection: models.Collection) -> schemas.CollectionProductCombination:
        collection_products_combinations = schemas.CollectionProductCombination(collection=collection)
        is_last_page = False
        pagen_2 = 1

        while not is_last_page and pagen_2 < config.SCRAPER_PAGE_LOAD_MAX_COUNT:
            for i in range(config.SCRAPER_PAGE_LOAD_MAX_TRYINGS):
                try:
                    url = f"{collection.vsrap_url}?PAGEN_2={pagen_2}&AJAX_REQUEST=Y&ajax_get=Y&bitrix_include_areas=N&BLOCK=goods-list-inner"
                    async with self.session.get(url) as resp:
                        res = await resp.text()
                        soup = BeautifulSoup(res, 'html.parser')

                        products_combinations = await self.validate_products_combinations(soup)

                        collection_products_combinations.products += products_combinations.products
                        collection_products_combinations.combinations += products_combinations.combinations

                        pages = len(soup.findAll("a", {"class": "module-pagination__item"})) + 1
                        if pagen_2 >= pages: is_last_page = True

                        break

                except Exception as e:
                    # traceback.print_exc()
                    await asyncio.sleep(config.SCRAPER_SLEEP_ON_ERROR)
            pagen_2 += 1

        return collection_products_combinations
    
    async def get_product_page_soup(self, vsrap_url: str) -> BeautifulSoup:
        for i in range(config.SCRAPER_PAGE_LOAD_MAX_TRYINGS):
            try:
                url = vsrap_url
                async with self.session.get(url) as resp:
                    res = await resp.text()
                    soup = BeautifulSoup(res, 'html.parser')
                    return soup                    

            except Exception as e:
                traceback.print_exc()
                await asyncio.sleep(config.SCRAPER_SLEEP_ON_ERROR)

async def update_base(engine):
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(config.SCRAPER_PAGE_LOAD_TIMEOUT)) as session:
        with Session(engine) as db:
            scraper = Scraper(session)

            print("Getting collections")
            collections: list[schemas.CollectionCreate] = await scraper.get_collections()
            print(f"Got collections {len(collections)} - obj")

            collections_json = [collection.model_dump(mode='json') for collection in collections]
            
            collections_ids: list[list] = crud.upsert_collections(db, collections_json, need_return=True)
            db.commit()
            # collections_ids: [(id_2,), (id_1,)...] So we need to convert it to list[int]
            collections_ids: list[int] = [collection_info[0] for collection_info in collections_ids]
            collections: list[models.Collection] = crud.get_collections_by_id(db, collections_ids)
            print("Collections updated")

            print("Getting products info")
            product_tasks = [scraper.get_products_combinations(collection) for collection in collections]        
            products_info: list[schemas.CollectionProductCombination] = await asyncio.gather(*product_tasks)
            products_count: int = sum([len(product_info.products) for product_info in products_info])
            print(f"Got products info {products_count} - obj")

            for ind, product_info in enumerate(products_info):
                try:
                    collection: models.Collection = product_info.collection
                    schema_products: list[schemas.ProductCreate] = product_info.products
                    schema_combinations: list[schemas.CombinationCreate] = product_info.combinations
                    print(f"Collection - {collection.title}")

                    print(f"Products len - {len(schema_products)}")
                    if len(schema_products) > 0:
                        try:
                            products_json: list[dict] = [product.model_dump(mode='json') for product in schema_products]
                            products_ids: list[list] = crud.upsert_products(db, products_json, need_return=True)
                            # products_ids: [(id_2,), (id_1,)...] So we need to convert it to list[int]
                            products_ids: list[int] = [product_info[0] for product_info in products_ids]
                            db.commit()
                            print(f"Products updated")

                        except Exception as e:
                            print(f"Unexpected error - {e}")

                        model_products: list[models.Product] = crud.get_products_by_id(db, products_ids)
                        collection.products += model_products

                    print(f"Combinations len - {len(schema_combinations)}")
                    if len(schema_combinations) > 0:
                        try:
                            combinations: list[schemas.CombinationCreate] = [combination for combination in schema_combinations]
                            combinations_json: list[dict] = [combination.model_dump(mode='json') for combination in combinations]
                            crud.upsert_combinations(db, combinations_json)
                            db.commit()
                            print("Combinations updated")

                        except Exception as e:
                            print(f"Unexpected error - {e}")

                except Exception as e:
                    print(f"Unexpected error - {e}")

            print("All data updated")
