"""
智能 AI 客戶端
根據配置自動切換使用 OpenAI GPT-4o-mini 或本地 Lemonade Server
"""

from openai import OpenAI
import os

# OpenAI 可用模型列表
OPENAI_MODELS = {
    "gpt-4o": "GPT-4 Omni - 最強大的多模態模型",
    "gpt-4o-mini": "GPT-4 Omni Mini - 快速且經濟的模型 (推薦)",
    "gpt-4-turbo": "GPT-4 Turbo - 高性能模型",
    "gpt-4": "GPT-4 - 標準版本",
}

# 預設模型
DEFAULT_OPENAI_MODEL = "gpt-4o-mini"
DEFAULT_LEMONADE_MODEL = "Qwen-2.5-3B-Instruct-NPU"


def get_smart_client(model_name: str = None):
    """
    獲取智能 AI 客戶端
    - 如果有 OpenAI API Key (以 sk- 開頭): 使用 OpenAI 模型
    - 如果沒有或 API Key 不是 OpenAI 的: 使用本地 Lemonade Server
    
    Args:
        model_name: 指定要使用的模型名稱，如果不指定則使用預設模型
    
    Returns:
        配置好的 OpenAI 客戶端和模型名稱
    """
    # 從環境變數或配置獲取 API Key
    api_key = os.getenv("OPENAI_API_KEY", "lemonade")
    
    # 檢查是否為 OpenAI API Key (以 sk- 開頭)
    if api_key and api_key.startswith("sk-"):
        # 使用 OpenAI
        client = OpenAI(
            api_key=api_key
        )
        
        # 優先使用傳入的模型，其次使用環境變數，最後使用預設值
        if model_name:
            # 有傳入模型，直接使用
            model = model_name
        else:
            # 沒有傳入模型，從環境變數獲取
            model = os.getenv("OPENAI_MODEL", DEFAULT_OPENAI_MODEL)
        
        print(f"使用 OpenAI {model}")
    else:
        # 使用本地 Lemonade Server
        client = OpenAI(
            base_url="http://localhost:8000/api/v1",
            api_key="lemonade"
        )
        model = model_name if model_name else DEFAULT_LEMONADE_MODEL
        print(f"使用本地 Lemonade Server - {model}")
    
    return client, model


def chat(prompt: str, api_key: str = None, model: str = None) -> str:
    """
    簡單的聊天函數
    
    Args:
        prompt: 使用者輸入
        api_key: 可選的 API Key，如果不提供則使用環境變數
        model: 可選的模型名稱，如果不提供則使用預設模型
        
    Returns:
        AI 回應
    """
    # 如果提供了 api_key，暫時設定環境變數
    if api_key:
        old_key = os.getenv("OPENAI_API_KEY")
        os.environ["OPENAI_API_KEY"] = api_key
    
    try:
        client, selected_model = get_smart_client(model)
        
        completion = client.chat.completions.create(
            model=selected_model,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        return completion.choices[0].message.content
    
    finally:
        # 恢復原來的環境變數
        if api_key:
            if old_key:
                os.environ["OPENAI_API_KEY"] = old_key
            else:
                os.environ.pop("OPENAI_API_KEY", None)


def get_available_models():
    """
    取得可用的模型列表
    
    Returns:
        dict: 如果是 OpenAI 模式返回 OpenAI 模型列表，否則返回 Lemonade 資訊
    """
    api_key = os.getenv("OPENAI_API_KEY", "lemonade")
    
    if api_key and api_key.startswith("sk-"):
        return {
            "mode": "openai",
            "models": OPENAI_MODELS,
            "default": DEFAULT_OPENAI_MODEL
        }
    else:
        return {
            "mode": "lemonade",
            "default": DEFAULT_LEMONADE_MODEL,
            "message": "使用本地 Lemonade Server，模型由 Server 提供"
        }


def set_openai_model(model_name: str):
    """
    設定要使用的 OpenAI 模型 (通過環境變數)
    
    Args:
        model_name: OpenAI 模型名稱
    """
    if model_name in OPENAI_MODELS:
        os.environ["OPENAI_MODEL"] = model_name
        print(f"已設定 OpenAI 模型: {model_name}")
        return True
    else:
        print(f"警告: {model_name} 不在可用模型列表中，但仍會嘗試使用")
        os.environ["OPENAI_MODEL"] = model_name
        return True


def get_completion_params(model: str, max_tokens: int, **kwargs):
    """
    根據模型自動選擇正確的參數名稱和限制
    - GPT-5 系列: 使用 max_completion_tokens，不支援自訂 temperature
    - GPT-4o 系列: 使用 max_completion_tokens
    - 舊版模型和 Lemonade: 使用 max_tokens
    
    Args:
        model: 模型名稱
        max_tokens: 最大 token 數
        **kwargs: 其他參數 (如 temperature, messages 等)
    
    Returns:
        dict: 適合該模型的參數字典
    """
    # GPT-5 系列模型 (有特殊限制)
    gpt5_models = ["gpt-5", "gpt-5-mini", "gpt-5-nano"]
    # GPT-4o 系列模型
    gpt4o_models = ["gpt-4o", "gpt-4o-mini", "chatgpt-4o-latest"]
    
    params = {
        "model": model,
    }
    
    # 檢查是否為 GPT-5 系列
    is_gpt5 = any(gpt5_model in model.lower() for gpt5_model in gpt5_models)
    # 檢查是否為 GPT-4o 系列
    is_gpt4o = any(gpt4o_model in model.lower() for gpt4o_model in gpt4o_models)
    
    # 設定 token 限制參數
    if is_gpt5 or is_gpt4o:
        params["max_completion_tokens"] = max_tokens
    else:
        params["max_tokens"] = max_tokens
    
    # 處理其他參數
    for key, value in kwargs.items():
        # GPT-5 不支援自訂 temperature，只能使用預設值 1
        if is_gpt5 and key == "temperature":
            # 跳過 temperature 參數，讓它使用預設值
            continue
        params[key] = value
    
    return params
