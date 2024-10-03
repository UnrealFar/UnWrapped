from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import time
import aiohttp
import os
import random
import base64
import datetime
import asyncio
import tortoise
import pytz
from tortoise import Tortoise
from dotenv import load_dotenv

from models import User

load_dotenv()

class App(FastAPI):
    client: "Client"

class Client:
    app: "App"
    session: aiohttp.ClientSession
    
    def __init__(self, client_id: str, client_secret: str, *, scopes = [],  app: App= None):
        self.client_id = client_id
        self.client_secret = client_secret
        self.app = app
        self.redirect_uri = os.getenv("REDIRECT_URI")
        self.auth_header = f"Basic {base64.b64encode(f'{self.client_id}:{self.client_secret}'.encode()).decode()}"
        
        self.scope = " ".join(scopes)
        self.states = []

    async def setup(self):
        self.session = aiohttp.ClientSession()
        
        await Tortoise.init(
            db_url=os.getenv("POSTGRES_URL"),
            modules={"models": ["models"]},
        )

        await Tortoise.generate_schemas()

        for user in await User.all():
            asyncio.create_task(self.refresh_task(user))

            
    async def refresh_task(self, user):
        now = datetime.datetime.now(pytz.utc)
        token_expires = user.token_expires.replace(tzinfo=pytz.utc)
        await asyncio.sleep((token_expires - now).total_seconds())
        await self.refresh_token(user)
        asyncio.create_task(self.refresh_task(user))


    async def refresh_token(self, user):
        url = "https://accounts.spotify.com/api/token"
        async with self.session.post(
            url,
            data={
                "grant_type": "refresh_token",
                "refresh_token": user.refresh_token,
            },
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Authorization": self.auth_header,
            },
        ) as response:
            data = await response.json()
            user.access_token = data["access_token"]
            user.token_expires = datetime.datetime.now(pytz.utc) + datetime.timedelta(seconds=data["expires_in"])
            await user.save()

app = App(
    title="UnWrapped",
    description="Get your spotify unwrapped any time of the year(You can modify it too!)",
)
client = Client(
    os.getenv("CLIENT_ID"), os.getenv("CLIENT_SECRET"),
    scopes=[
        'user-top-read',
        'user-read-recently-played',
        'user-read-email',
        'user-read-private',
    ],
    app=app
)


templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse(
        "index.html", {"request": request}
    )

@app.get("/profile")
async def profile(request: Request):
    return templates.TemplateResponse(
        "profile.html", {"request": request}
    )

@app.get("/login")
async def login(
    request: Request,
):
    state = str(time.time() * random.random())
    client.states.append(state)
    url = "https://accounts.spotify.com/authorize?"\
        f"client_id={client.client_id}"\
        f"&response_type=code"\
        f"&redirect_uri={client.redirect_uri}"\
        f"&scope={client.scope}"\
        f"&state={state}"
    return RedirectResponse(url)

@app.get("/callback")
async def callback(
    request: Request,
    code: str,
    state: str,
    error: str = None,
):
    if error:
        client.states.remove(state)
        return RedirectResponse("/login")
    url = "https://accounts.spotify.com/api/token"
    async with client.session.post(
        url,
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": client.redirect_uri,
        },
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": client.auth_header,
        },
    ) as response:
        data = await response.json()
        print(data)
        access_token = data["access_token"]
        expires_in = data["expires_in"]
        refresh_token = data["refresh_token"]
        token_type = data["token_type"]
        
        url = "https://api.spotify.com/v1/me"
        async with client.session.get(
            url,
            headers={
                "Authorization": f"{token_type} {access_token}",
            },
        ) as response:
            data = await response.json()
            try:
                user = await User.get(spotify_id=data["id"])
            except tortoise.exceptions.DoesNotExist:
                user = User(
                    spotify_id=data["id"],
                    access_token=access_token,
                    refresh_token=refresh_token,
                    token_expires=datetime.datetime.now() + datetime.timedelta(seconds=expires_in),
                    display_name=data["display_name"],
                    email=data["email"],
                    uri=data["uri"],
                    image=data["images"][0]["url"],
                    country=data["country"],
                    product=data["product"],
                )
            else:
                user.access_token = access_token
                user.refresh_token = refresh_token
                user.token_expires = datetime.datetime.now() + datetime.timedelta(seconds=expires_in)
                user.display_name = data["display_name"]
                user.email = data["email"]
                user.uri = data["uri"]
                user.image = data["images"][0]["url"]
                user.country = data["country"]
                user.product = data["product"]
            await user.save()
    return templates.TemplateResponse("loggedin.html", {"request": request, "user": user})


async def startup():
    await client.setup()

async def shutdown():
    await client.session.close()

app.add_event_handler("startup", startup)
app.add_event_handler("shutdown", shutdown)

