from testcontainers.neo4j import Neo4jContainer
from src.database.neo4j_client import Neo4jClient


def test_neo4j_with_container():
    print("🐳 Starting Neo4j Docker container for automated testing...")

    with Neo4jContainer("neo4j:5") as neo4j_docker:
        uri = neo4j_docker.get_connection_url()
        username = neo4j_docker.username
        password = neo4j_docker.password

        print(f"⚡ Neo4j container running at dynamic URL: {uri}")

        db = Neo4jClient(uri=uri, user=username, password=password)
        db.connect()

        try:
            validate_licid(db)
        finally:
            db.close()

    print("🧹 Test completed! Ephemeral Docker container destroyed successfully.")


def validate_licid(db: Neo4jClient):
    print("🏗️ Inserting test subgraph (Tender + Companies + Partners)...")

    cypher_population = create_licd_scenario()
    db.query(cypher_population)

    print("✅ Subgraph inserted into Neo4j successfully!")

    print("\n🔍 Running Cypher audit on ephemeral graph...")
    cypher_audit = query_licd_scenario()
    results = db.query(cypher_audit)

    assert len(results) > 0, "Audit query should return at least one alert."

    result = results[0]
    print("\n🚨 FRAUD ALERT DETECTED AND VALIDATED:")
    print(f" • Audited Tender: {result['tender']}")
    print(f" • Competitor Company A: {result['company1']}")
    print(f" • Competitor Company B: {result['company2']}")
    print(f" • Hidden Common Partner: {result['partner']}")
    print(f" • Matching Addresses: {result['address1'] == result['address2']}")
    print("-" * 60)


def query_licd_scenario() -> str:
    cypher_audit = """
            MATCH (c1:Company)-[:PARTICIPATED_IN]->(t:Tender)<-[:PARTICIPATED_IN]-(c2:Company)
            WHERE c1.cnpj < c2.cnpj
            MATCH (p:Partner)-[:PARTNER_OF]->(c1)
            MATCH (p)-[:PARTNER_OF]->(c2)
            RETURN 
                t.id AS tender, 
                c1.company_name AS company1, 
                c2.company_name AS company2, 
                p.name AS partner,
                c1.address AS address1,
                c2.address AS address2
            """
    return cypher_audit


def create_licd_scenario() -> str:
    return """
            // 1. Create Tender
            CREATE (t:Tender {id: "LIC-102/2026", object: "Hospital Renovation", value: 1500000.00})

            // 2. Create Competitor Companies
            CREATE (c1:Company {cnpj: "11.111.111/0001-11", company_name: "Alfa Construções LTDA", address: "Rua das Flores, 100"})
            CREATE (c2:Company {cnpj: "22.222.222/0001-22", company_name: "Beta Engenharia LTDA", address: "Rua das Flores, 100"})

            // 3. Create Common Partner
            CREATE (p:Partner {cpf: "000.111.222-33", name: "Carlos Alberto da Silva"})

            // 4. Create Relationships
            CREATE (c1)-[:PARTICIPATED_IN {proposal: 1490000.00}]->(t)
            CREATE (c2)-[:PARTICIPATED_IN {proposal: 1495000.00}]->(t)
            CREATE (p)-[:PARTNER_OF {participation_pct: 50.0}]->(c1)
            CREATE (p)-[:PARTNER_OF {participation_pct: 80.0}]->(c2)
            """


if __name__ == "__main__":
    test_neo4j_with_container()