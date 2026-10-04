import pytest
from models.ingestor_schemas_v2 import CompanyNode, AddressNode, PartnerNode
from services.mappers.brasilapi_company_mapper import BrasilCompanyMapper
from services.mappers.exceptions import RequiredValueNotFoundException, NoContentException


@pytest.fixture
def valid_brasilapi_payload() -> dict:
    return {
        "cnpj": "14208934000128",
        "razao_social": "CONSTRUTORA KARBONE E COMERCIAL LTDA",
        "capital_social": 100000.0,
        "data_inicio_atividade": "2011-08-15",
        "descricao_tipo_de_logradouro": "RUA",
        "logradouro": "PEIXOTO GOMIDE",
        "numero": "100",
        "cep": "01409000",
        "municipio": "SAO PAULO",
        "uf": "SP",
        "qsa": [
            {
                "cpf_cnpj_socio": "***123456**",
                "nome_socio": "JOAO DA SILVA",
                "qualificacao_socio": "Sócio-Administrador"
            }
        ]
    }


class TestBrasilCompanyMapper:

    def test_to_company_node_success(self, valid_brasilapi_payload: dict):
        company = BrasilCompanyMapper.to_company_node(valid_brasilapi_payload)

        assert isinstance(company, CompanyNode)
        assert company.cnpj == "14208934000128"
        assert company.legal_name == "CONSTRUTORA KARBONE E COMERCIAL LTDA"
        assert company.share_capital == 100000.0
        assert company.creation_date == "2011-08-15"

        assert isinstance(company.address, AddressNode)
        assert company.address.street == "RUA PEIXOTO GOMIDE"
        assert company.address.number == "100"
        assert company.address.zip_code == "01409000"
        assert company.address.city == "SAO PAULO"
        assert company.address.state == "SP"
        assert company.address.address_hash is not None

        assert len(company.partners) == 1
        partner = company.partners[0]
        assert isinstance(partner, PartnerNode)
        assert partner.partner_id == "***123456**"
        assert partner.partner_name == "JOAO DA SILVA"
        assert partner.qualification == "Sócio-Administrador"

    def test_to_company_node_empty_payload_raises_no_content_exception(self):
        with pytest.raises(NoContentException, match="The returned payload is empty."):
            BrasilCompanyMapper.to_company_node(None)

    def test_to_company_node_empty_qsa_and_address_fallbacks(self, valid_brasilapi_payload: dict):
        valid_brasilapi_payload["qsa"] = []
        valid_brasilapi_payload["descricao_tipo_de_logradouro"] = None
        valid_brasilapi_payload["logradouro"] = None
        valid_brasilapi_payload["numero"] = None
        valid_brasilapi_payload["cep"] = None

        company = BrasilCompanyMapper.to_company_node(valid_brasilapi_payload)

        assert len(company.partners) == 0
        assert company.address.street == "NAO_INFORMADO"
        assert company.address.number == "S/N"
        assert company.address.zip_code == "00000000"

    @pytest.mark.parametrize("missing_field", [
        "cnpj",
        "razao_social",
        "capital_social",
        "data_inicio_atividade"
    ])
    def test_to_company_node_missing_required_field_raises_required_value_not_found_exception(
        self, valid_brasilapi_payload: dict, missing_field: str
    ):
        valid_brasilapi_payload[missing_field] = None

        with pytest.raises(RequiredValueNotFoundException, match=f"Missing required fields in BrasilAPI payload: {missing_field}"):
            BrasilCompanyMapper.to_company_node(valid_brasilapi_payload)