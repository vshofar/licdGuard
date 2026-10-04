import httpx
from typing import Optional, Dict, Any
from src.services.apis.exceptions.exceptions import (
    BadRequest,
    ResourceNotFound,
    InternalError,
    UnknownRequestException
)


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

    def fetch_company(self, cnpj: str) -> Optional[Dict[str, Any]]:
        clean_cnpj = "".join(filter(str.isdigit, cnpj))
        url = f"{self.BASE_URL}/{clean_cnpj}"

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(url, headers=self.headers)
                self._handle_response_status(response.status_code, clean_cnpj)
                
                if not response.content:
                    return None
                    
                data = response.json()
                return data if data else None

        except Exception as e:
            if isinstance(e, (BadRequest, ResourceNotFound, InternalError, UnknownRequestException)):
                raise
            raise Exception(f"Failed to fetch company {clean_cnpj}: {e}") from e