import os
from dotenv import load_dotenv
from groq import Groq

# Carrega as variáveis de ambiente (.env ou ~/.bashrc)
load_dotenv()

groq_key = os.getenv("GROQ_API_KEY")

if not groq_key:
    print("❌ GROQ_API_KEY não foi encontrada nas variáveis de ambiente.")
else:
    try:
        client = Groq(api_key=groq_key)
        models = client.models.list()

        print("✅ Conexão bem-sucedida! Modelos disponíveis na sua chave Groq:\n")
        for model in models.data:
            print(f" • {model.id}")

    except Exception as e:
        print(f"❌ Erro ao listar modelos: {e}")