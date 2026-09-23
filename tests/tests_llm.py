import os
import time

from dotenv import load_dotenv
from google import genai
from groq import Groq

load_dotenv()

groq_key = os.getenv("GROQ_API_KEY")
gemini_key = os.getenv("GEMINI_API_KEY")

print("🔍 Checando Chaves de API:")
print(f" - GROQ_API_KEY: {'✅ Carregada' if groq_key else '❌ Não encontrada'}")
print(f" - GEMINI_API_KEY: {'✅ Carregada' if gemini_key else '❌ Não encontrada'}\n")

def testar_groq():
    print("🚀 Testando Groq (llama-3.3-70b-versatile)...")
    client = Groq(api_key=groq_key)

    prompt = (
        "Analise a seguinte situação em uma licitação: "
        "Duas empresas concorrentes (Empresa A e Empresa B) enviaram propostas com diferença de R$ 10,00 "
        "e ambas possuem o mesmo endereço fiscal cadastrado."
    )

    inicio = time.time()
    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1
    )
    tempo = (time.time() - inicio) * 1000

    print(f"⚡ Resposta da Groq em {tempo:.2f} ms:")
    print(response.choices[0].message.content)
    print("-" * 50)

def testar_gemini():
    print("\n♊ Testando Google Gemini (gemini-2.5-flash)...")
    client = genai.Client(api_key=gemini_key)

    prompt = (
        "Você é um auditor do TCO/CGU. Redija uma nota técnica prévia "
        "recomendando a suspensão cautelar de um edital sob suspeita de direcionamento."
    )

    inicio = time.time()
    response = client.models.generate_content(
        model="models/gemini-3.5-flash-lite",
        contents=prompt,
    )
    tempo = (time.time() - inicio) * 1000

    print(f"⚡ Resposta do Gemini em {tempo:.2f} ms:")
    print(response.text[:300] + "...\n[Texto truncado para exibição]")
    print("-" * 50)

if __name__ == "__main__":
    if groq_key:
        testar_groq()
    if gemini_key:
        testar_gemini()