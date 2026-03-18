from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

UnitType = Literal["Full Amount", "Thousands", "Millions", "Billions"]


class IncomeStatement(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total_revenue: float = Field(ge=0.0)
    net_income: float
    total_revenue_previous: float = Field(ge=0.0)
    net_income_previous: float
    currency: str = Field(pattern=r"^[A-Z]{3}$")
    units: UnitType


class BalanceSheet(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total_assets: float = Field(ge=0.0)
    total_equity: float
    total_assets_previous: float = Field(ge=0.0)
    total_equity_previous: float
    currency: str = Field(pattern=r"^[A-Z]{3}$")
    units: UnitType


class AuditInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    auditor_company: str
    auditor_assessment: str


class AnnualReportExtraction(BaseModel):
    model_config = ConfigDict(extra="forbid")

    parent_company: str
    financial_statement_period: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    previous_period: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    income_statement: IncomeStatement
    balance_sheet: BalanceSheet
    audit: AuditInfo
