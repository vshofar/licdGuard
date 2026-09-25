from typing import Dict, Any
from src.database.neo4j_client import Neo4jClient


class AuditorAgent:
    def __init__(self, db: Neo4jClient):
        self.db = db

    def audit_tender(self, licitacao_id: str) -> Dict[str, Any]:
        """Executa auditoria completa para uma licitação específica."""

        query_socios = """
        MATCH (e1:Company)-[:PARTICIPATED_IN]->(l:Licitacao {id: $id_licitacao})
        MATCH (e2:Company)-[:PARTICIPATED_IN]->(l)
        WHERE e1.cnpj <> e2.cnpj
        MATCH (s:Socio)-[:PARTNER_OF]->(e1)
        MATCH (s)-[:PARTNER_OF]->(e2)
        RETURN e1.razao_social AS e1, e2.razao_social AS e2, s.nome AS socio
        """

        query_enderecos = """
        MATCH (e1:Company)-[:PARTICIPATED_IN]->(l:Licitacao {id: $id_licitacao})
        MATCH (e2:Company)-[:PARTICIPATED_IN]->(l)
        WHERE e1.cnpj < e2.cnpj AND e1.endereco = e2.endereco AND e1.endereco IS NOT NULL
        RETURN e1.razao_social AS e1, e2.razao_social AS e2, e1.endereco AS endereco
        """

        query_cobertura = """
        MATCH (e:Company)-[p:PARTICIPATED_IN]->(l:Licitacao {id: $id_licitacao})
        WHERE p.proposta > (l.valor_estimado * 1.20)
        RETURN e.razao_social AS Company, p.proposta AS proposta, l.valor_estimado AS estimado
        """

        params = {"id_licitacao": licitacao_id}

        socios_suspeitos = self.db.query(query_socios, params)
        enderecos_suspeitos = self.db.query(query_enderecos, params)
        propostas_cobertura = self.db.query(query_cobertura, params)

        # Cálculo de pontuação de risco (Risk Score)
        score = 0
        score += len(socios_suspeitos) * 40
        score += len(enderecos_suspeitos) * 30
        score += len(propostas_cobertura) * 20

        return {
            "licitacao_id": licitacao_id,
            "risk_score": min(score, 100),
            "alertas": {
                "socios_compartilhados": socios_suspeitos,
                "enderecos_coincidentes": enderecos_suspeitos,
                "propostas_cobertura": propostas_cobertura
            }
        }