import pytest
from pytest_httpx import HTTPXMock
from testcontainers.neo4j import Neo4jContainer

from database.neo4j_client import Neo4jClient
from services.apis.comprasnet_tender_service import ComprasnetTenderService
from services.apis.comprasnet_winners_service import ComprasnetWinnersService
from services.apis.brasil_api_service import BrasilAPIService
from services.storage.licdguard_graph_storage_service import LicitGuardGraphStorageService
from services.licidguard_retriever_service import LicidGuardRetrieverService


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


class TestLicidGuardRetrieverServiceIntegration:

    @pytest.fixture(autouse=True)
    def setup_and_teardown_db(self, neo4j_client: Neo4jClient):
        neo4j_client.query("MATCH (n) DETACH DELETE n")
        yield
        neo4j_client.query("MATCH (n) DETACH DELETE n")

    @pytest.mark.asyncio
    async def test_full_pipeline_integration_success(
        self,
        httpx_mock: HTTPXMock,
        neo4j_client: Neo4jClient,
    ):
        id_compra = "16017505900062024"
        winner_cnpj = "14208934000128"

        # 1. Mock HTTP ComprasNet - Dados da Licitação
        httpx_mock.add_response(
            method="GET",
            url=f"https://dadosabertos.compras.gov.br/modulo-contratacoes/1.1_consultarContratacoes_PNCP_14133_Id?tipo=idCompra&codigo={id_compra}",
            json={
                "resultado": [
                    {
                        "idCompra": id_compra,
                        "numeroCompra": "90003",
                        "anoCompraPncp": 2024,
                        "objetoCompra": "Aquisicao de equipamentos de TI",
                        "valorTotalEstimado": 750000.0,
                        "dataPublicacaoPncp": "2024-03-15T09:00:00",
                        "orgaoEntidadeCnpj": "00394452000103",
                        "orgaoEntidadeRazaoSocial": "MINISTERIO DA DEFESA",
                        "unidadeOrgaoCodigoUnidade": "160175",
                        "unidadeOrgaoNomeUnidade": "UASG TESTE",
                    }
                ]
            },
            status_code=200,
        )

        # 2. Mock HTTP ComprasNet - Itens e Vencedores
        httpx_mock.add_response(
            method="GET",
            url=f"https://dadosabertos.compras.gov.br/modulo-contratacoes/3.1_consultarResultadoItensContratacoes_PNCP_14133_Id?tipo=idCompra&codigo={id_compra}",
            json={
                "resultado": [
                    {
                        "idCompraItem": f"{id_compra}00001",
                        "idCompra": id_compra,
                        "numeroItemPncp": 1,
                        "niFornecedor": winner_cnpj,
                        "nomeRazaoSocialFornecedor": "CONSTRUTORA KARBONE LTDA",
                        "quantidadeHomologada": 5.0,
                        "valorUnitarioHomologado": 10000.0,
                        "valorTotalHomologado": 50000.0,
                        "situacaoCompraItemResultadoId": 1,
                    }
                ]
            },
            status_code=200,
        )

        # 3. Mock HTTP BrasilAPI - Dados Cadastrais e QSA da Empresa
        httpx_mock.add_response(
            method="GET",
            url=f"https://brasilapi.com.br/api/cnpj/v1/{winner_cnpj}",
            json={
                "cnpj": winner_cnpj,
                "razao_social": "CONSTRUTORA KARBONE E COMERCIAL LTDA",
                "capital_social": 300000.0,
                "data_inicio_atividade": "2011-08-15",
                "descricao_tipo_de_logradouro": "RUA",
                "logradouro": "PEIXOTO GOMIDE",
                "numero": "100",
                "cep": "01409000",
                "municipio": "SAO PAULO",
                "uf": "SP",
                "qsa": [
                    {
                        "cpf_cnpj_socio": "***123456**",
                        "nome_socio": "JOAO DA SILVA",
                        "qualificacao_socio": "Sócio-Administrador",
                    }
                ],
            },
            status_code=200,
        )

        # Instanciação dos serviços das APIs com suas respectivas dependências
        tender_service = ComprasnetTenderService()
        winners_service = ComprasnetWinnersService()
        brasilapi_service = BrasilAPIService()

        # Instanciação das camadas principais
        ingestion_service = LicitGuardGraphStorageService(
            neo4j_client=neo4j_client
        )
        retriever_service = LicidGuardRetrieverService(
            tender_service=tender_service,
            winners_service=winners_service,
            brasilapi_service=brasilapi_service,
            ingestion_service=ingestion_service,
        )

        # Execução do orquestrador
        result = await retriever_service.process_and_ingest_tender(id_compra)

        # Validações de saída
        assert result["status"] == "success"
        assert result["tender_id"] == id_compra
        assert result["items_count"] == 1
        assert result["winners_count"] == 1

        # Validações de persistência no Neo4j
        tender_nodes = neo4j_client.query(
            """
            MATCH (a:PublicAgency {cnpj: '00394452000103'})-[:PUBLISHED]->(t:Tender {tender_id: $id_compra})
            RETURN a.agency_name AS agency, t.estimated_value AS val
            """,
            {"id_compra": id_compra},
        )
        assert len(tender_nodes) == 1
        assert tender_nodes[0]["agency"] == "MINISTERIO DA DEFESA - UASG TESTE"
        assert tender_nodes[0]["val"] == 750000.0

        company_graph = neo4j_client.query(
            """
            MATCH (c:Company {cnpj: $cnpj})-[w:WON_ITEM]->(i:TenderItem)
            MATCH (c)-[:LOCATED_AT]->(addr:Address)
            MATCH (p:Partner)-[r:PARTNER_OF]->(c)
            RETURN c.share_capital AS capital, addr.street AS street, p.partner_name AS partner
            """,
            {"cnpj": winner_cnpj},
        )
        assert len(company_graph) == 1
        assert company_graph[0]["capital"] == 300000.0
        assert company_graph[0]["street"] == "RUA PEIXOTO GOMIDE"
        assert company_graph[0]["partner"] == "JOAO DA SILVA"