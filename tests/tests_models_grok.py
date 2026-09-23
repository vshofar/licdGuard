from config import GROQ_API_KEY
from groq import Groq

if not GROQ_API_KEY:
    print("❌ GROQ_API_KEY não foi encontrada nas variáveis de ambiente.")
else:
    try:
        client = Groq(api_key=GROQ_API_KEY)
        models = client.models.list()

        print("✅ Conexão bem-sucedida! Modelos disponíveis na sua chave Groq:\n")
        for model in models.data:
            print(f" • {model.id}")

    except Exception as e:
        print(f"❌ Erro ao listar modelos: {e}")