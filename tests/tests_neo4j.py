from testcontainers.neo4j import Neo4jContainer
from src.database.neo4j_client import Neo4jClient


def testar_neo4j_com_container_automatico():
    print("🐳 Subindo container Docker do Neo4j de forma automática para os testes...")

    # Utiliza a tag oficial "neo4j:5" para evitar divergências de versão
    with Neo4jContainer("neo4j:5") as neo4j_docker:
        # Recupera as credenciais dinâmicas da porta efêmera
        uri = neo4j_docker.get_connection_url()
        username = neo4j_docker.username
        password = neo4j_docker.password

        print(f"⚡ Container Neo4j rodando na URL dinâmica: {uri}")

        # Instancia o nosso cliente passando a URI e credenciais dinâmicas do container
        db = Neo4jClient(uri=uri, user=username, password=password)
        db.connect()

        try:
            print("🏗️ Inserindo subgrafo de teste (Licitação + Empresas + Sócios)...")
            cypher_populacao = """
            // 1. Criar a Licitação
            CREATE (l:Licitacao {id: "LIC-102/2026", objeto: "Reforma Hospital Municipal", valor: 1500000.00})

            // 2. Criar Empresas Concorrentes
            CREATE (e1:Empresa {cnpj: "11.111.111/0001-11", razao_social: "Alfa Construções LTDA", endereco: "Rua das Flores, 100"})
            CREATE (e2:Empresa {cnpj: "22.222.222/0001-22", razao_social: "Beta Engenharia LTDA", endereco: "Rua das Flores, 100"})

            // 3. Criar Sócio em Comum
            CREATE (s:Socio {cpf: "000.111.222-33", nome: "Carlos Alberto da Silva"})

            // 4. Criar Relacionamentos
            CREATE (e1)-[:PARTICIPOU_DE {proposta: 1490000.00}]->(l)
            CREATE (e2)-[:PARTICIPOU_DE {proposta: 1495000.00}]->(l)
            CREATE (s)-[:SOCIO_DE {pct_participacao: 50.0}]->(e1)
            CREATE (s)-[:SOCIO_DE {pct_participacao: 80.0}]->(e2)
            """
            db.query(cypher_populacao)
            print("✅ Subgrafo inserido no Neo4j com sucesso!")

            print("\n🔍 Executando auditoria em Cypher no grafo efêmero...")
            cypher_auditoria = """
            MATCH (e1:Empresa)-[:PARTICIPOU_DE]->(l:Licitacao)<-[:PARTICIPOU_DE]-(e2:Empresa)
            WHERE e1.cnpj < e2.cnpj
            MATCH (s:Socio)-[:SOCIO_DE]->(e1)
            MATCH (s)-[:SOCIO_DE]->(e2)
            RETURN 
                l.id AS licitacao, 
                e1.razao_social AS emp1, 
                e2.razao_social AS emp2, 
                s.nome AS socio,
                e1.endereco AS endereco1,
                e2.endereco AS endereco2
            """
            resultados = db.query(cypher_auditoria)

            # Validação do teste
            assert len(resultados) > 0, "A consulta de auditoria deveria retornar pelo menos um alerta."

            res = resultados[0]
            print("\n🚨 ALERTA DE FRAUDE DETECTADO E VALIDADO:")
            print(f" • Licitação Auditada: {res['licitacao']}")
            print(f" • Empresa Concorrente A: {res['emp1']}")
            print(f" • Empresa Concorrente B: {res['emp2']}")
            print(f" • Sócio Oculto em Comum: {res['socio']}")
            print(f" • Endereços Coincidentes: {res['endereco1'] == res['endereco2']}")
            print("-" * 60)

        finally:
            db.close()

    print("🧹 Teste finalizado! Container Docker efêmero destruído com sucesso.")


if __name__ == "__main__":
    testar_neo4j_com_container_automatico()