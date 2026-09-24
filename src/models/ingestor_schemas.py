from pydantic import BaseModel, Field, ConfigDict, field_validator


class PartnerInput(BaseModel):
    masked_cpf: str = Field(description="Masked CPF of the partner")
    name: str = Field(description="Full name of the partner")
    participation_pct: float = Field(default=0.0, description="Percentage of shareholding participation")


class CompanyInput(BaseModel):
    cnpj: str = Field(description="Clean or formatted CNPJ of the company")
    company_name: str = Field(description="Company name")
    address: str = Field(default="", description="Complete headquarters address")
    partners: list[PartnerInput] = Field(default_factory=list, description="List of company partners")

    @field_validator("cnpj")
    @classmethod
    def normalize_cnpj(cls, v: str) -> str:
        # Remove non-numeric characters to standardize Neo4j searches
        clean_cnpj = "".join(filter(str.isdigit, v))
        if len(clean_cnpj) != 14:
            raise ValueError(f"Invalid CNPJ: {v}")
        return clean_cnpj


class ProposalInput(BaseModel):
    company_cnpj: str = Field(description="CNPJ of the participating company")
    offer_value: float = Field(description="Value offered in the bid/proposal")


class TenderInput(BaseModel):
    tender_id: str = Field(description="Unique identifier in PNCP/agency")
    object: str = Field(description="Description/Object of public procurement")
    estimated_value: float = Field(description="Estimated value by the procuring agency")
    buyer_agency: str = Field(description="Name of the public buyer agency")
    proposals: list[ProposalInput] = Field(default_factory=list)