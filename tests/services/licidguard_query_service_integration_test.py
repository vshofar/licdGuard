import pytest
from services.licidguard_query_service import LicitGuardQueryService
from services.apis.comprasnet_tender_service import ComprasnetTenderService
from services.apis.comprasnet_winners_service import ComprasnetWinnersService
from services.apis.brasil_api_service import BrasilAPIService
from src.services.apis.exceptions.exceptions import ResourceNotFound, BadRequest, InternalError
from services.mappers.exceptions import NoContentException


@pytest.fixture
def query_service():
    return LicitGuardQueryService(
        tender_service=ComprasnetTenderService(timeout=5.0),
        winners_service=ComprasnetWinnersService(timeout=5.0),
        brasilapi_service=BrasilAPIService(timeout=5.0)
    )


@pytest.fixture
def valid_tender_payload():
    return {
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


@pytest.fixture
def valid_winners_payload():
    return {
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


@pytest.fixture
def valid_company_payload():
    return {
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


class TestLicitGuardQueryServiceIntegration:

    def test_build_payload_for_tender_success_all_apis(
        self, httpx_mock, query_service, valid_tender_payload, valid_winners_payload, valid_company_payload
    ):
        tender_id = "16017505900062024"
        cnpj = "14208934000128"

        # Mock tender service
        httpx_mock.add_response(
            method="GET",
            url=f"https://dadosabertos.compras.gov.br/modulo-contratacoes/1.1_consultarContratacoes_PNCP_14133_Id?tipo=idCompra&codigo={tender_id}",
            json={"resultado": [valid_tender_payload]},
            status_code=200
        )

        # Mock winners service
        httpx_mock.add_response(
            method="GET",
            url=f"https://dadosabertos.compras.gov.br/modulo-contratacoes/3.1_consultarResultadoItensContratacoes_PNCP_14133_Id?tipo=idCompra&codigo={tender_id}",
            json=valid_winners_payload,
            status_code=200
        )

        # Mock brasilapi service
        httpx_mock.add_response(
            method="GET",
            url=f"https://brasilapi.com.br/api/cnpj/v1/{cnpj}",
            json=valid_company_payload,
            status_code=200
        )

        payload = query_service.build_payload_for_tender(tender_id)

        assert payload.public_agency.cnpj == "00394452000103"
        assert payload.tender.tender_id == tender_id
        assert len(payload.items) == 1
        assert len(payload.winners) == 1
        assert payload.winners[0].cnpj == cnpj
        assert payload.winners[0].share_capital == 150000.0
        assert payload.winners[0].address is not None

    def test_tender_service_404_error(self, httpx_mock, query_service):
        tender_id = "16017505900062024"

        httpx_mock.add_response(
            method="GET",
            url=f"https://dadosabertos.compras.gov.br/modulo-contratacoes/1.1_consultarContratacoes_PNCP_14133_Id?tipo=idCompra&codigo={tender_id}",
            status_code=404
        )

        with pytest.raises(ResourceNotFound):
            query_service.build_payload_for_tender(tender_id)

    def test_tender_service_400_error(self, httpx_mock, query_service):
        tender_id = "16017505900062024"

        httpx_mock.add_response(
            method="GET",
            url=f"https://dadosabertos.compras.gov.br/modulo-contratacoes/1.1_consultarContratacoes_PNCP_14133_Id?tipo=idCompra&codigo={tender_id}",
            status_code=400
        )

        with pytest.raises(BadRequest):
            query_service.build_payload_for_tender(tender_id)

    def test_tender_service_500_error(self, httpx_mock, query_service):
        tender_id = "16017505900062024"

        httpx_mock.add_response(
            method="GET",
            url=f"https://dadosabertos.compras.gov.br/modulo-contratacoes/1.1_consultarContratacoes_PNCP_14133_Id?tipo=idCompra&codigo={tender_id}",
            status_code=500
        )

        with pytest.raises(InternalError):
            query_service.build_payload_for_tender(tender_id)

    def test_tender_service_200_null_result(self, httpx_mock, query_service):
        tender_id = "16017505900062024"

        httpx_mock.add_response(
            method="GET",
            url=f"https://dadosabertos.compras.gov.br/modulo-contratacoes/1.1_consultarContratacoes_PNCP_14133_Id?tipo=idCompra&codigo={tender_id}",
            json={"resultado": []},
            status_code=200
        )

        with pytest.raises(NoContentException, match="The returned payload is empty"):
            query_service.build_payload_for_tender(tender_id)

    def test_winners_service_404_error(self, httpx_mock, query_service, valid_tender_payload):
        tender_id = "16017505900062024"

        httpx_mock.add_response(
            method="GET",
            url=f"https://dadosabertos.compras.gov.br/modulo-contratacoes/1.1_consultarContratacoes_PNCP_14133_Id?tipo=idCompra&codigo={tender_id}",
            json={"resultado": [valid_tender_payload]},
            status_code=200
        )

        httpx_mock.add_response(
            method="GET",
            url=f"https://dadosabertos.compras.gov.br/modulo-contratacoes/3.1_consultarResultadoItensContratacoes_PNCP_14133_Id?tipo=idCompra&codigo={tender_id}",
            status_code=404
        )

        with pytest.raises(ResourceNotFound):
            query_service.build_payload_for_tender(tender_id)

    def test_winners_service_400_error(self, httpx_mock, query_service, valid_tender_payload):
        tender_id = "16017505900062024"

        httpx_mock.add_response(
            method="GET",
            url=f"https://dadosabertos.compras.gov.br/modulo-contratacoes/1.1_consultarContratacoes_PNCP_14133_Id?tipo=idCompra&codigo={tender_id}",
            json={"resultado": [valid_tender_payload]},
            status_code=200
        )

        httpx_mock.add_response(
            method="GET",
            url=f"https://dadosabertos.compras.gov.br/modulo-contratacoes/3.1_consultarResultadoItensContratacoes_PNCP_14133_Id?tipo=idCompra&codigo={tender_id}",
            status_code=400
        )

        with pytest.raises(BadRequest):
            query_service.build_payload_for_tender(tender_id)

    def test_winners_service_500_error(self, httpx_mock, query_service, valid_tender_payload):
        tender_id = "16017505900062024"

        httpx_mock.add_response(
            method="GET",
            url=f"https://dadosabertos.compras.gov.br/modulo-contratacoes/1.1_consultarContratacoes_PNCP_14133_Id?tipo=idCompra&codigo={tender_id}",
            json={"resultado": [valid_tender_payload]},
            status_code=200
        )

        httpx_mock.add_response(
            method="GET",
            url=f"https://dadosabertos.compras.gov.br/modulo-contratacoes/3.1_consultarResultadoItensContratacoes_PNCP_14133_Id?tipo=idCompra&codigo={tender_id}",
            status_code=500
        )

        with pytest.raises(InternalError):
            query_service.build_payload_for_tender(tender_id)

    def test_winners_service_200_empty_result(self, httpx_mock, query_service, valid_tender_payload):
        tender_id = "16017505900062024"

        httpx_mock.add_response(
            method="GET",
            url=f"https://dadosabertos.compras.gov.br/modulo-contratacoes/1.1_consultarContratacoes_PNCP_14133_Id?tipo=idCompra&codigo={tender_id}",
            json={"resultado": [valid_tender_payload]},
            status_code=200
        )

        httpx_mock.add_response(
            method="GET",
            url=f"https://dadosabertos.compras.gov.br/modulo-contratacoes/3.1_consultarResultadoItensContratacoes_PNCP_14133_Id?tipo=idCompra&codigo={tender_id}",
            json={"resultado": []},
            status_code=200
        )

        with pytest.raises(NoContentException, match="The returned payload is empty"):
            query_service.build_payload_for_tender(tender_id)

    def test_brasilapi_service_404_error(self, httpx_mock, query_service, valid_tender_payload, valid_winners_payload):
        tender_id = "16017505900062024"
        cnpj = "14208934000128"

        httpx_mock.add_response(
            method="GET",
            url=f"https://dadosabertos.compras.gov.br/modulo-contratacoes/1.1_consultarContratacoes_PNCP_14133_Id?tipo=idCompra&codigo={tender_id}",
            json={"resultado": [valid_tender_payload]},
            status_code=200
        )

        httpx_mock.add_response(
            method="GET",
            url=f"https://dadosabertos.compras.gov.br/modulo-contratacoes/3.1_consultarResultadoItensContratacoes_PNCP_14133_Id?tipo=idCompra&codigo={tender_id}",
            json=valid_winners_payload,
            status_code=200
        )

        httpx_mock.add_response(
            method="GET",
            url=f"https://brasilapi.com.br/api/cnpj/v1/{cnpj}",
            status_code=404
        )

        with pytest.raises(ResourceNotFound):
            query_service.build_payload_for_tender(tender_id)

    def test_brasilapi_service_500_error(self, httpx_mock, query_service, valid_tender_payload, valid_winners_payload):
        tender_id = "16017505900062024"
        cnpj = "14208934000128"

        httpx_mock.add_response(
            method="GET",
            url=f"https://dadosabertos.compras.gov.br/modulo-contratacoes/1.1_consultarContratacoes_PNCP_14133_Id?tipo=idCompra&codigo={tender_id}",
            json={"resultado": [valid_tender_payload]},
            status_code=200
        )

        httpx_mock.add_response(
            method="GET",
            url=f"https://dadosabertos.compras.gov.br/modulo-contratacoes/3.1_consultarResultadoItensContratacoes_PNCP_14133_Id?tipo=idCompra&codigo={tender_id}",
            json=valid_winners_payload,
            status_code=200
        )

        httpx_mock.add_response(
            method="GET",
            url=f"https://brasilapi.com.br/api/cnpj/v1/{cnpj}",
            status_code=500
        )

        with pytest.raises(InternalError):
            query_service.build_payload_for_tender(tender_id)

    def test_brasilapi_service_200_null_result(self, httpx_mock, query_service, valid_tender_payload, valid_winners_payload):
        tender_id = "16017505900062024"
        cnpj = "14208934000128"

        httpx_mock.add_response(
            method="GET",
            url=f"https://dadosabertos.compras.gov.br/modulo-contratacoes/1.1_consultarContratacoes_PNCP_14133_Id?tipo=idCompra&codigo={tender_id}",
            json={"resultado": [valid_tender_payload]},
            status_code=200
        )

        httpx_mock.add_response(
            method="GET",
            url=f"https://dadosabertos.compras.gov.br/modulo-contratacoes/3.1_consultarResultadoItensContratacoes_PNCP_14133_Id?tipo=idCompra&codigo={tender_id}",
            json=valid_winners_payload,
            status_code=200
        )

        httpx_mock.add_response(
            method="GET",
            url=f"https://brasilapi.com.br/api/cnpj/v1/{cnpj}",
            json=None,
            status_code=200
        )

        with pytest.raises(NoContentException, match="The returned payload is empty"):
            query_service.build_payload_for_tender(tender_id)

    def test_tender_service_200_missing_required_field(self, httpx_mock, query_service):
        tender_id = "16017505900062024"
        tender_payload_missing_field = {
            "numeroCompra": "90003",
            "anoCompraPncp": 2024,
            "objetoCompra": "Aquisicao de materiais",
            "valorTotalEstimado": 500000.0,
            "dataPublicacaoPncp": "2024-01-10T08:00:00",
            "orgaoEntidadeCnpj": "00394452000103",
            "orgaoEntidadeRazaoSocial": "MINISTERIO DA DEFESA",
            "unidadeOrgaoCodigoUnidade": "160175",
            "unidadeOrgaoNomeUnidade": "UASG TESTE"
            # Missing: idCompra
        }

        httpx_mock.add_response(
            method="GET",
            url=f"https://dadosabertos.compras.gov.br/modulo-contratacoes/1.1_consultarContratacoes_PNCP_14133_Id?tipo=idCompra&codigo={tender_id}",
            json={"resultado": [tender_payload_missing_field]},
            status_code=200
        )

        from services.mappers.exceptions import RequiredValueNotFoundException
        with pytest.raises(RequiredValueNotFoundException, match="Missing required fields"):
            query_service.build_payload_for_tender(tender_id)

    def test_winners_service_200_missing_required_field(self, httpx_mock, query_service, valid_tender_payload):
        tender_id = "16017505900062024"
        winners_payload_missing_field = {
            "resultado": [
                {
                    "idCompraItem": "1601750590006202400001",
                    "idCompra": "16017505900062024",
                    "numeroItemPncp": 1,
                    "niFornecedor": "14208934000128",
                    "quantidadeHomologada": 10.0,
                    "valorUnitarioHomologado": 100.0,
                    "valorTotalHomologado": 1000.0,
                    "situacaoCompraItemResultadoId": 1
                    # Missing: nomeRazaoSocialFornecedor
                }
            ]
        }

        httpx_mock.add_response(
            method="GET",
            url=f"https://dadosabertos.compras.gov.br/modulo-contratacoes/1.1_consultarContratacoes_PNCP_14133_Id?tipo=idCompra&codigo={tender_id}",
            json={"resultado": [valid_tender_payload]},
            status_code=200
        )

        httpx_mock.add_response(
            method="GET",
            url=f"https://dadosabertos.compras.gov.br/modulo-contratacoes/3.1_consultarResultadoItensContratacoes_PNCP_14133_Id?tipo=idCompra&codigo={tender_id}",
            json=winners_payload_missing_field,
            status_code=200
        )

        from services.mappers.exceptions import RequiredValueNotFoundException
        with pytest.raises(RequiredValueNotFoundException, match="Missing required fields"):
            query_service.build_payload_for_tender(tender_id)

    def test_brasilapi_service_200_missing_required_field(self, httpx_mock, query_service, valid_tender_payload, valid_winners_payload):
        tender_id = "16017505900062024"
        cnpj = "14208934000128"
        company_payload_missing_field = {
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
            # Missing: cnpj
        }

        httpx_mock.add_response(
            method="GET",
            url=f"https://dadosabertos.compras.gov.br/modulo-contratacoes/1.1_consultarContratacoes_PNCP_14133_Id?tipo=idCompra&codigo={tender_id}",
            json={"resultado": [valid_tender_payload]},
            status_code=200
        )

        httpx_mock.add_response(
            method="GET",
            url=f"https://dadosabertos.compras.gov.br/modulo-contratacoes/3.1_consultarResultadoItensContratacoes_PNCP_14133_Id?tipo=idCompra&codigo={tender_id}",
            json=valid_winners_payload,
            status_code=200
        )

        httpx_mock.add_response(
            method="GET",
            url=f"https://brasilapi.com.br/api/cnpj/v1/{cnpj}",
            json=company_payload_missing_field,
            status_code=200
        )

        from services.mappers.exceptions import RequiredValueNotFoundException
        with pytest.raises(RequiredValueNotFoundException, match="Missing required fields in BrasilAPI payload"):
            query_service.build_payload_for_tender(tender_id)

