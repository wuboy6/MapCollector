from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from models import *
from services import *
import os
import uuid
import base64
from pathlib import Path

app = FastAPI(title="Map Collector API")

# 添加CORS中间件，允许跨源请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 开发环境下允许所有源，生产环境应该限制特定源
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有HTTP方法
    allow_headers=["*"],  # 允许所有headers
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# 静态图片获取
# 获取当前文件所在目录的绝对路径
BASE_DIR = Path(__file__).parent.resolve()
# 定义资源文件夹路径
RES_DIR = BASE_DIR / "res"


@app.get("/image/{filename}")
async def get_image(filename: str):
    try:
        # 构造安全路径（自动过滤路径遍历攻击）
        target_path = (RES_DIR / filename).resolve().relative_to(RES_DIR.resolve())

        # 验证文件是否存在
        if not target_path.is_file():
            raise HTTPException(status_code=404, detail="Image not found")

        return FileResponse(target_path)

    except ValueError:
        # 处理路径越权访问
        raise HTTPException(status_code=403, detail="Access denied")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 用户相关端点
@app.post("/register", response_model=UserResponse)
def register(req: RegisterRequest):
    status, uid = register_user(req.email, req.password)
    if status == 0:
        return {"uid": uid}
    raise HTTPException(status_code=400, detail=f"注册失败，状态码: {status}")

@app.post("/login", response_model=UserResponse)
def login(req: LoginRequest):
    status, uid = login_user(req.email, req.password)
    if status == 0:
        return {"uid": uid}
    raise HTTPException(status_code=400, detail=f"登录失败，状态码: {status}")

@app.get("/user/{uid}/name")
def get_user_name_route(uid: str):
    name = get_user_name(uid)
    if name:
        return {"name": name}
    raise HTTPException(status_code=404, detail="用户不存在")

@app.put("/user/{uid}/name")
def reset_user_name_route(uid: str, req: ResetNameRequest):
    status = reset_user_name(uid, req.new_name)
    if status != 0:
        raise HTTPException(status_code=400, detail=f"重置用户名失败，状态码: {status}")

@app.put("/user/{uid}/email")
def reset_user_email_route(uid: str, req: ResetEmailRequest):
    status = reset_user_email(uid, req.new_email)
    if status != 0:
        raise HTTPException(status_code=400, detail=f"重置邮箱失败，状态码: {status}")

# 地图相关端点
@app.get("/maps", response_model=MapListResponse)
def get_map_list_route():
    return {"maps": get_map_list()}

@app.get("/maps/{mapid}", response_model=MapDetailResponse)
def get_map_details_route(mapid: str):
    details = get_map_details(mapid)
    if details["details"]:
        return details
    raise HTTPException(status_code=404, detail="地图不存在")


@app.post("/maps")
async def add_map_route(req: AddMapRequest):
    file_path = None
    try:
        # 解码 Base64 图片内容
        file_content = base64.b64decode(req.file)
        file_ext = ".png"  # 假设文件为 PNG 格式。如果可能有多种格式，需从 Base64 数据中解析文件类型。

        # 生成唯一文件名防止冲突
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)

        # 保存文件到本地
        with open(file_path, "wb") as buffer:
            buffer.write(file_content)

        # 调用原有函数处理本地文件
        status, mapid = add_map(file_path, req.map_name)

        # 返回成功结果
        if status == 0:
            return {"mapid": mapid}
        else:
            raise HTTPException(status_code=500, detail=f"地图处理失败，状态码: {status}")

    except Exception as e:
        # 错误处理（如删除临时文件）
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")

# 用户视图相关端点
@app.get("/user/{uid}/changes/selfall", response_model=ChangeResponse)
def get_change_details_route(uid: str):
    status, details = get_change_details(uid)
    if status == 0:
        return details
    raise HTTPException(status_code=500, detail=f"服务器错误: 错误码{status}")

@app.get("/user/{uid}/changes/selfcurr", response_model=ChangeResponse)
def get_change_details_by_current_map_route(uid: str):
    status, details = get_change_details_by_current_map(uid)
    print(f"debug1{details}")
    if status == 0:
        return {"details": details}
    raise HTTPException(status_code=500, detail=f"服务器错误: 错误码{status}")

@app.get("/user/{uid}/changes/curr", response_model=ChangeResponse)
def get_current_map_full_change_details_route(uid: str):
    status, details = get_current_map_full_change_details(uid)
    print(f"debug1{details}")
    if status == 0:
        return {"details": details}
    raise HTTPException(status_code=500, detail=f"服务器错误: 错误码{status}")

@app.put("/user/{uid}/current_map/{mapid}")
def set_current_map_route(uid: str, mapid: str):
    set_current_map(uid, mapid)

@app.post("/user/{uid}/search")
def user_search_route(uid: str, req: SearchRequest):
    status = user_search(uid, req.query_name, req.query_type, req.query_media, req.query_desc, req.top_n)
    if status != 0:
        raise HTTPException(status_code=400, detail=f"搜索失败，状态码: {status}")

@app.post("/user/{uid}/next")
def user_next_route(uid: str):
    map_id = user_next(uid)
    if map_id:
        return {"map_id": map_id}
    raise HTTPException(status_code=400, detail="无法切换到下一个地图")

@app.post("/user/{uid}/before")
def user_before_route(uid: str):
    map_id = user_before(uid)
    if map_id:
        return {"map_id": map_id}
    raise HTTPException(status_code=400, detail="无法切换到上一个地图")

@app.get("/user/{uid}/current_map/details", response_model=MapDetailResponse)
def get_current_map_details_route(uid: str):
    details = get_current_map_details(uid)
    if details.get("mapid"):
        return details
    raise HTTPException(status_code=404, detail="当前地图不存在")

@app.get("/user/{uid}/current_map/notes", response_model=List[NoteResponse])
def get_current_map_notes_route(uid: str):
    notes = get_current_map_notes(uid)
    return notes

@app.post("/user/{uid}/current_map/notes")
def write_note_route(uid: str, req: WriteNoteRequest):
    status = write_note(uid, req.note)
    if status == 0:
        return {"status": status}
    raise HTTPException(status_code=400, detail=f"写入评论失败，状态码: {status}")

@app.put("/user/{uid}/maps/{mapid}")
def user_change_map_route(uid: str, mapid: str, req: ChangeMapRequest):
    print(req.arcs)
    status = user_change_map(uid, mapid, req.arcs)
    if status != 0:
        raise HTTPException(status_code=400, detail=f"修改地图失败，状态码: {status}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)