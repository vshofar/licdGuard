import logging
from typing import Dict, Any

from services.ingestion.licdguard_graph_ingestion_service import LicitGuardGraphIngestionService
from services.licidguard_query_service import LicitGuardQueryService

logger = logging.getLogger(__name__)


class LicidGuardRetrieverService:

    def __init__(
        self,
        query_service: LicitGuardQueryService,
        ingestion_service: LicitGuardGraphIngestionService,
    ):
        self.query_service = query_service
        self.ingestion_service = ingestion_service

    async def process_and_ingest_tender(self, id_compra: str) -> Dict[str, Any]:
        logger.info(f"Starting ingestion process for tender ID: {id_compra}")

        payload = self.query_service.build_payload_for_tender(id_compra)
        logger.info(
            f"Payload built for tender {id_compra}. Total items: {len(payload.items)}, Winners: {len(payload.winners)}"
        )

        self.ingestion_service.ingest_payload(payload)
        logger.info(f"Successfully processed and ingested tender ID: {id_compra}")

        return {
            "status": "success",
            "tender_id": payload.tender.tender_id,
            "items_count": len(payload.items),
            "winners_count": len(payload.winners),
        }