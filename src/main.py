import sys
from config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD

from src.database.neo4j_client import Neo4jClient
from src.models.ingestor_schemas import (
    CompanyInput,
    PartnerInput,
    TenderInput,
    ProposalInput
)
from src.agents.ingestor_agent import IngestorAgent
from src.agents.auditor_agent import AuditorAgent
from src.agents.redactor_agent import RedactorAgent


def populate_mock_data(ingestor: IngestorAgent):
    """Populates the Neo4j Knowledge Graph with a controlled fraud scenario."""
    print("📥 Ingerindo dados simulados de licitação e fraude no grafo...")

    company_a = CompanyInput(
        cnpj="11111111000111",
        company_name="Alpha Serviços EIRELI",
        address="Av. Paulista, 1500 - Sala 42",
        partners=[
            PartnerInput(masked_cpf="00011122233", name="Carlos Oculto", participation_pct=70.0)
        ]
    )

    company_b = CompanyInput(
        cnpj="22222222000122",
        company_name="Beta Soluções de TI LTDA",
        address="Av. Paulista, 1500 - Sala 42",  # Endereço compartilhado
        partners=[
            PartnerInput(masked_cpf="00011122233", name="Carlos Oculto", participation_pct=70.0)
        ]
    )

    tender = TenderInput(
        tender_id="PNCP-FRAUDE-01",
        object="Aquisição de Licenças de Software",
        buyer_agency="Prefeitura Municipal",
        estimated_value=1000000.0,
        proposals=[
            ProposalInput(company_cnpj="11111111000111", offer_value=950000.0),
            ProposalInput(company_cnpj="22222222000122", offer_value=1300000.0)
        ]
    )

    ingestor.save_company_with_partners(company_a)
    ingestor.save_company_with_partners(company_b)
    ingestor.save_tender_with_proposals(tender)
    print("✅ Ingestão concluída com sucesso.")


def run_pipeline(bidding_id: str = "PNCP-FRAUDE-01") -> dict:
    print("🚀 Iniciando Pipeline Licit-Guard...")

    db = Neo4jClient(uri=NEO4J_URI, user=NEO4J_USER, password=NEO4J_PASSWORD)
    db.connect()

    try:
        ingestor = IngestorAgent(neo4j_client=db)
        auditor = AuditorAgent(neo4j_client=db)
        redactor = RedactorAgent()

        populate_mock_data(ingestor)

        print(f"\n🔍 Auditando licitação '{bidding_id}' no Knowledge Graph...")
        audit_results = auditor.audit_tender(bidding_id)

        print(f" • Score de Risco Calculado: {audit_results['risk_score']}/100")

        print("\n🤖 Gerando parecer técnico de auditoria com Gemini...")
        forensic_report = redactor.generate_report(audit_results)

        print("\n" + "=" * 70)
        print("📄 PARECER TÉCNICO DE AUDITORIA FORENSE (LICIT-GUARD)")
        print("=" * 70)
        print(forensic_report)
        print("=" * 70)

        return {
            "audit_results": audit_results,
            "report": forensic_report
        }

    finally:
        db.close()


if __name__ == "__main__":
    target_id = sys.argv[1] if len(sys.argv) > 1 else "PNCP-FRAUDE-01"
    run_pipeline(target_id)