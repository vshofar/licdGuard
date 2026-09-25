import httpx
from typing import Optional

from models import PartnerInput
from src.models.ingestor_schemas import CompanyInput, PartnerInput


class BrasilAPIService:

    BASE_URL = "https://brasilapi.com.br/api/cnpj/v1"

    def __init__(self, timeout: float = 10.0):
        self.timeout = timeout
        self.headers = {"accept": "application/json"}

    def fetch_company(self, cnpj: str) -> Optional[CompanyInput]:

        clean_cnpj = "".join(filter(str.isdigit, cnpj))
        url = f"{self.BASE_URL}/{clean_cnpj}"

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(url, headers=self.headers)
                if response.status_code != 200:
                    print(f"⚠️ BrasilAPI: Falha ao buscar CNPJ {clean_cnpj} (Status {response.status_code})")
                    return None

                data = response.json()

                address, partners = self.parse_company_and_address(data)

                return CompanyInput(
                    cnpj=clean_cnpj,
                    company_name=data.get("razao_social") or data.get("nome_fantasia", "DESCONHECIDO"),
                    address=address if address else "ENDEREÇO NÃO INFORMADO",
                    partners=partners
                )

        except Exception as e:
            print(f"❌ Erro de conexão com BrasilAPI para o CNPJ {clean_cnpj}: {e}")
            return None

    def parse_company_and_address(self, data) -> tuple[str, list[PartnerInput]]:
        street = data.get("logradouro", "")
        number = data.get("numero", "")
        neighborhood = data.get("bairro", "")
        city = data.get("municipio", "")
        state = data.get("uf", "")
        address = f"{street}, {number} - {neighborhood}, {city}/{state}".strip(" ,-/")

        partners = [
            PartnerInput(
                masked_cpf=qsa.get("cnpj_cpf_do_socio") or "NÃO INFORMADO",
                name=qsa.get("nome_socio", "DESCONHECIDO"),
                role=qsa.get("qualificacao_socio", "Sócio"),
                participation_pct=None
            )
            for qsa in data.get("qsa", [])
        ]
        return address, partners