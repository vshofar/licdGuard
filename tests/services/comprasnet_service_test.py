import os
import sys
import pytest
from unittest.mock import Mock

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.services.comprasnet_service import ComprasnetService


@pytest.fixture
def comprasnet_service():
    return ComprasnetService(timeout=5.0)


@pytest.fixture
def mock_tender_data():
    return {
        "idCompra": "123456789",
        "objetoCompra": "Prestação de Serviços de TI",
        "valorTotalEstimado": 1500000.0,
        "orgaoEntidadeRazaoSocial": "MINISTERIO DA GESTAO"
    }


@pytest.fixture
def mock_items_data():
    return [
        {
            "descricaoItem": "Servidor",
            "quantidade": 10
        }
    ]


@pytest.fixture
def mock_proposals_data():
    return [
        {
            "niFornecedor": "33333333000133",
            "valorTotalHomologado": 1400000.0
        },
        {
            "niFornecedor": "44444444000144",
            "valorUnitarioHomologado": 75000.0
        }
    ]


class TestComprasnetService:
    def test_comprasnet_service_fetch_tender_by_id_success(
        self, comprasnet_service, mock_tender_data, mock_items_data, mock_proposals_data
    ):
        id_compra = "123456789"

        comprasnet_service.tender_service.fetch_tender = Mock(return_value=mock_tender_data)
        comprasnet_service.items_service.fetch_items = Mock(return_value=mock_items_data)
        comprasnet_service.proposals_service.fetch_proposals = Mock(return_value=mock_proposals_data)

        tender = comprasnet_service.fetch_tender_by_id(id_compra)

        assert tender is not None
        assert tender.tender_id == "123456789"
        assert tender.object == "Prestação de Serviços de TI"
        assert tender.estimated_value == 1500000.0
        assert tender.buyer_agency == "MINISTERIO DA GESTAO"
        assert len(tender.proposals) == 2
        assert tender.proposals[0].company_cnpj == "33333333000133"
        assert tender.proposals[0].offer_value == 1400000.0
        assert tender.proposals[1].company_cnpj == "44444444000144"
        assert tender.proposals[1].offer_value == 75000.0


    def test_comprasnet_service_fetch_tender_by_id_tender_not_found(self, comprasnet_service):
        id_compra = "000000000"

        comprasnet_service.tender_service.fetch_tender = Mock(return_value=None)
        comprasnet_service.items_service.fetch_items = Mock(return_value=[])
        comprasnet_service.proposals_service.fetch_proposals = Mock(return_value=[])

        tender = comprasnet_service.fetch_tender_by_id(id_compra)

        assert tender is None
        comprasnet_service.items_service.fetch_items.assert_not_called()
        comprasnet_service.proposals_service.fetch_proposals.assert_not_called()


    def test_comprasnet_service_get_full_payload_success(
        self, comprasnet_service, mock_tender_data, mock_items_data, mock_proposals_data
    ):
        id_compra = "123456789"

        comprasnet_service.tender_service.fetch_tender = Mock(return_value=mock_tender_data)
        comprasnet_service.items_service.fetch_items = Mock(return_value=mock_items_data)
        comprasnet_service.proposals_service.fetch_proposals = Mock(return_value=mock_proposals_data)

        payload = comprasnet_service.get_full_payload(id_compra)

        assert payload is not None
        assert payload["tender"] == mock_tender_data
        assert payload["items"] == mock_items_data
        assert payload["proposals"] == mock_proposals_data


    def test_comprasnet_service_get_full_payload_tender_not_found(self, comprasnet_service):
        id_compra = "000000000"

        comprasnet_service.tender_service.fetch_tender = Mock(return_value=None)

        payload = comprasnet_service.get_full_payload(id_compra)

        assert payload is None


    def test_comprasnet_service_proposals_without_cnpj(self, comprasnet_service, mock_tender_data):
        id_compra = "123456789"

        mock_proposals_data = [
            {
                "valorTotalHomologado": 1400000.0
            }
        ]

        comprasnet_service.tender_service.fetch_tender = Mock(return_value=mock_tender_data)
        comprasnet_service.items_service.fetch_items = Mock(return_value=[])
        comprasnet_service.proposals_service.fetch_proposals = Mock(return_value=mock_proposals_data)

        tender = comprasnet_service.fetch_tender_by_id(id_compra)

        assert tender is not None
        assert len(tender.proposals) == 0


    def test_comprasnet_service_proposals_fallback_to_unit_value(self, comprasnet_service, mock_tender_data):
        id_compra = "123456789"

        mock_proposals_data = [
            {
                "niFornecedor": "55555555000155",
                "valorUnitarioHomologado": 80000.0
            }
        ]

        comprasnet_service.tender_service.fetch_tender = Mock(return_value=mock_tender_data)
        comprasnet_service.items_service.fetch_items = Mock(return_value=[])
        comprasnet_service.proposals_service.fetch_proposals = Mock(return_value=mock_proposals_data)

        tender = comprasnet_service.fetch_tender_by_id(id_compra)

        assert tender is not None
        assert len(tender.proposals) == 1
        assert tender.proposals[0].company_cnpj == "55555555000155"
        assert tender.proposals[0].offer_value == 80000.0


    def test_comprasnet_service_tender_id_fallback(self, comprasnet_service, mock_tender_data):
        id_compra = "999999999"

        mock_tender_data_no_code = {
            "objetoCompra": "Prestação de Serviços",
            "valorTotalEstimado": 1000000.0,
            "orgaoEntidadeRazaoSocial": "ORGÃO TESTE"
        }

        comprasnet_service.tender_service.fetch_tender = Mock(return_value=mock_tender_data_no_code)
        comprasnet_service.items_service.fetch_items = Mock(return_value=[])
        comprasnet_service.proposals_service.fetch_proposals = Mock(return_value=[])

        tender = comprasnet_service.fetch_tender_by_id(id_compra)

        assert tender is not None
        assert tender.tender_id == "999999999"


if __name__ == "__main__":
    pytest.main(["-s", "-v", __file__])
