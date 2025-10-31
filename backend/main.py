# backend/main.py
from fastapi import FastAPI
from api import ai
from api import ai_config
from fastapi.middleware.cors import CORSMiddleware
from api import participants
from api import network
from api import mindmap
import asyncio
from api import host_style
from contextlib import asynccontextmanager

# 設置美化的日誌系統
from utility.logger import setup_logger
logger = setup_logger("mbbuddy")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """應用生命週期管理 - 啟動和關閉事件"""
    # ==================== 啟動事件 ====================
    logger.info("🚀 MBBuddy 後端服務啟動中...")
    
    # 檢測並初始化 AMD Ryzen AI 平台
    try:
        from utility.amd_config import amd_config
        logger.info(amd_config.get_platform_info_summary())
        
        # 驗證環境
        validation = amd_config.validate_environment()
        logger.info(f"環境驗證: {validation}")
        
        if not all(validation.values()):
            logger.warning("⚠️ 部分環境驗證未通過，某些功能可能無法使用")
    except Exception as e:
        logger.error(f"❌ AMD 平台初始化失敗: {e}")
    
    # 測試 Lemonade Server 連接
    try:
        from utility.lemonade_client import lemonade_client
        logger.info("🔗 測試 Lemonade Server 連接...")
        
        health_ok = await lemonade_client.check_health()
        if health_ok:
            logger.info("✅ Lemonade Server 連接正常")
            
            # 列出可用模型
            models = await lemonade_client.list_models()
            if models:
                logger.info(f"📋 找到 {len(models)} 個可用模型:")
                for model in models[:5]:  # 只顯示前5個
                    logger.info(f"  - {model.get('id', 'unknown')}")
            
            # 嘗試載入默認模型
            try:
                default_model = "Qwen-2.5-3B-Instruct-NPU"
                logger.info(f"📥 嘗試載入默認模型: {default_model}")
                success = await lemonade_client.load_model(default_model)
                if success:
                    logger.info(f"✅ 默認模型 {default_model} 已載入")
                else:
                    logger.warning(f"⚠️ 默認模型 {default_model} 載入失敗，將在首次調用時載入")
            except Exception as e:
                logger.warning(f"⚠️ 載入默認模型失敗: {e}")
        else:
            logger.warning("⚠️ Lemonade Server 連接測試失敗")
            logger.warning("⚠️ 請確保 Lemonade Server 正在運行")
            logger.info("💡 啟動 Lemonade Server: 請參考 https://lemonade-server.ai/docs/")
            
    except Exception as e:
        logger.error(f"❌ Lemonade Server 連接測試時發生錯誤: {e}")
        logger.info("💡 如果您尚未安裝 Lemonade Server，請參考 AMD 文檔")
    
    logger.info("🎉 MBBuddy 後端服務啟動完成！")
    
    # yield 之前是啟動邏輯，之後是關閉邏輯
    yield
    
    # ==================== 關閉事件 ====================
    logger.info("🛑 MBBuddy 後端服務正在關閉...")
    
    # 清理 Lemonade Client
    try:
        from utility.lemonade_client import lemonade_client
        if lemonade_client.is_model_loaded:
            await lemonade_client.unload_model()
            logger.info("✅ Lemonade 模型已卸載")
        await lemonade_client.close()
        logger.info("✅ Lemonade Client 已關閉")
    except Exception as e:
        logger.error(f"❌ 關閉 Lemonade Client 時發生錯誤: {e}")
    
    logger.info("👋 MBBuddy 後端服務已關閉")

# 創建 FastAPI 應用，使用 lifespan
app = FastAPI(title="MBBuddy API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(participants.router)
app.include_router(ai.router)
app.include_router(ai_config.router)
app.include_router(network.router)
app.include_router(mindmap.router)
app.include_router(host_style.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
    # uvicorn main:app --port 8001 --reload
