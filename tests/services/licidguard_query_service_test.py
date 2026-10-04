import pytest
from unittest.mock import Mock
from models.ingestor_schemas_v2 import IngestionPayload, CompanyNode
from services.licidguard_query_service import LicitGuardQueryService
from services.apis.comprasnet_tender_service import ComprasnetTenderService
from services.apis.comprasnet_winners_service import ComprasnetWinnersService
from services.apis.brasil_api_service import BrasilAPIService
from src.services.apis.exceptions.exceptions import ResourceNotFound, BadRequest, InternalError
from services.mappers.exceptions import RequiredValueNotFoundException, NoContentException


@pytest.fixture
def mock_tender_service():
    service = Mock(spec=ComprasnetTenderService)
    service.fetch_tender.return_value = {
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
    return service


@pytest.fixture
def mock_winners_service():
    service = Mock(spec=ComprasnetWinnersService)
    service.fetch_winners.return_value = [
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
    return service


@pytest.fixture
def mock_brasilapi_service():
    service = Mock(spec=BrasilAPIService)
    service.fetch_company.return_value = {
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
    return service


class TestLicitGuardQueryService:

    def test_build_payload_for_tender_success(
        self, mock_tender_service, mock_winners_service, mock_brasilapi_service
    ):
        query_service = LicitGuardQueryService(
            tender_service=mock_tender_service,
            winners_service=mock_winners_service,
            brasilapi_service=mock_brasilapi_service
        )

        payload = query_service.build_payload_for_tender("16017505900062024")

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

    def test_build_payload_for_tender_tender_service_exception(
        self, mock_tender_service, mock_winners_service, mock_brasilapi_service
    ):
        mock_tender_service.fetch_tender.side_effect = ResourceNotFound("Tender not found")

        query_service = LicitGuardQueryService(
            tender_service=mock_tender_service,
            winners_service=mock_winners_service,
            brasilapi_service=mock_brasilapi_service
        )

        with pytest.raises(ResourceNotFound, match="Tender not found"):
            query_service.build_payload_for_tender("16017505900062024")

    def test_build_payload_for_tender_winners_service_exception(
        self, mock_tender_service, mock_winners_service, mock_brasilapi_service
    ):
        mock_winners_service.fetch_winners.side_effect = BadRequest("Bad request")

        query_service = LicitGuardQueryService(
            tender_service=mock_tender_service,
            winners_service=mock_winners_service,
            brasilapi_service=mock_brasilapi_service
        )

        with pytest.raises(BadRequest, match="Bad request"):
            query_service.build_payload_for_tender("16017505900062024")

    def test_build_payload_for_tender_brasilapi_service_exception(
        self, mock_tender_service, mock_winners_service, mock_brasilapi_service
    ):
        mock_brasilapi_service.fetch_company.side_effect = InternalError("Internal error")

        query_service = LicitGuardQueryService(
            tender_service=mock_tender_service,
            winners_service=mock_winners_service,
            brasilapi_service=mock_brasilapi_service
        )

        with pytest.raises(InternalError, match="Internal error"):
            query_service.build_payload_for_tender("16017505900062024")

    def test_build_payload_for_tender_tender_mapper_exception(
        self, mock_tender_service, mock_winners_service, mock_brasilapi_service
    ):
        mock_tender_service.fetch_tender.return_value = None

        query_service = LicitGuardQueryService(
            tender_service=mock_tender_service,
            winners_service=mock_winners_service,
            brasilapi_service=mock_brasilapi_service
        )

        with pytest.raises(NoContentException, match="The returned payload is empty"):
            query_service.build_payload_for_tender("16017505900062024")

    def test_build_payload_for_tender_winners_mapper_exception(
        self, mock_tender_service, mock_winners_service, mock_brasilapi_service
    ):
        mock_winners_service.fetch_winners.return_value = []

        query_service = LicitGuardQueryService(
            tender_service=mock_tender_service,
            winners_service=mock_winners_service,
            brasilapi_service=mock_brasilapi_service
        )

        with pytest.raises(NoContentException, match="The returned payload is empty"):
            query_service.build_payload_for_tender("16017505900062024")

    def test_build_payload_for_tender_company_mapper_exception(
        self, mock_tender_service, mock_winners_service, mock_brasilapi_service
    ):
        mock_brasilapi_service.fetch_company.return_value = {
            "cnpj": None,
            "razao_social": "TEST COMPANY",
            "capital_social": 100000.0,
            "data_inicio_atividade": "2011-08-15"
        }

        query_service = LicitGuardQueryService(
            tender_service=mock_tender_service,
            winners_service=mock_winners_service,
            brasilapi_service=mock_brasilapi_service
        )

        with pytest.raises(RequiredValueNotFoundException, match="Missing required fields in BrasilAPI payload"):
            query_service.build_payload_for_tender("16017505900062024")