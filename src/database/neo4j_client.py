from neo4j import GraphDatabase, Driver
from config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD

class Neo4jClient:
    def __init__(self, uri: str = None, user: str = None, password: str = None):
        self.uri = uri or NEO4J_URI
        self.user = user or NEO4J_USER
        self.password = password or NEO4J_PASSWORD
        self._driver: Driver | None = None

    def connect(self):
        if not self._driver:
            self._driver = GraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password)
            )
            # Testa a conectividade
            self._driver.verify_connectivity()
            print("✅ Conexão estabelecida com o Neo4j com sucesso!")

    def close(self):
        if self._driver:
            self._driver.close()
            print("🔌 Conexão com o Neo4j encerrada.")

    def query(self, cypher_query: str, parameters: dict = None) -> list[dict]:
        if not self._driver:
            self.connect()

        with self._driver.session() as session:
            result = session.run(cypher_query, parameters or {})
            return [record.data() for record in result]