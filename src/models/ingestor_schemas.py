from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional


class PartnerInput(BaseModel):
    masked_cpf: str = Field(description="CPF mascarado do sócio")
    name: str = Field(description="Nome completo do sócio")
    participation_pct: Optional[float] = Field(default=None, description="Percentual de participação societária")
    role: Optional[str] = Field(default=None, description="Cargo/qualificação do sócio")


class CompanyInput(BaseModel):
    cnpj: str = Field(description="CNPJ limpo ou formatado da empresa")
    company_name: str = Field(description="Razão social da empresa")
    address: str = Field(default="", description="Endereço completo da sede")
    partners: list[PartnerInput] = Field(default_factory=list, description="Lista de sócios da empresa")

    @field_validator("cnpj")
    @classmethod
    def normalize_cnpj(cls, v: str) -> str:
        clean_cnpj = "".join(filter(str.isdigit, v))
        if len(clean_cnpj) != 14:
            raise ValueError(f"CNPJ inválido: {v}")
        return clean_cnpj


class ProposalInput(BaseModel):
    company_cnpj: str = Field(description="CNPJ da empresa participante")
    offer_value: float = Field(description="Valor ofertado no lance/proposta")


class TenderInput(BaseModel):
    tender_id: str = Field(description="Identificador único no PNCP/órgão")
    object: str = Field(description="Descrição/Objeto da contratação pública")
    estimated_value: float = Field(description="Valor estimado pelo órgão licitante")
    buyer_agency: str = Field(description="Nome do órgão público comprador")
    proposals: list[ProposalInput] = Field(default_factory=list)