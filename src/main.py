import os
import sys
from dotenv import load_dotenv

load_dotenv()

from src.database.neo4j_client import Neo4jClient
from src.services.pncp_api_service import PNCPApiService
from src.services.brasil_api_service import BrasilAPIService
from src.agents.ingestor_agent import IngestorAgent
from src.agents.auditor_agent import AuditorAgent
from src.agents.redactor_agent import RedactorAgent


def run_pipeline_live(cnpj_orgao: str, ano: int, sequencial: int) -> dict:
    bidding_id = f"{cnpj_orgao}-{ano}-{sequencial}"
    print(f"🚀 Iniciando Pipeline Licit-Guard (Modo REAL): Licitação {bidding_id}...")

    # Instanciação dos Clientes e Serviços
    pncp_api_service = PNCPApiService()
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

        # 1. Busca licitação e propostas no PNCP
        print(f"🔍 [PNCP] Consultando licitação {cnpj_orgao}/{ano}-{sequencial}...")
        tender = pncp_api_service.fetch_tender(cnpj_orgao, ano, sequencial)

        if not tender:
            print("❌ Licitação não encontrada no PNCP.")
            return {}

        # 2. Ingestão da Licitação no Neo4j
        ingestor.save_tender_with_proposals(tender)
        print(f"✅ Licitação '{tender.tender_id}' salva no Neo4j.")

        # 3. Para cada proposta, consulta a empresa/QSA na BrasilAPI e salva no Neo4j
        for proposal in tender.proposals:
            if proposal.company_cnpj:
                print(f"🔍 [BrasilAPI] Consultando empresa {proposal.company_cnpj}...")
                company = brasil_api_service.fetch_company(proposal.company_cnpj)
                if company:
                    ingestor.save_company_with_partners(company)
                    print(f"✅ Empresa '{company.company_name}' e QSA salvos no Neo4j.")

        # 4. Auditoria Forense via Cypher
        print("🔍 Executando auditoria no Neo4j...")
        audit_results = auditor.audit_tender(bidding_id)

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