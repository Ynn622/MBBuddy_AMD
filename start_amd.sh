#!/bin/bash

# MBBuddy AMD Ryzen AI 快速啟動腳本

echo "========================================"
echo "   MBBuddy - AMD Ryzen AI 版本"
echo "========================================"
echo ""

# 檢查是否在正確的目錄
if [ ! -f "backend/main.py" ]; then
    echo "❌ 錯誤: 請在項目根目錄執行此腳本"
    exit 1
fi

# 檢查 Python
echo "🔍 檢查 Python..."
if ! command -v python3 &> /dev/null; then
    echo "❌ 未找到 Python3，請先安裝 Python 3.8+"
    exit 1
fi
echo "✅ Python: $(python3 --version)"

# 檢查 Node.js
echo "🔍 檢查 Node.js..."
if ! command -v node &> /dev/null; then
    echo "❌ 未找到 Node.js，請先安裝 Node.js"
    exit 1
fi
echo "✅ Node.js: $(node --version)"

# 檢查環境變量文件
echo ""
echo "🔍 檢查環境配置..."
if [ ! -f "backend/.env" ]; then
    echo "⚠️  未找到 .env 文件，複製範例文件..."
    cp backend/.env.example backend/.env
    echo "✅ 已創建 .env 文件，請編輯 backend/.env 配置 Lemonade Server URL"
fi

# 安裝後端依賴
echo ""
echo "📦 安裝後端依賴..."
cd backend
if [ ! -d "venv" ]; then
    echo "創建虛擬環境..."
    python3 -m venv venv
fi

source venv/bin/activate
pip install -r requirements.txt

# 檢查 Lemonade Server
echo ""
echo "🔗 測試 Lemonade Server 連接..."
LEMONADE_URL=$(grep LEMONADE_SERVER_URL .env | cut -d '=' -f2)
if [ -z "$LEMONADE_URL" ]; then
    LEMONADE_URL="http://localhost:8080"
fi

if curl -s "$LEMONADE_URL/health" > /dev/null 2>&1; then
    echo "✅ Lemonade Server 連接正常: $LEMONADE_URL"
else
    echo "⚠️  無法連接到 Lemonade Server: $LEMONADE_URL"
    echo "   請確保 Lemonade Server 正在運行"
    echo "   參考: https://lemonade-server.ai/docs/"
fi

# 檢查模型
echo ""
echo "🔍 檢查 AI 模型..."
if [ -d "ai_models" ] && [ "$(ls -A ai_models)" ]; then
    echo "✅ 找到已下載的模型:"
    ls -1 ai_models/
else
    echo "⚠️  未找到模型文件"
    echo "   執行以下命令下載推薦模型:"
    echo "   cd backend/api && python amd_model_downloader.py download-all"
fi

cd ..

# 安裝前端依賴
echo ""
echo "📦 安裝前端依賴..."
cd frontend
if [ ! -d "node_modules" ]; then
    npm install
fi
cd ..

# 啟動服務
echo ""
echo "========================================"
echo "   🚀 啟動服務"
echo "========================================"
echo ""

# 啟動後端
echo "啟動後端服務..."
cd backend
source venv/bin/activate
python -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload &
BACKEND_PID=$!
cd ..

# 等待後端啟動
echo "等待後端服務啟動..."
sleep 3

# 啟動前端
echo "啟動前端服務..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "========================================"
echo "   ✅ 服務已啟動"
echo "========================================"
echo ""
echo "後端服務: http://localhost:8001"
echo "前端服務: http://localhost:5173"
echo "API 文檔: http://localhost:8001/docs"
echo ""
echo "按 Ctrl+C 停止所有服務"
echo ""

# 等待用戶中斷
trap "echo ''; echo '🛑 正在停止服務...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" INT

wait
