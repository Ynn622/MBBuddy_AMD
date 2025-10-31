"""
AMD Ryzen AI 平台優化配置
針對 AMD Ryzen AI PC 的 AI 推理優化
使用 OpenAI 相容 API (Lemonade Server)
"""

import os
import platform
from typing import Dict, Any, Optional
from .logger import get_logger

logger = get_logger("mbbuddy.amd_config")

class AMDRyzenAIConfig:
    """AMD Ryzen AI 平台配置管理器"""
    
    def __init__(self):
        self.platform_info = self._detect_platform()
        self.is_amd_platform = self._is_amd_platform()
        
        # OpenAI 相容 API 配置 (Lemonade Server)
        # Lemonade Server API 結構: http://localhost:8000/api
        # 完整端點: /api/v1/models, /api/v1/chat/completions
        self.openai_base_url = os.getenv("OPENAI_BASE_URL", "http://localhost:8000/api")
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "lemonade")  # required but unused
        
        # 向後相容:舊的 Lemonade 屬性名稱
        self.lemonade_base_url = self.openai_base_url
        self.lemonade_api_key = self.openai_api_key
        
    def _detect_platform(self) -> Dict[str, Any]:
        """檢測平台信息"""
        return {
            "system": platform.system(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "architecture": platform.architecture(),
            "python_version": platform.python_version(),
        }
    
    def _is_amd_platform(self) -> bool:
        """檢測是否為 AMD Ryzen AI 平台"""
        # 通過環境變量檢測
        if os.getenv("AMD_RYZEN_AI", "false").lower() == "true":
            return True
        
        # 通過處理器信息檢測
        processor = platform.processor().lower()
        if "amd" in processor or "ryzen" in processor:
            logger.info(f"檢測到 AMD 處理器: {processor}")
            return True
        
        return False
    
    def get_openai_config(self) -> Dict[str, Any]:
        """獲取 OpenAI 相容 API 配置"""
        if self.is_amd_platform:
            return {
                "base_url": self.openai_base_url,
                "api_key": self.openai_api_key,
                "max_concurrent_requests": 8,      # AMD Ryzen AI 可同時處理多個請求
                "request_timeout": 120.0,          # 請求超時（秒）- OpenAI 標準
                "retry_attempts": 3,               # 重試次數
                "connection_pool_size": 16,        # 連接池大小
                "enable_streaming": True,          # 啟用流式回應
                "default_model": "Llama-3.2-1B-Instruct-awq-g128-int4-asym-fp16-onnx-hybrid",
                "organization": None,              # OpenAI organization (unused)
                "max_retries": 3,                  # OpenAI SDK 重試次數
            }
        else:
            # 通用配置
            return {
                "base_url": self.openai_base_url,
                "api_key": self.openai_api_key,
                "max_concurrent_requests": 4,
                "request_timeout": 60.0,
                "retry_attempts": 2,
                "connection_pool_size": 8,
                "enable_streaming": True,
                "default_model": "Llama-3.2-1B-Instruct-awq-g128-int4-asym-fp16-onnx-hybrid",
                "organization": None,
                "max_retries": 2,
            }
    
    def get_lemonade_config(self) -> Dict[str, Any]:
        """
        向後相容方法：返回 OpenAI 相容 API 配置
        (原 Lemonade Server 現在使用 OpenAI 相容 API)
        """
        return self.get_openai_config()
    
    def get_model_config(self) -> Dict[str, Any]:
        """獲取推薦的 AMD 優化模型配置 (OpenAI Chat Completion 格式)"""
        if self.is_amd_platform:
            return {
                # AMD Ryzen AI 推薦模型（INT4 量化 ONNX 格式）
                "recommended_models": [
                    {"name": "Qwen-2.5-3B-Instruct-NPU"},
                    {
                        "name": "Llama-3.2-1B-Instruct-int4-hybrid",
                        "model_id": "Llama-3.2-1B-Instruct-awq-g128-int4-asym-fp16-onnx-hybrid",
                        "repo_id": "amd/Llama-3.2-1B-Instruct-onnx-ryzen-strix",
                        "description": "Llama 3.2 1B INT4 量化，針對 AMD Ryzen AI 優化",
                        "size": "1.2GB",
                        "performance": "excellent",
                        "recommended": True,
                        "quantization": "int4",
                        "format": "onnx",
                        "supports_chat": True,
                        "supports_streaming": True,
                    },
                    {
                        "name": "Llama-3.2-3B-Instruct-int4-hybrid",
                        "model_id": "Llama-3.2-3B-Instruct-awq-g128-int4-asym-fp16-onnx-hybrid",
                        "repo_id": "amd/Llama-3.2-3B-Instruct-onnx-ryzen-strix",
                        "description": "Llama 3.2 3B INT4 量化，更強大的推理能力",
                        "size": "2.8GB",
                        "performance": "excellent",
                        "recommended": True,
                        "quantization": "int4",
                        "format": "onnx",
                        "supports_chat": True,
                        "supports_streaming": True,
                    },
                    {
                        "name": "Phi-3.5-mini-instruct-int4",
                        "model_id": "Phi-3.5-mini-instruct-int4-onnx-hybrid",
                        "repo_id": "microsoft/Phi-3.5-mini-instruct",
                        "description": "Microsoft Phi-3.5 Mini INT4，輕量級高效模型",
                        "size": "2.5GB",
                        "performance": "very_good",
                        "recommended": True,
                        "quantization": "int4",
                        "format": "onnx",
                        "supports_chat": True,
                        "supports_streaming": True,
                    },
                    {
                        "name": "Qwen2.5-1.5B-Instruct-int4",
                        "model_id": "Qwen2.5-1.5B-Instruct-int4-onnx-hybrid",
                        "repo_id": "Qwen/Qwen2.5-1.5B-Instruct",
                        "description": "Qwen2.5 1.5B INT4 量化版本",
                        "size": "1.5GB",
                        "performance": "good",
                        "recommended": False,
                        "quantization": "int4",
                        "format": "onnx",
                        "supports_chat": True,
                        "supports_streaming": True,
                    }
                ],
                # OpenAI Chat Completion API 默認參數
                "default_params": {
                    "max_tokens": 2048,
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "frequency_penalty": 0.0,
                    "presence_penalty": 0.0,
                    "stream": True,
                    "n": 1,
                },
                "optimal_quantization": "int4",        # AMD Ryzen AI 最佳量化級別
                "max_model_size": "4GB",               # 最大模型大小
                "concurrent_models": 2,                # 同時運行模型數
                "use_hybrid_inference": True,          # 使用混合推理 (CPU+GPU+NPU)
            }
        else:
            return {
                "recommended_models": [
                    {
                        "name": "Llama-3.2-1B-Instruct",
                        "model_id": "Llama-3.2-1B-Instruct",
                        "repo_id": "meta-llama/Llama-3.2-1B-Instruct",
                        "description": "輕量級模型，適合普通硬件",
                        "size": "2.5GB",
                        "performance": "good",
                        "recommended": True,
                        "quantization": "fp16",
                        "format": "gguf",
                        "supports_chat": True,
                        "supports_streaming": True,
                    }
                ],
                "default_params": {
                    "max_tokens": 1024,
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "frequency_penalty": 0.0,
                    "presence_penalty": 0.0,
                    "stream": False,
                    "n": 1,
                },
                "optimal_quantization": "q4_0",
                "max_model_size": "4GB",
                "concurrent_models": 1,
                "use_hybrid_inference": False,
            }
    
    def get_inference_config(self) -> Dict[str, Any]:
        """獲取推理配置 (OpenAI API 格式)"""
        model_config = self.get_model_config()
        
        if self.is_amd_platform:
            return {
                # AMD Ryzen AI 混合推理配置
                "inference_mode": "hybrid",            # hybrid (CPU+GPU+NPU), gpu, cpu
                "use_npu": True,                       # 使用 NPU 加速
                "npu_priority": "high",                # NPU 優先級
                "gpu_memory_fraction": 0.8,            # GPU 記憶體使用比例
                "cpu_threads": 8,                      # CPU 線程數
                "enable_tensor_parallelism": True,     # 張量並行
                "precision": "int4",                   # 精度模式
                "enable_kv_cache": True,               # KV 緩存
                "kv_cache_size": 2048,                 # KV 緩存大小
                **model_config,
            }
        else:
            return {
                "inference_mode": "cpu",
                "use_npu": False,
                "cpu_threads": 4,
                "precision": "fp16",
                "enable_kv_cache": True,
                "kv_cache_size": 1024,
                **model_config,
            }
    
    def get_performance_config(self) -> Dict[str, Any]:
        """獲取性能優化配置"""
        if self.is_amd_platform:
            return {
                "enable_profiling": False,              # 性能分析
                "memory_optimization": "aggressive",    # 記憶體優化級別
                "compute_optimization": "performance",  # 計算優化模式
                "power_mode": "balanced",               # 電源模式
                "thermal_management": "auto",           # 熱管理
                "cache_policy": "adaptive",             # 緩存策略
                "prefetch_enabled": True,               # 預取啟用
                "async_execution": True,                # 異步執行
                "pipeline_stages": 3,                   # 流水線階段數
            }
        else:
            return {
                "enable_profiling": False,
                "memory_optimization": "normal",
                "compute_optimization": "balanced",
                "power_mode": "balanced",
                "cache_policy": "normal",
                "prefetch_enabled": False,
                "async_execution": False,
                "pipeline_stages": 1,
            }
    
    def get_model_download_info(self, model_name: str) -> Optional[Dict[str, Any]]:
        """獲取模型下載信息"""
        models = self.get_model_config()["recommended_models"]
        
        for model in models:
            if model["name"] == model_name or model.get("model_id") == model_name:
                return {
                    "name": model["name"],
                    "model_id": model.get("model_id", model["name"]),
                    "repo_id": model["repo_id"],
                    "size": model["size"],
                    "quantization": model["quantization"],
                    "format": model["format"],
                    "download_url": f"https://huggingface.co/{model['repo_id']}",
                    "local_path": f"ai_models/{model['name']}",
                    "supports_chat": model.get("supports_chat", True),
                    "supports_streaming": model.get("supports_streaming", True),
                }
        
        return None
    
    def validate_environment(self) -> Dict[str, bool]:
        """驗證 AMD Ryzen AI 環境"""
        validation = {
            "amd_platform_detected": self.is_amd_platform,
            "openai_api_configured": bool(self.openai_base_url),
            "python_version_compatible": True,  # Python 3.8+
        }
        
        # 檢查必要的環境變量
        if self.is_amd_platform:
            validation["openai_base_url_set"] = bool(self.openai_base_url)
            validation["openai_api_key_set"] = bool(self.openai_api_key)
        
        return validation
    
    def get_platform_info_summary(self) -> str:
        """獲取平台信息摘要"""
        info = [
            "=" * 60,
            "AMD Ryzen AI 平台配置 (OpenAI 相容 API)",
            "=" * 60,
            f"系統: {self.platform_info['system']}",
            f"架構: {self.platform_info['machine']}",
            f"處理器: {self.platform_info['processor']}",
            f"AMD 平台: {'是' if self.is_amd_platform else '否'}",
            f"OpenAI API Base URL: {self.openai_base_url}",
            f"API Key: {'已設定' if self.openai_api_key else '未設定'}",
            "=" * 60,
        ]
        
        return "\n".join(info)

# 全局配置實例
amd_config = AMDRyzenAIConfig()

# 啟動時輸出平台信息
if __name__ == "__main__":
    logger.info(amd_config.get_platform_info_summary())
    logger.info(f"環境驗證: {amd_config.validate_environment()}")
