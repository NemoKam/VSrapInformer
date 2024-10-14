from email.message import EmailMessage

import aiosmtplib

from fastapp import exceptions
from core import config
from logger import get_logger

py_logger = get_logger("sender.py")


async def send_email(receiver_email: str, title: str, message: str) -> dict:
    sender_email: str = config.EMAIL_LOGIN

    msg = EmailMessage()
    msg["From"] = sender_email
    msg["To"] = receiver_email
    msg["Subject"] = title
    msg.set_content(message)

    username: str = sender_email.split("@")[0]

    py_logger.debug(f"Sending mail to {receiver_email}")
    await aiosmtplib.send(
        msg,
        sender=sender_email,
        recipients=receiver_email,
        hostname=config.EMAIL_SMTP_HOST,
        port=config.EMAIL_SMTP_PORT,
        username=username,
        password=config.EMAIL_PASSWORD,
        use_tls=True
    )
    py_logger.debug("Mail successfully sended")
    return {"status": "success"}


async def send_phone_number(phone_number: str, title: str, message: str) -> dict:
    py_logger.debug("Send phone number. Unavailable now")
    raise exceptions.UnAvailable()
