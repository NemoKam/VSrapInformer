import asyncio

from sqlalchemy.orm import Session

from fastapp import sender, crud, exceptions
from core.celeryconfig import celery_app
from fastapp.scrape import update_base
from fastapp.database import engine, get_db_non_gen
from logger import get_logger


py_logger = get_logger("celery_tasks.py")


@celery_app.task()
def send_mail(receiver_email: str, title: str, message: str):
    try:
        py_logger.debug("Sending mail.")
        asyncio.run(sender.send_email(receiver_email, title, message))
    except Exception:
        py_logger.error("Error while sending email", exc_info=True)


@celery_app.task()
def send_phone_message(phone_number: str, title: str, message: str):
    py_logger.debug("Sending phone_number. Unavailable.")
    raise exceptions.UnAvailable()


@celery_app.task()
def start_scraper():
    py_logger.debug("Staring scraping.")
    asyncio.run(update_base(engine))
    py_logger.debug("Scraped.")


@celery_app.task()
def clear_unverified_users(db: Session = get_db_non_gen()):
    py_logger.debug("Deleting expired users.")
    crud.delete_expired_users(db)
    py_logger.debug("Expired users deleted.")
