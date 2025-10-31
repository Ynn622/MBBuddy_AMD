"""
Lemonade Server 客戶端
用於與 AMD Ryzen AI 的 Lemonade Server API 交互
支援 OGA (ONNX Generation API) INT4 量化模型
"""

import asyncio
import httpx
from typing import Optional, Dict, Any, AsyncGenerator
from pathlib import Path
import json
from .amd_config import amd_config
from .logger import get_logger

logger = get_logger("mbbuddy.lemonade")

class LemonadeClient:
    """Lemonade Server API 客戶端"""
    
    def __init__(self):
        self.config = amd_config.get_lemonade_config()
        self.inference_config = amd_config.get_inference_config()
        self.base_url = self.config["base_url"]
        self.api_key = self.config.get("api_key", "")
        
        # HTTP 客戶端
        self._client: Optional[httpx.AsyncClient] = None
        
        # 模型狀態
        self.current_model: Optional[str] = None
        self.is_model_loaded = False
        
        logger.info(f"Lemonade Client 初始化: {self.base_url}")
    
    @property
    def client(self) -> httpx.AsyncClient:
        """獲取 HTTP 客戶端（懶加載）"""
        if self._client is None:
            timeout = httpx.Timeout(
                timeout=self.config["request_timeout"],
                connect=10.0
            )
            limits = httpx.Limits(
                max_keepalive_connections=self.config["connection_pool_size"],
                max_connections=self.config["connection_pool_size"] * 2
            )
            self._client = httpx.AsyncClient(
                timeout=timeout,
                limits=limits,
                headers=self._get_headers()
            )
        return self._client
    
    def _get_headers(self) -> Dict[str, str]:
        """獲取請求標頭"""
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
            # Lemonade Server 沒有 /health 端點,使用 /v1/models 來檢查
            response = await self.client.get(f"{self.base_url}/v1/models")
            if response.status_code == 200:
                logger.info("Lemonade Server 健康檢查通過")
                return True
            else:
                logger.warning(f"Lemonade Server 健康檢查失敗: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"無法連接到 Lemonade Server: {e}")
            return False
    
    async def list_models(self) -> list[Dict[str, Any]]:
        """列出可用的模型"""
        try:
            response = await self.client.get(f"{self.base_url}/v1/models")
            if response.status_code == 200:
                data = response.json()
                models = data.get("data", [])
                logger.info(f"找到 {len(models)} 個可用模型")
                return models
            else:
                logger.error(f"獲取模型列表失敗: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"列出模型時發生錯誤: {e}")
            return []
    
    async def load_model(self, model_name: str) -> bool:
        """
        載入指定的模型
        
        Args:
            model_name: 模型名稱（例如 "Llama-3.2-1B-Instruct-int4"）
            
        Returns:
            是否載入成功
        """
        try:
            # 檢查模型是否已載入
            if self.is_model_loaded and self.current_model == model_name:
                logger.info(f"模型 {model_name} 已載入")
                return True
            
            # 檢查模型是否在可用列表中
            models = await self.list_models()
            model_ids = [m.get("id") for m in models]
            
            if model_name not in model_ids:
                logger.error(f"模型 {model_name} 不在可用模型列表中: {model_ids}")
                return False
            
            # Lemonade Server 通常不需要明確載入，模型會在首次推理時自動載入
            # 只需標記模型為已選擇
            self.current_model = model_name
            self.is_model_loaded = True
            logger.info(f"模型 {model_name} 已設定，將在首次推理時自動載入")
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
        payload = {
            "model": self.current_model,
            "prompt": prompt,
            "max_tokens": max_tokens or self.inference_config.get("max_tokens", 2048),
            "temperature": temperature or self.inference_config.get("temperature", 0.7),
            "top_p": top_p or self.inference_config.get("top_p", 0.9),
            "top_k": kwargs.get("top_k", self.inference_config.get("top_k", 40)),
            "repeat_penalty": kwargs.get("repeat_penalty", self.inference_config.get("repeat_penalty", 1.1)),
            "stream": stream,
        }
        
        # 添加其他參數
        for key, value in kwargs.items():
            if key not in payload:
                payload[key] = value
        
        try:
            if stream:
                # 流式生成
                return await self._generate_stream(payload)
            else:
                # 非流式生成
                response = await self.client.post(
                    f"{self.base_url}/v1/completions",
                    json=payload,
                    timeout=self.config["request_timeout"]
                )
                
                if response.status_code == 200:
                    data = response.json()
                    text = data.get("choices", [{}])[0].get("text", "")
                    logger.debug(f"生成完成，長度: {len(text)}")
                    return text
                else:
                    logger.error(f"生成失敗: {response.status_code} - {response.text}")
                    raise RuntimeError(f"生成失敗: {response.status_code}")
                    
        except Exception as e:
            logger.error(f"生成時發生錯誤: {e}")
            raise
    
    async def _generate_stream(self, payload: Dict[str, Any]) -> str:
        """流式生成（內部方法）"""
        full_text = ""
        
        try:
            async with self.client.stream(
                "POST",
                f"{self.base_url}/v1/completions",
                json=payload
            ) as response:
                if response.status_code != 200:
                    raise RuntimeError(f"流式生成失敗: {response.status_code}")
                
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]  # 移除 "data: " 前綴
                        
                        if data_str.strip() == "[DONE]":
                            break
                        
                        try:
                            data = json.loads(data_str)
                            delta = data.get("choices", [{}])[0].get("delta", {})
                            content = delta.get("content", "")
                            full_text += content
                        except json.JSONDecodeError:
                            continue
                
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
        
        payload = {
            "model": self.current_model,
            "messages": messages,
            "max_tokens": max_tokens or self.inference_config.get("max_tokens", 2048),
            "temperature": temperature or self.inference_config.get("temperature", 0.7),
            "stream": stream,
        }
        
        # 添加其他參數
        for key, value in kwargs.items():
            if key not in payload:
                payload[key] = value
        
        try:
            response = await self.client.post(
                f"{self.base_url}/v1/chat/completions",
                json=payload,
                timeout=self.config["request_timeout"]
            )
            
            if response.status_code == 200:
                data = response.json()
                message = data.get("choices", [{}])[0].get("message", {})
                content = message.get("content", "")
                logger.debug(f"聊天完成，長度: {len(content)}")
                return content
            else:
                logger.error(f"聊天完成失敗: {response.status_code} - {response.text}")
                raise RuntimeError(f"聊天完成失敗: {response.status_code}")
                
        except Exception as e:
            logger.error(f"聊天完成時發生錯誤: {e}")
            raise
    
    async def close(self):
        """關閉客戶端連接"""
        if self._client:
            await self._client.aclose()
            self._client = None
            logger.info("Lemonade Client 已關閉")
    
    async def __aenter__(self):
        """異步上下文管理器入口"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """異步上下文管理器出口"""
        await self.close()

# 全局客戶端實例
lemonade_client = LemonadeClient()
