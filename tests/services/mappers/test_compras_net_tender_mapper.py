import pytest
from models.ingestor_schemas_v2 import PublicAgencyNode, TenderNode
from services.mappers.compras_net_tender_mapper import ComprasNetTenderMapper


@pytest.fixture
def valid_tender_payload() -> dict:
    return {
        "resultado": [
            {
                "idCompra": "16017505900062024",
                "numeroControlePNCP": "00394452000103-1-000003/2024",
                "anoCompraPncp": 2024,
                "orgaoEntidadeCnpj": "00394452000103",
                "orgaoEntidadeRazaoSocial": "COMANDO DO EXERCITO",
                "unidadeOrgaoCodigoUnidade": "160175",
                "unidadeOrgaoNomeUnidade": "ADMINISTRATIVA DA GUARNICÃO DE JOÃO PESSOA",
                "numeroCompra": "90006",
                "objetoCompra": "Contratação de Serviço de Instalação de Forro PVC e Gesso.",
                "valorTotalEstimado": 465799.67,
                "dataPublicacaoPncp": "2023-11-27T07:05:52"
            }
        ],
        "totalRegistros": 1
    }


class TestComprasNetTenderMapper:

    def test_to_nodes_success(self, valid_tender_payload: dict):
        public_agency, tender = ComprasNetTenderMapper.to_nodes(valid_tender_payload)

        assert isinstance(public_agency, PublicAgencyNode)
        assert public_agency.cnpj == "00394452000103"
        assert public_agency.agency_name == "COMANDO DO EXERCITO - ADMINISTRATIVA DA GUARNICÃO DE JOÃO PESSOA"
        assert public_agency.uasg_code == "160175"

        assert isinstance(tender, TenderNode)
        assert tender.tender_id == "16017505900062024"
        assert tender.notice_number == "90006/2024"
        assert tender.object_description == "Contratação de Serviço de Instalação de Forro PVC e Gesso."
        assert tender.estimated_value == 465799.67
        assert tender.publication_date == "2023-11-27"

    def test_to_nodes_agency_without_optional_unit_name(self, valid_tender_payload: dict):
        valid_tender_payload["resultado"][0]["unidadeOrgaoNomeUnidade"] = None

        public_agency, _ = ComprasNetTenderMapper.to_nodes(valid_tender_payload)

        assert public_agency.agency_name == "COMANDO DO EXERCITO"

    def test_to_nodes_empty_results_raises_value_error(self):
        empty_payload = {"resultado": [], "totalRegistros": 0}

        with pytest.raises(ValueError, match="The returned payload contains no records in the 'resultado' key."):
            ComprasNetTenderMapper.to_nodes(empty_payload)

    @pytest.mark.parametrize("missing_field", [
        "orgaoEntidadeCnpj",
        "orgaoEntidadeRazaoSocial",
        "unidadeOrgaoCodigoUnidade",
        "idCompra",
        "numeroCompra",
        "anoCompraPncp",
        "objetoCompra",
        "valorTotalEstimado",
        "dataPublicacaoPncp",
    ])
    def test_to_nodes_missing_required_field_raises_value_error(
        self, valid_tender_payload: dict, missing_field: str
    ):
        valid_tender_payload["resultado"][0][missing_field] = None

        with pytest.raises(ValueError, match=f"Missing required fields for fraud analysis mapping: {missing_field}"):
            ComprasNetTenderMapper.to_nodes(valid_tender_payload)