from tortoise import Model, fields
from dataclasses import dataclass
from typing import List, Dict

class User(Model):
    id = fields.BigIntField(pk=True, generated=True)
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
    images: List[str]
    owner: str
    public: bool
    snapshot_id: str
    tracks: List[str]
    track_count: int
    uri: str

