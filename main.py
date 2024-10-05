from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import time
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
from _http import HTTP

load_dotenv()

class App(FastAPI):
    client: "Client"

class Client:
    app: "App"
    http: HTTP
    
    def __init__(self, client_id: str, client_secret: str, *, scopes = [],  app: App= None):
        self.client_id = client_id
        self.client_secret = client_secret
        self.app = app
        self.redirect_uri = os.getenv("REDIRECT_URI")
        self.auth_header = f"Basic {base64.b64encode(f'{self.client_id}:{self.client_secret}'.encode()).decode()}"
        
        self.scope = " ".join(scopes)
        self.states = []
        self.http = HTTP(self)

    async def setup(self):
        await Tortoise.init(
            db_url=os.getenv("POSTGRES_URL"),
            modules={"models": ["models"]},
        )
        #sql = ...
        #await Tortoise.get_connection("default").execute_script(sql)
        #in case you need to run some sql script


        await Tortoise.generate_schemas()

        for user in await User.all():
            asyncio.create_task(self.refresh_task(user))


    async def refresh_task(self, user):
        now = datetime.datetime.now(pytz.utc)
        token_expires = user.token_expires.replace(tzinfo=pytz.utc)
        await asyncio.sleep((token_expires - now).total_seconds())
        await self.http.refresh_token(user)
        asyncio.create_task(self.refresh_task(user))

app = App(
    title="UnWrapped",
    description="Get your spotify unwrapped any time of the year(You can modify it too!)",
)
client = Client(
    os.getenv("CLIENT_ID"), os.getenv("CLIENT_SECRET"),
    scopes=[
        'user-top-read',
        'user-read-recently-played',
        'playlist-modify-public',
        'playlist-modify-private',
        'playlist-read-private',
        'user-read-email',
        'user-read-private',
        'user-read-playback-state',
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

@app.get("/playlists")
async def playlists(request: Request):
    playlists = await client.http.get_playlists()
    return templates.TemplateResponse(
        "playlists.html", {"request": request}
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
    
    user_data, token_data = await client.http.get_user_data(code)
    user = await client.http.get_or_create_user(user_data, token_data)
    
    return templates.TemplateResponse("loggedin.html", {"request": request, "user": user})


async def startup():
    await client.setup()

async def shutdown():
    await client.http.close()

app.add_event_handler("startup", startup)
app.add_event_handler("shutdown", shutdown)