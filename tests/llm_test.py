import time
import pytest
from config import GROQ_API_KEY, GEMINI_API_KEY
from google import genai
from groq import Groq


@pytest.mark.skipif(not GROQ_API_KEY, reason="GROQ_API_KEY not set")
def test_groq():
    print("🚀 Testing Groq (llama-3.3-70b-versatile)...")
    client = Groq(api_key=GROQ_API_KEY)

    prompt = (
        "Analise a seguinte situação em uma licitação: "
        "Duas empresas concorrentes (Empresa A e Empresa B) enviaram propostas com diferença de R$ 10,00 "
        "e ambas possuem o mesmo endereço fiscal cadastrado."
    )

    start = time.time()
    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1
    )
    elapsed_time = (time.time() - start) * 1000

    print(f"⚡ Groq response in {elapsed_time:.2f} ms:")
    print(response.choices[0].message.content)
    print("-" * 50)

    assert response.choices[0].message.content is not None


@pytest.mark.skipif(not GEMINI_API_KEY, reason="GEMINI_API_KEY not set")
def test_gemini():
    print("\n♊ Testing Google Gemini (gemini-2.5-flash)...")
    client = genai.Client(api_key=GEMINI_API_KEY)

    prompt = (
        "Você é um auditor do TCO/CGU. Redija uma nota técnica prévia "
        "recomendando a suspensão cautelar de um edital sob suspeita de direcionamento."
    )

    start = time.time()
    response = client.models.generate_content(
        model="models/gemini-3.5-flash-lite",
        contents=prompt,
    )
    elapsed_time = (time.time() - start) * 1000

    print(f"⚡ Gemini response in {elapsed_time:.2f} ms:")
    print(response.text[:300] + "...\n[Texto truncado para exibição]")
    print("-" * 50)

    assert response.text is not None