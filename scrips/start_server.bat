@echo off
set PYTHONPATH=%~dp0..\System

call %~dp0..\System\venv\Scripts\activate.bat

REM echo Installing dependencies...
REM pip install -r %~dp0..\System\requirements.txt

echo 正在初始化数据库...
python %~dp0..\System\file_system\db.py
IF %ERRORLEVEL% NEQ 0 (
    echo 初始化数据库脚本出现错误！
    pause
    exit /b 1
)

echo 正在启动 FastAPI 服务器...
python %~dp0..\System\api\fastapi\main.py
IF %ERRORLEVEL% NEQ 0 (
    echo 启动 FastAPI 服务器出现错误！
    pause
    exit /b 1
)

pause