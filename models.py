from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class RiskRating(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    DECLINED = "declined"


class Decision(str, Enum):
    APPROVED = "approved"
    CONDITIONAL = "conditional"
    DECLINED = "declined"


class CustomerApplication(BaseModel):
    name: str
    industry: str
    annual_revenue: float = Field(..., gt=0, description="Annual revenue in USD")
    years_trading: int = Field(..., ge=0)
    country: str


class FinancialData(BaseModel):
    revenue_trend: float = Field(..., description="YoY revenue growth as a decimal, e.g. 0.12 for 12%")
    debt_ratio: float = Field(..., ge=0, le=1, description="Total debt / total assets")
    payment_history_score: int = Field(..., ge=0, le=100)
    bank_balance: float = Field(..., description="Current bank balance in USD")


class RiskScore(BaseModel):
    overall_score: int = Field(..., ge=0, le=100)
    credit_limit_recommended: float = Field(..., ge=0, description="Recommended credit limit in USD")
    risk_rating: RiskRating
    flags: list[str] = Field(default_factory=list)


class UnderwritingReport(BaseModel):
    application: CustomerApplication
    financial_data: FinancialData
    risk_score: RiskScore
    reasoning: str
    decision: Decision
    hubspot_lead: dict | None = None
    gocardless_mandate: dict | None = None
    wise_payment_request: dict | None = None
    hubspot_created: dict | None = None
