from sqlmodel import SQLModel, Field, Session
from typing import Optional
from pydantic import EmailStr
import uuid
from datetime import datetime


class MapBase(SQLModel):
    map_name : str = Field(max_length=127)
    map_type : str = Field(default="未分类", max_length=63)
    media_type : str = Field(default="未分类", max_length=63)
    description : str = Field(default="尚未添加任何描述", max_length=511)

class Map(MapBase, table = True):
    mapid : uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    public_time : datetime = Field(default_factory=datetime.now)
    collect_time : datetime = Field(default_factory=datetime.now)
    stars : int = Field(default=5, max_items=5, min_items=0)
    file_path : str = Field(max_length=255)
class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    name : str = Field(default="Collector", max_length=127)

class User(UserBase, table = True):
    uid : uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_passward : str
    last_read: uuid.UUID|None = Field(
        default=None,
        nullable=True,
        sa_column_kwargs={
            "comment": "最后访问的地图ID",
            "index": True
        })

class Note(SQLModel, table = True):
    noteid : uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    uid : uuid.UUID = Field(foreign_key="user.uid")
    mapid : uuid.UUID = Field(foreign_key="map.mapid")
    content : str = Field(max_length=511)
    time : datetime = Field(default_factory=datetime.now)

class MapChange(SQLModel, table = True):
    change_id : uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    mapid : uuid.UUID = Field(foreign_key="map.mapid")
    uid : uuid.UUID = Field(foreign_key="user.uid")
    change_time: datetime = Field(default_factory=datetime.now)
    public_time: datetime = Field(nullable=True, default=None)
    map_name: str = Field(max_length=127, nullable=True, default=None)
    map_type: str = Field(max_length=63, nullable=True, default=None)
    media_type: str = Field(nullable=True, default=None, max_length=63)
    description: str = Field(nullable=True, default=None, max_length=511)
