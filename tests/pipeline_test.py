import os
import sys
import pytest
from unittest.mock import MagicMock

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.main import run_pipeline_live
from src.models.ingestor_schemas import TenderInput, ProposalInput, CompanyInput, PartnerInput


@pytest.fixture
def mock_pncp_service():
    """Fixture para PNCPApiService mockado."""
    service = MagicMock()
    return service


@pytest.fixture
def mock_brasil_api_service():
    """Fixture para BrasilAPIService mockado."""
    service = MagicMock()
    return service


@pytest.fixture
def mock_ingestor_agent():
    """Fixture para IngestorAgent mockado."""
    agent = MagicMock()
    return agent


@pytest.fixture
def mock_auditor_agent():
    """Fixture para AuditorAgent mockado."""
    agent = MagicMock()
    return agent


@pytest.fixture
def mock_redactor_agent():
    """Fixture para RedactorAgent mockado."""
    agent = MagicMock()
    return agent


@pytest.fixture
def mock_neo4j_client():
    """Fixture para Neo4jClient mockado."""
    client = MagicMock()
    return client


@pytest.fixture
def mock_tender_input():
    """Fixture com dados de licitação para testes."""
    return TenderInput(
        tender_id="00394460000141-2024-1",
        object="Contratação de Serviços de TI",
        buyer_agency="Ministério da Gestão",
        estimated_value=500000.0,
        proposals=[
            ProposalInput(company_cnpj="11111111000111", offer_value=480000.0)
        ]
    )


@pytest.fixture
def mock_company_input():
    """Fixture com dados de empresa para testes."""
    return CompanyInput(
        cnpj="11111111000111",
        company_name="Empresa Teste LTDA",
        address="Rua A, 100",
        partners=[PartnerInput(masked_cpf="12345678900", name="João Silva", role="Sócio")]
    )


def test_run_pipeline_live_success(
    mock_pncp_service,
    mock_brasil_api_service,
    mock_ingestor_agent,
    mock_auditor_agent,
    mock_redactor_agent,
    mock_neo4j_client,
    mock_tender_input,
    mock_company_input,
    monkeypatch
):
    """Testa a orquestração do run_pipeline_live encadeando os serviços e agentes."""

    mock_pncp_service.fetch_tender.return_value = mock_tender_input
    mock_brasil_api_service.fetch_company.return_value = mock_company_input
    mock_auditor_agent.audit_tender.return_value = {"risk_score": 0.0, "findings": []}
    mock_redactor_agent.generate_report.return_value = "PARECER: Licitação sem indícios de conluio."

    monkeypatch.setattr("src.main.PNCPApiService", lambda: mock_pncp_service)
    monkeypatch.setattr("src.main.BrasilAPIService", lambda: mock_brasil_api_service)
    monkeypatch.setattr("src.main.IngestorAgent", lambda neo4j_client: mock_ingestor_agent)
    monkeypatch.setattr("src.main.AuditorAgent", lambda neo4j_client: mock_auditor_agent)
    monkeypatch.setattr("src.main.RedactorAgent", lambda: mock_redactor_agent)
    monkeypatch.setattr("src.main.Neo4jClient", lambda uri, user, password: mock_neo4j_client)

    result = run_pipeline_live(cnpj_orgao="00394460000141", ano=2024, sequencial=1)

    mock_pncp_service.fetch_tender.assert_called_once_with("00394460000141", 2024, 1)
    mock_ingestor_agent.save_tender_with_proposals.assert_called_once_with(mock_tender_input)
    mock_brasil_api_service.fetch_company.assert_called_once_with("11111111000111")
    mock_ingestor_agent.save_company_with_partners.assert_called_once_with(mock_company_input)
    mock_auditor_agent.audit_tender.assert_called_once_with("00394460000141-2024-1")
    mock_redactor_agent.generate_report.assert_called_once()

    assert result["report"] == "PARECER: Licitação sem indícios de conluio."


def test_run_pipeline_live_bidding_not_found(
    mock_pncp_service,
    mock_ingestor_agent,
    mock_auditor_agent,
    mock_redactor_agent,
    mock_neo4j_client,
    monkeypatch
):
    """Testa a interrupção da pipeline caso a licitação não exista no PNCP."""
    mock_pncp_service.fetch_tender.return_value = None

    monkeypatch.setattr("src.main.PNCPApiService", lambda: mock_pncp_service)
    monkeypatch.setattr("src.main.BrasilAPIService", lambda: MagicMock())
    monkeypatch.setattr("src.main.IngestorAgent", lambda neo4j_client: mock_ingestor_agent)
    monkeypatch.setattr("src.main.AuditorAgent", lambda neo4j_client: mock_auditor_agent)
    monkeypatch.setattr("src.main.RedactorAgent", lambda: mock_redactor_agent)
    monkeypatch.setattr("src.main.Neo4jClient", lambda uri, user, password: mock_neo4j_client)

    result = run_pipeline_live(cnpj_orgao="00000000000000", ano=2024, sequencial=999)

    mock_pncp_service.fetch_tender.assert_called_once()
    mock_ingestor_agent.save_tender_with_proposals.assert_not_called()
    assert result == {}
