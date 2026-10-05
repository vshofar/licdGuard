import pytest
from testcontainers.neo4j import Neo4jContainer

from database import Neo4jClient
from models.ingestor_schemas_v2 import (
    IngestionPayload,
    PublicAgencyNode,
    TenderNode,
    TenderItemNode,
    CompanyNode,
    AddressNode,
    PartnerNode,
)
from services.storage.licdguard_graph_storage_service import LicitGuardGraphStorageService


@pytest.fixture(scope="module")
def neo4j_container():
    with Neo4jContainer("neo4j:5-community") as container:
        yield container


@pytest.fixture(scope="module")
def neo4j_client(neo4j_container):
    client = Neo4jClient(
        uri=neo4j_container.get_connection_url(),
        user="neo4j",
        password=neo4j_container.password,
    )
    client.connect()
    yield client
    client.close()


class TestLicitGuardGraphStorageServiceIntegration:

    @pytest.fixture(autouse=True)
    def setup_and_teardown_db(self, neo4j_client: Neo4jClient):
        neo4j_client.query("MATCH (n) DETACH DELETE n")
        yield
        neo4j_client.query("MATCH (n) DETACH DELETE n")

    @pytest.fixture
    def sample_payload(self) -> IngestionPayload:
        return IngestionPayload(
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

    def test_full_graph_ingestion_and_persistence(
        self, neo4j_client: Neo4jClient, sample_payload: IngestionPayload
    ):
        service = LicitGuardGraphStorageService(neo4j_client=neo4j_client)
        service.ingest_payload(sample_payload)

        agency_res = neo4j_client.query(
            "MATCH (a:PublicAgency {cnpj: $cnpj}) RETURN a",
            {"cnpj": "00394452000103"},
        )
        assert len(agency_res) == 1
        assert agency_res[0]["a"]["agency_name"] == "MINISTERIO DA DEFESA"

        tender_res = neo4j_client.query(
            "MATCH (a:PublicAgency)-[:PUBLISHED]->(t:Tender {tender_id: $id}) RETURN t",
            {"id": "16017505900062024"},
        )
        assert len(tender_res) == 1
        assert tender_res[0]["t"]["estimated_value"] == 500000.0

        item_res = neo4j_client.query(
            "MATCH (t:Tender)-[:HAS_ITEM]->(i:TenderItem {item_id: $item_id}) RETURN i",
            {"item_id": "1601750590006202400001"},
        )
        assert len(item_res) == 1

        winner_res = neo4j_client.query(
            """
            MATCH (c:Company {cnpj: $cnpj})-[w:WON_ITEM]->(i:TenderItem {item_id: $item_id})
            MATCH (c)-[:LOCATED_AT]->(a:Address)
            MATCH (p:Partner)-[r:PARTNER_OF]->(c)
            RETURN c, a, p, r.qualification AS qual
            """,
            {
                "cnpj": "14208934000128",
                "item_id": "1601750590006202400001",
            },
        )
        assert len(winner_res) == 1
        assert winner_res[0]["c"]["share_capital"] == 150000.0
        assert winner_res[0]["a"]["city"] == "SAO PAULO"
        assert winner_res[0]["p"]["partner_name"] == "JOAO DA SILVA"
        assert winner_res[0]["qual"] == "Sócio-Administrador"

    def test_idempotency_on_multiple_ingestions(
        self, neo4j_client: Neo4jClient, sample_payload: IngestionPayload
    ):
        service = LicitGuardGraphStorageService(neo4j_client=neo4j_client)

        service.ingest_payload(sample_payload)
        service.ingest_payload(sample_payload)

        count_nodes = neo4j_client.query("MATCH (n) RETURN count(n) AS total")
        assert count_nodes[0]["total"] == 6
