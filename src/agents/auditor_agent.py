from typing import Dict, Any
from src.database.neo4j_client import Neo4jClient


class AuditorAgent:
    def __init__(self, neo4j_client: Neo4jClient):
        self.db = neo4j_client

    def audit_tender(self, tender_id: str) -> Dict[str, Any]:
        """Executa auditoria no grafo LicitGuard para um id_compra específico."""

        # 1. Sócios em comum entre empresas vencedoras/participantes dos itens do certame
        query_partners = """
        MATCH (t:Tender {tender_id: $tender_id})<-[:FOR_TENDER]-(i:TenderItem)<-[:WON_ITEM]-(c1:Company)
        MATCH (t)<-[:FOR_TENDER]-(i2:TenderItem)<-[:WON_ITEM]-(c2:Company)
        WHERE c1.cnpj < c2.cnpj
        MATCH (p:Partner)-[:PARTNER_OF]->(c1)
        MATCH (p)-[:PARTNER_OF]->(c2)
        RETURN DISTINCT c1.legal_name AS company1, c2.legal_name AS company2, p.partner_name AS partner
        """

        # 2. Endereço compartilhado entre empresas no mesmo certame
        query_addresses = """
        MATCH (t:Tender {tender_id: $tender_id})<-[:FOR_TENDER]-(i:TenderItem)<-[:WON_ITEM]-(c1:Company)-[:LOCATED_AT]->(addr:Address)
        MATCH (t)<-[:FOR_TENDER]-(i2:TenderItem)<-[:WON_ITEM]-(c2:Company)-[:LOCATED_AT]->(addr)
        WHERE c1.cnpj < c2.cnpj
        RETURN DISTINCT c1.legal_name AS company1, c2.legal_name AS company2, addr.street AS street, addr.number AS number
        """

        # 3. Empresa recém-criada (< 1 ano) levando valor alto em relação ao capital social
        query_recent_companies = """
        MATCH (t:Tender {tender_id: $tender_id})<-[:FOR_TENDER]-(i:TenderItem)<-[:WON_ITEM]-(c:Company)
        WITH t, c, SUM(i.total_value_homologated) AS total_won
        WHERE c.creation_date IS NOT NULL 
          AND duration.between(date(c.creation_date), date(substring(t.publication_date, 0, 10))).years < 1
          AND (c.share_capital IS NULL OR total_won > (c.share_capital * 10))
        RETURN c.legal_name AS company, c.creation_date AS creation_date, c.share_capital AS share_capital, total_won
        """

        # 4. Elementos gerais da licitação para contexto
        all_elements = """
        MATCH (a:PublicAgency)-[:PUBLISHED]->(t:Tender {tender_id: $tender_id})<-[:FOR_TENDER]-(i:TenderItem)<-[:WON_ITEM]-(c:Company)
        RETURN a, t, i, c
        """

        params = {"tender_id": tender_id}

        suspicious_partners = self.db.query(query_partners, params)
        suspicious_addresses = self.db.query(query_addresses, params)
        recent_companies = self.db.query(query_recent_companies, params)
        elements = self.db.query(all_elements, params)

        # Risk Score Calculation
        score = 0
        score += len(suspicious_partners) * 40
        score += len(suspicious_addresses) * 30
        score += len(recent_companies) * 20

        return {
            "tender_id": tender_id,
            "risk_score": min(score, 100),
            "alerts": {
                "shared_partners": suspicious_partners,
                "matching_addresses": suspicious_addresses,
                "recent_companies_high_value": recent_companies
            }
        }