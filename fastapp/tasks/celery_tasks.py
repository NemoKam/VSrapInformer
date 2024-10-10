import asyncio

from sqlalchemy.orm import Session

from fastapp import sender
from fastapp.core.celeryconfig import celery_app
from fastapp.scrape import update_base
from fastapp.database import engine, get_db_non_gen
from fastapp import crud


@celery_app.task()
def send_mail(receiver_email: str, title: str, message: str):
    try:
        asyncio.run(sender.send_email(receiver_email, title, message))
    except Exception as e:
        pass
        

@celery_app.task()
def send_phone_message(phone_number: str, title: str, message: str):
    pass


@celery_app.task()
def start_scraper():
    asyncio.run(update_base(engine))

@celery_app.task()
def clear_unverified_users(db: Session = get_db_non_gen()):
    crud.delete_expired_users(db)