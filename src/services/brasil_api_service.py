import httpx
from typing import Optional
from src.services.exceptions.exceptions import (
    BadRequest,
    ResourceNotFound,
    InternalError,
    UnknownRequestException
)
from src.models.ingestor_schemas import CompanyInput, PartnerInput


class BrasilAPIService:

    BASE_URL = "https://brasilapi.com.br/api/cnpj/v1"

    def __init__(self, timeout: float = 10.0):
        self.timeout = timeout
        self.headers = {"accept": "application/json"}

    def _handle_response_status(self, status_code: int, resource_id: str):
        if status_code == 400:
            raise BadRequest(f"Bad request for company {resource_id}")
        elif status_code == 404:
            raise ResourceNotFound(f"Company {resource_id} not found")
        elif status_code == 500:
            raise InternalError(f"Internal server error fetching company {resource_id}")
        elif status_code != 200:
            raise UnknownRequestException(f"Unknown error fetching company {resource_id}. Status code: {status_code}")

    def fetch_company(self, cnpj: str) -> Optional[CompanyInput]:

        clean_cnpj = "".join(filter(str.isdigit, cnpj))
        url = f"{self.BASE_URL}/{clean_cnpj}"

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(url, headers=self.headers)
                self._handle_response_status(response.status_code, clean_cnpj)

                data = response.json()

                address, partners = self.parse_company_and_address(data)

                return CompanyInput(
                    cnpj=clean_cnpj,
                    company_name=data.get("razao_social") or data.get("nome_fantasia", "DESCONHECIDO"),
                    address=address if address else "ENDEREÇO NÃO INFORMADO",
                    partners=partners
                )

        except Exception as e:
            if isinstance(e, (BadRequest, ResourceNotFound, InternalError, UnknownRequestException)):
                raise
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