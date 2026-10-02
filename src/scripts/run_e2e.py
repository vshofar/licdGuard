import os
import sys
import time
import subprocess
from dotenv import load_dotenv

load_dotenv()

# Garante que a raiz do projeto esteja no PYTHONPATH
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.database.neo4j_client import Neo4jClient
from src.main import run_pipeline_live

# Dados de uma licitação pública real mantida no PNCP para validação
REAL_TEST_CNPJ = "00394460000141"
REAL_TEST_ANO = 2024
REAL_TEST_SEQ = 1

CONTAINER_NAME = "licitguard-neo4j-e2e"
NEO4J_IMAGE = "neo4j:5.18.0"


def ensure_docker_container():
    """Garante que o container Docker do Neo4j esteja rodando."""
    print(f"🐳 Verificando status do container Docker '{CONTAINER_NAME}'...")

    # 1. Verifica se o container já está rodando
    check_running = subprocess.run(
        ["docker", "ps", "-q", "-f", f"name={CONTAINER_NAME}"],
        capture_output=True, text=True
    )
    if check_running.stdout.strip():
        print(f"✅ Container '{CONTAINER_NAME}' já está em execução.")
        return

    # 2. Verifica se o container existe, mas está parado
    check_exists = subprocess.run(
        ["docker", "ps", "-a", "-q", "-f", f"name={CONTAINER_NAME}"],
        capture_output=True, text=True
    )
    if check_exists.stdout.strip():
        print(f"🔄 Iniciando container existente '{CONTAINER_NAME}'...")
        subprocess.run(["docker", "start", CONTAINER_NAME], check=True)
        return

    # 3. Se não existir, cria e inicia o container
    print(f"🚀 Criando e iniciando novo container Docker para o Neo4j...")
    subprocess.run([
        "docker", "run", "-d",
        "--name", CONTAINER_NAME,
        "-p", "7474:7474",
        "-p", "7687:7687",
        "-e", "NEO4J_AUTH=neo4j/password",
        NEO4J_IMAGE
    ], check=True)
    print(f"✅ Container '{CONTAINER_NAME}' criado com sucesso.")


def wait_for_neo4j(uri, user, password, max_retries=15, delay=3) -> bool:
    """Aguarda até que o banco de dados aceite conexões (Warm-up)."""
    print("⏳ Aguardando o Neo4j inicializar...")
    for i in range(max_retries):
        try:
            client = Neo4jClient(uri, user, password)
            client.connect()
            client.close()
            print("⚡ Neo4j está pronto para receber consultas!")
            return True
        except Exception:
            time.sleep(delay)
    return False


def run_e2e_test():
    print("🚀 [E2E Automation] Iniciando automação do teste real...")

    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "password")

    if not os.getenv("GEMINI_API_KEY"):
        print("❌ Erro: Variável GOOGLE_API_KEY não configurada no .env ou ambiente.")
        sys.exit(1)

    try:
        ensure_docker_container()

        if not wait_for_neo4j(uri, user, password):
            print("❌ Erro: Tempo limite excedido aguardando o Neo4j.")
            sys.exit(1)

        print(f"🔄 Executando consulta real no PNCP ({REAL_TEST_CNPJ}/{REAL_TEST_ANO}-{REAL_TEST_SEQ})...")
        result = run_pipeline_live(REAL_TEST_CNPJ, REAL_TEST_ANO, REAL_TEST_SEQ)

        if not result or "report" not in result or not result["report"]:
            print("❌ Teste E2E falhou: O relatório gerado veio vazio.")
            sys.exit(1)

        print("\n" + "=" * 60)
        print("🎉 TESTE E2E REAL CONCLUÍDO COM SUCESSO!")
        print("=" * 60)

    except Exception as e:
        print(f"❌ Falha durante a execução do teste E2E: {e}")
        sys.exit(1)


if __name__ == "__main__":
    run_e2e_test()