import outlines
from typing import Literal, Optional
from pydantic import BaseModel, Field

UnitType = Literal["Full Amount", "Thousands", "Millions", "Billions"]
AuditOpinionType = Literal["Unqualified", "Qualified", "Adverse", "Disclaimer"]

class IncomeStatement(BaseModel):
    total_revenue: Optional[float] = Field(default=None, ge=0.0)
    net_income: Optional[float] = Field(default=None)
    total_revenue_previous: Optional[float] = Field(default=None, ge=0.0)
    net_income_previous: Optional[float] = Field(default=None)
    currency: Optional[str] = Field(default=None, pattern=r"^[A-Z]{3}$")
    units: UnitType = Field(...)

class BalanceSheet(BaseModel):
    total_assets: Optional[float] = Field(default=None, ge=0.0)
    total_equity: Optional[float] = Field(default=None)
    total_assets_previous: Optional[float] = Field(default=None, ge=0.0)
    total_equity_previous: Optional[float] = Field(default=None)
    currency: Optional[str] = Field(default=None, pattern=r"^[A-Z]{3}$")
    units: UnitType = Field(...)

class AuditInfo(BaseModel):
    auditor_firms: list[str] = Field(default_factory=list)
    auditor_assessment: Optional[AuditOpinionType] = Field(default=None)

class AnnualReportExtraction(BaseModel):
    parent_company: str = Field(...)
    # Utilisation de str + pattern car date fait souvent bugger l'automate Outlines
    financial_statement_period: Optional[str] = Field(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    previous_period: Optional[str] = Field(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    income_statement: Optional[IncomeStatement] = Field(default=None)
    balance_sheet: Optional[BalanceSheet] = Field(default=None)
    audit: Optional[AuditInfo] = Field(default=None)