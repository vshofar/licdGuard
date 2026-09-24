import pytest
from testcontainers.neo4j import Neo4jContainer
from src.database.neo4j_client import Neo4jClient
from src.agents.ingestor_agent import IngestorAgent
from src.models.ingestor_schemas import CompanyInput, PartnerInput, TenderInput, ProposalInput


@pytest.fixture(scope="module")
def neo4j_container():
    """Create a Neo4j container that persists across all tests in the module."""
    print("🐳 Starting Neo4j container for module...")
    with Neo4jContainer("neo4j:5") as neo4j_docker:
        yield neo4j_docker
    print("🧹 Neo4j container destroyed after all tests")


@pytest.fixture(scope="module")
def neo4j_client(neo4j_container):
    """Create a Neo4j client that persists across all tests in the module."""
    uri = neo4j_container.get_connection_url()
    username = neo4j_container.username
    password = neo4j_container.password
    
    print(f"⚡ Neo4j running at: {uri}")
    
    db = Neo4jClient(uri=uri, user=username, password=password)
    db.connect()
    yield db
    db.close()


def clear_database(db):
    """Clear all data from the Neo4j database."""
    cypher = "MATCH (n) DETACH DELETE n"
    db.query(cypher)


def test_save_company_with_partners_integration(neo4j_client):
    print("🧪 Running test_save_company_with_partners_integration...")
    
    clear_database(neo4j_client)
    
    agent = IngestorAgent(neo4j_client)
    
    # Create test company with partners
    company = CompanyInput(
        cnpj="11111111000111",
        company_name="Test Company Ltda",
        address="Rua Teste, 123",
        partners=[
            PartnerInput(
                masked_cpf="***.111.222-**",
                name="Partner One",
                participation_pct=50.0
            ),
            PartnerInput(
                masked_cpf="***.333.444-**",
                name="Partner Two",
                participation_pct=30.0
            )
        ]
    )
    
    # Save to database
    agent.save_company_with_partners(company)
    print("✅ Company saved to Neo4j")
    
    # Verify data was inserted correctly
    cypher_verify = """
    MATCH (c:Company {cnpj: $cnpj})
    OPTIONAL MATCH (c)<-[r:PARTNER_OF]-(p:Partner)
    RETURN c.company_name AS company, 
           c.address AS address,
           collect({name: p.name, cpf: p.cpf, pct: r.participation_pct}) AS partners
    """
    result = neo4j_client.query(cypher_verify, {"cnpj": "11111111000111"})
    
    assert len(result) == 1, "Company should be found"
    company_data = result[0]
    
    assert company_data["company"] == "Test Company Ltda"
    assert company_data["address"] == "Rua Teste, 123"
    assert len(company_data["partners"]) == 2
    
    # Verify partners
    partner_names = {p["name"] for p in company_data["partners"]}
    assert "Partner One" in partner_names
    assert "Partner Two" in partner_names
    
    print("✅ Data verified in Neo4j")
    print(f"   Company: {company_data['company']}")
    print(f"   Partners: {len(company_data['partners'])}")


def test_save_tender_with_proposals_integration(neo4j_client):
    print("🧪 Running test_save_tender_with_proposals_integration...")
    
    clear_database(neo4j_client)
    
    agent = IngestorAgent(neo4j_client)
    
    # First, create companies
    company1 = CompanyInput(
        cnpj="11111111000111",
        company_name="Company A",
        address="Address A"
    )
    company2 = CompanyInput(
        cnpj="22222222000122",
        company_name="Company B",
        address="Address B"
    )
    
    agent.save_company_with_partners(company1)
    agent.save_company_with_partners(company2)
    print("✅ Companies created")
    
    # Create tender with proposals
    tender = TenderInput(
        tender_id="LIC-102/2026",
        object="Hospital Renovation",
        estimated_value=1500000.00,
        buyer_agency="Health Department",
        proposals=[
            ProposalInput(
                company_cnpj="11111111000111",
                offer_value=1490000.00
            ),
            ProposalInput(
                company_cnpj="22222222000122",
                offer_value=1495000.00
            )
        ]
    )
    
    agent.save_tender_with_proposals(tender)
    print("✅ Tender saved to Neo4j")
    
    # Verify data was inserted correctly
    cypher_verify = """
    MATCH (t:Tender {id: $tender_id})
    OPTIONAL MATCH (c:Company)-[p:PARTICIPATED_IN]->(t)
    RETURN t.object AS object,
           t.estimated_value AS value,
           t.buyer_agency AS agency,
           collect({cnpj: c.cnpj, offer: p.offer_value}) AS proposals
    """
    result = neo4j_client.query(cypher_verify, {"tender_id": "LIC-102/2026"})
    
    assert len(result) == 1, "Tender should be found"
    tender_data = result[0]
    
    assert tender_data["object"] == "Hospital Renovation"
    assert tender_data["value"] == 1500000.00
    assert tender_data["agency"] == "Health Department"
    assert len(tender_data["proposals"]) == 2
    
    # Verify proposals
    proposal_values = {p["offer"] for p in tender_data["proposals"]}
    assert 1490000.00 in proposal_values
    assert 1495000.00 in proposal_values
    
    print("✅ Data verified in Neo4j")
    print(f"   Tender: {tender_data['object']}")
    print(f"   Proposals: {len(tender_data['proposals'])}")


def test_full_workflow_integration(neo4j_client):
    print("🧪 Running test_full_workflow_integration...")
    
    clear_database(neo4j_client)
    
    agent = IngestorAgent(neo4j_client)
    
    # Create companies with shared partner (fraud scenario)
    company1 = CompanyInput(
        cnpj="11111111000111",
        company_name="Alpha Construction",
        address="Rua das Flores, 100",
        partners=[
            PartnerInput(
                masked_cpf="***.111.222-**",
                name="Common Partner",
                participation_pct=50.0
            )
        ]
    )
    
    company2 = CompanyInput(
        cnpj="22222222000122",
        company_name="Beta Engineering",
        address="Rua das Flores, 100",
        partners=[
            PartnerInput(
                masked_cpf="***.111.222-**",
                name="Common Partner",
                participation_pct=80.0
            )
        ]
    )
    
    agent.save_company_with_partners(company1)
    agent.save_company_with_partners(company2)
    print("✅ Companies with shared partner created")
    
    # Create tender
    tender = TenderInput(
        tender_id="LIC-102/2026",
        object="Road Construction",
        estimated_value=2000000.00,
        buyer_agency="Transport Department",
        proposals=[
            ProposalInput(
                company_cnpj="11111111000111",
                offer_value=1990000.00
            ),
            ProposalInput(
                company_cnpj="22222222000122",
                offer_value=1995000.00
            )
        ]
    )
    
    agent.save_tender_with_proposals(tender)
    print("✅ Tender with proposals saved")
    
    # Run fraud detection query
    cypher_audit = """
    MATCH (c1:Company)-[:PARTICIPATED_IN]->(t:Tender)<-[:PARTICIPATED_IN]-(c2:Company)
    WHERE c1.cnpj < c2.cnpj
    MATCH (p:Partner)-[:PARTNER_OF]->(c1)
    MATCH (p)-[:PARTNER_OF]->(c2)
    RETURN 
        t.id AS tender,
        c1.company_name AS company1,
        c2.company_name AS company2,
        p.name AS common_partner,
        c1.address AS address1,
        c2.address AS address2
    """
    results = neo4j_client.query(cypher_audit)
    
    assert len(results) > 0, "Fraud should be detected"
    fraud_alert = results[0]
    
    assert fraud_alert["tender"] == "LIC-102/2026"
    assert fraud_alert["company1"] == "Alpha Construction"
    assert fraud_alert["company2"] == "Beta Engineering"
    assert fraud_alert["common_partner"] == "Common Partner"
    assert fraud_alert["address1"] == fraud_alert["address2"]
    
    print("🚨 Fraud detected and validated:")
    print(f"   Tender: {fraud_alert['tender']}")
    print(f"   Companies: {fraud_alert['company1']} & {fraud_alert['company2']}")
    print(f"   Common Partner: {fraud_alert['common_partner']}")
    print(f"   Same Address: {fraud_alert['address1'] == fraud_alert['address2']}")

