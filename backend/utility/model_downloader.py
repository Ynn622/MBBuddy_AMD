"""
AMD 模型下載器
從 Hugging Face 下載 AMD 優化的 INT4 量化模型
支援 Ryzen AI 工具鏈推薦的模型
"""

import asyncio
from pathlib import Path
from typing import Optional, Dict, Any
from huggingface_hub import snapshot_download, hf_hub_download
from .amd_config import amd_config
from .logger import get_logger

logger = get_logger("mbbuddy.model_downloader")

class AMDModelDownloader:
    """AMD 模型下載器"""
    
    def __init__(self):
        self.models_dir = Path("ai_models")
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.model_config = amd_config.get_model_config()
        
    def get_available_models(self) -> list[Dict[str, Any]]:
        """獲取可用的 AMD 優化模型列表"""
        return self.model_config["recommended_models"]
    
    async def download_model(
        self,
        model_name: str,
        force_download: bool = False
    ) -> Optional[str]:
        """
        下載指定的模型
        
        Args:
            model_name: 模型名稱
            force_download: 是否強制重新下載
            
        Returns:
            模型本地路徑，失敗則返回 None
        """
        # 查找模型配置
        model_info = None
        for model in self.model_config["recommended_models"]:
            if model["name"] == model_name:
                model_info = model
                break
        
        if not model_info:
            logger.error(f"未找到模型: {model_name}")
            logger.info(f"可用模型: {[m['name'] for m in self.model_config['recommended_models']]}")
            return None
        
        model_dir = self.models_dir / model_name
        
        # 檢查是否已存在
        if model_dir.exists() and not force_download:
            logger.info(f"模型已存在: {model_dir}")
            return str(model_dir)
        
        logger.info(f"開始下載模型: {model_name}")
        logger.info(f"倉庫: {model_info['repo_id']}")
        logger.info(f"大小: {model_info['size']}")
        logger.info(f"格式: {model_info['format']}")
        logger.info(f"量化: {model_info['quantization']}")
        
        try:
            # 下載整個模型倉庫
            downloaded_path = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: snapshot_download(
                    repo_id=model_info["repo_id"],
                    local_dir=str(model_dir),
                    local_dir_use_symlinks=False,
                    resume_download=True
                )
            )
            
            logger.info(f"模型下載完成: {downloaded_path}")
            return downloaded_path
            
        except Exception as e:
            logger.error(f"下載模型失敗: {e}")
            return None
    
    async def download_recommended_models(self) -> Dict[str, Optional[str]]:
        """
        下載所有推薦的模型
        
        Returns:
            模型名稱到本地路徑的映射
        """
        results = {}
        recommended = [
            m for m in self.model_config["recommended_models"]
            if m.get("recommended", False)
        ]
        
        logger.info(f"開始下載 {len(recommended)} 個推薦模型")
        
        for model in recommended:
            model_name = model["name"]
            path = await self.download_model(model_name)
            results[model_name] = path
            
            if path:
                logger.info(f"✅ {model_name} 下載成功")
            else:
                logger.error(f"❌ {model_name} 下載失敗")
        
        return results
    
    def get_model_path(self, model_name: str) -> Optional[Path]:
        """
        獲取模型的本地路徑
        
        Args:
            model_name: 模型名稱
            
        Returns:
            模型路徑，如果不存在則返回 None
        """
        model_dir = self.models_dir / model_name
        if model_dir.exists():
            return model_dir
        return None
    
    def list_downloaded_models(self) -> list[str]:
        """列出已下載的模型"""
        if not self.models_dir.exists():
            return []
        
        downloaded = []
        for item in self.models_dir.iterdir():
            if item.is_dir():
                downloaded.append(item.name)
        
        return downloaded
    
    async def verify_model(self, model_name: str) -> bool:
        """
        驗證模型完整性
        
        Args:
            model_name: 模型名稱
            
        Returns:
            模型是否完整有效
        """
        model_path = self.get_model_path(model_name)
        if not model_path:
            return False
        
        # 檢查必要文件
        required_files = ["config.json"]  # 根據實際模型格式調整
        
        for file in required_files:
            file_path = model_path / file
            if not file_path.exists():
                logger.warning(f"缺少必要文件: {file}")
                return False
        
        return True
    
    def get_model_info(self, model_name: str) -> Optional[Dict[str, Any]]:
        """
        獲取模型詳細信息
        
        Args:
            model_name: 模型名稱
            
        Returns:
            模型信息字典
        """
        for model in self.model_config["recommended_models"]:
            if model["name"] == model_name:
                model_path = self.get_model_path(model_name)
                return {
                    **model,
                    "local_path": str(model_path) if model_path else None,
                    "downloaded": model_path is not None,
                }
        return None

# 全局下載器實例
amd_model_downloader = AMDModelDownloader()

# 命令行工具
if __name__ == "__main__":
    import sys
    
    async def main():
        if len(sys.argv) < 2:
            print("用法:")
            print("  python amd_model_downloader.py list          # 列出可用模型")
            print("  python amd_model_downloader.py download <模型名稱>  # 下載指定模型")
            print("  python amd_model_downloader.py download-all  # 下載所有推薦模型")
            print("  python amd_model_downloader.py downloaded    # 列出已下載的模型")
            return
        
        command = sys.argv[1]
        
        if command == "list":
            print("\n可用的 AMD 優化模型:")
            print("=" * 80)
            for model in amd_model_downloader.get_available_models():
                print(f"\n名稱: {model['name']}")
                print(f"倉庫: {model['repo_id']}")
                print(f"描述: {model['description']}")
                print(f"大小: {model['size']}")
                print(f"性能: {model['performance']}")
                print(f"推薦: {'是' if model['recommended'] else '否'}")
                print(f"量化: {model['quantization']}")
                print(f"格式: {model['format']}")
        
        elif command == "download" and len(sys.argv) > 2:
            model_name = sys.argv[2]
            print(f"\n下載模型: {model_name}")
            path = await amd_model_downloader.download_model(model_name)
            if path:
                print(f"✅ 下載成功: {path}")
            else:
                print(f"❌ 下載失敗")
        
        elif command == "download-all":
            print("\n下載所有推薦模型...")
            results = await amd_model_downloader.download_recommended_models()
            print("\n下載結果:")
            for model_name, path in results.items():
                status = "✅" if path else "❌"
                print(f"{status} {model_name}: {path}")
        
        elif command == "downloaded":
            print("\n已下載的模型:")
            downloaded = amd_model_downloader.list_downloaded_models()
            if downloaded:
                for model_name in downloaded:
                    print(f"  - {model_name}")
            else:
                print("  (無)")
        
        else:
            print(f"未知命令: {command}")
    
    asyncio.run(main())
