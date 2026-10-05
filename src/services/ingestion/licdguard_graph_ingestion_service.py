import logging
from typing import Dict, Any

from database import Neo4jClient
from models.ingestor_schemas_v2 import IngestionPayload

logger = logging.getLogger(__name__)


class LicitGuardGraphIngestionService:

    INGESTION_CYPHER = """
    MERGE (agency:PublicAgency {cnpj: $agency.cnpj})
    ON CREATE SET 
        agency.agency_name = $agency.agency_name,
        agency.uasg_code = $agency.uasg_code
    ON MATCH SET 
        agency.agency_name = $agency.agency_name,
        agency.uasg_code = $agency.uasg_code

    MERGE (tender:Tender {tender_id: $tender.tender_id})
    ON CREATE SET 
        tender.notice_number = $tender.notice_number,
        tender.object_description = $tender.object_description,
        tender.estimated_value = $tender.estimated_value,
        tender.publication_date = datetime($tender.publication_date)
    ON MATCH SET 
        tender.notice_number = $tender.notice_number,
        tender.object_description = $tender.object_description,
        tender.estimated_value = $tender.estimated_value,
        tender.publication_date = datetime($tender.publication_date)

    MERGE (agency)-[:PUBLISHED]->(tender)

    WITH tender
    UNWIND $winners AS w
    MERGE (company:Company {cnpj: w.cnpj})
    ON CREATE SET 
        company.legal_name = w.legal_name,
        company.share_capital = w.share_capital,
        company.creation_date = CASE WHEN w.creation_date IS NOT NULL THEN date(w.creation_date) ELSE NULL END
    ON MATCH SET 
        company.legal_name = coalesce(w.legal_name, company.legal_name),
        company.share_capital = CASE WHEN w.share_capital > 0.0 THEN w.share_capital ELSE company.share_capital END,
        company.creation_date = CASE WHEN w.creation_date IS NOT NULL THEN date(w.creation_date) ELSE company.creation_date END

    FOREACH (addr IN CASE WHEN w.address IS NOT NULL THEN [w.address] ELSE [] END |
        MERGE (address:Address {address_hash: addr.address_hash})
        ON CREATE SET 
            address.street = addr.street,
            address.number = addr.number,
            address.zip_code = addr.zip_code,
            address.city = addr.city,
            address.state = addr.state
        MERGE (company)-[:LOCATED_AT]->(address)
    )

    FOREACH (p IN w.partners |
        MERGE (partner:Partner {partner_id: p.partner_id})
        ON CREATE SET 
            partner.partner_name = p.partner_name
        ON MATCH SET 
            partner.partner_name = p.partner_name
        MERGE (partner)-[r:PARTNER_OF]->(company)
        SET r.qualification = p.qualification
    )

    WITH tender
    UNWIND $items AS item
    MERGE (tender_item:TenderItem {item_id: item.item_id})
    ON CREATE SET 
        tender_item.item_number = item.item_number,
        tender_item.quantity_homologated = item.quantity_homologated,
        tender_item.unit_value_homologated = item.unit_value_homologated,
        tender_item.total_value_homologated = item.total_value_homologated
    ON MATCH SET 
        tender_item.item_number = item.item_number,
        tender_item.quantity_homologated = item.quantity_homologated,
        tender_item.unit_value_homologated = item.unit_value_homologated,
        tender_item.total_value_homologated = item.total_value_homologated

    MERGE (tender)-[:HAS_ITEM]->(tender_item)

    WITH tender_item, item
    MATCH (winner:Company {cnpj: item.winner_cnpj})
    MERGE (winner)-[:WON_ITEM]->(tender_item)
    """

    def __init__(self, neo4j_client: Neo4jClient):
        self.client = neo4j_client

    def _prepare_params(self, payload: IngestionPayload) -> Dict[str, Any]:
        return {
            "agency": payload.public_agency.model_dump(),
            "tender": payload.tender.model_dump(),
            "items": [item.model_dump() for item in payload.items],
            "winners": [winner.model_dump() for winner in payload.winners],
        }

    def ingest_payload(self, payload: IngestionPayload) -> None:
        params = self._prepare_params(payload)
        try:
            self.client.query(self.INGESTION_CYPHER, params)
            logger.info(
                f"Successfully ingested tender {payload.tender.tender_id} into Neo4j."
            )
        except Exception as e:
            logger.error(
                f"Failed to ingest tender {payload.tender.tender_id} into Neo4j: {str(e)}"
            )
            raise e