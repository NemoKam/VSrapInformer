from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordBearer

from fastapp import models
from fastapp.core import config
from fastapp.api.routes import router as api_router
from fastapp.database import engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=config.PROJECT_TITLE,
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

app.include_router(api_router, prefix="/api")

# load static and templates
app.mount("/static", StaticFiles(directory="fastapp/static"), name="static")
templates = Jinja2Templates(directory="fastapp/templates")

@app.get("/", response_class=HTMLResponse)
async def get_main(request: Request):
    return templates.TemplateResponse(
        request=request, name="main.html", context={'title': app.title}
    )


