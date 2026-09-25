import os
import sys

import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from testcontainers.neo4j import Neo4jContainer
from src.database.neo4j_client import Neo4jClient
from src.models.ingestor_schemas import CompanyInput, PartnerInput, TenderInput, ProposalInput
from src.agents.ingestor_agent import IngestorAgent
from src.agents.auditor_agent import AuditorAgent


@pytest.fixture(scope="module")
def neo4j_container():
    """Create a Neo4j container that persists across all tests in the module."""
    print("🐳 Starting Neo4j container for module...")
    with Neo4jContainer("neo4j:5") as neo4j_docker:
        yield neo4j_docker
    print("🧹 Neo4j container destroyed after all tests")


@pytest.fixture(scope="module")
def neo4j_client(neo4j_container):
    """Create a Neo4j client that persists across all tests in the module."""
    uri = neo4j_container.get_connection_url()
    username = neo4j_container.username
    password = neo4j_container.password

    print(f"⚡ Neo4j running at: {uri}")

    db = Neo4jClient(uri=uri, user=username, password=password)
    db.connect()
    yield db
    db.close()


def clear_database(db):
    """Clear all data from the Neo4j database."""
    cypher = "MATCH (n) DETACH DELETE n"
    db.query(cypher)


def test_auditor_agent_no_fraud(neo4j_client: Neo4jClient):
    print("🐳 Starting ephemeral Neo4j container to test fraud detection...")
    clear_database(neo4j_client)


    ingestor = IngestorAgent(neo4j_client=neo4j_client)
    auditor = AuditorAgent(db=neo4j_client)

    # -------------------------------------------------------------
    # SCENARIO : Legit Bidding (Low Risk)
    # -------------------------------------------------------------
    print("🟢 Ingesting Scenario : Bidding 'PNCP-LEGIT-02' (Fair Competition)...")

    company_c = CompanyInput(
        cnpj="33.333.333/0001-33",
        company_name="Gamma Tech Distribuidora",
        address="Rua Faria Lima, 200",
        partners=[
            PartnerInput(masked_cpf="***.333.444-**", name="Mariana Lima", participation_pct=100.0)
        ]
    )

    company_d = CompanyInput(
        cnpj="44.444.444/0001-44",
        company_name="Delta Inovações S/A",
        address="Rua Berrini, 800",
        partners=[
            PartnerInput(masked_cpf="***.555.666-**", name="Fernando Dias", participation_pct=100.0)
        ]
    )

    ingestor.save_company_with_partners(company_c)
    ingestor.save_company_with_partners(company_d)

    bidding_legit = TenderInput(
        tender_id="PNCP-LEGIT-02",
        object="Local Area Network Maintenance",
        estimated_value=500000.00,
        buyer_agency="Tribunal de Contas",
        proposals=[
            ProposalInput(company_cnpj="33.333.333/0001-33", offer_value=480000.00),
            ProposalInput(company_cnpj="44.444.444/0001-44", offer_value=495000.00)
        ]
    )
    ingestor.save_tender_with_proposals(bidding_legit)

    # -------------------------------------------------------------
    # RUN AUDITS
    # -------------------------------------------------------------

    print("\n🔍 Auditing Legitimate Scenario...")
    legit_report = auditor.audit_tender("PNCP-LEGIT-02")

    print(f" • Calculated Risk Score: {legit_report['risk_score']}/100")

    assert legit_report["risk_score"] == 0
    assert len(legit_report["alerts"]["shared_partners"]) == 0
    assert len(legit_report["alerts"]["matching_addresses"]) == 0
    assert len(legit_report["alerts"]["cover_bids"]) == 0

    print("\n✅ All assertions passed successfully!")


def test_auditor_agent_fraud_scenarios(neo4j_client):
    print("🐳 Starting ephemeral Neo4j container to test fraud detection...")
    clear_database(neo4j_client)

    ingestor = IngestorAgent(neo4j_client=neo4j_client)
    auditor = AuditorAgent(db=neo4j_client)

    # -------------------------------------------------------------
    # SCENARIO 1: Bidding with Full Cartel Setup (High Risk)
    # -------------------------------------------------------------
    print("\n🚨 Ingesting Scenario 1: Bidding 'PNCP-FRAUD-01' (Cartel Mapped)...")

    company_a = CompanyInput(
        cnpj="11.111.111/0001-11",
        company_name="Alpha Serviços EIRELI",
        address="Av. Paulista, 1500 - Sala 42",
        partners=[
            PartnerInput(masked_cpf="***.111.222-**", name="Carlos Oculto", participation_pct=100.0)
        ]
    )

    company_b = CompanyInput(
        cnpj="22.222.222/0001-22",
        company_name="Beta Soluções de TI LTDA",
        address="Av. Paulista, 1500 - Sala 42",
        partners=[
            PartnerInput(masked_cpf="***.111.222-**", name="Carlos Oculto", participation_pct=50.0)
        ]
    )

    ingestor.save_company_with_partners(company_a)
    ingestor.save_company_with_partners(company_b)

    tender_fraud = TenderInput(
        tender_id="PNCP-FRAUD-01",
        object="High-Performance Server Acquisition",
        estimated_value=1000000.00,
        buyer_agency="Secretaria de Tecnologia",
        proposals=[
            ProposalInput(company_cnpj="11.111.111/0001-11", offer_value=990000.00),
            ProposalInput(company_cnpj="22.222.222/0001-22", offer_value=1300000.00)
        ]
    )
    ingestor.save_tender_with_proposals(tender_fraud)

    # -------------------------------------------------------------
    # RUN AUDITS
    # -------------------------------------------------------------
    print("\n🔍 Auditing Fraudulent Scenario...")
    fraud_report = auditor.audit_tender("PNCP-FRAUD-01")

    print(f" • Calculated Risk Score: {fraud_report['risk_score']}/100")
    print(f" • Shared Partners: {len(fraud_report['alerts']['shared_partners'])}")
    print(f" • Matching Addresses: {len(fraud_report['alerts']['matching_addresses'])}")
    print(f" • Cover Biddings: {len(fraud_report['alerts']['cover_bids'])}")

    assert fraud_report["risk_score"] >= 80
    assert len(fraud_report["alerts"]["shared_partners"]) == 1
    assert len(fraud_report["alerts"]["matching_addresses"]) == 1
    assert len(fraud_report["alerts"]["cover_bids"]) == 1

    print("🧹 Ephemeral container cleaned up.")

