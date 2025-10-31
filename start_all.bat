@echo off
chcp 65001 >nul
title MBBuddy AMD - 啟動中...
color 0A

:: 獲取當前目錄
set ROOT_DIR=%~dp0
cd /d "%ROOT_DIR%"

cls
echo.
echo  ╔════════════════════════════════════════════╗
echo  ║        MBBuddy AMD 一鍵啟動                ║
echo  ╚════════════════════════════════════════════╝
echo.

echo  [1/4] 啟動 Lemonade Server...
start /min "Lemonade Server" cmd /c "conda activate ryzen-ai-1.6.0 && lemonade-server serve"
timeout /t 3 /nobreak >nul
echo  ✓ Lemonade Server 已啟動 (最小化視窗)
echo.

echo  [2/4] 啟動 Backend Server...
start /min "Backend Server" cmd /c "conda activate ryzenai312 && cd backend && python main.py"
timeout /t 3 /nobreak >nul
echo  ✓ Backend Server 已啟動 (最小化視窗)
echo.

echo  [3/4] 啟動 Frontend Dev Server...
start /min "Frontend Dev Server" cmd /c "cd frontend && npm run dev -- --host"
timeout /t 5 /nobreak >nul
echo  ✓ Frontend Server 已啟動 (最小化視窗)
echo.

echo  [4/4] 開啟網站...
:: 獲取本機 IPv4 位址
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /C:"IPv4"') do (
    set IP=%%a
    goto :found_ip
)
:found_ip
:: 移除空格
set IP=%IP: =%

:: 開啟瀏覽器
start http://%IP%:5173
timeout /t 1 /nobreak >nul
echo  ✓ 瀏覽器已開啟
echo.

echo  ════════════════════════════════════════════
echo   所有服務已在背景啟動!
echo  ════════════════════════════════════════════
echo.
echo   📡 Lemonade Server: http://localhost:8000
echo   🔧 Backend API:     http://localhost:8001
echo   🌐 Frontend:        http://localhost:5173
echo   🌍 網路訪問:         http://%IP%:5173
echo.
echo   � 三個服務視窗已最小化到工作列
echo.
echo  ════════════════════════════════════════════
echo   按任意鍵停止所有服務並退出
echo  ════════════════════════════════════════════
echo.

:: 等待用戶按鍵
pause

:: 停止所有服務
cls
echo.
echo  正在停止所有服務...
echo.

echo  停止 Frontend Server...
taskkill /F /FI "WINDOWTITLE eq Frontend Dev Server*" >nul 2>&1

echo  停止 Backend Server...
taskkill /F /FI "WINDOWTITLE eq Backend Server*" >nul 2>&1

echo  停止 Lemonade Server...
taskkill /F /FI "WINDOWTITLE eq Lemonade Server*" >nul 2>&1

:: 額外確保相關進程都已停止
taskkill /F /IM node.exe >nul 2>&1
for /f "tokens=2" %%a in ('tasklist ^| findstr "python.exe"') do (
    taskkill /F /PID %%a >nul 2>&1
)

echo.
echo  ✓ 所有服務已停止
timeout /t 2 /nobreak >nul
