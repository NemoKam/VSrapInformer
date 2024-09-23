from fastapi import FastAPI

from fastapp.api.routes import router as main_router

from core import config
from sqlalchemyapp import models
from fastapp.database import engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=config.PROJECT_TITLE,
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

app.include_router(main_router, prefix="/api")
