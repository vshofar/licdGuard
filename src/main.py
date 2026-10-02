import os
import sys
from dotenv import load_dotenv

load_dotenv()

from src.database.neo4j_client import Neo4jClient
from src.services.comprasnet_service import ComprasnetService
from src.services.brasil_api_service import BrasilAPIService
from src.agents.ingestor_agent import IngestorAgent
from src.agents.auditor_agent import AuditorAgent
from src.agents.redactor_agent import RedactorAgent


def run_pipeline_live(id_compra: str) -> dict:
    print(f"🚀 Iniciando Pipeline Licit-Guard (Modo REAL): Licitação {id_compra}...")

    # Instanciação dos Clientes e Serviços
    comprasnet_service = ComprasnetService()
    brasil_api_service = BrasilAPIService()

    neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_user = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password = os.getenv("NEO4J_PASSWORD", "password")

    db = Neo4jClient(uri=neo4j_uri, user=neo4j_user, password=neo4j_password)
    db.connect()

    try:
        ingestor = IngestorAgent(neo4j_client=db)
        auditor = AuditorAgent(neo4j_client=db)
        redactor = RedactorAgent()

        print(f"🔍 [Comprasnet] Consultando licitação {id_compra}...")
        tender = comprasnet_service.fetch_tender_by_id(id_compra)

        if not tender:
            print("❌ Licitação não encontrada no Comprasnet.")
            return {}

        ingestor.save_tender_with_proposals(tender)
        print(f"✅ Licitação '{tender.tender_id}' salva no Neo4j.")

        for proposal in tender.proposals:
            if proposal.company_cnpj:
                print(f"🔍 [BrasilAPI] Consultando empresa {proposal.company_cnpj}...")
                try:
                    company = brasil_api_service.fetch_company(proposal.company_cnpj)
                    if company:
                        ingestor.save_company_with_partners(company)
                        print(f"✅ Empresa '{company.company_name}' e QSA salvos no Neo4j.")
                except Exception as e:
                    print(f"⚠️ Erro ao buscar empresa {proposal.company_cnpj}: {e}")

        # 4. Auditoria Forense via Cypher
        print("🔍 Executando auditoria no Neo4j...")
        audit_results = auditor.audit_tender(id_compra)

        # 5. Geração do Parecer com a LLM Gemini
        print("🧠 Gerando parecer técnico com Gemini...")
        report = redactor.generate_report(audit_results)

        print("\n" + "=" * 70)
        print("📄 PARECER TÉCNICO DE AUDITORIA FORENSE (LICIT-GUARD)")
        print("=" * 70)
        print(report)
        print("=" * 70)

        return {"audit_results": audit_results, "report": report}

    finally:
        db.close()