from neo4j import GraphDatabase, Driver
from config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD

class Neo4jClient:
    def __init__(self):
        self.uri = NEO4J_URI
        self.user = NEO4J_USER
        self.password = NEO4J_PASSWORD
        self._driver: Driver | None = None

    def connect(self):
        """Inicializa a conexão com o banco Neo4j."""
        if not self._driver:
            self._driver = GraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password)
            )
            # Testa a conectividade
            self._driver.verify_connectivity()
            print("✅ Conexão estabelecida com o Neo4j com sucesso!")

    def close(self):
        """Encerra o driver do Neo4j."""
        if self._driver:
            self._driver.close()
            print("🔌 Conexão com o Neo4j encerrada.")

    def query(self, cypher_query: str, parameters: dict = None) -> list[dict]:
        """Executa uma query Cypher e retorna os resultados formatados como lista de dicionários."""
        if not self._driver:
            self.connect()

        with self._driver.session() as session:
            result = session.run(cypher_query, parameters or {})
            return [record.data() for record in result]