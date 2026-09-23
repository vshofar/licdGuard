from config import GEMINI_API_KEY
from google import genai

client = genai.Client(api_key=GEMINI_API_KEY)

print("🔍 Modelos Gemini disponíveis na sua chave:\n")
for model in client.models.list():
    if "generateContent" in getattr(model, "supported_actions", []):
        print(f" • {model.name}")