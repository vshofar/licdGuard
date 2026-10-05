import pytest
from unittest.mock import AsyncMock, MagicMock, Mock

from services.audit_pipeline_service import AuditPipeline
from database.neo4j_client import Neo4jClient


class TestAuditPipeline:

    @pytest.fixture
    def mock_neo4j_client(self):
        return Mock(spec=Neo4jClient)

    @pytest.mark.asyncio
    async def test_run_pipeline_success(self, mock_neo4j_client):
        # Mock do retriever service
        mock_retriever = AsyncMock()
        mock_retriever.process_and_ingest_tender.return_value = {
            "status": "success",
            "tender_id": "16017505900062024",
            "items_count": 1,
            "winners_count": 1,
        }

        # Mock do auditor agent
        mock_auditor = MagicMock()
        mock_auditor.audit_tender.return_value = {
            "tender_id": "16017505900062024",
            "risk_score": 0,
            "alerts": {
                "shared_partners": [],
                "matching_addresses": [],
                "recent_companies_high_value": [],
            },
        }

        # Criar pipeline e substituir os serviços
        pipeline = AuditPipeline(neo4j_client=mock_neo4j_client)
        pipeline.retriever_service = mock_retriever
        pipeline.auditor_agent = mock_auditor

        result = await pipeline.run("16017505900062024")

        # Verificações
        mock_retriever.process_and_ingest_tender.assert_called_once_with(
            id_compra="16017505900062024"
        )
        mock_auditor.audit_tender.assert_called_once_with(tender_id="16017505900062024")
        assert result["tender_id"] == "16017505900062024"
        assert result["risk_score"] == 0

    @pytest.mark.asyncio
    async def test_run_pipeline_retriever_failure_propagates(self, mock_neo4j_client):
        # Mock do retriever service que falha
        mock_retriever = AsyncMock()
        mock_retriever.process_and_ingest_tender.side_effect = Exception("API Error")

        # Mock do auditor agent
        mock_auditor = MagicMock()

        # Criar pipeline e substituir os serviços
        pipeline = AuditPipeline(neo4j_client=mock_neo4j_client)
        pipeline.retriever_service = mock_retriever
        pipeline.auditor_agent = mock_auditor

        # Verifica se a exceção é propagada
        with pytest.raises(Exception, match="API Error"):
            await pipeline.run("16017505900062024")

        # Verifica que o auditor não foi chamado
        mock_auditor.audit_tender.assert_not_called()

    @pytest.mark.asyncio
    async def test_run_pipeline_auditor_failure_propagates(self, mock_neo4j_client):
        # Mock do retriever service que funciona
        mock_retriever = AsyncMock()
        mock_retriever.process_and_ingest_tender.return_value = {
            "status": "success",
            "tender_id": "16017505900062024",
            "items_count": 1,
            "winners_count": 1,
        }

        # Mock do auditor agent que falha
        mock_auditor = MagicMock()
        mock_auditor.audit_tender.side_effect = Exception("Query Error")

        # Criar pipeline e substituir os serviços
        pipeline = AuditPipeline(neo4j_client=mock_neo4j_client)
        pipeline.retriever_service = mock_retriever
        pipeline.auditor_agent = mock_auditor

        # Verifica se a exceção é propagada
        with pytest.raises(Exception, match="Query Error"):
            await pipeline.run("16017505900062024")

        # Verifica que o retriever foi chamado antes da falha
        mock_retriever.process_and_ingest_tender.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_pipeline_with_high_risk_score(self, mock_neo4j_client):
        # Mock do retriever service
        mock_retriever = AsyncMock()
        mock_retriever.process_and_ingest_tender.return_value = {
            "status": "success",
            "tender_id": "16017505900062024",
            "items_count": 2,
            "winners_count": 2,
        }

        # Mock do auditor agent com alto risco
        mock_auditor = MagicMock()
        mock_auditor.audit_tender.return_value = {
            "tender_id": "16017505900062024",
            "risk_score": 90,
            "alerts": {
                "shared_partners": [
                    {
                        "company1": "EMP A",
                        "company2": "EMP B",
                        "partner": "SOCIO X",
                    }
                ],
                "matching_addresses": [
                    {
                        "company1": "EMP A",
                        "company2": "EMP B",
                        "street": "RUA X",
                        "number": "100",
                    }
                ],
                "recent_companies_high_value": [
                    {
                        "company": "EMP NOVA",
                        "creation_date": "2024-01-01",
                        "share_capital": 10000.0,
                        "total_won": 500000.0,
                    }
                ],
            },
        }

        # Criar pipeline e substituir os serviços
        pipeline = AuditPipeline(neo4j_client=mock_neo4j_client)
        pipeline.retriever_service = mock_retriever
        pipeline.auditor_agent = mock_auditor

        result = await pipeline.run("16017505900062024")

        assert result["risk_score"] == 90
        assert len(result["alerts"]["shared_partners"]) == 1
        assert len(result["alerts"]["matching_addresses"]) == 1
        assert len(result["alerts"]["recent_companies_high_value"]) == 1

    def test_initialization_creates_all_dependencies(self, mock_neo4j_client):
        pipeline = AuditPipeline(neo4j_client=mock_neo4j_client)

        # Verifica se todos os serviços foram instanciados
        assert pipeline.retriever_service is not None
        assert pipeline.auditor_agent is not None
        assert pipeline.db == mock_neo4j_client

        # Verifica se o retriever tem as dependências corretas
        assert pipeline.retriever_service.tender_service is not None
        assert pipeline.retriever_service.winners_service is not None
        assert pipeline.retriever_service.brasilapi_service is not None
        assert pipeline.retriever_service.ingestion_service is not None
