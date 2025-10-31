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

class ConfigRequest(BaseModel):
    """AI 服務配置請求"""
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    default_model: Optional[str] = None
    endpoint_type: Optional[str] = None  # "standard" 或 "response"

# ==================== 配置管理端點 ====================

@router.get("/config")
async def get_ai_config():
    """獲取當前 AI 服務配置"""
    try:
        return {
            "base_url": amd_config.openai_base_url,
            "api_key_set": bool(amd_config.openai_api_key),
            "api_key_masked": f"{amd_config.openai_api_key[:4]}****" if amd_config.openai_api_key else None,
            "current_model": lemonade_client.current_model,
            "model_loaded": lemonade_client.is_model_loaded,
            "platform": "AMD Ryzen AI" if amd_config.is_amd_platform else "Generic"
        }
    except Exception as e:
        logger.error(f"獲取配置失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取配置失敗: {str(e)}")

@router.post("/config")
async def update_ai_config(config: ConfigRequest):
    """
    更新 AI 服務配置
    
    可以更新:
    - base_url: API 基礎 URL (例如: http://localhost:8000/api)
      - 如果 api_key 以 "sk-" 開頭（OpenAI key），會自動使用 https://api.openai.com/v1
      - GPT-5 模型會自動使用 https://api.openai.com/v1/response
    - api_key: API 密鑰
    - default_model: 預設使用的模型
    - endpoint_type: 端點類型 ("standard" 或 "response")
    """
    try:
        updated_fields = []
        need_reinit_client = False
        
        # 檢測是否為 OpenAI API key（以 "sk-" 開頭）
        is_openai_key = config.api_key and config.api_key.startswith("sk-")
        
        # 檢測是否為 GPT-5 模型
        is_gpt5_model = config.default_model and ("gpt-5" in config.default_model.lower() or "gpt5" in config.default_model.lower())
        
        # 更新 api_key
        if config.api_key is not None:
            amd_config.openai_api_key = config.api_key
            amd_config.lemonade_api_key = config.api_key
            updated_fields.append("api_key")
            need_reinit_client = True
            logger.info("更新 api_key: ****")
        
        # 更新 base_url（根據模型類型自動選擇）
        if config.base_url is not None:
            amd_config.openai_base_url = config.base_url
            amd_config.lemonade_base_url = config.base_url
            updated_fields.append("base_url")
            need_reinit_client = True
            logger.info(f"更新 base_url: {config.base_url}")
        elif is_openai_key:
            amd_config.openai_base_url = "https://api.openai.com/v1"
            amd_config.lemonade_base_url = "https://api.openai.com/v1"
            updated_fields.append("base_url (auto-standard)")
            logger.info("檢測到 OpenAI API key，自動設定 base_url: https://api.openai.com/v1")
            need_reinit_client = True
        
        # 如果更新了 base_url 或 api_key，先重新初始化客戶端
        if need_reinit_client:
            await lemonade_client.close()
            lemonade_client._client = None  # 強制重新創建客戶端
            lemonade_client.is_model_loaded = False
            lemonade_client.current_model = None
            logger.info("客戶端已重新初始化")
        
        # 更新 default_model（在重新初始化客戶端之後）
        if config.default_model is not None:
            # 載入新模型
            success = await lemonade_client.load_model(config.default_model)
            if success:
                updated_fields.append("default_model")
                logger.info(f"更新並載入模型: {config.default_model}")
            else:
                raise HTTPException(
                    status_code=400, 
                    detail=f"無法載入模型 {config.default_model}"
                )
        
        return {
            "status": "success",
            "message": f"已更新配置: {', '.join(updated_fields)}",
            "updated_fields": updated_fields,
            "current_config": {
                "base_url": amd_config.openai_base_url,
                "api_key_set": bool(amd_config.openai_api_key),
                "current_model": lemonade_client.current_model,
                "model_loaded": lemonade_client.is_model_loaded
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新配置失敗: {e}")
        raise HTTPException(status_code=500, detail=f"更新配置失敗: {str(e)}")

@router.post("/config/reset")
async def reset_ai_config():
    """重置 AI 服務配置到預設值"""
    try:
        # 重置到環境變數或預設值
        import os
        amd_config.openai_base_url = os.getenv("OPENAI_BASE_URL", "http://localhost:8000/api")
        amd_config.openai_api_key = os.getenv("OPENAI_API_KEY", "lemonade")
        amd_config.lemonade_base_url = amd_config.openai_base_url
        amd_config.lemonade_api_key = amd_config.openai_api_key
        
        # 關閉並重置客戶端
        await lemonade_client.close()
        lemonade_client._client = None
        lemonade_client.is_model_loaded = False
        lemonade_client.current_model = None
        
        logger.info("配置已重置到預設值")
        
        return {
            "status": "success",
            "message": "配置已重置到預設值",
            "current_config": {
                "base_url": amd_config.openai_base_url,
                "api_key_set": bool(amd_config.openai_api_key)
            }
        }
        
    except Exception as e:
        logger.error(f"重置配置失敗: {e}")
        raise HTTPException(status_code=500, detail=f"重置配置失敗: {str(e)}")

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

# @router.post("/generate_topics")
# async def generate_topics_ai(req: TopicGenerationRequest):
#     """根據討論室內容生成主題建議"""
#     try:
#         if req.room not in ROOMS:
#             return {"topics": [], "message": "找不到指定的討論室"}

#         # 建立主題生成 prompt
#         prompt = prompt_builder.build_topic_generation_prompt(req.room)

#         # 確保模型已載入
#         if not lemonade_client.is_model_loaded:
#             default_model = amd_config.get_model_config()["recommended_models"][0]["name"]
#             success = await lemonade_client.load_model(default_model)
#             if not success:
#                 raise HTTPException(status_code=500, detail="模型載入失敗")

#         # 生成主題
#         raw_text = await lemonade_client.generate(
#             prompt=prompt,
#             max_tokens=1024,
#             temperature=0.8
#         )

#         # 解析主題
#         suggested_topics = topic_parser.parse_topics(raw_text)

#         return {
#             "topics": suggested_topics,
#             "raw_response": raw_text
#         }

#     except Exception as e:
#         logger.error(f"主題生成失敗: {e}")
#         raise HTTPException(status_code=500, detail=f"主題生成失敗: {str(e)}")

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

        print(raw_text)
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
        room_code = req.room.strip()
        logger.info(f"收到單一主題生成請求，房間代碼: {room_code}")
        logger.debug(f"當前 ROOMS 內容: {list(ROOMS.keys())}")
        
        # 檢查討論室是否存在
        if room_code not in ROOMS:
            logger.error(f"找不到房間 {room_code}，現有房間: {list(ROOMS.keys())}")
            return {"topic": f"錯誤：找不到指定的討論室 '{room_code}'。"
        }
        
        # 建立 prompt
        prompt = prompt_builder.build_single_topic_generation_prompt(room_code, req.custom_prompt)
        
        if prompt.startswith("錯誤"):
            return {"topic": prompt}

        # 確保模型已載入
        if not lemonade_client.is_model_loaded:
            default_model = amd_config.get_model_config()["recommended_models"][0]["name"]
            logger.info(f"載入預設模型: {default_model}")
            success = await lemonade_client.load_model(default_model)
            if not success:
                raise HTTPException(status_code=500, detail="模型載入失敗")

        # 生成主題
        logger.info(f"開始生成主題，prompt 長度: {len(prompt)}")
        topic = await lemonade_client.generate(
            prompt=prompt,
            max_tokens=512,
            temperature=0.8
        )

        logger.info(f"主題生成完成: {topic[:50]}...")
        return {"topic": topic.strip()}

    except Exception as e:
        logger.error(f"單一主題生成失敗: {e}", exc_info=True)
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
