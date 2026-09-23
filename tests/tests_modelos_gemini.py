import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

print("🔍 Modelos Gemini disponíveis na sua chave:\n")
for model in client.models.list():
    if "generateContent" in getattr(model, "supported_actions", []):
        print(f" • {model.name}")