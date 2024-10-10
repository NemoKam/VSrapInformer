from email.message import EmailMessage

import aiosmtplib

from fastapp import exceptions
from fastapp.core import config

async def send_email(receiver_email: str, title: str, message: str) -> dict:
    sender_email: str = config.EMAIL_LOGIN

    msg = EmailMessage()
    msg["From"] = sender_email
    msg["To"] = receiver_email
    msg["Subject"] = title
    msg.set_content(message)

    username: str = sender_email.split("@")[0]

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
    return {"status": "success"}

async def send_phone_number(phone_number: str, title: str, message: str) -> dict:
    raise exceptions.UnAvailable()