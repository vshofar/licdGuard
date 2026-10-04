from typing import Optional, List, Dict, Any
from src.models import TenderInput, ProposalInput
from src.services.apis.comprasnet_tender_service import ComprasnetTenderService
from src.services.apis.comprasnet_items_service import ComprasnetItemsService
from src.services.apis.comprasnet_winners_service import ComprasnetWinnersService


class ComprasnetService:
    def __init__(self, timeout: float = 20.0):
        self.tender_service = ComprasnetTenderService(timeout=timeout)
        self.items_service = ComprasnetItemsService(timeout=timeout)
        self.proposals_service = ComprasnetWinnersService(timeout=timeout)

    def get_full_payload(self, id_compra: str) -> Optional[Dict[str, Any]]:
        try:
            tender = self.tender_service.fetch_tender(id_compra)
            if not tender:
                return None

            items = self.items_service.fetch_items(id_compra)
            proposals = self.proposals_service.fetch_winners(id_compra)

            return {
                "tender": tender,
                "items": items,
                "proposals": proposals
            }
        except Exception:
            return None

    def fetch_tender_by_id(self, id_tender: str) -> Optional[TenderInput]:
        payload = self.get_full_payload(id_tender)
        if not payload or not payload.get("tender"):
            return None

        metadata = payload["tender"]
        raw_proposals = payload.get("proposals", [])

        proposals_input: List[ProposalInput] = []
        for proposal in raw_proposals:
            cnpj = proposal.get("niFornecedor")
            valor = (
                proposal.get("valorTotalHomologado")
                or proposal.get("valorUnitarioHomologado")
                or 0.0
            )

            if cnpj:
                proposals_input.append(
                    ProposalInput(
                        company_cnpj=str(cnpj).strip(),
                        offer_value=float(valor)
                    )
                )

        return TenderInput(
            tender_id=str(metadata.get("idCompra") or metadata.get("codigoCompraPncp") or id_tender),
            object=str(metadata.get("objetoCompra", "")),
            estimated_value=float(metadata.get("valorTotalEstimado") or 0.0),
            buyer_agency=str(metadata.get("orgaoEntidadeRazaoSocial") or metadata.get("nomeUasg", "")),
            proposals=proposals_input
        )
