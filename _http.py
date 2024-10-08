from __future__ import annotations

from typing import Any, Dict, List, Tuple, TYPE_CHECKING
import aiohttp
import bcrypt
import datetime
import pytz
import tortoise
import logging
from models import (
    User,
    Playlist,
    Track,
    Artist,
    Album,
)

if TYPE_CHECKING:
    from main import Client

class HTTP:
    client: Client
    session: aiohttp.ClientSession
    
    def __init__(self, client: Client):
        self.client = client
        self.session = None
        
        self.user_playlists: Dict[str, List[Playlist]] = {}

    async def setup(self):
        self.session = aiohttp.ClientSession()

    async def close(self):
        if self.session:
            await self.session.close()


    async def request(self, method, url, **kwargs):
        if not self.session:
            self.session = aiohttp.ClientSession()
        async with self.session.request(method, url, **kwargs) as response:
            try:
                return await response.json()
            except aiohttp.ContentTypeError:
                raise Exception(await response.text())


    async def refresh_token(self, user) -> None:
        url = "https://accounts.spotify.com/api/token"
        data = await self.request(
            "POST",
            url,
            data={
                "grant_type": "refresh_token",
                "refresh_token": user.refresh_token,
            },
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Authorization": self.client.auth_header,
            },
        )
        user.access_token = data["access_token"]
        user.token_expires = datetime.datetime.now(pytz.utc) + datetime.timedelta(seconds=data["expires_in"])
        await user.save()

    async def get_user_data(self, code: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        url = "https://accounts.spotify.com/api/token"
        data = await self.request(
            "POST",
            url,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": self.client.redirect_uri,
            },
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Authorization": self.client.auth_header,
            },
        )
        access_token = data["access_token"]
        token_type = data["token_type"]
        
        url = "https://api.spotify.com/v1/me"
        user_data = await self.request(
            "GET",
            url,
            headers={
                "Authorization": f"{token_type} {access_token}",
            },
        )
        return user_data, data

    async def get_or_create_user(self, user_data, token_data) -> User:
        access_token = token_data["access_token"]
        expires_in = token_data["expires_in"]
        refresh_token = token_data["refresh_token"]
        
        try:
            user = await User.get(spotify_id=user_data["id"])
        except tortoise.exceptions.DoesNotExist:
            user = User(
                spotify_id=user_data["id"],
                access_token=access_token,
                refresh_token=refresh_token,
                token_expires=datetime.datetime.now() + datetime.timedelta(seconds=expires_in),
                display_name=user_data["display_name"],
                email=user_data["email"],
                uri=user_data["uri"],
                image=user_data["images"][0]["url"],
                country=user_data["country"],
                product=user_data["product"],
                key=bcrypt.hashpw(user_data["id"].encode(), bcrypt.gensalt()).decode(),
            )
        else:
            user.access_token = access_token
            user.refresh_token = refresh_token
            user.token_expires = datetime.datetime.now() + datetime.timedelta(seconds=expires_in)
            user.display_name = user_data["display_name"]
            user.email = user_data["email"]
            user.uri = user_data["uri"]
            user.image = user_data["images"][0]["url"]
            user.country = user_data["country"]
            user.product = user_data["product"]
        await user.save()
        return user

    async def get_user_playlists(self, user, limit: int = 50, offset: int = 0) -> List[Playlist]:
        url = "https://api.spotify.com/v1/me/playlists"
        data = await self.request(
            "GET",
            url,
            headers={
                "Authorization": f"Bearer {user.access_token}",
            },
            params={
                "limit": limit,
                "offset": offset,
            },
        )
        next_url = data["next"]
        while next_url:
            next_data = await self.request(
                "GET",
                next_url,
                headers={
                    "Authorization": f"Bearer {user.access_token}",
                },
            )
            data["items"].extend(next_data["items"])
            next_url = next_data["next"]

        playlists = []
        for item in data["items"]:
            playlist = Playlist(
                id=item["id"],
                name=item["name"],
                collaborative=item["collaborative"],
                description=item["description"],
                href=item["href"],
                images=[image["url"] for image in item["images"]],
                owner=item["owner"]["id"],
                public=item["public"],
                snapshot_id=item["snapshot_id"],
                tracks=[track["track"]["id"] for track in item["tracks"]["items"]],
                track_count=item["tracks"]["total"],
                uri=item["uri"],
            )
            playlists.append(playlist)
        self.user_playlists[user.spotify_id] = playlists
        return playlists

    async def get_top_tracks(
            self, user: User,
            type: str = "short_term",
            offset: int = 0,
            limit: int = 20
    ) -> List[Track]:
        url = f"https://api.spotify.com/v1/me/top/tracks"
        data = await self.request(
            "GET",
            url,
            headers={
                "Authorization": f"Bearer {user.access_token}",
            },
            params={
                "time_range": type,
                "offset": offset,
                "limit": limit,
            },
        )
        tracks = []
        for item in data["items"]:
            track = Track(
                id=item["id"],
                name=item["name"],
                artists=[Artist(id=artist["id"], name=artist["name"], uri=artist["uri"]) for artist in item["artists"]],
                album=Album(
                    id=item["album"]["id"],
                    name=item["album"]["name"],
                    artists=[Artist(id=artist["id"], name=artist["name"], uri=artist["uri"]) for artist in item["album"]["artists"]],
                    image=item["album"]["images"][0]["url"],
                    uri=item["album"]["uri"],
                ),
                duration_ms=item["duration_ms"],
                popularity=item["popularity"],
                explicit=item["explicit"],
                uri=item["uri"],
            )
            tracks.append(track)
        return tracks

    async def get_top_artists(
        self, user: User,
        type: str = "short_term",
        offset: int = 0,
        limit: int = 20
    ) -> List[Artist]:
        url = f"https://api.spotify.com/v1/me/top/artists"
        data = await self.request(
            "GET",
            url,
            headers={
                "Authorization": f"Bearer {user.access_token}",
            },
            params={
                "time_range": type,
                "offset": offset,
                "limit": limit,
            },
        )
        artists = []
        for item in data["items"]:
            artist = Artist(
                id=item["id"],
                name=item["name"],
                uri=item["uri"],
                image=item["images"][0]["url"],
                popularity=item["popularity"],
                followers=item["followers"]["total"],
                genres=item["genres"],
            )
            artists.append(artist)
        return artists

    async def close(self):
        await self.session.close()
