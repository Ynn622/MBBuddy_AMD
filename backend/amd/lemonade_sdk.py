from lemonade.api import from_pretrained
from huggingface_hub import snapshot_download

snapshot_download(
    repo_id="amd/Llama-3.2-1B-Instruct-awq-g128-int4-asym-fp16-onnx-hybrid",
    local_dir="./ai_model",
    local_files_only=False
)

# 使用 Lemonade SDK 載入 AMD ONNX 模型
model, tokenizer = from_pretrained("./ai_model", recipe="oga-hybrid")

def generate_response(prompt):
    input_ids = tokenizer(prompt, return_tensors="pt").input_ids
    response = model.generate(input_ids, max_new_tokens=512)
    return tokenizer.decode(response[0])

if __name__ == "__main__":
    prompt = "請簡短介紹一下宜蘭頭城的觀光特色"
    print(generate_response(prompt))