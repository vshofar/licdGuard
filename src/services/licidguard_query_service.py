import logging
from typing import Dict, Any, List
from models.ingestor_schemas_v2 import IngestionPayload, CompanyNode
from services.mappers.comprasnet_tender_mapper import ComprasNetTenderMapper
from services.mappers.comprasnet_winners_mapper import ComprasNetWinnersMapper
from services.mappers.brasilapi_company_mapper import BrasilCompanyMapper
from services.apis.comprasnet_tender_service import ComprasnetTenderService
from services.apis.comprasnet_winners_service import ComprasnetWinnersService
from services.apis.brasil_api_service import BrasilAPIService

logger = logging.getLogger(__name__)


class LicitGuardQueryService:

    def __init__(
        self,
        tender_service: ComprasnetTenderService,
        winners_service: ComprasnetWinnersService,
        brasilapi_service: BrasilAPIService
    ):
        self.tender_service = tender_service
        self.winners_service = winners_service
        self.brasilapi_service = brasilapi_service

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

    def build_payload_for_tender(self, tender_id: str) -> IngestionPayload:
        raw_tender_data = self.tender_service.fetch_tender(tender_id)
        public_agency, tender = ComprasNetTenderMapper.to_nodes(raw_tender_data)

        raw_winners_data = self.winners_service.fetch_winners(tender_id)
        items, partial_companies = ComprasNetWinnersMapper.to_nodes(raw_winners_data)

        enriched_winners: List[CompanyNode] = []

        for partial_company in partial_companies:
            raw_company_data = self.brasilapi_service.fetch_company(
                partial_company.cnpj
            )
            enriched_company = BrasilCompanyMapper.to_company_node(
                raw_company_data
            )
            merged_company = self._merge_company_data(
                partial_company, enriched_company
            )
            enriched_winners.append(merged_company)

        return IngestionPayload(
            public_agency=public_agency,
            tender=tender,
            items=items,
            winners=enriched_winners,
        )