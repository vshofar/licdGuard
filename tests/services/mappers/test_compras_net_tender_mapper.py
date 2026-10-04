import pytest
from models.ingestor_schemas_v2 import CompanyNode, TenderItemNode
from services.mappers.comprasnet_winners_mapper import ItemResultadoMapper


@pytest.fixture
def valid_result_payload() -> dict:
    return {
        "resultado": [
            {
                "idCompraItem": "1601750590006202400001",
                "idCompra": "16017505900062024",
                "numeroItemPncp": 1,
                "niFornecedor": "14208934000128",
                "nomeRazaoSocialFornecedor": "CONSTRUTORA KARBONE E COMERCIAL LTDA",
                "quantidadeHomologada": 310.0,
                "valorUnitarioHomologado": 49.0,
                "valorTotalHomologado": 15190.0,
                "situacaoCompraItemResultadoId": 1
            },
            {
                "idCompraItem": "1601750590006202400002",
                "idCompra": "16017505900062024",
                "numeroItemPncp": 2,
                "niFornecedor": "14208934000128",
                "nomeRazaoSocialFornecedor": "CONSTRUTORA KARBONE E COMERCIAL LTDA",
                "quantidadeHomologada": 1542.0,
                "valorUnitarioHomologado": 54.0,
                "valorTotalHomologado": 83268.0,
                "situacaoCompraItemResultadoId": 1
            }
        ],
        "totalRegistros": 2
    }


class TestItemResultadoConverter:

    def test_to_nodes_success(self, valid_result_payload: dict):
        items, companies = ItemResultadoMapper.to_nodes(valid_result_payload)

        assert len(items) == 2
        assert isinstance(items[0], TenderItemNode)
        assert items[0].item_id == "1601750590006202400001"
        assert items[0].tender_id == "16017505900062024"
        assert items[0].item_number == 1
        assert items[0].quantity_homologated == 310.0
        assert items[0].unit_value_homologated == 49.0
        assert items[0].total_value_homologated == 15190.0
        assert items[0].winner_cnpj == "14208934000128"

        assert len(companies) == 1
        assert isinstance(companies[0], CompanyNode)
        assert companies[0].cnpj == "14208934000128"
        assert companies[0].legal_name == "CONSTRUTORA KARBONE E COMERCIAL LTDA"

    def test_to_nodes_empty_results_raises_value_error(self):
        empty_payload = {"resultado": [], "totalRegistros": 0}

        with pytest.raises(ValueError, match="The returned payload contains no records in the 'resultado' key."):
            ItemResultadoMapper.to_nodes(empty_payload)

    @pytest.mark.parametrize("missing_field", [
        "idCompraItem",
        "idCompra",
        "niFornecedor",
        "nomeRazaoSocialFornecedor",
        "numeroItemPncp",
        "quantidadeHomologada",
        "valorUnitarioHomologado",
        "valorTotalHomologado",
        "situacaoCompraItemResultadoId"
    ])
    def test_to_nodes_missing_required_field_raises_value_error(
        self, valid_result_payload: dict, missing_field: str
    ):
        valid_result_payload["resultado"][0][missing_field] = None

        with pytest.raises(ValueError, match=f"Missing required fields for fraud analysis mapping: {missing_field}"):
            ItemResultadoMapper.to_nodes(valid_result_payload)