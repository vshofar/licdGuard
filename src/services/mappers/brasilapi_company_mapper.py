from typing import Dict, Any, List
from models.ingestor_schemas_v2 import CompanyNode, AddressNode, PartnerNode


class ReceitaFederalCompanyConverter:

    REQUIRED_FIELDS = [
        "cnpj",
        "razao_social",
        "capital_social",
        "data_inicio_atividade",
    ]

    @classmethod
    def _validate_required_fields(cls, payload: Dict[str, Any]) -> None:
        missing_fields = [
            field for field in cls.REQUIRED_FIELDS
            if payload.get(field) is None or str(payload.get(field)).strip() == ""
        ]
        if missing_fields:
            raise ValueError(
                f"Missing required fields in BrasilAPI payload: {', '.join(missing_fields)}"
            )

    @classmethod
    def _parse_partners(cls, raw_qsa: List[Dict[str, Any]]) -> List[PartnerNode]:
        partners: List[PartnerNode] = []
        if not raw_qsa:
            return partners

        for raw_partner in raw_qsa:
            partner_id = (
                raw_partner.get("cpf_cnpj_socio")
                or raw_partner.get("cnpj_cpf_do_socio")
                or "NOT_PROVIDED"
            )
            partner_name = (
                raw_partner.get("nome_socio")
                or raw_partner.get("nome_socio_raz_social")
                or "DESCONHECIDO"
            )
            qualification = (
                raw_partner.get("qualificacao_socio")
                or raw_partner.get("qualificacao_representante_legal")
            )

            partner = PartnerNode(
                partner_id=str(partner_id),
                partner_name=str(partner_name),
                qualification=str(qualification) if qualification else None,
            )
            partners.append(partner)

        return partners

    @classmethod
    def _parse_address(cls, payload: Dict[str, Any]) -> AddressNode:
        street_type = payload.get("descricao_tipo_de_logradouro") or ""
        street_name = payload.get("logradouro") or ""

        street = f"{street_type} {street_name}".strip() if street_type else street_name.strip()
        if not street:
            street = "NAO_INFORMADO"

        return AddressNode(
            street=street,
            number=str(payload.get("numero") or "S/N"),
            zip_code=str(payload.get("cep") or "00000000"),
            city=payload.get("municipio"),
            state=payload.get("uf"),
        )

    @classmethod
    def to_company_node(cls, raw_response: Dict[str, Any]) -> CompanyNode:
        cls._validate_required_fields(raw_response)

        cnpj = "".join(filter(str.isdigit, str(raw_response["cnpj"])))
        legal_name = str(raw_response["razao_social"])
        share_capital = float(raw_response["capital_social"])
        creation_date = str(raw_response["data_inicio_atividade"]).split("T")[0]

        address = cls._parse_address(raw_response)
        raw_qsa = raw_response.get("qsa") or []
        partners = cls._parse_partners(raw_qsa)

        return CompanyNode(
            cnpj=cnpj,
            legal_name=legal_name,
            share_capital=share_capital,
            creation_date=creation_date,
            address=address,
            partners=partners,
        )