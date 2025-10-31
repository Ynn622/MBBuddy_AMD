@echo off
chcp 65001 >nul
echo ====================================
echo   停止所有 MBBuddy 服務
echo ====================================
echo.

echo 正在停止 Node.js (Frontend)...
taskkill /F /IM node.exe /T 2>nul
if %errorlevel% equ 0 (
    echo   ✓ Frontend 已停止
) else (
    echo   ℹ Frontend 未運行
)

echo.
echo 正在停止 Python (Backend)...
for /f "tokens=2" %%a in ('tasklist ^| findstr "python.exe"') do (
    taskkill /F /PID %%a 2>nul
)
if %errorlevel% equ 0 (
    echo   ✓ Backend 已停止
) else (
    echo   ℹ Backend 未運行
)

echo.
echo 正在停止 Lemonade Server...
taskkill /F /FI "WINDOWTITLE eq Lemonade Server*" 2>nul
if %errorlevel% equ 0 (
    echo   ✓ Lemonade Server 已停止
) else (
    echo   ℹ Lemonade Server 未運行
)

echo.
echo ====================================
echo   所有服務已停止
echo ====================================
echo.
pause
