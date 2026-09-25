from typing import Dict, Any
from src.database.neo4j_client import Neo4jClient


class AuditorAgent:
    def __init__(self, db: Neo4jClient):
        self.db = db

    def audit_tender(self, tender_id: str) -> Dict[str, Any]:
        """Executes a full audit for a specific tender."""

        query_partners = """
        MATCH (c1:Company)-[:PARTICIPATED_IN]->(t:Tender {id: $tender_id})
        MATCH (c2:Company)-[:PARTICIPATED_IN]->(t)
        WHERE c1.cnpj < c2.cnpj
        MATCH (p:Partner)-[:PARTNER_OF]->(c1)
        MATCH (p)-[:PARTNER_OF]->(c2)
        RETURN c1.company_name AS company1, c2.company_name AS company2, p.name AS partner
        """

        query_addresses = """
        MATCH (c1:Company)-[:PARTICIPATED_IN]->(t:Tender {id: $tender_id})
        MATCH (c2:Company)-[:PARTICIPATED_IN]->(t)
        WHERE c1.cnpj < c2.cnpj AND c1.address = c2.address AND c1.address IS NOT NULL
        RETURN c1.company_name AS company1, c2.company_name AS company2, c1.address AS address
        """

        query_cover_bids = """
        MATCH (c:Company)-[p:PARTICIPATED_IN]->(t:Tender {id: $tender_id})
        WHERE p.offer_value > (t.estimated_value * 1.20)
        RETURN c.company_name AS company, p.offer_value AS offer_value, t.estimated_value AS estimated_value
        """

        all_elements = """
        MATCH (c:Company)-[p:PARTICIPATED_IN]->(t:Tender {id: $tender_id})
        RETURN c, p.offer_amount, t.estimated_value
        """

        params = {"tender_id": tender_id}

        suspicious_partners = self.db.query(query_partners, params)
        suspicious_addresses = self.db.query(query_addresses, params)
        cover_bids = self.db.query(query_cover_bids, params)
        all_elements = self.db.query(all_elements, params)

        # Risk Score Calculation
        score = 0
        score += len(suspicious_partners) * 40
        score += len(suspicious_addresses) * 30
        score += len(cover_bids) * 20

        return {
            "tender_id": tender_id,
            "risk_score": min(score, 100),
            "alerts": {
                "shared_partners": suspicious_partners,
                "matching_addresses": suspicious_addresses,
                "cover_bids": cover_bids
            }
        }