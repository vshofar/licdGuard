import os
import sys
import pytest

# Garante que a raiz do projeto esteja no PYTHONPATH
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.services.pncp_api_service import PNCPApiService


# --- FIXTURES LOCAIS ---

@pytest.fixture
def pncp_service():
    """Fixture local que fornece uma instância isolada do PNCPService."""
    return PNCPApiService(timeout=5.0)


@pytest.fixture
def mock_bidding_payload():
    """Fixture local com o payload simulado do endpoint da licitação."""
    return {
        "objetoCompra": "Prestação de Serviços de TI",
        "valorTotalEstimado": 1200000.0,
        "orgaoEntidade": {
            "razaoSocial": "MINISTERIO DA GESTAO"
        }
    }


@pytest.fixture
def mock_proposals_payload():
    """Fixture local com a lista de propostas simuladas no PNCP."""
    return [
        {
            "niFornecedor": "11111111000111",
            "valorTotal": 1150000.0
        },
        {
            "niFornecedor": "22222222000122",
            "valorTotal": 1180000.0
        }
    ]


# --- CASOS DE TESTE ---

def test_pncp_service_http_integration_success(
    httpx_mock, pncp_service, mock_bidding_payload, mock_proposals_payload
):
    """Testa a sequência de requisições HTTP (Licitação + Propostas) com sucesso."""
    cnpj_orgao = "00394460000141"
    ano = 2024
    seq = 1

    # 1. Intercepta a chamada de busca da Licitação/Contrato
    httpx_mock.add_response(
        method="GET",
        url=f"https://pncp.gov.br/api/pncp/v1/orgaos/{cnpj_orgao}/compras/{ano}/{seq}",
        json=mock_bidding_payload,
        status_code=200
    )

    # 2. Intercepta a chamada subsequente de busca das Propostas
    httpx_mock.add_response(
        method="GET",
        url=f"https://pncp.gov.br/api/pncp/v1/orgaos/{cnpj_orgao}/compras/{ano}/{seq}/propostas",
        json=mock_proposals_payload,
        status_code=200
    )

    # Executa o método do serviço
    bidding = pncp_service.fetch_tender(cnpj_orgao, ano, seq)

    # Validações do resultado montado
    assert bidding is not None
    assert bidding.tender_id == f"{cnpj_orgao}-{ano}-{seq}"
    assert bidding.buyer_agency == "MINISTERIO DA GESTAO"
    assert len(bidding.proposals) == 2
    assert bidding.proposals[0].company_cnpj == "11111111000111"
    assert bidding.proposals[0].offer_value == 1150000.0


def test_pncp_service_http_integration_404_not_found(httpx_mock, pncp_service):
    """Testa o tratamento de erro quando a licitação não é encontrada (404)."""
    cnpj_orgao = "00000000000000"
    ano = 2024
    seq = 999

    httpx_mock.add_response(
        method="GET",
        url=f"https://pncp.gov.br/api/pncp/v1/orgaos/{cnpj_orgao}/compras/{ano}/{seq}",
        status_code=404
    )

    bidding = pncp_service.fetch_tender(cnpj_orgao, ano, seq)

    assert bidding is None


if __name__ == "__main__":
    pytest.main(["-s", "-v", __file__])