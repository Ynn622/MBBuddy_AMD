"""
OpenAI 相容 API 客戶端
用於與 AMD Ryzen AI 的 Lemonade Server (OpenAI 相容 API) 交互
支援 Chat Completions API 標準格式
"""

from openai import OpenAI, AsyncOpenAI
from typing import Optional, Dict, Any, List, AsyncGenerator
import asyncio
from .amd_config import amd_config
from .logger import get_logger

logger = get_logger("mbbuddy.openai_client")


class OpenAICompatibleClient:
    """OpenAI 相容 API 客戶端 (用於 Lemonade Server)"""
    
    def __init__(self):
        self.config = amd_config.get_openai_config()
        self.inference_config = amd_config.get_inference_config()
        self.base_url = self.config["base_url"]
        self.api_key = self.config["api_key"]
        
        # 同步和異步客戶端
        self._sync_client: Optional[OpenAI] = None
        self._async_client: Optional[AsyncOpenAI] = None
        
        # 當前使用的模型
        self.current_model = self.config.get("default_model")
        
        logger.info(f"OpenAI 相容客戶端初始化: {self.base_url}")
    
    @property
    def sync_client(self) -> OpenAI:
        """獲取同步客戶端（懶加載）"""
        if self._sync_client is None:
            self._sync_client = OpenAI(
                base_url=self.base_url,
                api_key=self.api_key,
                timeout=self.config["request_timeout"],
                max_retries=self.config["max_retries"],
            )
        return self._sync_client
    
    @property
    def async_client(self) -> AsyncOpenAI:
        """獲取異步客戶端（懶加載）"""
        if self._async_client is None:
            self._async_client = AsyncOpenAI(
                base_url=self.base_url,
                api_key=self.api_key,
                timeout=self.config["request_timeout"],
                max_retries=self.config["max_retries"],
            )
        return self._async_client
    
    async def check_health(self) -> bool:
        """檢查服務健康狀態"""
        try:
            # 嘗試列出模型以驗證連接
            models = await self.list_models()
            if models:
                logger.info("OpenAI 相容 API 服務健康檢查通過")
                return True
            return False
        except Exception as e:
            logger.error(f"無法連接到 OpenAI 相容 API 服務: {e}")
            return False
    
    async def list_models(self) -> List[Dict[str, Any]]:
        """列出可用的模型"""
        try:
            response = await self.async_client.models.list()
            models = [
                {
                    "id": model.id,
                    "object": model.object,
                    "created": model.created,
                    "owned_by": getattr(model, "owned_by", "unknown"),
                }
                for model in response.data
            ]
            logger.info(f"找到 {len(models)} 個可用模型")
            return models
        except Exception as e:
            logger.error(f"列出模型時發生錯誤: {e}")
            return []
    
    def set_model(self, model_name: str):
        """設置當前使用的模型"""
        self.current_model = model_name
        logger.info(f"當前模型設為: {model_name}")
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        stream: bool = False,
        **kwargs
    ) -> str:
        """
        聊天補全 (OpenAI Chat Completions API)
        
        Args:
            messages: 消息列表，格式: [{"role": "user", "content": "..."}]
            model: 模型名稱（如果不指定則使用當前模型）
            max_tokens: 最大生成 tokens 數
            temperature: 溫度參數 (0.0-2.0)
            top_p: Top-p 採樣 (0.0-1.0)
            stream: 是否使用流式輸出
            **kwargs: 其他 OpenAI API 參數
            
        Returns:
            生成的回應文本
        """
        # 使用指定模型或當前模型
        model_name = model or self.current_model
        if not model_name:
            raise RuntimeError("未指定模型，請先調用 set_model() 或傳入 model 參數")
        
        # 獲取默認參數
        default_params = self.inference_config.get("default_params", {})
        
        # 構建請求參數
        params = {
            "model": model_name,
            "messages": messages,
            "max_tokens": max_tokens or default_params.get("max_tokens", 2048),
            "temperature": temperature if temperature is not None else default_params.get("temperature", 0.7),
            "top_p": top_p if top_p is not None else default_params.get("top_p", 0.9),
            "stream": stream,
        }
        
        # 添加其他 OpenAI 參數
        for key in ["frequency_penalty", "presence_penalty", "stop", "n", "logit_bias", "user"]:
            if key in kwargs:
                params[key] = kwargs[key]
            elif key in default_params:
                params[key] = default_params[key]
        
        try:
            if stream:
                # 流式生成
                return await self._chat_completion_stream(params)
            else:
                # 非流式生成
                response = await self.async_client.chat.completions.create(**params)
                content = response.choices[0].message.content
                logger.debug(f"聊天完成，長度: {len(content)}")
                return content
                
        except Exception as e:
            logger.error(f"聊天完成時發生錯誤: {e}")
            raise
    
    async def _chat_completion_stream(self, params: Dict[str, Any]) -> str:
        """流式聊天補全（內部方法）"""
        full_text = ""
        
        try:
            stream = await self.async_client.chat.completions.create(**params)
            
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_text += content
            
            logger.debug(f"流式聊天完成，總長度: {len(full_text)}")
            return full_text
            
        except Exception as e:
            logger.error(f"流式聊天完成時發生錯誤: {e}")
            raise
    
    async def chat_completion_stream_generator(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        流式聊天補全生成器（用於實時輸出）
        
        Args:
            messages: 消息列表
            model: 模型名稱
            max_tokens: 最大 tokens
            temperature: 溫度參數
            **kwargs: 其他參數
            
        Yields:
            生成的文本片段
        """
        model_name = model or self.current_model
        if not model_name:
            raise RuntimeError("未指定模型")
        
        default_params = self.inference_config.get("default_params", {})
        
        params = {
            "model": model_name,
            "messages": messages,
            "max_tokens": max_tokens or default_params.get("max_tokens", 2048),
            "temperature": temperature if temperature is not None else default_params.get("temperature", 0.7),
            "stream": True,
        }
        
        try:
            stream = await self.async_client.chat.completions.create(**params)
            
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error(f"流式生成器錯誤: {e}")
            raise
    
    def chat_completion_sync(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> str:
        """
        同步聊天補全
        
        Args:
            messages: 消息列表
            model: 模型名稱
            max_tokens: 最大 tokens
            temperature: 溫度參數
            **kwargs: 其他參數
            
        Returns:
            生成的回應文本
        """
        model_name = model or self.current_model
        if not model_name:
            raise RuntimeError("未指定模型")
        
        default_params = self.inference_config.get("default_params", {})
        
        params = {
            "model": model_name,
            "messages": messages,
            "max_tokens": max_tokens or default_params.get("max_tokens", 2048),
            "temperature": temperature if temperature is not None else default_params.get("temperature", 0.7),
            "stream": False,
        }
        
        try:
            response = self.sync_client.chat.completions.create(**params)
            content = response.choices[0].message.content
            logger.debug(f"同步聊天完成，長度: {len(content)}")
            return content
        except Exception as e:
            logger.error(f"同步聊天完成時發生錯誤: {e}")
            raise
    
    async def close(self):
        """關閉客戶端連接"""
        if self._async_client:
            await self._async_client.close()
            self._async_client = None
        if self._sync_client:
            self._sync_client.close()
            self._sync_client = None
        logger.info("OpenAI 相容客戶端已關閉")
    
    async def __aenter__(self):
        """異步上下文管理器入口"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """異步上下文管理器出口"""
        await self.close()


# 全局客戶端實例
openai_client = OpenAICompatibleClient()
