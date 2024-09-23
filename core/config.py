import os

from dotenv import load_dotenv

load_dotenv()

POSTGRESQL_USER = os.environ.get("POSTGRESQL_USER")
POSTGRESQL_PASSWORD = os.environ.get("POSTGRESQL_PASSWORD")
POSTGRESQL_HOST = os.environ.get("POSTGRESQL_HOST")
POSTGRESQL_PORT = os.environ.get("POSTGRESQL_PORT")
POSTGRESQL_DATABASE = os.environ.get("POSTGRESQL_DATABASE")

EMAIL_LOGIN = os.environ.get("EMAIL_LOGIN")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")
EMAIL_SMTP_HOST = os.environ.get("EMAIL_SMTP_HOST")
EMAIL_SMTP_PORT = os.environ.get("EMAIL_SMTP_PORT")

CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL")
CELERY_BACKEND_URL = os.environ.get("CELERY_BACKEND_URL")

JWT_SECRET = os.environ.get("JWT_SECRET")
JWT_ALGORITHM = os.environ.get("JWT_ALGORITHM")
JWT_TIME_LIVE = 15 * 60 # seconds (15 minutes)
JWT_EMAIL_PHONE_TIME_LIVE = 15 * 60 # seconds (15 minutes)

VERIFICATION_CODE_LENGTH = 6
VERIFICATION_CODE_ONLY_DIGITS = True
VERIFICATION_CODE_TIME_LIVE = 15 * 60 # seconds (15 minutes)

UNVERIFIED_USER_TIME_LIVE = 15 * 60 # seconds (15 minutes)

BASE_API_URL = "http://127.0.0.1:8000"
PROJECT_TITLE = "VSrapInformer"
