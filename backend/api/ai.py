"""
AI API 路由
使用 AMD Ryzen AI 的 Lemonade Server 進行推理
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import json
from typing import List, Optional
from .data_store import ROOMS, topics, votes
from utility.smart_ai_client import (
    get_smart_client, 
    get_available_models, 
    set_openai_model, 
    get_completion_params,
    OPENAI_MODELS, 
    DEFAULT_OPENAI_MODEL, 
    DEFAULT_LEMONADE_MODEL
)
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
        import os
        api_key = os.getenv("OPENAI_API_KEY", "lemonade")
        is_openai = api_key.startswith("sk-")
        
        # 取得當前模型設定
        current_model = os.getenv("OPENAI_MODEL", DEFAULT_OPENAI_MODEL) if is_openai else DEFAULT_LEMONADE_MODEL
        
        # 取得可用模型
        available = get_available_models()
        
        return {
            "mode": "OpenAI" if is_openai else "Lemonade",
            "api_key_set": bool(api_key),
            "api_key_masked": f"{api_key[:4]}****" if api_key else None,
            "current_model": current_model,
            "available_models": available.get("models") if is_openai else None,
            "platform": "AMD Ryzen AI" if amd_config.is_amd_platform else "Generic"
        }
    except Exception as e:
        logger.error(f"獲取配置失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取配置失敗: {str(e)}")

@router.post("/config")
async def update_ai_config(config: ConfigRequest):
    """
    更新 AI 服務配置
    - api_key: 設定 OpenAI API Key (以 sk- 開頭會自動切換到 OpenAI 模式)
    - default_model: 設定要使用的模型 (OpenAI 模式下可選擇不同模型)
    """
    try:
        import os
        updated_fields = []
        
        # 更新 api_key
        if config.api_key is not None:
            os.environ["OPENAI_API_KEY"] = config.api_key
            amd_config.openai_api_key = config.api_key
            updated_fields.append("api_key")
            logger.info("更新 api_key: ****")
        
        # 更新 default_model (如果有指定)
        if config.default_model is not None:
            # 檢查是否為 OpenAI 模式
            api_key = config.api_key or os.getenv("OPENAI_API_KEY", "lemonade")
            is_openai = api_key.startswith("sk-")
            
            if is_openai:
                # OpenAI 模式 - 設定模型
                if config.default_model in OPENAI_MODELS:
                    set_openai_model(config.default_model)
                    updated_fields.append("default_model")
                    logger.info(f"更新 OpenAI 模型: {config.default_model}")
                else:
                    logger.warning(f"模型 {config.default_model} 不在推薦列表中，但仍會嘗試使用")
                    set_openai_model(config.default_model)
                    updated_fields.append("default_model")
            else:
                logger.info(f"Lemonade 模式下模型由 Server 管理，忽略 default_model 參數")
        
        # 取得最新配置
        api_key = os.getenv("OPENAI_API_KEY", "lemonade")
        is_openai = api_key.startswith("sk-")
        current_model = os.getenv("OPENAI_MODEL", DEFAULT_OPENAI_MODEL) if is_openai else DEFAULT_LEMONADE_MODEL
        
        return {
            "status": "success",
            "message": f"已更新配置: {', '.join(updated_fields)}" if updated_fields else "無變更",
            "updated_fields": updated_fields,
            "current_config": {
                "mode": "OpenAI" if is_openai else "Lemonade",
                "api_key_set": bool(api_key) and api_key != "lemonade",
                "current_model": current_model
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
        import os
        # 重置環境變數
        if "OPENAI_API_KEY" in os.environ:
            del os.environ["OPENAI_API_KEY"]
        if "OPENAI_MODEL" in os.environ:
            del os.environ["OPENAI_MODEL"]
        
        amd_config.openai_api_key = "lemonade"
        
        logger.info("配置已重置到預設值")
        
        return {
            "status": "success",
            "message": "配置已重置到預設值 (使用 Lemonade Server)",
            "current_config": {
                "mode": "Lemonade",
                "api_key_set": False,
                "current_model": DEFAULT_LEMONADE_MODEL
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
        import os
        api_key = os.getenv("OPENAI_API_KEY", "lemonade")
        is_openai = api_key.startswith("sk-")
        
        client, model = get_smart_client()
        
        # 簡單測試
        try:
            models = client.models.list()
            model_count = len(list(models.data))
        except:
            model_count = 0
        
        return {
            "status": "healthy",
            "backend": "OpenAI" if is_openai else "AMD Lemonade Server",
            "platform": "AMD Ryzen AI" if amd_config.is_amd_platform else "Generic",
            "current_model": model,
            "available_models": model_count
        }
    except Exception as e:
        logger.error(f"健康檢查失敗: {e}")
        return {
            "status": "error",
            "error": str(e)
        }

@router.get("/test_connection")
async def test_lemonade_connection():
    """測試 AI 服務連接"""
    try:
        client, model = get_smart_client()
        
        # 測試簡單請求
        params = get_completion_params(
            model=model,
            max_tokens=10,
            messages=[{"role": "user", "content": "Hi"}]
        )
        completion = client.chat.completions.create(**params)
        
        import os
        api_key = os.getenv("OPENAI_API_KEY", "lemonade")
        is_openai = api_key.startswith("sk-")
        
        return {
            "status": "success",
            "message": f"{'OpenAI' if is_openai else 'Lemonade Server'} 連接正常",
            "model": model,
            "test_response": completion.choices[0].message.content
        }
    except Exception as e:
        logger.error(f"連接測試失敗: {e}")
        raise HTTPException(status_code=500, detail=f"連接測試失敗: {str(e)}")

# ==================== AI 推理端點 ====================

@router.post("/ask")
async def ask_ai(req: AskRequest):
    """AI 問答"""
    try:
        client, model = get_smart_client()
        
        # 生成回答
        params = get_completion_params(
            model=model,
            max_tokens=1024,
            messages=[{"role": "user", "content": req.prompt}],
            temperature=0.7
        )
        completion = client.chat.completions.create(**params)
        
        answer = completion.choices[0].message.content
        return {"answer": answer}
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

        client, model = get_smart_client()

        # 生成總結
        params = get_completion_params(
            model=model,
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        completion = client.chat.completions.create(**params)
        
        summary_text = completion.choices[0].message.content
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

        client, model = get_smart_client()

        # 生成主題
        params = get_completion_params(
            model=model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8
        )
        completion = client.chat.completions.create(**params)
        
        raw_text = completion.choices[0].message.content
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
            return {"topic": f"錯誤：找不到指定的討論室 '{room_code}'。"}
        
        # 建立 prompt
        prompt = prompt_builder.build_single_topic_generation_prompt(room_code, req.custom_prompt)
        
        if prompt.startswith("錯誤"):
            return {"topic": prompt}

        client, model = get_smart_client()

        # 生成主題
        logger.info(f"開始生成主題，prompt 長度: {len(prompt)}")
        params = get_completion_params(
            model=model,
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8
        )
        completion = client.chat.completions.create(**params)
        
        topic = completion.choices[0].message.content

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

        client, model = get_smart_client()

        # 生成問題
        params = get_completion_params(
            model=model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8
        )
        completion = client.chat.completions.create(**params)
        
        topic = completion.choices[0].message.content
        return {"topic": topic}

    except Exception as e:
        logger.error(f"問題生成失敗: {e}")
        raise HTTPException(status_code=500, detail=f"問題生成失敗: {str(e)}")

# ==================== 統計和管理端點 ====================

@router.get("/stats")
async def get_ai_stats():
    """獲取 AI 服務統計信息"""
    try:
        import os
        api_key = os.getenv("OPENAI_API_KEY", "lemonade")
        is_openai = api_key.startswith("sk-")
        
        return {
            "backend": "OpenAI" if is_openai else "AMD Lemonade Server",
            "platform": "AMD Ryzen AI" if amd_config.is_amd_platform else "Generic",
            "status": "運行中",
            "current_model": "gpt-4o-mini" if is_openai else "Llama-3.2-1B-Instruct-Hybrid"
        }
    except Exception as e:
        logger.error(f"獲取統計失敗: {e}")
        return {
            "status": "錯誤",
            "error": str(e)
        }

@router.get("/models")
async def list_models():
    """列出所有可用的模型"""
    try:
        import os
        api_key = os.getenv("OPENAI_API_KEY", "lemonade")
        is_openai = api_key.startswith("sk-")
        
        client, model = get_smart_client()
        
        try:
            models_list = client.models.list()
            server_models = [{"id": m.id, "object": m.object} for m in models_list.data]
        except:
            server_models = []
        
        return {
            "mode": "OpenAI" if is_openai else "Lemonade",
            "current_model": model,
            "available_models": server_models[:10] if server_models else []
        }
    except Exception as e:
        logger.error(f"列出模型失敗: {e}")
        raise HTTPException(status_code=500, detail=f"列出模型失敗: {str(e)}")

@router.post("/load_model")
async def load_model(model_name: str):
    """載入指定的模型 (簡化版 - 不支援動態切換)"""
    return {
        "status": "info",
        "message": "簡化版 AI 客戶端會自動選擇模型，無需手動載入"
    }

@router.post("/unload_model")
async def unload_model():
    """卸載當前模型 (簡化版 - 不支援)"""
    return {
        "status": "info",
        "message": "簡化版 AI 客戶端無需手動卸載模型"
    }
