from lemonade.api import from_pretrained
# from huggingface_hub import snapshot_download

# snapshot_download(
#     repo_id="amd/Qwen2-1.5B-onnx-ryzenai-hybrid",
#     local_dir="./backend/ai_models/Qwen2-1.5B-onnx-ryzenai-hybrid",
#     local_files_only=False
# )
# 使用 Lemonade SDK 載入 AMD ONNX 模型
model, tokenizer = from_pretrained("Qwen2-1.5B-onnx-ryzenai-hybrid", recipe="oga-hybrid")

def generate_response(prompt):
    input_ids = tokenizer(prompt, return_tensors="pt").input_ids
    response = model.generate(input_ids, max_new_tokens=512)
    return tokenizer.decode(response[0])

if __name__ == "__main__":
    prompt = "請簡短介紹一下宜蘭頭城的觀光特色"
    print(generate_response(prompt))

# lemonade-server run Phi-3-Mini-Instruct-Hybrid --port 9000
# lemonade-server serve
 
'''
from lemonade.api import from_pretrained

model, tokenizer = from_pretrained("amd/Llama-3.2-1B-Instruct-awq-g128-int4-asym-fp16-onnx-hybrid", recipe="oga-hybrid")

input_ids = tokenizer("This is my prompt", return_tensors="pt").input_ids
response = model.generate(input_ids, max_new_tokens=30)

print(tokenizer.decode(response[0]))
'''