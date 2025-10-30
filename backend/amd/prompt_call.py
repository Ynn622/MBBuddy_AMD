from openai import OpenAI

# 初始化 Lemonade Server
client = OpenAI(
    base_url="http://localhost:9000/api/v1",
    api_key="lemonade"  # required but unused
)

completion = client.chat.completions.create(
    model="Llama-3.2-1B-Instruct-awq-g128-int4-asym-fp16-onnx-hybrid",  # or any other available model
    messages=[
        {"role": "user", "content": "What is the capital of France?"}
    ]
)

# Print the response
print(completion.choices[0].message.content)

# lemonade-server-dev run backend/ai_model/Llama-3.2-1B-Instruct-awq-g128-int4-asym-fp16-onnx-hybrid --port 9000