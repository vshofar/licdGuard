from typing import Dict, Any, Tuple
from models.ingestor_schemas_v2 import PublicAgencyNode, TenderNode


class ComprasNetTenderMapper:

    REQUIRED_FIELDS = [
        "orgaoEntidadeCnpj",
        "orgaoEntidadeRazaoSocial",
        "unidadeOrgaoCodigoUnidade",
        "idCompra",
        "numeroCompra",
        "anoCompraPncp",
        "objetoCompra",
        "valorTotalEstimado",
        "dataPublicacaoPncp",
    ]

    @staticmethod
    def _parse_date(datetime_str: str) -> str:
        return datetime_str.split("T")[0]

    @classmethod
    def _validate_required_fields(cls, payload_item: Dict[str, Any]) -> None:
        missing_fields = [
            field for field in cls.REQUIRED_FIELDS
            if payload_item.get(field) is None or str(payload_item.get(field)).strip() == ""
        ]
        if missing_fields:
            raise ValueError(
                f"Missing required fields for fraud analysis mapping: {', '.join(missing_fields)}"
            )

    @classmethod
    def to_nodes(cls, raw_response: Dict[str, Any]) -> Tuple[PublicAgencyNode, TenderNode]:
        results = raw_response.get("resultado", [])
        if not results:
            raise ValueError("The returned payload contains no records in the 'resultado' key.")

        payload_item = results[0]

        cls._validate_required_fields(payload_item)

        agency_name = str(payload_item["orgaoEntidadeRazaoSocial"])
        unit_name = payload_item.get("unidadeOrgaoNomeUnidade")
        if unit_name and str(unit_name).strip():
            agency_name = f"{agency_name} - {unit_name}"

        public_agency = PublicAgencyNode(
            cnpj=str(payload_item["orgaoEntidadeCnpj"]),
            agency_name=agency_name,
            uasg_code=str(payload_item["unidadeOrgaoCodigoUnidade"])
        )

        notice_number = f"{payload_item['numeroCompra']}/{payload_item['anoCompraPncp']}"

        tender = TenderNode(
            tender_id=str(payload_item["idCompra"]),
            notice_number=notice_number,
            object_description=str(payload_item["objetoCompra"]),
            estimated_value=float(payload_item["valorTotalEstimado"]),
            publication_date=cls._parse_date(str(payload_item["dataPublicacaoPncp"]))
        )

        return public_agency, tender