import asyncio
import json
from email.message import EmailMessage
from venv import create
from webbrowser import get

import aiosmtplib
import requests

def create_user():
    url = "http://127.0.0.1:8000/api/auth/v1/users"

    data = {
        "password": "123123123",
        "email": "kamkamuch.8@gmail.com",
        "phone_number": "+793939393"
    }


    res = requests.post(url, data=json.dumps(data), timeout=10)


    return res.json()

def login():
    url = "http://127.0.0.1:8000/api/auth/v1/login"

    data = {
        "email": "kamkamuch.8@gmail.com",
        "password": "123123123",
    }


    res = requests.post(url, data=json.dumps(data), timeout=10)


    return res.json()

def get_user_products():
    jwt = login()

    for attempt in range(2):
        url = f"http://127.0.0.1:8000/api/v1/user/products?jwt={jwt}"

        res = requests.get(url)

        print(res.text)

        if res.status_code == 200:
            return res.json()
        elif res.status_code == 401:
            jwt = login()



def get_combinations():
    jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjo2NSwiZXhwIjoxNzI2MDcwMzAzfQ.sOZjcyNVPJ_K1aGV_I6cXJW2G8plL-aI1bMNIbI0nvU"
    for attempt in range(2):
        url = f"http://127.0.0.1:8000/api/v1/user/combination?jwt={jwt}"
        res = requests.get(url)

        if res.status_code == 200:
            return res.json()
        elif res.status_code == 401:
            jwt = login()
    
    return ""

def add_combinations():
    combination_id = 3007 #[{"id": 3007}, {"id": 3008}]

    jwt = login()


    for attempt in range(2):
        url = f"http://127.0.0.1:8000/api/v1/user/combination?jwt={jwt}&combination_id={combination_id}"

        data = {
            "combination_id": combination_id
        }

        res = requests.post(url, data=json.dumps(data))

        print(res.text)

        if res.status_code == 200:
            return res.json()
        elif res.status_code == 401:
            jwt = login()
    
    return ""

def select_combinations():
    jwt = login()

    url = f"http://127.0.0.1:8000/api/v1/user/combination?jwt={jwt}"

    res = requests.get(url)

    return res.json()

    

async def send_mail(
        sender_email: str = "thebulldok@yandex.ru",
        receiver_email: str = "kamkamuch.7@gmail.com",
        title: str = "Title",
        message: str = "message",
        smtp_host: str = "smtp.yandex.ru",
        smtp_port: int = 465,
        password: str = "excgvkdxrglxkzyg"):
    try:
        msg = EmailMessage()
        msg["From"] = sender_email
        msg["To"] = receiver_email
        msg["Subject"] = title
        msg.set_content(message)

        username: str = sender_email.split("@")[0]
        print("send")
        con = aiosmtplib.SMTP(hostname='smtp.yandex.ru', port=465, timeout=10, use_tls=True)
        print("connecting")
        await con.connect()
        print("connected")
        await con.login(sender_email, password)
        print("logged in")
        await con.sendmail(sender_email, receiver_email, msg.as_string())
        await con.quit()
        # await aiosmtplib.send(
        #     msg,
        #     sender=sender_email,
        #     recipients=receiver_email,
        #     hostname=smtp_host,
        #     port=smtp_port,
        #     username=username,
        #     password=password,
        #     use_tls=True
        # )
    except Exception as e:
        print(e)



# res = add_combinations()

# print(res)

# import requests


# url = "http://92.38.240.248:2053/"

# res = requests.get(url)

# print(res.text)

print(get_user_products())