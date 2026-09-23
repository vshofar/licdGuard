from neo4j import AsyncGraphDatabase
from typing import Optional
from config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD


class Neo4jClient:
    def __init__(self):
        self.uri = NEO4J_URI
        self.user = NEO4J_USER
        self.password = NEO4J_PASSWORD
        self.driver: Optional[AsyncGraphDatabase.driver] = None

    async def connect(self):
        """Establish connection to Neo4j database."""
        self.driver = AsyncGraphDatabase.driver(
            self.uri,
            auth=(self.user, self.password)
        )
        await self.driver.verify_connectivity()
        print("Conectado ao Neo4j com sucesso")

    async def close(self):
        """Close the Neo4j database connection."""
        if self.driver:
            await self.driver.close()
            print("Conexão Neo4j fechada")

    async def execute_query(self, query: str, parameters: Optional[dict] = None):
        """Execute a Cypher query and return the results."""
        if not self.driver:
            raise RuntimeError("Driver Neo4j não está conectado. Chame connect() primeiro.")
        
        async with self.driver.session() as session:
            result = await session.run(query, parameters or {})
            records = await result.data()
            return records

    async def execute_write(self, query: str, parameters: Optional[dict] = None):
        """Execute a write Cypher query."""
        if not self.driver:
            raise RuntimeError("Driver Neo4j não está conectado. Chame connect() primeiro.")
        
        async with self.driver.session() as session:
            result = await session.run(query, parameters or {})
            await result.consume()
