from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from core import config
from fastapp import models, dependencies
from fastapp.api.routes import router as api_router
from fastapp.database import engine
from logger import get_logger

py_logger = get_logger("fast.py")

py_logger.debug("Creating all metadata")
models.Base.metadata.create_all(bind=engine)

py_logger.debug("Starting FastAPI")
app = FastAPI(
    title=config.PROJECT_TITLE,
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

py_logger.debug("Including router")
app.include_router(api_router, prefix="/api")

# load static and templates
py_logger.debug("Including static")
app.mount("/static", StaticFiles(directory="fastapp/static"), name="static")
py_logger.debug("Including templates")
templates = Jinja2Templates(directory="fastapp/templates")

py_logger.debug("Started FastAPI")


@app.get("/", response_class=HTMLResponse)
async def get_main(request: Request, user_ip: str = Depends(dependencies.get_ip_from_request)):
    py_logger.debug(f"Getting main page. IP: {user_ip}")

    return templates.TemplateResponse(
        request=request, name="main.html", context={'title': app.title}
    )
