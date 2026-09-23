import asyncio
from src.agentes.ingestor import Ingestor
from src.agentes.graph_auditor import GraphAuditor
from src.agentes.redator import Redator
from src.database.neo4j_client import Neo4jClient

async def main():
    ingestor = Ingestor()
    neo4j_client = Neo4jClient()
    graph_auditor = GraphAuditor(neo4j_client)
    redator = Redator()
    
    try:
        await neo4j_client.connect()
        print("Licit-Guard iniciado com sucesso")
    finally:
        await ingestor.close()
        await neo4j_client.close()

if __name__ == "__main__":
    asyncio.run(main())
