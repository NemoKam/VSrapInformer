import asyncio

from sqlalchemy import create_engine 

from fastapp.core import config
from fastapp.scrape import update_base

def scrape():
    SQLALCHEMY_DATABASE_URL = f"postgresql+psycopg2://{config.POSTGRESQL_USER}:{config.POSTGRESQL_PASSWORD}@{config.POSTGRESQL_HOST}:{config.POSTGRESQL_PORT}/{config.POSTGRESQL_DATABASE}"
    engine = create_engine(SQLALCHEMY_DATABASE_URL)

    asyncio.run(update_base(engine))

def fastapp():
    pass

scrape()