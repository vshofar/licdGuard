import httpx
from typing import Optional, Any

from httpx import Client

from src.models.ingestor_schemas import TenderInput, ProposalInput


class PNCPApiService:

    BASE_URL = "https://pncp.gov.br/api/pncp/v1"

    def __init__(self, timeout: float = 10.0):
        self.timeout = timeout
        self.headers = {"accept": "application/json"}

    def fetch_tender(self, cnpj_orgao: str, ano: int, sequencial: int) -> Optional[TenderInput]:

        clean_cnpj = "".join(filter(str.isdigit, cnpj_orgao))
        endpoint = f"{self.BASE_URL}/orgaos/{clean_cnpj}/compras/{ano}/{sequencial}"

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(endpoint, headers=self.headers)
                if response.status_code != 200:
                    print(f"⚠️ PNCP: Licitação não encontrada (Status {response.status_code})")
                    return None

                data = response.json()
                tender_id = f"{clean_cnpj}-{ano}-{sequencial}"

                proposals = self.query_proposals(client, endpoint)

                return TenderInput(
                    tender_id=tender_id,
                    object=data.get("objetoCompra", "Objeto não informado"),
                    buyer_agency=data.get("orgaoEntidade", {}).get("razaoSocial", "Órgão Desconhecido"),
                    estimated_value=float(data.get("valorTotalEstimado", 0.0)),
                    proposals=proposals
                )

        except Exception as e:
            print(f"❌ Erro de conexão com PNCP API: {e}")
            return None

    def query_proposals(self, client: Client, endpoint: str) -> list[Any]:
        proposals = []
        proposals_resp = client.get(f"{endpoint}/propostas", headers=self.headers)

        if proposals_resp.status_code == 200:
            for prop in proposals_resp.json():
                proposals.append(
                    ProposalInput(
                        company_cnpj=prop.get("niFornecedor"),
                        offer_value=float(prop.get("valorTotal", 0.0))
                    )
                )
        return proposals