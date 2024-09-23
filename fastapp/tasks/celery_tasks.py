import asyncio

from fastapp.celeryconfig import celery_app
from fastapp import sender

from ..scrape import update_base
from ..database import engine

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

