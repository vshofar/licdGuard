from unittest.mock import Mock, patch
from src.agents.ingestor_agent import IngestorAgent
from src.models.ingestor_schemas import CompanyInput, PartnerInput, TenderInput, ProposalInput


def test_save_company_with_partners():
    """Test saving a company with partners to Neo4j."""
    # Mock Neo4jClient
    mock_db = Mock()
    
    # Create IngestorAgent with mocked database
    agent = IngestorAgent(mock_db)
    
    # Create test data
    company = CompanyInput(
        cnpj="11.111.111/0001-11",
        company_name="Test Company Ltda",
        address="Test Address, 123",
        partners=[
            PartnerInput(
                masked_cpf="***.111.222-**",
                name="Test Partner",
                participation_pct=50.0
            )
        ]
    )
    
    # Call the method
    agent.save_company_with_partners(company)
    
    # Verify db.query was called
    assert mock_db.query.called
    
    # Get the call arguments
    call_args = mock_db.query.call_args
    cypher_query = call_args[0][0]
    params = call_args[0][1]
    
    # Verify Cypher query structure
    assert "MERGE (c:Company {cnpj: $cnpj})" in cypher_query
    assert "MERGE (p:Partner {cpf: p_data.masked_cpf})" in cypher_query
    assert "MERGE (p)-[r:PARTNER_OF]->(c)" in cypher_query
    
    # Verify parameters
    assert params["cnpj"] == "11111111000111"
    assert params["company_name"] == "Test Company Ltda"
    assert params["address"] == "Test Address, 123"
    assert len(params["partners"]) == 1
    assert params["partners"][0]["masked_cpf"] == "***.111.222-**"
    assert params["partners"][0]["name"] == "Test Partner"
    assert params["partners"][0]["participation_pct"] == 50.0
    
    print("✅ test_save_company_with_partners passed")


def test_save_company_with_partners_empty_partners():
    """Test saving a company with no partners."""
    mock_db = Mock()
    agent = IngestorAgent(mock_db)
    
    company = CompanyInput(
        cnpj="11111111000111",
        company_name="Company Without Partners",
        address="Another Address, 456"
    )
    
    agent.save_company_with_partners(company)
    
    call_args = mock_db.query.call_args
    params = call_args[0][1]
    
    assert len(params["partners"]) == 0
    
    print("✅ test_save_company_with_partners_empty_partners passed")


def test_save_tender_with_proposals():
    """Test saving a tender with proposals to Neo4j."""
    mock_db = Mock()
    agent = IngestorAgent(mock_db)
    
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
    
    assert mock_db.query.called
    
    call_args = mock_db.query.call_args
    cypher_query = call_args[0][0]
    params = call_args[0][1]
    
    # Verify Cypher query structure
    assert "MERGE (t:Tender {id: $tender_id})" in cypher_query
    assert "MERGE (c:Company {cnpj: p_data.company_cnpj})" in cypher_query
    assert "MERGE (c)-[p:PARTICIPATED_IN]->(t)" in cypher_query
    
    # Verify parameters
    assert params["tender_id"] == "LIC-102/2026"
    assert params["object"] == "Hospital Renovation"
    assert params["estimated_value"] == 1500000.00
    assert params["buyer_agency"] == "Health Department"
    assert len(params["proposals"]) == 2
    
    # Verify CNPJ cleaning
    assert params["proposals"][0]["company_cnpj"] == "11111111000111"
    assert params["proposals"][0]["offer_value"] == 1490000.00
    assert params["proposals"][1]["company_cnpj"] == "22222222000122"
    assert params["proposals"][1]["offer_value"] == 1495000.00
    
    print("✅ test_save_tender_with_proposals passed")


def test_save_tender_with_proposals_empty():
    """Test saving a tender with no proposals."""
    mock_db = Mock()
    agent = IngestorAgent(mock_db)
    
    tender = TenderInput(
        tender_id="LIC-103/2026",
        object="Road Construction",
        estimated_value=2000000.00,
        buyer_agency="Transport Department"
    )
    
    agent.save_tender_with_proposals(tender)
    
    call_args = mock_db.query.call_args
    params = call_args[0][1]
    
    assert len(params["proposals"]) == 0
    
    print("✅ test_save_tender_with_proposals_empty passed")

