import os
import sys
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.services.comprasnet_tender_service import ComprasnetTenderService
from src.services.exceptions.exceptions import ResourceNotFound, InternalError


@pytest.fixture
def tender_service():
    return ComprasnetTenderService(timeout=5.0)


@pytest.fixture
def mock_tender_payload():
    return {
        "resultado": [
            {
                "idCompra": "123456789",
                "objetoCompra": "Prestação de Serviços de TI",
                "valorTotalEstimado": 1500000.0,
                "orgaoEntidadeRazaoSocial": "MINISTERIO DA GESTAO"
            }
        ]
    }


def test_tender_service_http_integration_success(httpx_mock, tender_service, mock_tender_payload):
    id_compra = "123456789"
    base_url = "https://dadosabertos.compras.gov.br/modulo-contratacoes"

    httpx_mock.add_response(
        method="GET",
        url=f"{base_url}/1.1_consultarContratacoes_PNCP_14133_Id?tipo=idCompra&codigo={id_compra}",
        json=mock_tender_payload,
        status_code=200
    )

    tender = tender_service.fetch_tender(id_compra)

    assert tender is not None
    assert tender["idCompra"] == "123456789"
    assert tender["objetoCompra"] == "Prestação de Serviços de TI"
    assert tender["valorTotalEstimado"] == 1500000.0
    assert tender["orgaoEntidadeRazaoSocial"] == "MINISTERIO DA GESTAO"


def test_tender_service_http_integration_empty_result(httpx_mock, tender_service):
    id_compra = "000000000"
    base_url = "https://dadosabertos.compras.gov.br/modulo-contratacoes"

    httpx_mock.add_response(
        method="GET",
        url=f"{base_url}/1.1_consultarContratacoes_PNCP_14133_Id?tipo=idCompra&codigo={id_compra}",
        json={"resultado": []},
        status_code=200
    )

    tender = tender_service.fetch_tender(id_compra)

    assert tender is None


def test_tender_service_http_integration_404_error(httpx_mock, tender_service):
    id_compra = "000000000"
    base_url = "https://dadosabertos.compras.gov.br/modulo-contratacoes"

    httpx_mock.add_response(
        method="GET",
        url=f"{base_url}/1.1_consultarContratacoes_PNCP_14133_Id?tipo=idCompra&codigo={id_compra}",
        status_code=404
    )

    with pytest.raises(ResourceNotFound):
        tender_service.fetch_tender(id_compra)


def test_tender_service_http_integration_500_error(httpx_mock, tender_service):
    id_compra = "123456789"
    base_url = "https://dadosabertos.compras.gov.br/modulo-contratacoes"

    httpx_mock.add_response(
        method="GET",
        url=f"{base_url}/1.1_consultarContratacoes_PNCP_14133_Id?tipo=idCompra&codigo={id_compra}",
        status_code=500
    )

    with pytest.raises(InternalError):
        tender_service.fetch_tender(id_compra)


if __name__ == "__main__":
    pytest.main(["-s", "-v", __file__])
