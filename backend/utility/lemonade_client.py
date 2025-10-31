"""
Lemonade Server 客戶端
用於與 AMD Ryzen AI 的 Lemonade Server API 交互
支援 OGA (ONNX Generation API) INT4 量化模型
使用 OpenAI SDK 進行 API 調用
"""

import asyncio
from openai import AsyncOpenAI
from typing import Optional, Dict, Any, AsyncGenerator
from pathlib import Path
import json
from .amd_config import amd_config
from .logger import get_logger

logger = get_logger("mbbuddy.lemonade")

class LemonadeClient:
    """Lemonade Server API 客戶端（使用 OpenAI SDK）"""
    
    def __init__(self):
        self.config = amd_config.get_lemonade_config()
        self.inference_config = amd_config.get_inference_config()
        
        # base_url 需要加上 /v1 後綴（OpenAI SDK 要求）
        raw_base_url = self.config["base_url"]
        if not raw_base_url.endswith("/v1"):
            self.base_url = f"{raw_base_url}/v1"
        else:
            self.base_url = raw_base_url
            
        # api_key 在 Lemonade 中必須提供但不會實際驗證
        self.api_key = self.config.get("api_key", "lemonade")
        
        # OpenAI 客戶端
        self._client: Optional[AsyncOpenAI] = None
        
        # 模型狀態
        self.current_model: Optional[str] = None
        self.is_model_loaded = False
        
        logger.info(f"Lemonade Client 初始化 (OpenAI SDK): {self.base_url}")
    
    @property
    def client(self) -> AsyncOpenAI:
        """獲取 OpenAI 客戶端（懶加載）"""
        if self._client is None:
            # 重新讀取配置（可能已被更新）
            self.config = amd_config.get_lemonade_config()
            raw_base_url = self.config["base_url"]
            
            # 確保 base_url 以 /v1 結尾
            if not raw_base_url.endswith("/v1"):
                self.base_url = f"{raw_base_url}/v1"
            else:
                self.base_url = raw_base_url
            
            # 更新 api_key
            self.api_key = self.config.get("api_key", "lemonade")
            
            # 創建新客戶端
            self._client = AsyncOpenAI(
                base_url=self.base_url,
                api_key=self.api_key,
                timeout=self.config["request_timeout"],
                max_retries=2
            )
            logger.info(f"OpenAI 客戶端已創建: {self.base_url}")
        return self._client
    
    def _get_headers(self) -> Dict[str, str]:
        """獲取請求標頭（已由 OpenAI SDK 處理，此方法保留作為參考）"""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers
    
    async def check_health(self) -> bool:
        """檢查 Lemonade Server 健康狀態"""
        try:
            # 使用 OpenAI SDK 列出模型來檢查健康狀態
            models = await self.client.models.list()
            logger.info("Lemonade Server 健康檢查通過")
            return True
        except Exception as e:
            logger.error(f"無法連接到 Lemonade Server: {e}")
            return False
    
    async def list_models(self) -> list[Dict[str, Any]]:
        """列出可用的模型"""
        try:
            models_response = await self.client.models.list()
            models = [{"id": model.id, "object": model.object, "created": getattr(model, "created", None)} 
                     for model in models_response.data]
            logger.info(f"找到 {len(models)} 個可用模型")
            return models
        except Exception as e:
            logger.error(f"列出模型時發生錯誤: {e}")
            return []
    
    async def load_model(self, model_name: str) -> bool:
        """
        載入指定的模型
        
        Args:
            model_name: 模型名稱（例如 "Llama-3.2-1B-Instruct-int4" 或 "gpt-4"）
            
        Returns:
            是否載入成功
        """
        try:
            # 檢查模型是否已載入
            if self.is_model_loaded and self.current_model == model_name:
                logger.info(f"模型 {model_name} 已載入")
                return True
            
            # 檢查模型是否在可用列表中（僅作為提示，不強制）
            try:
                models = await self.list_models()
                model_ids = [m.get("id") for m in models]
                
                if model_name not in model_ids:
                    logger.warning(f"模型 {model_name} 不在本地可用模型列表中: {model_ids}")
                    logger.info(f"將嘗試使用模型 {model_name}（可能是 OpenAI 或其他服務的模型）")
            except Exception as e:
                logger.warning(f"無法獲取模型列表，將直接使用指定模型: {e}")
            
            # 設定模型（不論是否在列表中）
            self.current_model = model_name
            self.is_model_loaded = True
            logger.info(f"模型 {model_name} 已設定")
            return True
                
        except Exception as e:
            logger.error(f"設定模型時發生錯誤: {e}")
            return False
    
    async def unload_model(self) -> bool:
        """卸載當前模型"""
        try:
            if not self.is_model_loaded:
                return True
            
            # Lemonade Server 可能不支援明確卸載
            # 只需清除本地狀態
            self.current_model = None
            self.is_model_loaded = False
            logger.info("模型已卸載（本地狀態清除）")
            return True
        except Exception as e:
            logger.error(f"卸載模型時發生錯誤: {e}")
            return False
    
    async def generate(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        stream: bool = False,
        **kwargs
    ) -> str:
        """
        生成文本回應
        
        Args:
            prompt: 輸入提示
            max_tokens: 最大生成 tokens 數
            temperature: 溫度參數
            top_p: Top-p 採樣
            stream: 是否使用流式輸出
            **kwargs: 其他生成參數
            
        Returns:
            生成的文本
        """
        if not self.is_model_loaded:
            raise RuntimeError("模型未載入，請先調用 load_model()")
        
        # 構建請求參數
        params = {
            "model": self.current_model,
            "prompt": prompt,
            "max_tokens": max_tokens or self.inference_config.get("max_tokens", 2048),
            "temperature": temperature or self.inference_config.get("temperature", 0.7),
            "top_p": top_p or self.inference_config.get("top_p", 0.9),
            "stream": stream,
        }
        
        # 添加其他參數（OpenAI SDK 會處理 extra_body）
        extra_params = {}
        if "top_k" in kwargs or "top_k" in self.inference_config:
            extra_params["top_k"] = kwargs.get("top_k", self.inference_config.get("top_k", 40))
        if "repeat_penalty" in kwargs or "repeat_penalty" in self.inference_config:
            extra_params["repeat_penalty"] = kwargs.get("repeat_penalty", self.inference_config.get("repeat_penalty", 1.1))
        
        for key, value in kwargs.items():
            if key not in params and key not in ["top_k", "repeat_penalty"]:
                extra_params[key] = value
        
        try:
            if stream:
                # 流式生成
                return await self._generate_stream(params, extra_params)
            else:
                # 非流式生成
                response = await self.client.completions.create(
                    **params,
                    extra_body=extra_params if extra_params else None
                )
                
                text = response.choices[0].text
                logger.debug(f"生成完成，長度: {len(text)}")
                return text
                    
        except Exception as e:
            logger.error(f"生成時發生錯誤: {e}")
            raise
    
    async def _generate_stream(self, params: Dict[str, Any], extra_params: Dict[str, Any]) -> str:
        """流式生成（內部方法）"""
        full_text = ""
        
        try:
            stream = await self.client.completions.create(
                **params,
                extra_body=extra_params if extra_params else None
            )
            
            async for chunk in stream:
                if chunk.choices and len(chunk.choices) > 0:
                    content = chunk.choices[0].text
                    if content:
                        full_text += content
            
            return full_text
                
        except Exception as e:
            logger.error(f"流式生成時發生錯誤: {e}")
            raise
    
    async def chat_completion(
        self,
        messages: list[Dict[str, str]],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        stream: bool = False,
        **kwargs
    ) -> str:
        """
        聊天補全（OpenAI 格式）
        
        Args:
            messages: 消息列表，格式: [{"role": "user", "content": "..."}]
            max_tokens: 最大生成 tokens 數
            temperature: 溫度參數
            stream: 是否使用流式輸出
            **kwargs: 其他生成參數
            
        Returns:
            生成的回應
        """
        if not self.is_model_loaded:
            raise RuntimeError("模型未載入，請先調用 load_model()")
        
        params = {
            "model": self.current_model,
            "messages": messages,
            "max_tokens": max_tokens or self.inference_config.get("max_tokens", 2048),
            "temperature": temperature or self.inference_config.get("temperature", 0.7),
            "stream": stream,
        }
        
        # 添加其他參數
        extra_params = {}
        for key, value in kwargs.items():
            if key not in params:
                extra_params[key] = value
        
        try:
            response = await self.client.chat.completions.create(
                **params,
                extra_body=extra_params if extra_params else None
            )
            
            content = response.choices[0].message.content
            logger.debug(f"聊天完成，長度: {len(content)}")
            return content
                
        except Exception as e:
            logger.error(f"聊天完成時發生錯誤: {e}")
            raise
    
    async def close(self):
        """關閉客戶端連接"""
        if self._client:
            await self._client.close()
            self._client = None
            logger.info("Lemonade Client 已關閉")
    
    def update_config(self, base_url: Optional[str] = None, api_key: Optional[str] = None):
        """
        更新客戶端配置
        
        Args:
            base_url: 新的 base URL
            api_key: 新的 API key
            
        Note:
            更新配置後需要關閉並重新創建客戶端
        """
        if base_url is not None:
            # 確保 base_url 以 /v1 結尾
            if not base_url.endswith("/v1"):
                self.base_url = f"{base_url}/v1"
            else:
                self.base_url = base_url
            logger.info(f"更新 base_url: {self.base_url}")
        
        if api_key is not None:
            self.api_key = api_key
            logger.info("更新 api_key: ****")
        
        # 標記需要重新創建客戶端
        if self._client:
            logger.info("配置已更新，客戶端將在下次使用時重新創建")
    
    async def __aenter__(self):
        """異步上下文管理器入口"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """異步上下文管理器出口"""
        await self.close()

# 全局客戶端實例
lemonade_client = LemonadeClient()
