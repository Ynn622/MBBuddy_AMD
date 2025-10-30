"""
AMD Ryzen AI 平台優化配置
針對 AMD Ryzen AI PC 的 AI 推理優化
使用 AMD 的 CPU+GPU 及 Lemonade Server
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
        
        # Lemonade Server 配置
        self.lemonade_base_url = os.getenv("LEMONADE_SERVER_URL", "http://localhost:8080")
        self.lemonade_api_key = os.getenv("LEMONADE_API_KEY", "")
        
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
    
    def get_lemonade_config(self) -> Dict[str, Any]:
        """獲取 Lemonade Server 配置"""
        if self.is_amd_platform:
            return {
                "base_url": self.lemonade_base_url,
                "api_key": self.lemonade_api_key,
                "max_concurrent_requests": 8,      # AMD Ryzen AI 可同時處理多個請求
                "request_timeout": 30.0,           # 請求超時（秒）
                "retry_attempts": 3,               # 重試次數
                "connection_pool_size": 16,        # 連接池大小
                "enable_batching": True,           # 啟用批處理
                "batch_size": 4,                   # 批處理大小
                "optimization_level": "high",      # 優化級別
                "enable_caching": True,            # 啟用結果緩存
                "cache_ttl": 600,                  # 緩存生存時間（秒）
                "use_gpu_acceleration": True,      # 使用 GPU 加速
                "npu_enabled": True,               # 啟用 NPU (如果可用)
            }
        else:
            # 通用配置
            return {
                "base_url": self.lemonade_base_url,
                "api_key": self.lemonade_api_key,
                "max_concurrent_requests": 4,
                "request_timeout": 30.0,
                "retry_attempts": 2,
                "connection_pool_size": 8,
                "enable_batching": False,
                "optimization_level": "medium",
                "enable_caching": True,
                "cache_ttl": 300,
                "use_gpu_acceleration": False,
                "npu_enabled": False,
            }
    
    def get_model_config(self) -> Dict[str, Any]:
        """獲取推薦的 AMD 優化模型配置"""
        if self.is_amd_platform:
            return {
                # AMD Ryzen AI 推薦模型（INT4 量化）
                "recommended_models": [
                    {
                        "name": "Llama-3.2-1B-Instruct-int4",
                        "repo_id": "amd/Llama-3.2-1B-Instruct-onnx-ryzen-strix",
                        "description": "Llama 3.2 1B INT4 量化，針對 AMD Ryzen AI 優化",
                        "size": "1.2GB",
                        "performance": "excellent",
                        "recommended": True,
                        "quantization": "int4",
                        "format": "onnx"
                    },
                    {
                        "name": "Llama-3.2-3B-Instruct-int4",
                        "repo_id": "amd/Llama-3.2-3B-Instruct-onnx-ryzen-strix",
                        "description": "Llama 3.2 3B INT4 量化，更強大的推理能力",
                        "size": "2.8GB",
                        "performance": "excellent",
                        "recommended": True,
                        "quantization": "int4",
                        "format": "onnx"
                    },
                    {
                        "name": "Phi-3.5-mini-instruct-int4",
                        "repo_id": "microsoft/Phi-3.5-mini-instruct",
                        "description": "Microsoft Phi-3.5 Mini INT4，輕量級高效模型",
                        "size": "2.5GB",
                        "performance": "very_good",
                        "recommended": True,
                        "quantization": "int4",
                        "format": "onnx"
                    },
                    {
                        "name": "Qwen2.5-1.5B-Instruct-int4",
                        "repo_id": "Qwen/Qwen2.5-1.5B-Instruct",
                        "description": "Qwen2.5 1.5B INT4 量化版本",
                        "size": "1.5GB",
                        "performance": "good",
                        "recommended": False,
                        "quantization": "int4",
                        "format": "onnx"
                    }
                ],
                "optimal_quantization": "int4",        # AMD Ryzen AI 最佳量化級別
                "max_model_size": "4GB",               # 最大模型大小
                "concurrent_models": 2,                # 同時運行模型數
                "use_hybrid_inference": True,          # 使用混合推理 (CPU+GPU+NPU)
                "max_tokens": 2048,                    # 最大生成 tokens
                "temperature": 0.7,
                "top_p": 0.9,
                "top_k": 40,
                "repeat_penalty": 1.1,
            }
        else:
            return {
                "recommended_models": [
                    {
                        "name": "Llama-3.2-1B-Instruct",
                        "repo_id": "meta-llama/Llama-3.2-1B-Instruct",
                        "description": "輕量級模型，適合普通硬件",
                        "size": "2.5GB",
                        "performance": "good",
                        "recommended": True,
                        "quantization": "fp16",
                        "format": "gguf"
                    }
                ],
                "optimal_quantization": "q4_0",
                "max_model_size": "4GB",
                "concurrent_models": 1,
                "use_hybrid_inference": False,
                "max_tokens": 1024,
                "temperature": 0.7,
                "top_p": 0.9,
                "top_k": 40,
                "repeat_penalty": 1.1,
            }
    
    def get_inference_config(self) -> Dict[str, Any]:
        """獲取推理配置"""
        model_config = self.get_model_config()
        
        if self.is_amd_platform:
            return {
                # AMD Ryzen AI 混合推理配置
                "inference_mode": "hybrid",            # hybrid (CPU+GPU+NPU), gpu, cpu
                "use_npu": True,                       # 使用 NPU 加速
                "npu_priority": "high",                # NPU 優先級
                "gpu_memory_fraction": 0.8,            # GPU 記憶體使用比例
                "cpu_threads": 8,                      # CPU 線程數
                "batch_size": 4,                       # 批次大小
                "max_batch_delay_ms": 100,             # 最大批次延遲
                "enable_dynamic_batching": True,       # 動態批次處理
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
                "batch_size": 1,
                "enable_dynamic_batching": False,
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
            if model["name"] == model_name:
                return {
                    "name": model["name"],
                    "repo_id": model["repo_id"],
                    "size": model["size"],
                    "quantization": model["quantization"],
                    "format": model["format"],
                    "download_url": f"https://huggingface.co/{model['repo_id']}",
                    "local_path": f"ai_models/{model_name}",
                }
        
        return None
    
    def validate_environment(self) -> Dict[str, bool]:
        """驗證 AMD Ryzen AI 環境"""
        validation = {
            "amd_platform_detected": self.is_amd_platform,
            "lemonade_server_configured": bool(self.lemonade_base_url),
            "python_version_compatible": True,  # Python 3.8+
        }
        
        # 檢查必要的環境變量
        if self.is_amd_platform:
            validation["lemonade_server_url_set"] = bool(self.lemonade_base_url)
        
        return validation
    
    def get_platform_info_summary(self) -> str:
        """獲取平台信息摘要"""
        info = [
            "=" * 60,
            "AMD Ryzen AI 平台配置",
            "=" * 60,
            f"系統: {self.platform_info['system']}",
            f"架構: {self.platform_info['machine']}",
            f"處理器: {self.platform_info['processor']}",
            f"AMD 平台: {'是' if self.is_amd_platform else '否'}",
            f"Lemonade Server: {self.lemonade_base_url}",
            "=" * 60,
        ]
        
        return "\n".join(info)

# 全局配置實例
amd_config = AMDRyzenAIConfig()

# 啟動時輸出平台信息
if __name__ == "__main__":
    logger.info(amd_config.get_platform_info_summary())
    logger.info(f"環境驗證: {amd_config.validate_environment()}")
