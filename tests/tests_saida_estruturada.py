import os
import time
from dotenv import load_dotenv
from groq import Groq
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

# Carregar variáveis do .env ou ~/.bashrc
load_dotenv()

groq_key = os.getenv("GROQ_API_KEY")
gemini_key = os.getenv("GEMINI_API_KEY")

# 1. Definição do Schema Pydantic para Saída Estruturada
class DiagnosticoFraude(BaseModel):
    nivel_de_risco: str = Field(description="Nível de risco: BAIXO, MEDIO, ALTO ou CRITICO")
    tipologia_fraude: str = Field(description="Ex: Cartel, Sociedade Oculta, Rodízio ou Regular")
    cnpjs_suspeitos: list[str] = Field(description="Lista de CNPJs identificados no padrão")
    resumo_evidencias: str = Field(description="Breve explicação técnica da evidência encontrada")


# 2. Teste da Groq com Saída JSON Estruturada
def testar_groq_estruturado():
    print("🚀 Testando Groq com Saída Estruturada (Pydantic)...")
    client = Groq(api_key=groq_key)

    prompt = (
        "Analise os dados desta licitação e retorne OBRIGATORIAMENTE um JSON válido com o diagnóstico:\n"
        "Licitação: 102/2026 - Obra Viária\n"
        "Proponente 1: Alfa Engenharia (CNPJ: 11.111.111/0001-11) - Valor: R$ 500.000,00\n"
        "Proponente 2: Beta Construções (CNPJ: 22.222.222/0001-22) - Valor: R$ 500.010,00\n"
        "Nota: Ambos os CNPJs compartilham o mesmo endereço e contador responsável."
    )

    try:
        inicio = time.time()
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
                    "name": "diagnostico_fraude",
                    "schema": DiagnosticoFraude.model_json_schema()
                }
            },
            temperature=0.1
        )
        tempo = (time.time() - inicio) * 1000

        # Parse e Validação com Pydantic
        raw_json = response.choices[0].message.content
        objeto_validado = DiagnosticoFraude.model_validate_json(raw_json)

        print(f"⚡ Sucesso Groq em {tempo:.2f} ms!")
        print(f" - Risco Detectado: {objeto_validado.nivel_de_risco}")
        print(f" - Tipologia: {objeto_validado.tipologia_fraude}")
        print(f" - CNPJs Suspeitos: {objeto_validado.cnpjs_suspeitos}")
        print(f" - Evidência: {objeto_validado.resumo_evidencias}\n")

    except Exception as e:
        print(f"❌ Erro no teste estruturado da Groq: {e}\n")


# 3. Teste do Gemini com Structured Output Nativo
def testar_gemini_estruturado():
    print("♊ Testando Gemini com Structured Output Nativo (Pydantic)...")
    client = genai.Client(api_key=gemini_key)

    prompt = (
        "Analise esta licitação:\n"
        "Empresa A (CNPJ 33.333.333/0001-33) venceu 12 licitações seguidas na mesma prefeitura, "
        "sempre com a Empresa B desistindo na fase de lances sem apresentar contraproposta."
    )

    # Lista de modelos por prioridade
    modelos = ["models/gemini-3.5-flash-lite"]

    for modelo in modelos:
        try:
            inicio = time.time()
            # Passamos o Schema Pydantic diretamente na configuração da requisição
            response = client.models.generate_content(
                model=modelo,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=DiagnosticoFraude,
                    temperature=0.1
                )
            )
            tempo = (time.time() - inicio) * 1000

            # Validação do resultado retornado
            objeto_validado = DiagnosticoFraude.model_validate_json(response.text)

            print(f"⚡ Sucesso Gemini ({modelo}) em {tempo:.2f} ms!")
            print(f" - Risco Detectado: {objeto_validado.nivel_de_risco}")
            print(f" - Tipologia: {objeto_validado.tipologia_fraude}")
            print(f" - Resumo: {objeto_validado.resumo_evidencias}\n")
            return

        except Exception as e:
            print(f"⚠️ Tentativa com {modelo} falhou: {e}")


if __name__ == "__main__":
    testar_groq_estruturado()
    testar_gemini_estruturado()