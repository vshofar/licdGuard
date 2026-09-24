from src.database.neo4j_client import Neo4jClient
from src.models.ingestor_schemas import CompanyInput, TenderInput


class IngestorAgent:
    def __init__(self, neo4j_client: Neo4jClient):
        self.db = neo4j_client

    def save_company_with_partners(self, company: CompanyInput):

        cypher = """
        MERGE (c:Company {cnpj: $cnpj})
        ON CREATE SET c.company_name = $company_name, c.address = $address
        ON MATCH SET c.company_name = $company_name, c.address = $address

        WITH c
        UNWIND $partners AS p_data
        MERGE (p:Partner {cpf: p_data.masked_cpf})
        ON CREATE SET p.name = p_data.name

        MERGE (p)-[r:PARTNER_OF]->(c)
        ON CREATE SET r.participation_pct = p_data.participation_pct
        """
        params = {
            "cnpj": company.cnpj,
            "company_name": company.company_name,
            "address": company.address,
            "partners": [p.model_dump() for p in company.partners],
        }
        self.db.query(cypher, params)

    def save_tender_with_proposals(self, tender: TenderInput):

        cypher = """
        MERGE (t:Tender {id: $tender_id})
        ON CREATE SET 
            t.object = $object, 
            t.estimated_value = $estimated_value,
            t.buyer_agency = $buyer_agency

        WITH t
        UNWIND $proposals AS p_data
        MERGE (c:Company {cnpj: p_data.company_cnpj})

        MERGE (c)-[p:PARTICIPATED_IN]->(t)
        ON CREATE SET p.offer_value = p_data.offer_value
        """
        # Clean CNPJs from proposals before persisting
        clean_proposals = [
            {
                "company_cnpj": "".join(filter(str.isdigit, prop.company_cnpj)),
                "offer_value": prop.offer_value,
            }
            for prop in tender.proposals
        ]

        params = {
            "tender_id": tender.tender_id,
            "object": tender.object,
            "estimated_value": tender.estimated_value,
            "buyer_agency": tender.buyer_agency,
            "proposals": clean_proposals,
        }
        self.db.query(cypher, params)