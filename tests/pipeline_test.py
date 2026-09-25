import os
import sys
import pytest
from testcontainers.neo4j import Neo4jContainer

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.database.neo4j_client import Neo4jClient
from src.agents.ingestor_agent import IngestorAgent
from src.agents.auditor_agent import AuditorAgent
from src.agents.redactor_agent import RedactorAgent
from src.main import populate_mock_data


@pytest.fixture(scope="module")
def neo4j_db():

    print("\n🐳 Subindo container efêmero do Neo4j via Testcontainers...")
    with Neo4jContainer("neo4j:5") as neo4j_container:
        bolt_url = neo4j_container.get_connection_url()
        username = "neo4j"
        password = neo4j_container.password

        db = Neo4jClient(uri=bolt_url, user=username, password=password)
        db.connect()

        yield db  # Fornece a instância do cliente para os testes

        db.close()


@pytest.fixture
def ingestor(neo4j_db):
    return IngestorAgent(neo4j_client=neo4j_db)


@pytest.fixture
def auditor(neo4j_db):
    return AuditorAgent(neo4j_client=neo4j_db)


@pytest.fixture
def redactor():
    return RedactorAgent()


def test_end_to_end_pipeline(ingestor, auditor, redactor):
    tender_id = "PNCP-FRAUDE-01"

    populate_mock_data(ingestor)

    audit_results = auditor.audit_tender(tender_id)

    assert audit_results["tender_id"] == tender_id
    assert audit_results["risk_score"] > 0, "O score de risco deveria ser elevado devido às anomalias."
    assert len(audit_results["alerts"]["shared_partners"]) > 0, "Deveria identificar sócios em comum."
    assert len(audit_results["alerts"]["matching_addresses"]) > 0, "Deveria identificar endereços em comum."

    report = redactor.generate_report(audit_results)

    assert report is not None
    assert len(report) > 100
    assert tender_id in report

    print("\n✅ Teste de integração de ponta a ponta executado com sucesso via fixtures Pytest!")