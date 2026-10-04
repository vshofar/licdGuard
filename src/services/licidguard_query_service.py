import logging
from typing import Dict, Any, List
from models.ingestor_schemas_v2 import IngestionPayload, CompanyNode
from services.mappers.compras_net_tender_mapper import ComprasNetTenderMapper
from services.mappers.comprasnet_winners_mapper import ItemResultadoMapper
from services.mappers.brasilapi_company_mapper import ReceitaFederalCompanyConverter

logger = logging.getLogger(__name__)


class LicitGuardQueryService:

    def __init__(self, comprasnet_client: Any, brasilapi_client: Any):
        self.comprasnet_client = comprasnet_client
        self.brasilapi_client = brasilapi_client

    def _merge_company_data(
        self, partial_company: CompanyNode, enriched_company: CompanyNode
    ) -> CompanyNode:
        return CompanyNode(
            cnpj=partial_company.cnpj,
            legal_name=enriched_company.legal_name or partial_company.legal_name,
            share_capital=enriched_company.share_capital,
            creation_date=enriched_company.creation_date,
            address=enriched_company.address,
            partners=enriched_company.partners,
        )

    async def build_payload_for_tender(self, id_compra: str) -> IngestionPayload:
        raw_tender_data = await self.comprasnet_client.get_tender_by_id(id_compra)
        public_agency, tender = ComprasNetTenderMapper.to_nodes(raw_tender_data)

        raw_items_data = await self.comprasnet_client.get_tender_items_results(id_compra)
        items, partial_companies = ItemResultadoMapper.to_nodes(raw_items_data)

        enriched_winners: List[CompanyNode] = []

        for partial_company in partial_companies:
            try:
                raw_company_data = await self.brasilapi_client.get_company_by_cnpj(
                    partial_company.cnpj
                )
                enriched_company = ReceitaFederalCompanyConverter.to_company_node(
                    raw_company_data
                )
                merged_company = self._merge_company_data(
                    partial_company, enriched_company
                )
                enriched_winners.append(merged_company)
            except Exception as e:
                logger.warning(
                    f"Failed to enrich company {partial_company.cnpj} via BrasilAPI: {str(e)}"
                )
                enriched_winners.append(partial_company)

        return IngestionPayload(
            public_agency=public_agency,
            tender=tender,
            items=items,
            winners=enriched_winners,
        )