from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

UnitType = Literal["Full Amount", "Thousands", "Millions", "Billions"]


class IncomeStatement(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total_revenue: Optional[float] = Field(default=None, ge=0.0)
    net_income: Optional[float] = None
    total_revenue_previous: Optional[float] = Field(default=None, ge=0.0)
    net_income_previous: Optional[float] = None
    currency: Optional[str] = Field(default=None, pattern=r"^[A-Z]{3}$")
    units: Optional[UnitType] = None


class BalanceSheet(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total_assets: Optional[float] = Field(default=None, ge=0.0)
    total_equity: Optional[float] = None
    total_assets_previous: Optional[float] = Field(default=None, ge=0.0)
    total_equity_previous: Optional[float] = None
    currency: Optional[str] = Field(default=None, pattern=r"^[A-Z]{3}$")
    units: Optional[UnitType] = None


class AuditInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    auditor_company: Optional[str] = None
    auditor_assessment: Optional[str] = None


class AnnualReportExtraction(BaseModel):
    model_config = ConfigDict(extra="forbid")

    parent_company: str
    financial_statement_period: str = Field(
        default=None,
        pattern=r"^\d{4}-\d{2}-\d{2}$",
    )
    previous_period: str = Field(
        default=None,
        pattern=r"^\d{4}-\d{2}-\d{2}$",
    )
    income_statement: IncomeStatement = Field(default_factory=IncomeStatement)
    balance_sheet: BalanceSheet = Field(default_factory=BalanceSheet)
    audit: AuditInfo = Field(default_factory=AuditInfo)
