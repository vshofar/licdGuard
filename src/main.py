import asyncio
import sys
from typing import Any

from config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD
from database.neo4j_client import Neo4jClient
from services.audit_pipeline_service import AuditPipeline


async def main():
    if len(sys.argv) < 2:
        print("Uso: python main.py <tender_id>")
        print("Exemplo: python main.py 16017505900062024")
        sys.exit(1)

    tender_id = sys.argv[1]

    neo4j_client = Neo4jClient(
        uri=NEO4J_URI,
        user=NEO4J_USER,
        password=NEO4J_PASSWORD
    )

    try:
        neo4j_client.connect()
        print(f"✅ Conectado ao Neo4j")

        pipeline = AuditPipeline(neo4j_client=neo4j_client)

        print(f"🚀 Iniciando auditoria para tender_id: {tender_id}")
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

        await print_details(result)

        print("\n" + "=" * 50)

    except Exception as e:
        print(f"❌ Erro durante a execução: {e}")
        raise
    finally:
        neo4j_client.close()
        print("🔌 Conexão com Neo4j fechada")


async def print_details(result: dict[str, Any]):
    if result['risk_score'] > 0:
        print("\n⚠️  DETALHES DOS ALERTAS:")
        if result['alerts']['shared_partners']:
            print("\n  Sócios em comum:")
            for alert in result['alerts']['shared_partners']:
                print(f"    - {alert['company1']} e {alert['company2']} compartilham sócio: {alert['partner']}")

        if result['alerts']['matching_addresses']:
            print("\n  Endereços compartilhados:")
            for alert in result['alerts']['matching_addresses']:
                print(
                    f"    - {alert['company1']} e {alert['company2']} no mesmo endereço: {alert['street']}, {alert['number']}")

        if result['alerts']['recent_companies_high_value']:
            print("\n  Empresas recentes com alto valor:")
            for alert in result['alerts']['recent_companies_high_value']:
                print(
                    f"    - {alert['company']} (criada em {alert['creation_date']}) ganhou R$ {alert['total_won']:.2f} com capital de R$ {alert['share_capital']:.2f}")


if __name__ == "__main__":
    asyncio.run(main())
