import asyncio

import uvicorn
from sqlalchemy import create_engine

from core import config
from fastapp.scrape import update_base
from logger import get_logger

py_logger = get_logger("main.py")


def scrape():
    py_logger.info("Starting scrape func")
    SQLALCHEMY_DATABASE_URL = f"postgresql+psycopg2://{config.POSTGRESQL_USER}:{config.POSTGRESQL_PASSWORD}@{config.POSTGRESQL_HOST}:{config.POSTGRESQL_PORT}/{config.POSTGRESQL_DATABASE}"
    py_logger.debug("Creating Engine")
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    py_logger.debug("Starting scraping")
    asyncio.run(update_base(engine))
    py_logger.info("Scrape func done")


def fastapp():
    py_logger.info("Starting fastapp func")
    uvicorn.run("fastapp.fast:app", host=config.PROJECT_HOST, port=config.PROJECT_PORT,
                workers=config.CELERY_WORKER_COUNT, reload=config.RELOAD)
    py_logger.info("Fastapp func done")


if __name__ == "__main__":
    fastapp()
