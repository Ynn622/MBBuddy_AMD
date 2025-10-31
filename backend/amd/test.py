from lemonade.api import get_device_info
print(get_device_info())

# import onnxruntime as ort

# print("ONNX Runtime 版本:", ort.__version__)
# print("\n可用的執行提供者 (Execution Providers):")
# providers = ort.get_available_providers()
# for provider in providers:
#     print(f"  - {provider}")

# # 檢查 DirectML (用於 AMD NPU/GPU)
# if 'DmlExecutionProvider' in providers:
#     print("\n✓ DirectML 可用 - 可以使用 AMD NPU/GPU 加速")
# else:
#     print("\n✗ DirectML 不可用 - 需要安裝 DirectML 支援")

# # 測試 NPU session
# try:
#     import numpy as np
#     # 創建簡單的測試模型
#     sess_options = ort.SessionOptions()
#     print("\n✓ ONNX Runtime 基本功能正常")
# except Exception as e:
#     print(f"\n✗ 錯誤: {e}")