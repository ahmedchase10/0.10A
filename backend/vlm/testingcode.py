import os
import requests
from dotenv import load_dotenv

load_dotenv()

HF_TOKEN = os.getenv("HF_TOKEN")

API_URL = "https://dtujvjpyjnyev6ou.us-east-1.aws.endpoints.huggingface.cloud/v1/chat/completions"

headers = {
    "Authorization": f"Bearer {HF_TOKEN}",
    "Content-Type": "application/json"
}

payload = {
    "model": "Qwen/Qwen3.6-35B-A3B-FP8",
    "messages": [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "What is in this image? Describe it clearly."},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "https://images.unsplash.com/photo-1501785888041-af3ef285b470"
                    }
                }
            ]
        }
    ],
    "max_tokens": 1000,
    "temperature": 0.7,
"extra_body": {
        "chat_template_kwargs": {
            "enable_thinking": False
        }
    }
}

response = requests.post(API_URL, headers=headers, json=payload)

print("STATUS:", response.status_code)
print("RAW:", response.text)
data = response.json()

if "choices" in data:
    print(data["choices"][0]["message"]["content"])
else:
    print("No choices returned:", data)
