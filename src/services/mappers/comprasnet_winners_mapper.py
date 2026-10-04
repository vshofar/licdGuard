from typing import Dict, Any, List, Tuple
from models.ingestor_schemas_v2 import CompanyNode, TenderItemNode
from services.mappers.exceptions import RequiredValueNotFoundException, NoContentException


class ComprasNetWinnersMapper:

    REQUIRED_FIELDS = [
        "idCompraItem",
        "idCompra",
        "niFornecedor",
        "nomeRazaoSocialFornecedor",
        "numeroItemPncp",
        "quantidadeHomologada",
        "valorUnitarioHomologado",
        "valorTotalHomologado",
        "situacaoCompraItemResultadoId",
    ]

    @classmethod
    def _validate_required_fields(cls, item: Dict[str, Any]) -> None:
        missing_fields = [
            field for field in cls.REQUIRED_FIELDS
            if item.get(field) is None or str(item.get(field)).strip() == ""
        ]
        if missing_fields:
            raise RequiredValueNotFoundException(
                f"Missing required fields for fraud analysis mapping: {', '.join(missing_fields)}"
            )

    @classmethod
    def to_nodes(
        cls, raw_response: List[Dict[str, Any]]
    ) -> Tuple[List[TenderItemNode], List[CompanyNode]]:
        if not raw_response:
            raise NoContentException("The returned payload is empty.")

        items: List[TenderItemNode] = []
        unique_companies: Dict[str, CompanyNode] = {}

        for raw_item in raw_response:
            cls._validate_required_fields(raw_item)

            cnpj = "".join(filter(str.isdigit, str(raw_item["niFornecedor"])))

            item_node = TenderItemNode(
                item_id=str(raw_item["idCompraItem"]),
                tender_id=str(raw_item["idCompra"]),
                item_number=int(raw_item["numeroItemPncp"]),
                quantity_homologated=float(raw_item["quantidadeHomologada"]),
                unit_value_homologated=float(raw_item["valorUnitarioHomologado"]),
                total_value_homologated=float(raw_item["valorTotalHomologado"]),
                winner_cnpj=cnpj,
            )
            items.append(item_node)

            if cnpj not in unique_companies:
                unique_companies[cnpj] = CompanyNode(
                    cnpj=cnpj,
                    legal_name=str(raw_item["nomeRazaoSocialFornecedor"]),
                    share_capital=0.0,
                    creation_date=None,
                    address=None,
                    partners=[],
                )

        return items, list(unique_companies.values())