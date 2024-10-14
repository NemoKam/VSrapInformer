from fastapi import APIRouter

from .v1.routes import router as v1_router
from .auth.v1.routes import router as v1_auth_router
from logger import get_logger

py_logger = get_logger("/routes.py")

py_logger.debug("Starting Router")
router = APIRouter()

py_logger.debug("Including v1/routes.py")
router.include_router(v1_router)
py_logger.debug("Including auth/v1/routes.py")
router.include_router(v1_auth_router, prefix="/auth")
