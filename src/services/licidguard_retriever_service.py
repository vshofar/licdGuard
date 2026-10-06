from typing import Dict, Any, List

from models.ingestor_schemas_v2 import IngestionPayload, CompanyNode
from services.storage.licdguard_graph_storage_service import LicitGuardGraphStorageService
from services.mappers.comprasnet_tender_mapper import ComprasNetTenderMapper
from services.mappers.comprasnet_winners_mapper import ComprasNetWinnersMapper
from services.mappers.brasilapi_company_mapper import BrasilCompanyMapper
from services.apis.comprasnet_tender_service import ComprasnetTenderService
from services.apis.comprasnet_winners_service import ComprasnetWinnersService
from services.apis.brasil_api_service import BrasilAPIService



class LicidGuardRetrieverService:

    def __init__(
        self,
        tender_service: ComprasnetTenderService,
        winners_service: ComprasnetWinnersService,
        brasilapi_service: BrasilAPIService,
        ingestion_service: LicitGuardGraphStorageService,
    ):
        self.tender_service = tender_service
        self.winners_service = winners_service
        self.brasilapi_service = brasilapi_service
        self.ingestion_service = ingestion_service

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

    def _build_payload_for_tender(self, tender_id: str) -> IngestionPayload:
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

    async def process_and_ingest_tender(self, id_compra: str) -> Dict[str, Any]:
        print(f"Starting ingestion process for tender ID: {id_compra}")

        payload = self._build_payload_for_tender(id_compra)
        print(
            f"Payload built for tender {id_compra}. Total items: {len(payload.items)}, Winners: {len(payload.winners)}"
        )

        self.ingestion_service.ingest_payload(payload)
        print(f"Successfully processed and ingested tender ID: {id_compra}")

        return {
            "status": "success",
            "tender_id": payload.tender.tender_id,
            "items_count": len(payload.items),
            "winners_count": len(payload.winners),
        }
