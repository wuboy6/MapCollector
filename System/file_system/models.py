from sqlmodel import SQLModel, Field, Session
from typing import Optional
from pydantic import EmailStr
import uuid
from datetime import datetime


class MapBase(SQLModel):
    map_name : str = Field(max_length=127)
    map_type : str = Field(max_length=63)
    media_type : str = Field(max_length=63)
    description : str = Field(max_length=511)

class Map(MapBase, table = True):
    mapid : uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    public_time : datetime
    collect_time : datetime = Field(default_factory=datetime.now)
    stars : int = Field(default=5, max_items=5, min_items=0)
    file_path : str = Field(max_length=255)
class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    name : str | None = Field(default=None, max_length=127)

class User(UserBase, table = True):
    uid : uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_passward : str
    last_read : uuid.UUID

class Note(SQLModel, table = True):
    noteid : uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    uid : uuid.UUID = Field(foreign_key="user.uid")
    mapid : uuid.UUID = Field(foreign_key="map.mapid")
    content : str = Field(max_length=511)
    time : datetime = Field(default_factory=datetime.now)
