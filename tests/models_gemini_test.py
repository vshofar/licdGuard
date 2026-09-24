import pytest
from config import GEMINI_API_KEY
from google import genai


@pytest.mark.skipif(not GEMINI_API_KEY, reason="GEMINI_API_KEY not set")
def test_gemini_models():
    client = genai.Client(api_key=GEMINI_API_KEY)

    print("🔍 Gemini models available in your key:\n")
    models = []
    for model in client.models.list():
        if "generateContent" in getattr(model, "supported_actions", []):
            models.append(model.name)
            print(f" • {model.name}")
    
    assert len(models) > 0, "No Gemini models found"