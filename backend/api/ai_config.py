"""
AI 配置 API 路由
用於管理 AI 服務模式切換和配置
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Literal
from utility.call_ai import ai_service
from utility.logger import get_logger

logger = get_logger("mbbuddy.ai_config")
router = APIRouter(prefix="/ai/config", tags=["AI Config"])

# ==================== 請求模型 ====================

class SetModeRequest(BaseModel):
    """設定 AI 模式請求"""
    mode: Literal["lemonade", "openai"]
    api_key: Optional[str] = None
    model: Optional[str] = None

# ==================== API 端點 ====================

@router.get("")
async def get_ai_config():
    """取得當前 AI 配置"""
    try:
        config = ai_service.get_config()
        return {
            "status": "success",
            "config": config
        }
    except Exception as e:
        logger.error(f"取得配置失敗: {e}")
        raise HTTPException(status_code=500, detail=f"取得配置失敗: {str(e)}")

@router.post("/set_mode")
async def set_ai_mode(req: SetModeRequest):
    """
    設定 AI 服務模式
    
    - Lemonade 模式: 使用本地 AMD Ryzen AI
    - OpenAI 模式: 使用 OpenAI 雲端 API
    """
    try:
        # 驗證 OpenAI 模式必須提供 API Key
        if req.mode == "openai" and not req.api_key:
            current_key = ai_service.openai_api_key
            if not current_key:
                raise HTTPException(
                    status_code=400,
                    detail="OpenAI 模式需要提供 API Key"
                )
        
        # 設定模式
        ai_service.set_mode(
            mode=req.mode,
            api_key=req.api_key,
            model=req.model
        )
        
        config = ai_service.get_config()
        
        return {
            "status": "success",
            "message": f"已切換到 {req.mode} 模式",
            "config": config
        }
        
    except ValueError as e:
        logger.error(f"設定模式失敗: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"設定模式失敗: {e}")
        raise HTTPException(status_code=500, detail=f"設定模式失敗: {str(e)}")

@router.post("/test")
async def test_ai_service():
    """測試當前 AI 服務是否正常運作"""
    try:
        test_prompt = "請用一句話回答：你是什麼？"
        
        response = await ai_service.generate_async(
            prompt=test_prompt,
            max_tokens=100
        )
        
        config = ai_service.get_config()
        
        return {
            "status": "success",
            "mode": config["mode"],
            "model": config["model"],
            "response": response
        }
        
    except Exception as e:
        logger.error(f"測試失敗: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"AI 服務測試失敗: {str(e)}"
        )
