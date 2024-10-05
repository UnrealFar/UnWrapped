from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
import time
import os
import random
import base64
import datetime
import asyncio
import aiohttp
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
        #sql = 'ALTER TABLE "user" ALTER COLUMN "key" SET NOT NULL;'
        #await Tortoise.get_connection("default").execute_script(sql)
        #in case you need to run some sql script

        await Tortoise.generate_schemas()

        self.http.session = aiohttp.ClientSession()

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

app.add_middleware(SessionMiddleware, secret_key=os.getenv("SECRET_KEY"))

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
async def playlists(request: Request, refresh: bool = False):
    key = request.session.get("key")
    if not key:
        return RedirectResponse("/login")
    try:
        user = await User.get(key=key)
    except User.DoesNotExist:
        return RedirectResponse("/login")
    if refresh or not client.http.user_playlists:
        playlists = await client.http.get_playlists(user, offset=0, limit=20)
        client.http.user_playlists[user.spotify_id] = playlists
    else:
        playlists = client.http.user_playlists[user.spotify_id]
    return templates.TemplateResponse(
        "playlists.html", {"request": request}
    )

@app.get("/load_more_playlists")
async def load_more_playlists(request: Request, offset: int):
    key = request.session.get("key")
    try:
        user = await User.get(key=key)
    except User.DoesNotExist:
        return RedirectResponse("/login")
    playlists = await client.http.get_playlists(user, offset=offset, limit=20)
    client.http.user_playlists[user.spotify_id].extend(playlists)
    return templates.TemplateResponse(
        "playlists.html", {"request": request, "playlists": playlists}
    )

@app.get("/top_tracks")
async def top(request: Request, type: str = "medium_term"):
    key = request.session.get("key")
    try:
        user = await User.get(key=key)
    except User.DoesNotExist:
        return RedirectResponse("/login")
    tracks = await client.http.get_top_tracks(user, type=type)
    return templates.TemplateResponse(
        "top_tracks.html", {"request": request, tracks: tracks}
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
    request.session["key"] = user.key
    
    return templates.TemplateResponse("loggedin.html", {"request": request, "user": user})


async def startup():
    await client.setup()

async def shutdown():
    await client.http.close()

app.add_event_handler("startup", startup)
app.add_event_handler("shutdown", shutdown)