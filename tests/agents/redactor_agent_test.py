import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.agents.redactor_agent import RedactorAgent


def test_redactor_agent_report_generation():
    print("🤖 Testando a geração de Relatório de Auditoria com o RedactorAgent...")

    # Dados simulando o retorno estruturado do AuditorAgent
    mock_audit_data = {
        "bidding_id": "PNCP-FRAUDE-01",
        "risk_score": 90,
        "alerts": {
            "shared_partners": [
                {
                    "company_1": "Alpha Serviços EIRELI",
                    "company_2": "Beta Soluções de TI LTDA",
                    "shared_partner": "Carlos Oculto"
                }
            ],
            "shared_addresses": [
                {
                    "company_1": "Alpha Serviços EIRELI",
                    "company_2": "Beta Soluções de TI LTDA",
                    "shared_address": "Av. Paulista, 1500 - Sala 42"
                }
            ],
            "cover_bids": [
                {
                    "company": "Beta Soluções de TI LTDA",
                    "submitted_bid": 1300000.0,
                    "estimated_value": 1000000.0
                }
            ]
        }
    }

    redactor = RedactorAgent()
    report = redactor.generate_report(mock_audit_data)

    print("\n📄 PARECER TÉCNICO GERADO PELA LLM:")
    print("=" * 60)
    print(report)
    print("=" * 60)

    assert report is not None, "O relatório retornado não pode ser nulo."
    assert len(report) > 150, "O relatório gerado é muito curto para um parecer técnico."
    assert "Alpha Serviços EIRELI" in report or "Carlos Oculto" in report, "O parecer deve citar nominalmente as entidades envolvidas."
    assert "PNCP-FRAUDE-01" in report, "O parecer deve mencionar o ID da licitação auditada."

    print("\n✅ Sucesso! O RedactorAgent gerou o parecer técnico corretamente.")

