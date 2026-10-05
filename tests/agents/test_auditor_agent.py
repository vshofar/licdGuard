import pytest
from unittest.mock import MagicMock

from agents import AuditorAgent


class TestAuditorAgent:

    @pytest.fixture
    def mock_neo4j_client(self):
        return MagicMock()

    def test_audit_tender_no_frauds_returns_zero_score(self, mock_neo4j_client):
        # Simula retorno vazio para todas as 4 consultas Cypher
        mock_neo4j_client.query.side_effect = [[], [], [], []]

        agent = AuditorAgent(neo4j_client=mock_neo4j_client)
        result = agent.audit_tender("16017505900062024")

        assert result["tender_id"] == "16017505900062024"
        assert result["risk_score"] == 0
        assert result["alerts"]["shared_partners"] == []
        assert result["alerts"]["matching_addresses"] == []
        assert result["alerts"]["recent_companies_high_value"] == []

    def test_audit_tender_calculates_accumulated_risk_score(self, mock_neo4j_client):
        # Configura o retorno para as 4 queries em ordem de execução:
        # 1. query_partners (+40)
        # 2. query_addresses (+30)
        # 3. query_recent_companies (+20)
        # 4. all_elements
        mock_neo4j_client.query.side_effect = [
            [
                {
                    "company1": "CONSTRUTORA A",
                    "company2": "CONSTRUTORA B",
                    "partner": "JOAO DA SILVA",
                }
            ],
            [
                {
                    "company1": "CONSTRUTORA A",
                    "company2": "CONSTRUTORA B",
                    "street": "RUA PEIXOTO GOMIDE",
                    "number": "100",
                }
            ],
            [
                {
                    "company": "EMPRESA NOVA LTDA",
                    "creation_date": "2024-01-10",
                    "share_capital": 10000.0,
                    "total_won": 500000.0,
                }
            ],
            [],  # all_elements
        ]

        agent = AuditorAgent(neo4j_client=mock_neo4j_client)
        result = agent.audit_tender("16017505900062024")

        # Risk Score: 40 (sócios) + 30 (endereço) + 20 (empresa recente) = 90
        assert result["tender_id"] == "16017505900062024"
        assert result["risk_score"] == 90
        assert len(result["alerts"]["shared_partners"]) == 1
        assert len(result["alerts"]["matching_addresses"]) == 1
        assert len(result["alerts"]["recent_companies_high_value"]) == 1

    def test_audit_tender_caps_risk_score_at_100(self, mock_neo4j_client):
        # Simula múltiplos alertas para ultrapassar 100 pontos (ex: 3 ocorrências de sócios = 120 pts)
        mock_neo4j_client.query.side_effect = [
            [
                {"company1": "EMP A", "company2": "EMP B", "partner": "SOCIO 1"},
                {"company1": "EMP A", "company2": "EMP C", "partner": "SOCIO 2"},
                {"company1": "EMP B", "company2": "EMP C", "partner": "SOCIO 3"},
            ],
            [],
            [],
            [],
        ]

        agent = AuditorAgent(neo4j_client=mock_neo4j_client)
        result = agent.audit_tender("16017505900062024")

        # O score bruto seria 120, mas deve ser travado em 100
        assert result["risk_score"] == 100
        assert len(result["alerts"]["shared_partners"]) == 3

    def test_audit_tender_passes_correct_cypher_parameters(self, mock_neo4j_client):
        mock_neo4j_client.query.side_effect = [[], [], [], []]
        tender_id = "16017505900062024"

        agent = AuditorAgent(neo4j_client=mock_neo4j_client)
        agent.audit_tender(tender_id)

        # Verifica se o parâmetro tender_id foi repassado corretamente em todas as 4 chamadas ao Neo4j
        assert mock_neo4j_client.query.call_count == 4
        for call_args in mock_neo4j_client.query.call_args_list:
            args, kwargs = call_args
            assert kwargs == {} or args[1] == {"tender_id": tender_id}
            assert args[1] == {"tender_id": tender_id}