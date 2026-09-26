import os
import sys
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.services.brasil_api_service import BrasilAPIService


@pytest.fixture
def brasil_api_service():
    """Fixture local que instancia o BrasilAPIService."""
    return BrasilAPIService(timeout=5.0)


@pytest.fixture
def mock_cnpj_payload():
    """Fixture local que fornece o payload de resposta da BrasilAPI."""
    return {
        "cnpj": "11111111000111",
        "razao_social": "EMPRESA INTEGRACAO LTDA",
        "logradouro": "AV BRASIL",
        "numero": "500",
        "bairro": "CENTRO",
        "municipio": "RIO DE JANEIRO",
        "uf": "RJ",
        "qsa": [
            {
                "nome_socio": "MARIA OLIVEIRA",
                "qualificacao_socio": "Sócio",
                "cnpj_cpf_do_socio": "***987654**"
            }
        ]
    }


def test_brasil_api_service_http_integration_success(httpx_mock, brasil_api_service, mock_cnpj_payload):
    """Testa a pilha HTTP da BrasilAPI usando fixtures locais."""
    cnpj = "11111111000111"

    httpx_mock.add_response(
        method="GET",
        url=f"https://brasilapi.com.br/api/cnpj/v1/{cnpj}",
        json=mock_cnpj_payload,
        status_code=200
    )

    company = brasil_api_service.fetch_company(cnpj)

    assert company is not None
    assert company.cnpj == cnpj
    assert company.company_name == "EMPRESA INTEGRACAO LTDA"
    assert company.address == "AV BRASIL, 500 - CENTRO, RIO DE JANEIRO/RJ"
    assert len(company.partners) == 1
    assert company.partners[0].name == "MARIA OLIVEIRA"


def test_brasil_api_service_http_integration_500_error(httpx_mock, brasil_api_service):
    """Testa o tratamento de erro HTTP 500 da BrasilAPI usando a fixture local do serviço."""
    cnpj = "11111111000111"

    httpx_mock.add_response(
        method="GET",
        url=f"https://brasilapi.com.br/api/cnpj/v1/{cnpj}",
        status_code=500
    )

    company = brasil_api_service.fetch_company(cnpj)

    assert company is None


if __name__ == "__main__":
    pytest.main(["-s", "-v", "tests/test_brasil_api_service_http_integration.py"])