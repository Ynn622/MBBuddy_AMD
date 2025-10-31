# MBBuddy - AMD Ryzen AI 版本

## 概述

MBBuddy 已升級為使用 **AMD Ryzen AI** 技術，透過 **Lemonade Server** 提供高效能的 AI 推理服務。

### 技術架構

- **平台**: AMD Ryzen AI PC (CPU + GPU + NPU)
- **AI 引擎**: Lemonade Server
- **模型格式**: ONNX INT4 量化模型
- **推理加速**: 混合推理 (CPU + GPU + NPU)

## 功能特色

### 🚀 AMD Ryzen AI 優化
- 使用 AMD 的 CPU、GPU 和 NPU 進行混合推理
- 支援 INT4 量化模型，大幅提升推理速度
- 優化的記憶體使用和功耗管理

### 🤖 AI 模型支援
- **Llama 3.2 1B/3B** (INT4) - AMD 優化版本
- **Phi-3.5 Mini** (INT4) - Microsoft 輕量級模型
- **Qwen 2.5 1.5B** (INT4) - 阿里巴巴開源模型

### 📊 智慧會議功能
- AI 自動總結討論內容
- 智能生成討論主題
- 引導式問題生成
- 即時問答系統

## 系統需求

### 硬體需求
- **處理器**: AMD Ryzen AI 系列 (推薦)
- **記憶體**: 最少 8GB RAM (推薦 16GB+)
- **儲存空間**: 最少 10GB 可用空間

### 軟體需求
- **作業系統**: Windows 11 / Linux
- **Python**: 3.8 或更高版本
- **Lemonade Server**: 需要另外安裝

## 安裝指南

### 1. 安裝 Lemonade Server

請參考 AMD 官方文檔安裝 Lemonade Server：

```bash
# Lemonade Server 安裝
# 詳情請見: https://lemonade-server.ai/docs/
```

### 2. 下載 AMD 優化模型

使用內建的模型下載工具：

```bash
cd backend/api

# 列出可用模型
python amd_model_downloader.py list

# 下載推薦模型
python amd_model_downloader.py download-all

# 或下載單一模型
python amd_model_downloader.py download Llama-3.2-1B-Instruct-int4
```

### 3. 安裝 Python 依賴

```bash
cd backend
pip install -r requirements.txt
```

### 4. 配置環境變量

複製環境變量範例文件：

```bash
cp .env.example .env
```

編輯 `.env` 文件：

```env
# 標記為 AMD 平台
AMD_RYZEN_AI=true

# Lemonade Server URL
LEMONADE_SERVER_URL=http://localhost:8080

# Lemonade API Key（如果需要）
LEMONADE_API_KEY=your_api_key_here
```

### 5. 啟動後端服務

```bash
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

### 6. 啟動前端服務

```bash
cd frontend
npm install
npm run dev
```

## API 端點

### AI 服務

#### 健康檢查
```http
GET /ai/health
```

#### 測試連接
```http
GET /ai/test_connection
```

#### AI 問答
```http
POST /ai/ask
Content-Type: application/json

{
  "prompt": "你的問題"
}
```

#### 生成總結
```http
POST /ai/summary
Content-Type: application/json

{
  "room": "討論室代碼",
  "topic": "主題名稱"
}
```

#### 生成主題
```http
POST /ai/generate_ai_topics
Content-Type: application/json

{
  "room": "討論室代碼"
}
```

#### 列出模型
```http
GET /ai/models
```

#### 載入模型
```http
POST /ai/load_model?model_name=Llama-3.2-1B-Instruct-int4
```

#### 統計信息
```http
GET /ai/stats
```

## 推薦模型

### Llama 3.2 1B Instruct (INT4)
- **大小**: 1.2GB
- **性能**: 優秀
- **適用**: 一般對話、總結、問答
- **推薦**: ✅

### Llama 3.2 3B Instruct (INT4)
- **大小**: 2.8GB
- **性能**: 優秀
- **適用**: 複雜推理、長文本處理
- **推薦**: ✅

### Phi-3.5 Mini Instruct (INT4)
- **大小**: 2.5GB
- **性能**: 很好
- **適用**: 輕量級任務、快速回應
- **推薦**: ✅

## 性能優化

### AMD Ryzen AI 配置

系統會自動檢測 AMD 平台並啟用以下優化：

- **混合推理**: CPU + GPU + NPU
- **INT4 量化**: 減少記憶體使用，提升速度
- **動態批次處理**: 提高吞吐量
- **KV 緩存**: 加速生成速度
- **張量並行**: 利用多核心優勢

### 配置調整

在 `backend/api/amd_config.py` 中可以調整：

- 批次大小
- 最大 tokens 數
- 溫度參數
- NPU 優先級
- 記憶體優化級別

## 故障排除

### Lemonade Server 無法連接

1. 確認 Lemonade Server 正在運行
2. 檢查 `.env` 中的 `LEMONADE_SERVER_URL`
3. 測試連接: `curl http://localhost:8080/health`

### 模型載入失敗

1. 確認模型已下載到 `ai_models` 目錄
2. 檢查模型文件完整性
3. 查看日誌了解詳細錯誤訊息

### 推理速度慢

1. 確認已啟用 AMD Ryzen AI (`AMD_RYZEN_AI=true`)
2. 使用較小的模型 (1B 而非 3B)
3. 調整批次大小和 max_tokens

## 開發指南

### 項目結構

```
backend/
├── api/
│   ├── amd_config.py           # AMD 平台配置
│   ├── lemonade_client.py      # Lemonade Server 客戶端
│   ├── amd_model_downloader.py # 模型下載工具
│   ├── ai_api.py               # AI API 路由
│   └── ai_prompts.py           # Prompt 模板
├── main.py                     # FastAPI 主程式
└── requirements.txt            # Python 依賴
```

### 添加新模型

1. 在 `amd_config.py` 的 `get_model_config()` 中添加模型信息
2. 使用下載工具下載模型
3. 在 Lemonade Server 中配置模型

### 自定義 Prompt

編輯 `ai_prompts.py` 來自定義不同場景的 prompt 模板。

## 相關資源

- [AMD Ryzen AI](https://www.amd.com/en/products/ryzen-ai)
- [Lemonade SDK](https://github.com/lemonade-sdk/lemonade)
- [Lemonade Server](https://lemonade-server.ai/docs/)
- [AMD RyzenAI-SW](https://github.com/amd/RyzenAI-SW)

## 授權

MIT License

## 貢獻

歡迎提交 Issue 和 Pull Request！

---

**Made with ❤️ using AMD Ryzen AI**
