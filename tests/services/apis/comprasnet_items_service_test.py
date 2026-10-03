import os
import sys
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.services.apis.comprasnet_items_service import ComprasnetItemsService
from src.services.apis.exceptions import ResourceNotFound, InternalError


@pytest.fixture
def items_service():
    return ComprasnetItemsService(timeout=5.0)


@pytest.fixture
def mock_items_payload():
    return {
        "resultado": [
            {
                "descricaoItem": "Servidor",
                "quantidade": 10
            },
            {
                "descricaoItem": "Licença Software",
                "quantidade": 5
            }
        ]
    }


class TestComprasnetItemsService:
    def test_items_service_http_integration_success(self, httpx_mock, items_service, mock_items_payload):
        id_compra = "123456789"
        base_url = "https://dadosabertos.compras.gov.br/modulo-contratacoes"

        httpx_mock.add_response(
            method="GET",
            url=f"{base_url}/2.1_consultarItensContratacoes_PNCP_14133_Id?tipo=idCompra&codigo={id_compra}",
            json=mock_items_payload,
            status_code=200
        )

        items = items_service.fetch_items(id_compra)

        assert items is not None
        assert len(items) == 2
        assert items[0]["descricaoItem"] == "Servidor"
        assert items[0]["quantidade"] == 10
        assert items[1]["descricaoItem"] == "Licença Software"
        assert items[1]["quantidade"] == 5


    def test_items_service_http_integration_empty_result(self, httpx_mock, items_service):
        id_compra = "000000000"
        base_url = "https://dadosabertos.compras.gov.br/modulo-contratacoes"

        httpx_mock.add_response(
            method="GET",
            url=f"{base_url}/2.1_consultarItensContratacoes_PNCP_14133_Id?tipo=idCompra&codigo={id_compra}",
            json={"resultado": []},
            status_code=200
        )

        items = items_service.fetch_items(id_compra)

        assert items == []


    def test_items_service_http_integration_404_error(self, httpx_mock, items_service):
        id_compra = "000000000"
        base_url = "https://dadosabertos.compras.gov.br/modulo-contratacoes"

        httpx_mock.add_response(
            method="GET",
            url=f"{base_url}/2.1_consultarItensContratacoes_PNCP_14133_Id?tipo=idCompra&codigo={id_compra}",
            status_code=404
        )

        with pytest.raises(ResourceNotFound):
            items_service.fetch_items(id_compra)


    def test_items_service_http_integration_500_error(self, httpx_mock, items_service):
        id_compra = "123456789"
        base_url = "https://dadosabertos.compras.gov.br/modulo-contratacoes"

        httpx_mock.add_response(
            method="GET",
            url=f"{base_url}/2.1_consultarItensContratacoes_PNCP_14133_Id?tipo=idCompra&codigo={id_compra}",
            status_code=500
        )

        with pytest.raises(InternalError):
            items_service.fetch_items(id_compra)


if __name__ == "__main__":
    pytest.main(["-s", "-v", __file__])
