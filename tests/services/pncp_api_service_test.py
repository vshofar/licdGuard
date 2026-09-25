import os
import sys
from unittest.mock import patch, MagicMock

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.services.pncp_api_service import PNCPApiService


@patch("httpx.Client.get")
def test_pncp_service_success(mock_get):

    mock_bidding_resp = MagicMock()
    mock_bidding_resp.status_code = 200
    mock_bidding_resp.json.return_value = {
        "objetoCompra": "Aquisição de Equipamentos de Informática",
        "valorTotalEstimado": 500000.0,
        "orgaoEntidade": {
            "razaoSocial": "PREFEITURA MUNICIPAL DE TESTE"
        }
    }

    mock_proposals_resp = MagicMock()
    mock_proposals_resp.status_code = 200
    mock_proposals_resp.json.return_value = [
        {"niFornecedor": "11111111000111", "valorTotal": 480000.0},
        {"niFornecedor": "22222222000122", "valorTotal": 520000.0}
    ]

    mock_get.side_effect = [mock_bidding_resp, mock_proposals_resp]

    service = PNCPApiService()
    tender = service.fetch_tender(cnpj_orgao="00394460000141", ano=2024, sequencial=1)

    assert tender is not None
    assert tender.tender_id == "00394460000141-2024-1"
    assert tender.object == "Aquisição de Equipamentos de Informática"
    assert tender.buyer_agency == "PREFEITURA MUNICIPAL DE TESTE"
    assert tender.estimated_value == 500000.0
    assert len(tender.proposals) == 2
    assert tender.proposals[0].company_cnpj == "11111111000111"
    assert tender.proposals[0].offer_value == 480000.0


@patch("httpx.Client.get")
def test_pncp_service_not_found(mock_get):

    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_get.return_value = mock_response

    service = PNCPApiService()
    bidding = service.fetch_tender(cnpj_orgao="00000000000000", ano=2024, sequencial=999)

    assert bidding is None

