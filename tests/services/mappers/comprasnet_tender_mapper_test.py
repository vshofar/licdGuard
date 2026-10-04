import pytest
from models.ingestor_schemas_v2 import PublicAgencyNode, TenderNode
from services.mappers.comprasnet_tender_mapper import ComprasNetTenderMapper
from services.mappers.exceptions import RequiredValueNotFoundException, NoContentException


@pytest.fixture
def valid_tender_payload() -> dict:
    return {
        "idCompra": "16017505900062024",
        "numeroCompra": "90003",
        "anoCompraPncp": 2024,
        "objetoCompra": "Aquisicao de materiais",
        "valorTotalEstimado": 500000.0,
        "dataPublicacaoPncp": "2024-01-10T08:00:00",
        "orgaoEntidadeCnpj": "00394452000103",
        "orgaoEntidadeRazaoSocial": "MINISTERIO DA DEFESA",
        "unidadeOrgaoCodigoUnidade": "160175",
        "unidadeOrgaoNomeUnidade": "UASG TESTE"
    }


class TestComprasNetTenderMapper:

    def test_to_nodes_success(self, valid_tender_payload: dict):
        public_agency, tender = ComprasNetTenderMapper.to_nodes(valid_tender_payload)

        assert isinstance(public_agency, PublicAgencyNode)
        assert public_agency.cnpj == "00394452000103"
        assert public_agency.agency_name == "MINISTERIO DA DEFESA - UASG TESTE"
        assert public_agency.uasg_code == "160175"

        assert isinstance(tender, TenderNode)
        assert tender.tender_id == "16017505900062024"
        assert tender.notice_number == "90003/2024"
        assert tender.object_description == "Aquisicao de materiais"
        assert tender.estimated_value == 500000.0
        assert tender.publication_date == "2024-01-10"

    def test_to_nodes_empty_payload_raises_no_content_exception(self):
        empty_payload = None

        with pytest.raises(NoContentException, match="The returned payload is empty."):
            ComprasNetTenderMapper.to_nodes(empty_payload)

    def test_to_nodes_missing_unit_name(self, valid_tender_payload: dict):
        valid_tender_payload["unidadeOrgaoNomeUnidade"] = None

        public_agency, tender = ComprasNetTenderMapper.to_nodes(valid_tender_payload)

        assert public_agency.agency_name == "MINISTERIO DA DEFESA"

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
    def test_to_nodes_missing_required_field_raises_required_value_not_found_exception(
        self, valid_tender_payload: dict, missing_field: str
    ):
        valid_tender_payload[missing_field] = None

        with pytest.raises(RequiredValueNotFoundException, match=f"Missing required fields for fraud analysis mapping: {missing_field}"):
            ComprasNetTenderMapper.to_nodes(valid_tender_payload)
