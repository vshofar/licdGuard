import pytest
from unittest.mock import Mock, MagicMock
from models.ingestor_schemas_v2 import (
    IngestionPayload,
    PublicAgencyNode,
    TenderNode,
    TenderItemNode,
    CompanyNode,
)
from services.licidguard_retriever_service import LicidGuardRetrieverService
from services.apis.comprasnet_tender_service import ComprasnetTenderService
from services.apis.comprasnet_winners_service import ComprasnetWinnersService
from services.apis.brasil_api_service import BrasilAPIService


class TestLicidGuardRetrieverService:

    @pytest.fixture
    def mock_tender_service(self):
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
    def mock_winners_service(self):
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
    def mock_brasilapi_service(self):
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

    @pytest.fixture
    def mock_ingestion_service(self):
        service = MagicMock()
        return service

    @pytest.mark.asyncio
    async def test_process_and_ingest_tender_success(
            self, mock_tender_service, mock_winners_service, mock_brasilapi_service, mock_ingestion_service
    ):
        retriever = LicidGuardRetrieverService(
            tender_service=mock_tender_service,
            winners_service=mock_winners_service,
            brasilapi_service=mock_brasilapi_service,
            ingestion_service=mock_ingestion_service,
        )

        result = await retriever.process_and_ingest_tender("16017505900062024")

        mock_tender_service.fetch_tender.assert_called_once_with("16017505900062024")
        mock_winners_service.fetch_winners.assert_called_once_with("16017505900062024")
        mock_brasilapi_service.fetch_company.assert_called_once()
        mock_ingestion_service.ingest_payload.assert_called_once()
        assert result["status"] == "success"
        assert result["tender_id"] == "16017505900062024"
        assert result["items_count"] == 1
        assert result["winners_count"] == 1

    @pytest.mark.asyncio
    async def test_process_and_ingest_tender_raises_exception_on_tender_failure(
            self, mock_tender_service, mock_winners_service, mock_brasilapi_service, mock_ingestion_service
    ):
        mock_tender_service.fetch_tender.side_effect = Exception("ComprasNet Unreachable")

        retriever = LicidGuardRetrieverService(
            tender_service=mock_tender_service,
            winners_service=mock_winners_service,
            brasilapi_service=mock_brasilapi_service,
            ingestion_service=mock_ingestion_service,
        )

        with pytest.raises(Exception, match="ComprasNet Unreachable"):
            await retriever.process_and_ingest_tender("16017505900062024")

        mock_ingestion_service.ingest_payload.assert_not_called()



