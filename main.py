import traceback
from fastapi import FastAPI, Request, Depends
from fastapi.responses import RedirectResponse, JSONResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from itsdangerous import URLSafeSerializer
import time
import os
import random
import base64
import datetime
import asyncio
import pytz
import cachetools
from tortoise import Tortoise
from dotenv import load_dotenv
import logging


from models import User, dc_dumps
from _http import HTTP

load_dotenv()

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

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
        self.serializer = URLSafeSerializer(os.getenv("SECRET_KEY"),salt=os.getenv("SECRET_SALT").encode())

    async def retry_db_connection(self, retries=3, delay=5):
        for _ in range(retries):
            try:
                await Tortoise.init(
                    db_url=os.getenv("POSTGRES_URL"),
                    modules={"models": ["models"]},
                    use_tz=True,
                )
                await Tortoise.generate_schemas()
                break
            except Exception as e:
                print(f"DB connection failed: {e}, retrying...")
                await asyncio.sleep(delay)

    async def setup(self):
        await self.retry_db_connection()
        await self.http.setup()
        uc = 0

        for user in await User.all():
            uc += 1
            asyncio.create_task(self.refresh_task(user))

        logger.info(f"Loaded {uc} users")

    async def refresh_task(self, user):
        now = datetime.datetime.now(pytz.utc)
        token_expires = user.token_expires.replace(tzinfo=pytz.utc)
        await asyncio.sleep((token_expires - now).total_seconds())
        await self.http.refresh_token(user)
        asyncio.create_task(self.refresh_task(user))

app = App(
    title="UnWrapped",
    description="Get your Spotify Wrapped and other stats any time of the year!",
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

@app.get("/static/fonts/{font_name}")
async def get_font(font_name: str):
    file_path = f"static/fonts/{font_name}"
    headers = {
        "Cache-Control": "public, max-age=31536000"
    }
    return FileResponse(file_path, headers=headers)

@app.get("/static/logo/{logo_name}")
async def get_logo(logo_name: str):
    file_path = f"static/logo/{logo_name}"
    headers = {
        "Cache-Control": "public, max-age=1000"
    }
    return FileResponse(file_path, headers=headers)

@app.get("/spotify_logo")
async def get_spotify_logo():
    file_path = f"static/logo/SpotifyLogo.png"
    headers = {
        "Cache-Control": "public, max-age=31536000"
    }
    return FileResponse(file_path, headers=headers)

@app.get("/privacy_policy")
async def toc(request: Request):
    return templates.TemplateResponse(
        "priv_pol.html", {"request": request}
    )

app.add_middleware(SessionMiddleware, secret_key=os.getenv("SECRET_KEY"))

def sign_data(data):
    return client.serializer.dumps(data)

def unsign_data(data) -> str:
    return client.serializer.loads(data)

user_cache = cachetools.TTLCache(maxsize=100, ttl=30)

async def get_cached_user(key: str) -> User:
    try:
        return user_cache[key]
    except KeyError:
        user = await User.get(key=key)
        user_cache[key] = user
        return user

async def _get_user(request: Request) -> User| None:
    try:
        key = unsign_data(request.session.get("key"))
    except:
        request.session.pop("key", None)
        return None
    if not key:
        return None
    try:
        user = await get_cached_user(key)
    except User.DoesNotExist:
        return None
    return user

get_user = Depends(_get_user)

@app.get("/")
async def root(request: Request, user: User = get_user):
    return templates.TemplateResponse(
        "index.html", {"request": request, "user": user}
    )

@app.get("/favicon.ico")
async def favicon():
    file_path = f"static/logo/LogoCircle.png"
    headers = {
        #"Cache-Control": "public, max-age=31536000"
    }
    return FileResponse(file_path, headers=headers)

@app.get("/profile")
async def profile(request: Request, user: User = get_user):
    if not user:
        return RedirectResponse("/login")
    return templates.TemplateResponse(
        "profile.html", {"request": request}
    )

@app.get("/playlists")
async def playlists(request: Request, user: User = get_user):
    if not user:
        return RedirectResponse("/login")
    return templates.TemplateResponse(
        "playlists.html", {"request": request}
    )

@app.get("/load_more_playlists")
async def load_more_playlists(request: Request, page: int, user: User = get_user):
    offset = page * 20
    if not user:
        return RedirectResponse("/login")
    playlists = await client.http.get_user_playlists(user, offset=offset, limit=20)
    playlists = [dc_dumps(playlist) for playlist in playlists]
    return JSONResponse({"playlists": playlists})

@app.get("/playlist")
async def playlist(request: Request, playlist_id: str, user: User = get_user):
    if not user:
        return RedirectResponse("/login")
    playlist = await client.http.get_playlist(user, playlist_id)
    return templates.TemplateResponse(
        "playlist.html", {"request": request, "playlist": playlist}
    )

@app.get('/load_more_playlist_tracks')
async def load_more_playlist_tracks(request: Request, playlist_id: str, page:int, user: User = get_user):
    if not user:
        return RedirectResponse("/login")
    offset = page * 20
    tracks = await client.http.get_playlist_tracks(user, playlist_id, offset=offset)
    tracks.sort(key=lambda x: x.added_at, reverse=True)
    return JSONResponse({"tracks": [dc_dumps(track) for track in tracks]})

@app.get("/toptracks")
async def top_tracks(request: Request, type: str = "short_term", user: User = get_user):
    if not user:
        return RedirectResponse("/login")
    return templates.TemplateResponse(
        "top_tracks.html", {"request":request, "type":type}
    )

@app.get('/load_more_toptracks')
async def load_more_toptracks(request: Request, page:int, type: str = "short_term", user: User = get_user):
    if not user:
        return RedirectResponse("/login")
    offset = page * 20
    tracks = await client.http.get_top_tracks(user, type=type, offset=offset)
    tracks.sort(key=lambda x: x.popularity, reverse=True)
    return JSONResponse({"tracks": [dc_dumps(track) for track in tracks]})

@app.get("/topartists")
async def top_artists(request: Request, type: str = "short_term", user: User = get_user):
    if not user:
        return RedirectResponse("/login")
    return templates.TemplateResponse(
        "top_artists.html", {"request":request, "type":type}
    )

@app.get('/load_more_topartists')
async def load_more_topartists(request: Request, page:int, type: str = "short_term", user: User = get_user):
    if not user:
        return RedirectResponse("/login")
    offset = page * 20
    artists = await client.http.get_top_artists(user, type=type, offset=offset)
    artists.sort(key=lambda x: x.popularity, reverse=True)
    return JSONResponse({"artists": [dc_dumps(artist) for artist in artists]})

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
    try:
        if error:
            try:
                client.states.remove(state)
            except ValueError:
                return RedirectResponse("/login")
        if state not in client.states:
            return RedirectResponse("/login")
        
        user_data, token_data = await client.http.get_user_data(code)
        user = await client.http.get_or_create_user(user_data, token_data)
        user_cache[user.key] = user
        request.session["key"] = sign_data(user.key)
        
        return templates.TemplateResponse("loggedin.html", {"request": request, "user": user})
    except Exception as e:
        logger.error(f"Error during callback: {e}\n{traceback.format_exc()}")
        if "user may not be registered" in str(e):
            return {"error": "User is not registered as a tester. Please contact the administrator."}
        return {"error": str(e), "traceback": traceback.format_exc()}
@app.get("/logout")
async def logout(request: Request):
    request.session.pop("key", None)
    return RedirectResponse("/")

@app.head("/ping")
async def ping():
    return

async def startup():
    try:
        await client.setup()
    except Exception as e:
        print(f"Error during startup: {e}")
        raise e

async def shutdown():
    await Tortoise.close_connections()
    await client.http.close()

app.add_event_handler("startup", startup)
app.add_event_handler("shutdown", shutdown)