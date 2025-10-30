"""
AI API 路由
使用 AMD Ryzen AI 的 Lemonade Server 進行推理
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import json
from typing import List, Optional
from .data_store import ROOMS, topics, votes
from utility.lemonade_client import lemonade_client
from utility.amd_config import amd_config
from utility.prompts import prompt_builder, topic_parser
from utility.logger import get_logger

logger = get_logger("mbbuddy.ai")
router = APIRouter(prefix="/ai", tags=["AI"])

# ==================== 請求模型 ====================

class AskRequest(BaseModel):
    prompt: str

class SummaryRequest(BaseModel):
    room: str
    topic: str

class TopicGenerationRequest(BaseModel):
    room: str

class QuestionsRequest(BaseModel):
    room_code: str
    topic: str
    questions: List[str]

class GenerateTopicsRequest(BaseModel):
    """用於 AI 生成主題請求的模型"""
    meeting_title: str
    topic_count: int
    room_code: Optional[str] = None

class GenerateSingleTopicRequest(BaseModel):
    room: str
    custom_prompt: str

# ==================== 健康檢查端點 ====================

@router.get("/health")
async def check_ai_health():
    """檢查 AI 服務健康狀態"""
    try:
        health = await lemonade_client.check_health()
        models = await lemonade_client.list_models()
        
        return {
            "status": "healthy" if health else "unhealthy",
            "backend": "AMD Lemonade Server",
            "platform": "AMD Ryzen AI" if amd_config.is_amd_platform else "Generic",
            "model_loaded": lemonade_client.is_model_loaded,
            "current_model": lemonade_client.current_model,
            "available_models": len(models),
            "lemonade_url": amd_config.lemonade_base_url
        }
    except Exception as e:
        logger.error(f"健康檢查失敗: {e}")
        return {
            "status": "error",
            "backend": "AMD Lemonade Server",
            "error": str(e)
        }

@router.get("/test_connection")
async def test_lemonade_connection():
    """測試 Lemonade Server 連接"""
    try:
        health = await lemonade_client.check_health()
        if health:
            models = await lemonade_client.list_models()
            return {
                "status": "success",
                "message": "Lemonade Server 連接正常",
                "available_models": len(models),
                "models": [m.get("id", "unknown") for m in models[:5]]
            }
        else:
            return {
                "status": "error",
                "message": "Lemonade Server 健康檢查失敗"
            }
    except Exception as e:
        logger.error(f"連接測試失敗: {e}")
        raise HTTPException(status_code=500, detail=f"連接測試失敗: {str(e)}")

# ==================== AI 推理端點 ====================

@router.post("/ask")
async def ask_ai(req: AskRequest):
    """AI 問答"""
    try:
        # 確保模型已載入
        if not lemonade_client.is_model_loaded:
            default_model = amd_config.get_model_config()["recommended_models"][0]["name"]
            logger.info(f"載入預設模型: {default_model}")
            success = await lemonade_client.load_model(default_model)
            if not success:
                raise HTTPException(status_code=500, detail="模型載入失敗")
        
        # 生成回答
        answer = await lemonade_client.generate(
            prompt=req.prompt,
            max_tokens=1024,
            temperature=0.7
        )
        
        return {"answer": answer}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AI 處理失敗: {e}")
        raise HTTPException(status_code=500, detail=f"AI 處理失敗: {str(e)}")

@router.post("/summary")
async def summary_ai(req: SummaryRequest):
    """對指定討論室的特定主題進行 AI 總結"""
    try:
        # 檢查討論室是否存在
        if req.room not in ROOMS:
            return {"summary": "錯誤：找不到指定的討論室。"}

        # 檢查主題是否存在
        topic_id = f"{req.room}_{req.topic}"
        if topic_id not in topics:
            return {"summary": "錯誤：在該討論室中找不到指定的主題。"}

        # 建立總結 prompt
        prompt = prompt_builder.build_summary_prompt(req.room, req.topic)
        if prompt.startswith("錯誤"):
            return {"summary": prompt}

        # 確保模型已載入
        if not lemonade_client.is_model_loaded:
            default_model = amd_config.get_model_config()["recommended_models"][0]["name"]
            success = await lemonade_client.load_model(default_model)
            if not success:
                raise HTTPException(status_code=500, detail="模型載入失敗")

        # 生成總結
        summary_text = await lemonade_client.generate(
            prompt=prompt,
            max_tokens=2048,
            temperature=0.7
        )

        return {"summary": summary_text}
        
    except Exception as e:
        logger.error(f"總結生成失敗: {e}")
        raise HTTPException(status_code=500, detail=f"總結生成失敗: {str(e)}")

@router.post("/generate_topics")
async def generate_topics_ai(req: TopicGenerationRequest):
    """根據討論室內容生成主題建議"""
    try:
        if req.room not in ROOMS:
            return {"topics": [], "message": "找不到指定的討論室"}

        # 建立主題生成 prompt
        prompt = prompt_builder.build_topic_generation_prompt(req.room)

        # 確保模型已載入
        if not lemonade_client.is_model_loaded:
            default_model = amd_config.get_model_config()["recommended_models"][0]["name"]
            success = await lemonade_client.load_model(default_model)
            if not success:
                raise HTTPException(status_code=500, detail="模型載入失敗")

        # 生成主題
        raw_text = await lemonade_client.generate(
            prompt=prompt,
            max_tokens=1024,
            temperature=0.8
        )

        # 解析主題
        suggested_topics = topic_parser.parse_topics(raw_text)

        return {
            "topics": suggested_topics,
            "raw_response": raw_text
        }

    except Exception as e:
        logger.error(f"主題生成失敗: {e}")
        raise HTTPException(status_code=500, detail=f"主題生成失敗: {str(e)}")

@router.post("/generate_ai_topics")
async def generate_ai_topics(req: GenerateTopicsRequest):
    """根據討論名稱和指定數量，使用 AI 生成議程主題"""
    try:
        # 基本驗證
        topic_count = max(1, min(10, req.topic_count))
        meeting_title = req.meeting_title.strip()

        if not meeting_title:
            return {"topics": ["錯誤：討論名稱不可為空。"]}

        # 建立 prompt
        prompt = prompt_builder.build_topics_generation_prompt(meeting_title, topic_count)
        
        if prompt.startswith("錯誤"):
            return {"topics": [prompt]}

        # 確保模型已載入
        if not lemonade_client.is_model_loaded:
            default_model = amd_config.get_model_config()["recommended_models"][0]["name"]
            success = await lemonade_client.load_model(default_model)
            if not success:
                raise HTTPException(status_code=500, detail="模型載入失敗")

        # 生成主題
        raw_text = await lemonade_client.generate(
            prompt=prompt,
            max_tokens=1024,
            temperature=0.8
        )

        # 解析主題
        generated_topics = topic_parser.parse_topics_from_response(raw_text, topic_count)
        return {"topics": generated_topics}

    except Exception as e:
        logger.error(f"AI 主題生成失敗: {e}")
        return {"topics": [f"AI 服務暫時無法連線，請稍後再試。"]}

@router.post("/generate_single_topic")
async def generate_single_topic(req: GenerateSingleTopicRequest):
    """根據討論室和自訂提示，使用 AI 生成單一議程主題"""
    try:
        # 檢查討論室是否存在
        if req.room not in ROOMS:
            return {"topic": "錯誤：找不到指定的討論室。"}

        # 建立 prompt
        prompt = prompt_builder.build_single_topic_generation_prompt(req.room, req.custom_prompt)
        
        if prompt.startswith("錯誤"):
            return {"topic": prompt}

        # 確保模型已載入
        if not lemonade_client.is_model_loaded:
            default_model = amd_config.get_model_config()["recommended_models"][0]["name"]
            success = await lemonade_client.load_model(default_model)
            if not success:
                raise HTTPException(status_code=500, detail="模型載入失敗")

        # 生成主題
        topic = await lemonade_client.generate(
            prompt=prompt,
            max_tokens=512,
            temperature=0.8
        )

        return {"topic": topic.strip()}

    except Exception as e:
        logger.error(f"單一主題生成失敗: {e}")
        return {"topic": f"AI 主題生成失敗: {str(e)}"}

@router.post("/generate_questions")
async def generate_questions_ai(req: QuestionsRequest):
    """為特定主題生成引導問題"""
    try:
        # 建立問題生成 prompt
        prompt = prompt_builder.build_question_generation_prompt(
            req.room_code,
            req.topic,
            req.questions
        )

        # 確保模型已載入
        if not lemonade_client.is_model_loaded:
            default_model = amd_config.get_model_config()["recommended_models"][0]["name"]
            success = await lemonade_client.load_model(default_model)
            if not success:
                raise HTTPException(status_code=500, detail="模型載入失敗")

        # 生成問題
        topic = await lemonade_client.generate(
            prompt=prompt,
            max_tokens=1024,
            temperature=0.8
        )

        return {"topic": topic}

    except Exception as e:
        logger.error(f"問題生成失敗: {e}")
        raise HTTPException(status_code=500, detail=f"問題生成失敗: {str(e)}")

# ==================== 統計和管理端點 ====================

@router.get("/stats")
async def get_ai_stats():
    """獲取 AI 服務統計信息"""
    try:
        return {
            "backend": "AMD Lemonade Server",
            "platform": "AMD Ryzen AI" if amd_config.is_amd_platform else "Generic",
            "status": "運行中" if lemonade_client.is_model_loaded else "待機中",
            "model_loaded": lemonade_client.is_model_loaded,
            "current_model": lemonade_client.current_model,
            "config": {
                "max_tokens": amd_config.get_inference_config().get("max_tokens"),
                "precision": amd_config.get_inference_config().get("precision"),
                "use_npu": amd_config.get_inference_config().get("use_npu"),
                "inference_mode": amd_config.get_inference_config().get("inference_mode")
            }
        }
    except Exception as e:
        logger.error(f"獲取統計失敗: {e}")
        return {
            "backend": "AMD Lemonade Server",
            "status": "錯誤",
            "error": str(e)
        }

@router.get("/models")
async def list_models():
    """列出所有可用的模型"""
    try:
        # 從 Lemonade Server 獲取
        server_models = await lemonade_client.list_models()
        
        # 從配置獲取推薦模型
        recommended = amd_config.get_model_config()["recommended_models"]
        
        return {
            "server_models": server_models,
            "recommended_models": recommended,
            "current_model": lemonade_client.current_model
        }
    except Exception as e:
        logger.error(f"列出模型失敗: {e}")
        raise HTTPException(status_code=500, detail=f"列出模型失敗: {str(e)}")

@router.post("/load_model")
async def load_model(model_name: str):
    """載入指定的模型"""
    try:
        success = await lemonade_client.load_model(model_name)
        if success:
            return {
                "status": "success",
                "message": f"模型 {model_name} 載入成功",
                "model": model_name
            }
        else:
            raise HTTPException(status_code=500, detail="模型載入失敗")
    except Exception as e:
        logger.error(f"載入模型失敗: {e}")
        raise HTTPException(status_code=500, detail=f"載入模型失敗: {str(e)}")

@router.post("/unload_model")
async def unload_model():
    """卸載當前模型"""
    try:
        success = await lemonade_client.unload_model()
        if success:
            return {
                "status": "success",
                "message": "模型已卸載"
            }
        else:
            raise HTTPException(status_code=500, detail="模型卸載失敗")
    except Exception as e:
        logger.error(f"卸載模型失敗: {e}")
        raise HTTPException(status_code=500, detail=f"卸載模型失敗: {str(e)}")
