import pytest
from pydantic import ValidationError

from models import (
    CustomerApplication,
    Decision,
    FinancialData,
    RiskRating,
    RiskScore,
    UnderwritingReport,
)


# ── CustomerApplication ──────────────────────────────────────────────────────

def test_customer_application_valid():
    app = CustomerApplication(
        name="Test Co", industry="Retail",
        annual_revenue=1_000_000, years_trading=5, country="New Zealand",
    )
    assert app.annual_revenue == 1_000_000
    assert app.years_trading == 5


def test_customer_application_rejects_zero_revenue():
    with pytest.raises(ValidationError):
        CustomerApplication(
            name="Test Co", industry="Retail",
            annual_revenue=0, years_trading=5, country="New Zealand",
        )


def test_customer_application_rejects_negative_revenue():
    with pytest.raises(ValidationError):
        CustomerApplication(
            name="Test Co", industry="Retail",
            annual_revenue=-500, years_trading=5, country="New Zealand",
        )


def test_customer_application_allows_zero_years():
    app = CustomerApplication(
        name="Test Co", industry="Retail",
        annual_revenue=500_000, years_trading=0, country="New Zealand",
    )
    assert app.years_trading == 0


def test_customer_application_rejects_negative_years():
    with pytest.raises(ValidationError):
        CustomerApplication(
            name="Test Co", industry="Retail",
            annual_revenue=500_000, years_trading=-1, country="New Zealand",
        )


# ── FinancialData ─────────────────────────────────────────────────────────────

def test_financial_data_valid():
    fd = FinancialData(
        revenue_trend=0.12, debt_ratio=0.45,
        payment_history_score=70, bank_balance=150_000,
    )
    assert fd.debt_ratio == 0.45


def test_financial_data_rejects_debt_ratio_above_one():
    with pytest.raises(ValidationError):
        FinancialData(
            revenue_trend=0.1, debt_ratio=1.01,
            payment_history_score=70, bank_balance=100_000,
        )


def test_financial_data_rejects_negative_debt_ratio():
    with pytest.raises(ValidationError):
        FinancialData(
            revenue_trend=0.1, debt_ratio=-0.1,
            payment_history_score=70, bank_balance=100_000,
        )


def test_financial_data_rejects_payment_score_above_100():
    with pytest.raises(ValidationError):
        FinancialData(
            revenue_trend=0.1, debt_ratio=0.4,
            payment_history_score=101, bank_balance=100_000,
        )


def test_financial_data_rejects_negative_payment_score():
    with pytest.raises(ValidationError):
        FinancialData(
            revenue_trend=0.1, debt_ratio=0.4,
            payment_history_score=-1, bank_balance=100_000,
        )


# ── RiskScore ─────────────────────────────────────────────────────────────────

def test_risk_score_rejects_overall_above_100():
    with pytest.raises(ValidationError):
        RiskScore(
            overall_score=101, credit_limit_recommended=50_000,
            risk_rating=RiskRating.LOW, flags=[],
        )


def test_risk_score_rejects_negative_overall():
    with pytest.raises(ValidationError):
        RiskScore(
            overall_score=-1, credit_limit_recommended=50_000,
            risk_rating=RiskRating.LOW, flags=[],
        )


def test_risk_score_rejects_negative_credit_limit():
    with pytest.raises(ValidationError):
        RiskScore(
            overall_score=60, credit_limit_recommended=-1,
            risk_rating=RiskRating.LOW, flags=[],
        )


def test_risk_score_allows_zero_credit_limit():
    rs = RiskScore(
        overall_score=20, credit_limit_recommended=0,
        risk_rating=RiskRating.DECLINED, flags=["declined"],
    )
    assert rs.credit_limit_recommended == 0


# ── Enums ─────────────────────────────────────────────────────────────────────

def test_risk_rating_values():
    assert RiskRating.LOW.value == "low"
    assert RiskRating.MEDIUM.value == "medium"
    assert RiskRating.HIGH.value == "high"
    assert RiskRating.DECLINED.value == "declined"


def test_decision_values():
    assert Decision.APPROVED.value == "approved"
    assert Decision.CONDITIONAL.value == "conditional"
    assert Decision.DECLINED.value == "declined"
