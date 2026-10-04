import hashlib
from typing import List, Optional
from pydantic import BaseModel, Field, computed_field, field_validator


class PublicAgencyNode(BaseModel):
    cnpj: str = Field(..., description="CNPJ do órgão público (14 dígitos)")
    agency_name: str = Field(..., description="Razão social ou nome da UASG")
    uasg_code: str = Field(..., description="Código da UASG (ex: '160175')")

    @field_validator("cnpj", "uasg_code", mode="before")
    @classmethod
    def clean_digits(cls, value: str) -> str:
        return "".join(filter(str.isdigit, str(value))) if value else ""


class TenderNode(BaseModel):
    tender_id: str = Field(..., description="ID de 17 dígitos no Comprasnet/PNCP (ex: idCompra)")
    notice_number: str = Field(..., description="Número do edital/processo")
    object_description: str = Field(..., description="Descrição do objeto licitado")
    estimated_value: Optional[float] = Field(0.0, description="Valor estimado global pelo órgão")
    publication_date: Optional[str] = Field(None, description="Data de publicação (YYYY-MM-DD)")


class TenderItemNode(BaseModel):
    item_id: str = Field(..., description="ID único do item no Comprasnet (idCompraItem)")
    tender_id: str = Field(..., description="ID da licitação mãe (idCompra)")
    item_number: int = Field(..., description="Número do item na licitação (numeroItemPncp)")
    quantity_homologated: float = Field(..., description="Quantidade homologada")
    unit_value_homologated: float = Field(..., description="Valor unitário homologado")
    total_value_homologated: float = Field(..., description="Valor total homologado do item")
    winner_cnpj: str = Field(..., description="CNPJ do fornecedor vencedor do item")


class PartnerNode(BaseModel):
    partner_id: str = Field(..., description="CPF mascarado ou CNPJ do sócio vindo da Receita Federal")
    partner_name: str = Field(..., description="Nome completo ou razão social do sócio")
    qualification: Optional[str] = Field(None, description="Cargo/Qualificação (ex: 'Sócio-Administrador')")

    @field_validator("partner_id", mode="before")
    @classmethod
    def clean_partner_id(cls, value: str) -> str:
        return str(value).strip() if value else "NOT_PROVIDED"


class AddressNode(BaseModel):
    street: str = Field(..., description="Logradouro (Rua, Av, etc.)")
    number: str = Field(..., description="Número do imóvel")
    zip_code: str = Field(..., description="CEP sanitizado")
    city: Optional[str] = Field(None, description="Município")
    state: Optional[str] = Field(None, description="UF")

    @computed_field
    @property
    def address_hash(self) -> str:
        clean_zip = "".join(filter(str.isdigit, self.zip_code or ""))
        clean_street = (self.street or "").strip().upper()
        clean_number = (self.number or "").strip().upper()

        raw_key = f"{clean_zip}|{clean_street}|{clean_number}"
        return hashlib.md5(raw_key.encode("utf-8")).hexdigest()


class CompanyNode(BaseModel):
    cnpj: str = Field(..., description="CNPJ da empresa (14 dígitos)")
    legal_name: str = Field(..., description="Razão social")
    share_capital: float = Field(0.0, description="Capital Social cadastrado na Receita Federal")
    creation_date: Optional[str] = Field(None, description="Data de fundação (YYYY-MM-DD)")

    address: Optional[AddressNode] = Field(None, description="Nó de endereço fiscal")
    partners: List[PartnerNode] = Field(default_factory=list, description="Lista de sócios do QSA")

    @field_validator("cnpj", mode="before")
    @classmethod
    def clean_cnpj(cls, value: str) -> str:
        return "".join(filter(str.isdigit, str(value))) if value else ""


class IngestionPayload(BaseModel):
    public_agency: PublicAgencyNode
    tender: TenderNode
    items: List[TenderItemNode] = Field(default_factory=list)
    winners: List[CompanyNode] = Field(default_factory=list)