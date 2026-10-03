import os
import sys
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.services.apis.comprasnet_proposals_service import ComprasnetProposalsService
from src.services.apis.exceptions import ResourceNotFound, InternalError


@pytest.fixture
def proposals_service():
    return ComprasnetProposalsService(timeout=5.0)


@pytest.fixture
def mock_proposals_payload():
    return {
        "resultado": [
            {
                "niFornecedor": "33333333000133",
                "valorTotalHomologado": 1400000.0
            },
            {
                "niFornecedor": "44444444000144",
                "valorUnitarioHomologado": 75000.0
            }
        ]
    }


class TestComprasnetProposalsService:
    def test_proposals_service_http_integration_success(self, httpx_mock, proposals_service, mock_proposals_payload):
        id_compra = "123456789"
        base_url = "https://dadosabertos.compras.gov.br/modulo-contratacoes"

        httpx_mock.add_response(
            method="GET",
            url=f"{base_url}/3.1_consultarResultadoItensContratacoes_PNCP_14133_Id?tipo=idCompra&codigo={id_compra}",
            json=mock_proposals_payload,
            status_code=200
        )

        proposals = proposals_service.fetch_proposals(id_compra)

        assert proposals is not None
        assert len(proposals) == 2
        assert proposals[0]["niFornecedor"] == "33333333000133"
        assert proposals[0]["valorTotalHomologado"] == 1400000.0
        assert proposals[1]["niFornecedor"] == "44444444000144"
        assert proposals[1]["valorUnitarioHomologado"] == 75000.0


    def test_proposals_service_http_integration_empty_result(self, httpx_mock, proposals_service):
        id_compra = "000000000"
        base_url = "https://dadosabertos.compras.gov.br/modulo-contratacoes"

        httpx_mock.add_response(
            method="GET",
            url=f"{base_url}/3.1_consultarResultadoItensContratacoes_PNCP_14133_Id?tipo=idCompra&codigo={id_compra}",
            json={"resultado": []},
            status_code=200
        )

        proposals = proposals_service.fetch_proposals(id_compra)

        assert proposals == []


    def test_proposals_service_http_integration_404_error(self, httpx_mock, proposals_service):
        id_compra = "000000000"
        base_url = "https://dadosabertos.compras.gov.br/modulo-contratacoes"

        httpx_mock.add_response(
            method="GET",
            url=f"{base_url}/3.1_consultarResultadoItensContratacoes_PNCP_14133_Id?tipo=idCompra&codigo={id_compra}",
            status_code=404
        )

        with pytest.raises(ResourceNotFound):
            proposals_service.fetch_proposals(id_compra)


    def test_proposals_service_http_integration_500_error(self, httpx_mock, proposals_service):
        id_compra = "123456789"
        base_url = "https://dadosabertos.compras.gov.br/modulo-contratacoes"

        httpx_mock.add_response(
            method="GET",
            url=f"{base_url}/3.1_consultarResultadoItensContratacoes_PNCP_14133_Id?tipo=idCompra&codigo={id_compra}",
            status_code=500
        )

        with pytest.raises(InternalError):
            proposals_service.fetch_proposals(id_compra)


if __name__ == "__main__":
    pytest.main(["-s", "-v", __file__])
