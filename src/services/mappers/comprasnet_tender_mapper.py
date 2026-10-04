from typing import Dict, Any, Tuple
from models.ingestor_schemas_v2 import PublicAgencyNode, TenderNode
from services.mappers.exceptions import RequiredValueNotFoundException, NoContentException


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
    def _validate_required_fields(cls, payload: Dict[str, Any]) -> None:
        missing_fields = [
            field for field in cls.REQUIRED_FIELDS
            if payload.get(field) is None or str(payload.get(field)).strip() == ""
        ]
        if missing_fields:
            raise RequiredValueNotFoundException(
                f"Missing required fields for fraud analysis mapping: {', '.join(missing_fields)}"
            )

    @classmethod
    def to_nodes(cls, raw_response: Dict[str, Any]) -> Tuple[PublicAgencyNode, TenderNode]:
        if not raw_response:
            raise NoContentException("The returned payload is empty.")

        cls._validate_required_fields(raw_response)

        agency_name = str(raw_response["orgaoEntidadeRazaoSocial"])
        unit_name = raw_response.get("unidadeOrgaoNomeUnidade")
        if unit_name and str(unit_name).strip():
            agency_name = f"{agency_name} - {unit_name}"

        public_agency = PublicAgencyNode(
            cnpj=str(raw_response["orgaoEntidadeCnpj"]),
            agency_name=agency_name,
            uasg_code=str(raw_response["unidadeOrgaoCodigoUnidade"])
        )

        notice_number = f"{raw_response['numeroCompra']}/{raw_response['anoCompraPncp']}"

        tender = TenderNode(
            tender_id=str(raw_response["idCompra"]),
            notice_number=notice_number,
            object_description=str(raw_response["objetoCompra"]),
            estimated_value=float(raw_response["valorTotalEstimado"]),
            publication_date=cls._parse_date(str(raw_response["dataPublicacaoPncp"]))
        )

        return public_agency, tender