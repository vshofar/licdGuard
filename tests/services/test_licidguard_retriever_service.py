import pytest
from unittest.mock import AsyncMock, MagicMock
from models.ingestor_schemas_v2 import (
    IngestionPayload,
    PublicAgencyNode,
    TenderNode,
    TenderItemNode,
    CompanyNode,
)
from services.licidguard_retriever_service import LicidGuardRetrieverService


class TestLicidGuardRetrieverService:

    @pytest.fixture
    def mock_query_service(self):
        service = AsyncMock()
        payload = IngestionPayload(
            public_agency=PublicAgencyNode(
                cnpj="00394452000103",
                agency_name="MINISTERIO DA DEFESA",
                uasg_code="160175",
            ),
            tender=TenderNode(
                tender_id="16017505900062024",
                notice_number="90003/2024",
                object_description="Aquisicao de materiais",
                estimated_value=500000.0,
                publication_date="2024-01-10T08:00:00",
            ),
            items=[
                TenderItemNode(
                    item_id="1601750590006202400001",
                    tender_id="16017505900062024",
                    item_number=1,
                    quantity_homologated=10.0,
                    unit_value_homologated=100.0,
                    total_value_homologated=1000.0,
                    winner_cnpj="14208934000128",
                )
            ],
            winners=[
                CompanyNode(
                    cnpj="14208934000128",
                    legal_name="CONSTRUTORA KARBONE LTDA",
                    share_capital=150000.0,
                    creation_date="2011-08-15",
                )
            ],
        )
        service.build_payload_for_tender.return_value = payload
        return service

    @pytest.fixture
    def mock_ingestion_service(self):
        service = MagicMock()
        return service

    @pytest.mark.asyncio
    async def test_process_and_ingest_tender_success(
            self, mock_query_service, mock_ingestion_service
    ):
        orchestrator = LicidGuardRetrieverService(
            query_service=mock_query_service,
            ingestion_service=mock_ingestion_service,
        )

        result = await orchestrator.process_and_ingest_tender("16017505900062024")

        mock_query_service.build_payload_for_tender.assert_called_once_with("16017505900062024")
        mock_ingestion_service.ingest_payload.assert_called_once()
        assert result["status"] == "success"
        assert result["tender_id"] == "16017505900062024"
        assert result["items_count"] == 1
        assert result["winners_count"] == 1

    @pytest.mark.asyncio
    async def test_process_and_ingest_tender_raises_exception_on_query_failure(
            self, mock_query_service, mock_ingestion_service
    ):
        mock_query_service.build_payload_for_tender.side_effect = Exception("ComprasNet Unreachable")

        orchestrator = LicidGuardRetrieverService(
            query_service=mock_query_service,
            ingestion_service=mock_ingestion_service,
        )

        with pytest.raises(Exception, match="ComprasNet Unreachable"):
            await orchestrator.process_and_ingest_tender("16017505900062024")

        mock_ingestion_service.ingest_payload.assert_not_called()



