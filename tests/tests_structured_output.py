import time
from config import GROQ_API_KEY, GEMINI_API_KEY
from groq import Groq
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

# 1. Definição do Schema Pydantic para Saída Estruturada
class FraudDiagnosis(BaseModel):
    risk_level: str = Field(description="Nível de risco: BAIXO, MEDIO, ALTO ou CRITICO")
    fraud_typology: str = Field(description="Ex: Cartel, Sociedade Oculta, Rodízio ou Regular")
    suspicious_cnpjs: list[str] = Field(description="Lista de CNPJs identificados no padrão")
    evidence_summary: str = Field(description="Breve explicação técnica da evidência encontrada")


# 2. Teste da Groq com Saída JSON Estruturada
def test_groq_structured():
    print("🚀 Testando Groq com Saída Estruturada (Pydantic)...")
    client = Groq(api_key=GROQ_API_KEY)

    prompt = (
        "Analise os dados desta licitação e retorne OBRIGATORIAMENTE um JSON válido com o diagnóstico:\n"
        "Licitação: 102/2026 - Obra Viária\n"
        "Proponente 1: Alfa Engenharia (CNPJ: 11.111.111/0001-11) - Valor: R$ 500.000,00\n"
        "Proponente 2: Beta Construções (CNPJ: 22.222.222/0001-22) - Valor: R$ 500.010,00\n"
        "Nota: Ambos os CNPJs compartilham o mesmo endereço e contador responsável."
    )

    try:
        start = time.time()
        # Forçamos a resposta em formato JSON na Groq
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "system", "content": "Você é um auditor de dados. Responda APENAS em JSON no formato do schema."},
                {"role": "user", "content": prompt}
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "fraud_diagnosis",
                    "schema": FraudDiagnosis.model_json_schema()
                }
            },
            temperature=0.1
        )
        elapsed_time = (time.time() - start) * 1000

        # Parse e Validação com Pydantic
        raw_json = response.choices[0].message.content
        validated_object = FraudDiagnosis.model_validate_json(raw_json)

        print(f"⚡ Sucesso Groq em {elapsed_time:.2f} ms!")
        print(f" - Risco Detectado: {validated_object.risk_level}")
        print(f" - Tipologia: {validated_object.fraud_typology}")
        print(f" - CNPJs Suspeitos: {validated_object.suspicious_cnpjs}")
        print(f" - Evidência: {validated_object.evidence_summary}\n")

    except Exception as e:
        print(f"❌ Erro no teste estruturado da Groq: {e}\n")


# 3. Teste do Gemini com Structured Output Nativo
def test_gemini_structured():
    print("♊ Testando Gemini com Structured Output Nativo (Pydantic)...")
    client = genai.Client(api_key=GEMINI_API_KEY)

    prompt = (
        "Analise esta licitação:\n"
        "Empresa A (CNPJ 33.333.333/0001-33) venceu 12 licitações seguidas na mesma prefeitura, "
        "sempre com a Empresa B desistindo na fase de lances sem apresentar contraproposta."
    )

    # Lista de modelos por prioridade
    models = ["models/gemini-3.5-flash-lite"]

    for model in models:
        try:
            start = time.time()
            # Passamos o Schema Pydantic diretamente na configuração da requisição
            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=FraudDiagnosis,
                    temperature=0.1
                )
            )
            elapsed_time = (time.time() - start) * 1000

            # Validação do resultado retornado
            validated_object = FraudDiagnosis.model_validate_json(response.text)

            print(f"⚡ Sucesso Gemini ({model}) em {elapsed_time:.2f} ms!")
            print(f" - Risco Detectado: {validated_object.risk_level}")
            print(f" - Tipologia: {validated_object.fraud_typology}")
            print(f" - Resumo: {validated_object.evidence_summary}\n")
            return

        except Exception as e:
            print(f"⚠️ Tentativa com {model} falhou: {e}")


if __name__ == "__main__":
    test_groq_structured()
    test_gemini_structured()