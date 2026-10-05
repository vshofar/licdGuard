import pytest
from unittest.mock import MagicMock
from models.ingestor_schemas_v2 import (
    IngestionPayload,
    PublicAgencyNode,
    TenderNode,
    TenderItemNode,
    CompanyNode,
    AddressNode,
    PartnerNode,
)
from services.ingestion.licdguard_graph_ingestion_service import LicitGuardGraphIngestionService


class TestLicitGuardGraphIngestionService:

    @pytest.fixture
    def mock_neo4j_client(self):
        client = MagicMock()
        client.query.return_value = []
        return client

    @pytest.fixture
    def sample_ingestion_payload(self) -> IngestionPayload:
        return IngestionPayload(
            public_agency=PublicAgencyNode(
                cnpj="00394452000103",
                agency_name="MINISTERIO DA DEFESA - UASG TESTE",
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
                    address=AddressNode(
                        street="RUA PEIXOTO GOMIDE",
                        number="100",
                        zip_code="01409000",
                        city="SAO PAULO",
                        state="SP",
                    ),
                    partners=[
                        PartnerNode(
                            partner_id="***123456**",
                            partner_name="JOAO DA SILVA",
                            qualification="Sócio-Administrador",
                        )
                    ],
                )
            ],
        )

    def test_ingest_payload_success(
        self, mock_neo4j_client: MagicMock, sample_ingestion_payload: IngestionPayload
    ):
        service = LicitGuardGraphIngestionService(neo4j_client=mock_neo4j_client)

        service.ingest_payload(sample_ingestion_payload)

        mock_neo4j_client.query.assert_called_once()
        call_args = mock_neo4j_client.query.call_args
        assert call_args[0][0] == service.INGESTION_CYPHER
        assert call_args[0][1]["agency"]["cnpj"] == "00394452000103"
        assert call_args[0][1]["tender"]["tender_id"] == "16017505900062024"

    def test_ingest_payload_raises_exception_on_failure(
        self, mock_neo4j_client: MagicMock, sample_ingestion_payload: IngestionPayload
    ):
        mock_neo4j_client.query.side_effect = Exception("Neo4j Connection Error")

        service = LicitGuardGraphIngestionService(neo4j_client=mock_neo4j_client)

        with pytest.raises(Exception, match="Neo4j Connection Error"):
            service.ingest_payload(sample_ingestion_payload)