@echo off
chcp 65001
title MapCollector Frontend Development Server

echo ============================================
echo    MapCollector Frontend Development Server
echo ============================================
echo.

:: 切换到前端项目目录
cd ..\front\app

:: 检查是否在前端项目目录
if not exist "package.json" (
    echo [错误] 未找到前端项目目录
    echo 请确保项目结构正确: MapCollector/front/app/package.json
    echo 当前目录: %CD%
    pause
    exit
)

:: 检查 node_modules
if not exist "node_modules" (
    echo [信息] 首次运行，正在安装依赖...
    npm install
    if errorlevel 1 (
        echo [错误] 依赖安装失败
        pause
        exit
    )
)

:: 启动开发服务器
echo [信息] 正在启动开发服务器...
echo [提示] 按 Ctrl+C 停止服务器
echo.

npm run dev

if errorlevel 1 (
    echo [错误] 开发服务器异常退出
    pause
    exit
) 