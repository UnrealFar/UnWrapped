from tortoise import Model, fields
from dataclasses import dataclass, asdict
from typing import List, Optional
import json

class DataclassEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, '__dataclass_fields__'):
            return asdict(obj)
        return super().default(obj)

def dc_dumps(obj):
    return json.dumps(obj, cls=DataclassEncoder)

class User(Model):
    id = fields.BigIntField(pk=True, generated=True)
    key = fields.CharField(max_length=512, null=True)
    spotify_id = fields.CharField(max_length=255)
    country = fields.CharField(max_length=255, null=True)
    display_name = fields.CharField(max_length=255, null=True)
    email = fields.CharField(max_length=255, null=True)
    follower_count = fields.IntField(default=0)
    uri = fields.CharField(max_length=255, null=True)
    image = fields.CharField(max_length=255, null=True)
    product = fields.CharField(max_length=255, null=True)
    access_token = fields.CharField(max_length=512, null=True)
    refresh_token = fields.CharField(max_length=512, null=True)
    token_expires = fields.DatetimeField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    def __repr__(self):
        return f'User<{self.spotify_id}>'
    

# Dataclasses so we won't store the user's personal data :)

@dataclass
class Playlist:
    id: str
    name: str
    collaborative: bool
    description: str
    href: str
    owner_id: str
    owner_name: str
    public: bool
    snapshot_id: str
    track_href: str
    track_count: int
    image: str | None = None
    tracks: List[str] | None = None


@dataclass
class Artist:
    id: str
    name: str
    uri: str
    image: str | None = None
    popularity: str | None = None
    followers: int | None = None
    genres: List[str] | None = None

@dataclass
class Album:
    id: str
    uri: str
    name: str | None = None
    artists: List[Artist] | None = None
    image: str | None = None

@dataclass
class Track:
    id: str
    name: str
    artists: List[Artist]
    album: Album
    duration_ms: int
    popularity: int
    explicit: bool
    uri: str
    preview_url: str | None = None

@dataclass
class PlaylistTrack(Track):
    added_at: str | None = None
    added_by: str | None = None


