import re
from enum import Enum
from datetime import date
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator, model_validator

# Énumérations pour standardiser les valeurs métiers et limiter les hallucinations
class UnitType(str, Enum):
    FULL_AMOUNT = "Full Amount"
    THOUSANDS = "Thousands"
    MILLIONS = "Millions"
    BILLIONS = "Billions"

class AuditOpinionType(str, Enum):
    UNQUALIFIED = "Unqualified"
    QUALIFIED = "Qualified"
    ADVERSE = "Adverse"
    DISCLAIMER = "Disclaimer"

class ConfidenceLevel(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"

# Structure de base pour assurer la traçabilité de chaque point de donnée
class SourcedFloat(BaseModel):
    value: Optional[float] = Field(
        ...,
        description="The extracted numerical value. Must be null if the exact data point is missing. Do not calculate or estimate."
    )
    page: Optional[int] = Field(
        ...,
        description="The document page number where this value was found. Null if value is missing."
    )
    snippet: Optional[str] = Field(
        ...,
        description="Exact text excerpt (maximum 15 words) surrounding the value to prove its origin. Null if value is missing."
    )
    # Ajout du score de confiance
    confidence: ConfidenceLevel = Field(
        ..., 
        description="Your self-assessed confidence level in this specific extraction."
    )

class SourcedDate(BaseModel):
    value: Optional[date] = Field(..., description="Extracted date (YYYY-MM-DD). Null if missing.")
    page: Optional[int] = Field(..., description="Page number of the date. Null if missing.")

class Executive(BaseModel):
    name: str = Field(..., description="Full legal name of the executive or board member.")
    title: Optional[str] = Field(..., description="Official job title (e.g., Chief Executive Officer). Null if not specified.")
    page: Optional[int] = Field(..., description="Page number where this individual is mentioned.")

# Compte de résultat avec guardrails intégrés
class IncomeStatement(BaseModel):
    total_revenue: SourcedFloat = Field(..., description="Total revenue or sales for the current period. Must be >= 0.")
    operating_income: SourcedFloat = Field(..., description="Operating income (EBIT) for the current period.")
    net_income: SourcedFloat = Field(..., description="Net income or loss attributable to shareholders for the current period.")
    total_revenue_previous: SourcedFloat = Field(..., description="Total revenue for the previous comparative period.")
    net_income_previous: SourcedFloat = Field(..., description="Net income or loss for the previous comparative period.")
    currency: Optional[str] = Field(..., description="ISO 4217 3-letter currency code. Must strictly be 3 uppercase letters.")
    units: UnitType = Field(..., description="Scale factor applied to the numbers.")

    # Vérification stricte du format ISO 4217
    @field_validator('currency')
    @classmethod
    def validate_currency(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not re.match(r"^[A-Z]{3}$", v):
            raise ValueError(f"Currency must be strictly 3 uppercase letters, got: {v}")
        return v

    # Bloque les valeurs négatives aberrantes pour le CA
    @field_validator('total_revenue', 'total_revenue_previous')
    @classmethod
    def validate_non_negative_revenue(cls, v: SourcedFloat) -> SourcedFloat:
        if v.value is not None and v.value < 0:
            raise ValueError(f"Revenue cannot be negative, got: {v.value}")
        return v

# Bilan comptable
class BalanceSheet(BaseModel):
    total_assets: SourcedFloat = Field(..., description="Total assets at the end of the current period. Must be >= 0.")
    total_liabilities: SourcedFloat = Field(..., description="Total liabilities at the end of the current period. Must be >= 0.")
    total_equity: SourcedFloat = Field(..., description="Total shareholders' equity at the end of the current period.")
    cash_and_equivalents: SourcedFloat = Field(..., description="Cash and cash equivalents at the end of the current period.")
    total_assets_previous: SourcedFloat = Field(..., description="Total assets at the end of the previous period.")
    currency: Optional[str] = Field(..., description="ISO 4217 3-letter currency code.")
    units: UnitType = Field(..., description="Scale factor applied to the numbers.")

    @field_validator('currency')
    @classmethod
    def validate_currency(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not re.match(r"^[A-Z]{3}$", v):
            raise ValueError(f"Currency must be strictly 3 uppercase letters, got: {v}")
        return v

    # Les postes d'actifs et passifs principaux ne peuvent pas être négatifs
    @field_validator('total_assets', 'total_liabilities', 'total_assets_previous', 'cash_and_equivalents')
    @classmethod
    def validate_non_negative_balance(cls, v: SourcedFloat) -> SourcedFloat:
        if v.value is not None and v.value < 0:
            raise ValueError(f"Balance sheet value cannot be negative, got: {v.value}")
        return v

# Tableau des flux de trésorerie
class CashFlowStatement(BaseModel):
    operating_cash_flow: SourcedFloat = Field(..., description="Net cash provided by (used in) operating activities.")
    capital_expenditure: SourcedFloat = Field(..., description="Capital expenditures (CapEx) or purchases of property, plant, and equipment. Usually a negative outflow.")
    currency: Optional[str] = Field(..., description="ISO 4217 3-letter currency code.")
    units: UnitType = Field(..., description="Scale factor applied to the numbers.")

    @field_validator('currency')
    @classmethod
    def validate_currency(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not re.match(r"^[A-Z]{3}$", v):
            raise ValueError(f"Currency must be strictly 3 uppercase letters, got: {v}")
        return v

# Informations sur l'audit
class AuditInfo(BaseModel):
    auditor_firms: List[str] = Field(
        ...,
        description="List of auditing firms (e.g., PwC, EY, KPMG, Deloitte). Output empty list [] if missing."
    )
    auditor_assessment: Optional[AuditOpinionType] = Field(
        ...,
        description="Standardized audit opinion classification based on the independent auditor's report."
    )
    audit_report_page: Optional[int] = Field(
        ...,
        description="Page number where the Independent Auditor's Report begins. Null if missing."
    )

# Schéma global agrégé envoyé au LLM
class AnnualReportExtraction(BaseModel):
    parent_company: str = Field(..., description="Exact legal entity name of the reporting company.")
    financial_statement_period: SourcedDate = Field(..., description="Closing date of the current reporting period.")
    previous_period: SourcedDate = Field(..., description="Closing date of the previous comparative period.")

    key_executives: List[Executive] = Field(
        ...,
        description="List of key executives and board of directors identified in the report. Empty list [] if missing."
    )
    major_risk_factors: List[str] = Field(
        ...,
        description="List of maximum 5 principal risks and uncertainties identified by the company. Empty list [] if missing."
    )

    income_statement: Optional[IncomeStatement] = Field(..., description="Income statement metrics. Null if the section is completely unreadable.")
    balance_sheet: Optional[BalanceSheet] = Field(..., description="Balance sheet metrics. Null if the section is completely unreadable.")
    cash_flow_statement: Optional[CashFlowStatement] = Field(..., description="Cash flow statement metrics. Null if the section is completely unreadable.")
    audit: Optional[AuditInfo] = Field(..., description="Audit firm and opinion details. Null if missing.")