from pydantic import BaseModel, RootModel
from typing import Optional, Dict, List
from fastapi import Form, File, UploadFile

# 用户相关模型
class RegisterRequest(BaseModel):
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

class ResetNameRequest(BaseModel):
    new_name: str

class ResetEmailRequest(BaseModel):
    new_email: str

class UserResponse(BaseModel):
    uid: str

# 地图相关模型
class ChangeResponse(BaseModel):
    details: Optional[Dict] = []

class AddMapRequest(BaseModel):
    map_name: str
    file: str  # 字符串化的图片内容 (Base64 编码)

class ChangeMapRequest(BaseModel):
    arcs: Optional[List] = []

class SearchRequest(BaseModel):
    query_name: str = ""
    query_type: str = ""
    query_media: str = ""
    query_desc: str = ""
    top_n: int = 10

class MapDetailResponse(BaseModel):
    mapid: str
    details: Dict
    image: str  # base64 编码的图像数据

class MapListResponse(BaseModel):
    maps: List[Dict]

# 用户视图相关模型
class SetCurrentMapRequest(BaseModel):
    map_id: str

class WriteNoteRequest(BaseModel):
    note: str

class NoteResponse(BaseModel):
    uid: str
    time: str
    context: str