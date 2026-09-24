import pytest
from config import GROQ_API_KEY
from groq import Groq


@pytest.mark.skipif(not GROQ_API_KEY, reason="GROQ_API_KEY not set")
def test_groq_models():
    client = Groq(api_key=GROQ_API_KEY)
    models = client.models.list()

    print("✅ Connection successful! Groq models available in your key:\n")
    model_ids = []
    for model in models.data:
        model_ids.append(model.id)
        print(f" • {model.id}")

    assert len(model_ids) > 0, "No Groq models found"