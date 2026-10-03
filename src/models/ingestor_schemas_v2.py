import hashlib
from typing import List, Optional
from pydantic import BaseModel, Field, computed_field, field_validator


# ==========================================
# 1. NÓS SECUNDÁRIOS & COMPONENTES DO GRAFO
# ==========================================

class PublicAgencyNode(BaseModel):
    """Nó representando a Unidade Gestora / Órgão Licitante."""
    cnpj: str = Field(..., description="CNPJ do órgão público (14 dígitos)")
    agency_name: str = Field(..., description="Razão social ou nome da UASG")
    uasg_code: str = Field(..., description="Código da UASG (ex: '200122')")

    @field_validator("cnpj", "uasg_code", mode="before")
    @classmethod
    def clean_digits(cls, value: str) -> str:
        return "".join(filter(str.isdigit, str(value))) if value else ""


class TenderNode(BaseModel):
    """Nó representando a Licitação Homologada."""
    tender_id: str = Field(..., description="ID de 17 dígitos no Comprasnet/PNCP")
    notice_number: str = Field(..., description="Número do edital (ex: '90001/2026')")
    object_description: str = Field(..., description="Descrição do objeto licitado")
    estimated_value: Optional[float] = Field(0.0, description="Valor estimado global pelo órgão")
    publication_date: Optional[str] = Field(None, description="Data de publicação (YYYY-MM-DD)")


class PartnerNode(BaseModel):
    """Nó representando o Sócio ou Administrador do QSA."""
    partner_id: str = Field(..., description="CPF mascarado ou CNPJ do sócio vindo da Receita Federal")
    partner_name: str = Field(..., description="Nome completo ou razão social do sócio")
    qualification: Optional[str] = Field(None, description="Cargo/Qualificação (ex: 'Sócio-Administrador')")

    @field_validator("partner_id", mode="before")
    @classmethod
    def clean_partner_id(cls, value: str) -> str:
        return str(value).strip() if value else "NOT_PROVIDED"


class AddressNode(BaseModel):
    """Nó representando a Sede Fiscal da Empresa."""
    street: str = Field(..., description="Logradouro (Rua, Av, etc.)")
    number: str = Field(..., description="Número do imóvel")
    zip_code: str = Field(..., description="CEP sanitizado")
    city: Optional[str] = Field(None, description="Município")
    state: Optional[str] = Field(None, description="UF")

    @computed_field
    @property
    def address_hash(self) -> str:
        """MD5 Hash gerado a partir de CEP + Logradouro + Número normalizados."""
        clean_zip = "".join(filter(str.isdigit, self.zip_code or ""))
        clean_street = (self.street or "").strip().upper()
        clean_number = (self.number or "").strip().upper()

        raw_key = f"{clean_zip}|{clean_street}|{clean_number}"
        return hashlib.md5(raw_key.encode("utf-8")).hexdigest()


# ==========================================
# 2. LICITANTE UNIFICADO & PAYLOAD RAIZ
# ==========================================

class CompanyNode(BaseModel):
    """Nó da Empresa Vencedora unificando atributos cadastrais, endereço, QSA e dados da vitória."""
    # Propriedades do Nó (:CompanyNode)
    cnpj: str = Field(..., description="CNPJ da empresa (14 dígitos)")
    legal_name: str = Field(..., description="Razão social na Receita Federal")
    share_capital: float = Field(0.0, description="Capital Social cadastrado")
    creation_date: Optional[str] = Field(None, description="Data de fundação (YYYY-MM-DD)")

    # Entidades Filhas no Grafo
    address: AddressNode
    partners: List[PartnerNode] = Field(default_factory=list)

    # Propriedades da Aresta [:WON]
    won_items: List[int] = Field(default_factory=list, description="Números dos itens vencidos")
    total_homologated_value: float = Field(..., description="Valor total homologado ganho na compra")

    @field_validator("cnpj", mode="before")
    @classmethod
    def clean_cnpj(cls, value: str) -> str:
        return "".join(filter(str.isdigit, str(value))) if value else ""

    @computed_field
    @property
    def items_count(self) -> int:
        return len(self.won_items)


class IngestionPayload(BaseModel):
    """Payload completo de uma licitação pronto para ingestão via Cypher UNWIND."""
    public_agency: PublicAgencyNode
    tender: TenderNode
    winners: List[CompanyNode] = Field(default_factory=list)