"""
統一 AI 呼叫模組
支援 Lemonade Server (本地) 和 OpenAI API (雲端) 兩種模式
"""
import os
from openai import OpenAI, AsyncOpenAI
from typing import Optional, Dict, Any, Literal
from .logger import get_logger

logger = get_logger("mbbuddy.call_ai")

class AIService:
    """統一的 AI 服務管理類別"""
    
    def __init__(self):
        # 預設使用 Lemonade 模式
        self.mode: Literal["lemonade", "openai"] = "lemonade"
        self.openai_api_key: Optional[str] = None
        self.openai_model: str = "gpt-4o-mini"
        self.lemonade_model: str = "Qwen-2.5-3B-Instruct-NPU"
        self.lemonade_base_url: str = "http://localhost:8001/api/v1"
        
        # 客戶端實例（懶加載）
        self._sync_client: Optional[OpenAI] = None
        self._async_client: Optional[AsyncOpenAI] = None
        
        logger.info(f"AI Service 初始化，預設模式: {self.mode}")
    
    def set_mode(self, mode: Literal["lemonade", "openai"], 
                 api_key: Optional[str] = None, 
                 model: Optional[str] = None):
        """
        設定 AI 服務模式
        
        Args:
            mode: "lemonade" 或 "openai"
            api_key: OpenAI API Key (僅 openai 模式需要)
            model: 模型名稱 (可選)
        """
        if mode == "openai" and not api_key and not self.openai_api_key:
            raise ValueError("OpenAI 模式需要提供 API Key")
        
        self.mode = mode
        
        if mode == "openai":
            if api_key:
                self.openai_api_key = api_key
            if model:
                self.openai_model = model
            # 重置客戶端以使用新設定
            self._sync_client = None
            self._async_client = None
            logger.info(f"切換到 OpenAI 模式，模型: {self.openai_model}")
        else:
            if model:
                self.lemonade_model = model
            logger.info(f"切換到 Lemonade 模式，模型: {self.lemonade_model}")
    
    def get_config(self) -> Dict[str, Any]:
        """取得當前配置"""
        return {
            "mode": self.mode,
            "model": self.openai_model if self.mode == "openai" else self.lemonade_model,
            "lemonade_base_url": self.lemonade_base_url,
            "openai_configured": bool(self.openai_api_key)
        }
    
    @property
    def sync_client(self) -> OpenAI:
        """取得同步客戶端"""
        if self._sync_client is None:
            if self.mode == "openai":
                self._sync_client = OpenAI(
                    api_key=self.openai_api_key or os.environ.get("OPENAI_API_KEY")
                )
            else:
                self._sync_client = OpenAI(
                    base_url=self.lemonade_base_url,
                    api_key="lemonade"  # required but unused
                )
        return self._sync_client
    
    @property
    def async_client(self) -> AsyncOpenAI:
        """取得非同步客戶端"""
        if self._async_client is None:
            if self.mode == "openai":
                self._async_client = AsyncOpenAI(
                    api_key=self.openai_api_key or os.environ.get("OPENAI_API_KEY")
                )
            else:
                self._async_client = AsyncOpenAI(
                    base_url=self.lemonade_base_url,
                    api_key="lemonade"  # required but unused
                )
        return self._async_client
    
    def generate(self, prompt: str, 
                 system_instruction: Optional[str] = None,
                 temperature: float = 0.7,
                 max_tokens: int = 1024) -> str:
        """
        同步生成回應
        
        Args:
            prompt: 使用者輸入
            system_instruction: 系統指令 (可選)
            temperature: 溫度參數
            max_tokens: 最大 token 數
            
        Returns:
            生成的文字
        """
        try:
            model = self.openai_model if self.mode == "openai" else self.lemonade_model
            
            messages = []
            if system_instruction:
                messages.append({"role": "system", "content": system_instruction})
            messages.append({"role": "user", "content": prompt})
            
            completion = self.sync_client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            content = completion.choices[0].message.content
            logger.debug(f"生成成功 (模式: {self.mode}, 模型: {model})")
            return content
            
        except Exception as e:
            logger.error(f"AI 生成失敗: {e}")
            raise
    
    async def generate_async(self, prompt: str,
                            system_instruction: Optional[str] = None,
                            temperature: float = 0.7,
                            max_tokens: int = 1024) -> str:
        """
        非同步生成回應
        
        Args:
            prompt: 使用者輸入
            system_instruction: 系統指令 (可選)
            temperature: 溫度參數
            max_tokens: 最大 token 數
            
        Returns:
            生成的文字
        """
        try:
            model = self.openai_model if self.mode == "openai" else self.lemonade_model
            
            messages = []
            if system_instruction:
                messages.append({"role": "system", "content": system_instruction})
            messages.append({"role": "user", "content": prompt})
            
            completion = await self.async_client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            content = completion.choices[0].message.content
            logger.debug(f"生成成功 (模式: {self.mode}, 模型: {model})")
            return content
            
        except Exception as e:
            logger.error(f"AI 生成失敗: {e}")
            raise


# 全域單例實例
ai_service = AIService()
