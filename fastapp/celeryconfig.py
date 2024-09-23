from celery import Celery

from core import config


CELERY_BROKER_URL = config.CELERY_BROKER_URL
CELERY_BACKEND_URL = config.CELERY_BACKEND_URL

celery_app = Celery(__name__, broker=CELERY_BROKER_URL, backend=CELERY_BACKEND_URL)

celery_app.conf.update(
    imports=['fastapp.tasks.celery_tasks'],
    broker_connection_retry_on_startup=True,
    task_track_started=True
)
