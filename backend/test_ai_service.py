"""
測試統一 AI 服務
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utility.call_ai import ai_service

async def test_lemonade_mode():
    """測試 Lemonade 模式"""
    print("\n=== 測試 Lemonade 模式 ===")
    
    # 確認預設是 Lemonade 模式
    config = ai_service.get_config()
    print(f"當前配置: {config}")
    
    try:
        # 測試生成
        response = await ai_service.generate_async(
            prompt="請用一句話介紹你自己",
            max_tokens=50
        )
        print(f"回應: {response}")
        print("✅ Lemonade 模式測試成功")
    except Exception as e:
        print(f"❌ Lemonade 模式測試失敗: {e}")

async def test_openai_mode():
    """測試 OpenAI 模式"""
    print("\n=== 測試 OpenAI 模式切換 ===")
    
    # 讀取 API Key (需要設定環境變數或直接提供)
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print("⚠️  未設定 OPENAI_API_KEY，跳過 OpenAI 測試")
        return
    
    try:
        # 切換到 OpenAI 模式
        ai_service.set_mode(
            mode="openai",
            api_key=api_key,
            model="gpt-4o-mini"
        )
        
        config = ai_service.get_config()
        print(f"切換後配置: {config}")
        
        # 測試生成
        response = await ai_service.generate_async(
            prompt="請用一句話介紹你自己",
            max_tokens=50
        )
        print(f"回應: {response}")
        print("✅ OpenAI 模式測試成功")
        
        # 切回 Lemonade 模式
        ai_service.set_mode(mode="lemonade")
        print("已切回 Lemonade 模式")
        
    except Exception as e:
        print(f"❌ OpenAI 模式測試失敗: {e}")

async def main():
    print("開始測試統一 AI 服務...")
    
    # 測試 Lemonade 模式
    await test_lemonade_mode()
    
    # 測試 OpenAI 模式
    await test_openai_mode()
    
    print("\n測試完成！")

if __name__ == "__main__":
    asyncio.run(main())
