import os
import sys
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.services.apis.comprasnet_winners_service import ComprasnetWinnersService
from src.services.apis.exceptions import ResourceNotFound, InternalError


@pytest.fixture
def winners_service():
    return ComprasnetWinnersService(timeout=5.0)


@pytest.fixture
def mock_winners_payload():
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


class TestComprasnetWinnersService:
    def test_winners_service_http_integration_success(self, httpx_mock, winners_service, mock_winners_payload):
        id_compra = "123456789"
        base_url = "https://dadosabertos.compras.gov.br/modulo-contratacoes"

        httpx_mock.add_response(
            method="GET",
            url=f"{base_url}/3.1_consultarResultadoItensContratacoes_PNCP_14133_Id?tipo=idCompra&codigo={id_compra}",
            json=mock_winners_payload,
            status_code=200
        )

        winners = winners_service.fetch_winners(id_compra)

        assert winners is not None
        assert len(winners) == 2
        assert winners[0]["niFornecedor"] == "33333333000133"
        assert winners[0]["valorTotalHomologado"] == 1400000.0
        assert winners[1]["niFornecedor"] == "44444444000144"
        assert winners[1]["valorUnitarioHomologado"] == 75000.0


    def test_winners_service_http_integration_empty_result(self, httpx_mock, winners_service):
        id_compra = "000000000"
        base_url = "https://dadosabertos.compras.gov.br/modulo-contratacoes"

        httpx_mock.add_response(
            method="GET",
            url=f"{base_url}/3.1_consultarResultadoItensContratacoes_PNCP_14133_Id?tipo=idCompra&codigo={id_compra}",
            json={"resultado": []},
            status_code=200
        )

        winners = winners_service.fetch_winners(id_compra)

        assert winners == []


    def test_winners_service_http_integration_404_error(self, httpx_mock, winners_service):
        id_compra = "000000000"
        base_url = "https://dadosabertos.compras.gov.br/modulo-contratacoes"

        httpx_mock.add_response(
            method="GET",
            url=f"{base_url}/3.1_consultarResultadoItensContratacoes_PNCP_14133_Id?tipo=idCompra&codigo={id_compra}",
            status_code=404
        )

        with pytest.raises(ResourceNotFound):
            winners_service.fetch_winners(id_compra)


    def test_winners_service_http_integration_500_error(self, httpx_mock, winners_service):
        id_compra = "123456789"
        base_url = "https://dadosabertos.compras.gov.br/modulo-contratacoes"

        httpx_mock.add_response(
            method="GET",
            url=f"{base_url}/3.1_consultarResultadoItensContratacoes_PNCP_14133_Id?tipo=idCompra&codigo={id_compra}",
            status_code=500
        )

        with pytest.raises(InternalError):
            winners_service.fetch_winners(id_compra)

