import os
import sys
import pytest
from unittest.mock import patch, MagicMock

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.services.brasil_api_service import BrasilAPIService


@patch("httpx.Client.get")
def test_brasil_api_service_success(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "cnpj": "11111111000111",
        "razao_social": "ALPHA SERVICOS LTDA",
        "logradouro": "RUA DAS FLORES",
        "numero": "100",
        "bairro": "CENTRO",
        "municipio": "SAO PAULO",
        "uf": "SP",
        "qsa": [
            {
                "nome_socio": "CARLOS SILVA",
                "qualificacao_socio": "Sócio-Administrador",
                "cnpj_cpf_do_socio": "***123456**"
            }
        ]
    }
    mock_get.return_value = mock_response

    service = BrasilAPIService()
    company = service.fetch_company("11.111.111/0001-11")

    assert company is not None
    assert company.cnpj == "11111111000111"
    assert company.company_name == "ALPHA SERVICOS LTDA"
    assert company.address == "RUA DAS FLORES, 100 - CENTRO, SAO PAULO/SP"
    assert len(company.partners) == 1
    assert company.partners[0].name == "CARLOS SILVA"
    assert company.partners[0].role == "Sócio-Administrador"
    assert company.partners[0].participation_pct is None


@patch("httpx.Client.get")
def test_brasil_api_service_not_found(mock_get):
    """Testa o comportamento do serviço quando o CNPJ não é encontrado (404)."""
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_get.return_value = mock_response

    service = BrasilAPIService()
    company = service.fetch_company("00000000000000")

    assert company is None

