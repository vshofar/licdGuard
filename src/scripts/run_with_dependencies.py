import asyncio
import sys
import subprocess

from config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD
from database.neo4j_client import Neo4jClient
from services.audit_pipeline_service import AuditPipeline


def ensure_neo4j_container():
    container_name = "licitguard-neo4j"
    
    try:
        result = subprocess.run(
            ["docker", "inspect", "-f", "{{.State.Running}}", container_name],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0 and result.stdout.strip() == "true":
            print(f"✅ Container {container_name} já está rodando")
            return
    except subprocess.CalledProcessError:
        pass
    
    print(f"🐳 Iniciando container Neo4j...")
    cmd = [
        "docker", "run", "-d",
        "--name", container_name,
        "-p", "7474:7474",
        "-p", "7687:7687",
        "-e", f"NEO4J_AUTH=neo4j/{NEO4J_PASSWORD}",
        "neo4j:5"
    ]
    
    subprocess.run(cmd, check=True)
    print(f"✅ Container {container_name} iniciado")
    print("⏳ Aguardando Neo4j iniciar...")
    import time
    time.sleep(15)


async def main():

    tender_id = "15301505000012024"

    ensure_neo4j_container()

    print(f"🔗 Conectando ao Neo4j em: {NEO4J_URI}")
    print(f"🌐 Neo4j Browser: {NEO4J_URI.replace('bolt://', 'http://').replace(':7687', ':7474')}")
    print(f"🔑 Usuário: {NEO4J_USER}")

    neo4j_client = Neo4jClient(uri=NEO4J_URI, user=NEO4J_USER, password=NEO4J_PASSWORD)

    try:
        neo4j_client.connect()
        print("✅ Conectado ao Neo4j")

        pipeline = AuditPipeline(neo4j_client=neo4j_client)

        print(f"🚀 Executando pipeline com dados reais para tender_id: {tender_id}")
        print("⚠️  Este script fará chamadas reais às APIs (ComprasNet e BrasilAPI)")
        print()

        result = await pipeline.run(tender_id)

        print("\n" + "=" * 50)
        print("📊 RESULTADO DA AUDITORIA")
        print("=" * 50)
        print(f"Tender ID: {result['tender_id']}")
        print(f"Risk Score: {result['risk_score']}/100")
        print("\nAlertas:")
        print(f"  - Sócios em comum: {len(result['alerts']['shared_partners'])}")
        print(f"  - Endereços compartilhados: {len(result['alerts']['matching_addresses'])}")
        print(f"  - Empresas recentes com alto valor: {len(result['alerts']['recent_companies_high_value'])}")

        print("✅ Teste concluído com sucesso")
        print("\n⏸️  Pressione Enter para fechar a conexão e destruir o container...")
        input()

    except Exception as e:
        print(f"❌ Erro durante a execução: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        neo4j_client.close()
        print("🔌 Conexão com Neo4j fechada")

if __name__ == "__main__":
    asyncio.run(main())
