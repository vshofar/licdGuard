import httpx
from typing import List, Dict, Any
from src.services.apis.exceptions.exceptions import (
    BadRequest,
    ResourceNotFound,
    InternalError,
    UnknownRequestException
)


class ComprasnetItemsService:
    BASE_URL = "https://dadosabertos.compras.gov.br/modulo-contratacoes"

    def __init__(self, timeout: float = 20.0):
        self.headers = {
            "accept": "application/json",
            "User-Agent": "LicitGuard-AuditPipeline/1.0",
        }
        self.timeout = timeout

    def _handle_response_status(self, status_code: int, resource_id: str):
        if status_code == 400:
            raise BadRequest(f"Bad request for items {resource_id}")
        elif status_code == 404:
            raise ResourceNotFound(f"Items {resource_id} not found")
        elif status_code == 500:
            raise InternalError(f"Internal server error fetching items {resource_id}")
        elif status_code != 200:
            raise UnknownRequestException(f"Unknown error fetching items {resource_id}. Status code: {status_code}")

    def fetch_items(self, id_compra: str) -> List[Dict[str, Any]]:
        url = f"{self.BASE_URL}/2.1_consultarItensContratacoes_PNCP_14133_Id"
        params = {"tipo": "idCompra", "codigo": id_compra}

        try:
            with httpx.Client(headers=self.headers, follow_redirects=True, timeout=self.timeout) as client:
                response = client.get(url, params=params)
                self._handle_response_status(response.status_code, id_compra)
                return response.json().get("resultado", [])
        except Exception as e:
            if isinstance(e, (BadRequest, ResourceNotFound, InternalError, UnknownRequestException)):
                raise
            raise Exception(f"Failed to fetch items {id_compra}: {e}") from e
