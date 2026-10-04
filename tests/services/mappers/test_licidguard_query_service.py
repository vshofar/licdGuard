import pytest
from unittest.mock import AsyncMock
from models.ingestor_schemas_v2 import IngestionPayload, CompanyNode
from services.licidguard_query_service import LicitGuardQueryService


@pytest.fixture
def mock_comprasnet_client():
    client = AsyncMock()
    client.get_tender_by_id.return_value = {
        "resultado": [
            {
                "idCompra": "16017505900062024",
                "numeroCompra": "90003",
                "anoCompraPncp": 2024,
                "objetoCompra": "Aquisicao de materiais",
                "valorTotalEstimado": 500000.0,
                "dataPublicacaoPncp": "2024-01-10T08:00:00",
                "orgaoEntidadeCnpj": "00394452000103",
                "orgaoEntidadeRazaoSocial": "MINISTERIO DA DEFESA",
                "unidadeOrgaoCodigoUnidade": "160175",
                "unidadeOrgaoNomeUnidade": "UASG TESTE"
            }
        ]
    }
    client.get_tender_items_results.return_value = {
        "resultado": [
            {
                "idCompraItem": "1601750590006202400001",
                "idCompra": "16017505900062024",
                "numeroItemPncp": 1,
                "niFornecedor": "14208934000128",
                "nomeRazaoSocialFornecedor": "CONSTRUTORA KARBONE LTDA",
                "quantidadeHomologada": 10.0,
                "valorUnitarioHomologado": 100.0,
                "valorTotalHomologado": 1000.0,
                "situacaoCompraItemResultadoId": 1
            }
        ]
    }
    return client


@pytest.fixture
def mock_brasilapi_client():
    client = AsyncMock()
    client.get_company_by_cnpj.return_value = {
        "cnpj": "14208934000128",
        "razao_social": "CONSTRUTORA KARBONE E COMERCIAL LTDA",
        "capital_social": 150000.0,
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
                "qualificacao_socio": "Sócio-Administrador"
            }
        ]
    }
    return client


@pytest.mark.asyncio
async def test_build_payload_for_tender_success(
    mock_comprasnet_client, mock_brasilapi_client
):
    query_service = LicitGuardQueryService(
        comprasnet_client=mock_comprasnet_client,
        brasilapi_client=mock_brasilapi_client
    )

    payload = await query_service.build_payload_for_tender("16017505900062024")

    assert isinstance(payload, IngestionPayload)
    assert payload.public_agency.cnpj == "00394452000103"
    assert payload.tender.tender_id == "16017505900062024"
    assert len(payload.items) == 1
    assert payload.items[0].winner_cnpj == "14208934000128"

    assert len(payload.winners) == 1
    winner = payload.winners[0]
    assert winner.cnpj == "14208934000128"
    assert winner.share_capital == 150000.0
    assert winner.address is not None
    assert winner.address.street == "RUA PEIXOTO GOMIDE"
    assert len(winner.partners) == 1
    assert winner.partners[0].partner_name == "JOAO DA SILVA"


@pytest.mark.asyncio
async def test_build_payload_for_tender_brasilapi_failure_fallback(
    mock_comprasnet_client, mock_brasilapi_client
):
    mock_brasilapi_client.get_company_by_cnpj.side_effect = Exception("API Unavailable")

    query_service = LicitGuardQueryService(
        comprasnet_client=mock_comprasnet_client,
        brasilapi_client=mock_brasilapi_client
    )

    payload = await query_service.build_payload_for_tender("16017505900062024")

    assert isinstance(payload, IngestionPayload)
    assert len(payload.winners) == 1
    winner = payload.winners[0]
    assert winner.cnpj == "14208934000128"
    assert winner.share_capital == 0.0
    assert winner.address is None
    assert winner.partners == []