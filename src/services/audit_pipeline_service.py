from typing import Dict, Any
import logging

from database.neo4j_client import Neo4jClient
from services.apis.comprasnet_tender_service import ComprasnetTenderService
from services.apis.comprasnet_winners_service import ComprasnetWinnersService
from services.apis.brasil_api_service import BrasilAPIService
from services.storage.licdguard_graph_storage_service import LicitGuardGraphStorageService
from services.licidguard_retriever_service import LicidGuardRetrieverService
from agents.auditor_agent import AuditorAgent

logger = logging.getLogger(__name__)


class AuditPipeline:
    def __init__(self, neo4j_client: Neo4jClient):
        self.db = neo4j_client
        
        # Instancia os serviços de API
        tender_service = ComprasnetTenderService()
        winners_service = ComprasnetWinnersService()
        brasilapi_service = BrasilAPIService()
        
        # Instancia o serviço de storage no Neo4j
        ingestion_service = LicitGuardGraphStorageService(neo4j_client=self.db)
        
        # Instancia o retriever service com todas as dependências
        self.retriever_service = LicidGuardRetrieverService(
            tender_service=tender_service,
            winners_service=winners_service,
            brasilapi_service=brasilapi_service,
            ingestion_service=ingestion_service,
        )
        
        # Instancia o auditor agent
        self.auditor_agent = AuditorAgent(neo4j_client=self.db)

    async def run(self, tender_id: str) -> Dict[str, Any]:
        """
        Orquestra o fluxo completo:
        1. Coleta e ingere os dados do certame no Neo4j usando o LicitGuardRetrieverService.
        2. Executa o AuditorAgent para identificar fraudes do escopo e gerar o risk score.
        """
        logger.info(f"Iniciando pipeline de auditoria para o tender_id: {tender_id}")

        # Passo 1: Coleta de dados e Ingestão no Neo4j
        logger.info(f"1/2 - Executando LicitGuardRetrieverService para tender_id={tender_id}...")
        await self.retriever_service.process_and_ingest_tender(id_compra=tender_id)

        # Passo 2: Execução da Auditoria nos padrões do escopo
        logger.info(f"2/2 - Executando AuditorAgent sobre o grafo...")
        audit_result = self.auditor_agent.audit_tender(tender_id=tender_id)

        logger.info(
            f"Pipeline finalizada com sucesso para {tender_id}. "
            f"Risk Score: {audit_result.get('risk_score')}/100"
        )

        return audit_result
