import pytest

from mock_apis import (
    fetch_apollo_data,
    fetch_credit_bureau,
    fetch_hubspot_lead,
    fetch_xero_financials,
    simulate_gocardless_mandate,
    simulate_wise_payment_request,
)

_COMPANY = "Pacific Rim Trading Ltd"


# ── Shape checks ──────────────────────────────────────────────────────────────

async def test_apollo_returns_expected_keys():
    data = await fetch_apollo_data(_COMPANY)
    for key in ("company_name", "industry", "employee_headcount", "years_in_business",
                "estimated_annual_revenue_usd", "source"):
        assert key in data
    assert data["source"] == "apollo_mock_v1"


async def test_xero_returns_expected_keys():
    data = await fetch_xero_financials(_COMPANY)
    for key in ("revenue_trend", "debt_ratio", "bank_balance_usd",
                "net_profit_usd", "overdue_invoices_count", "source"):
        assert key in data
    assert data["source"] == "xero_mock_v1"


async def test_credit_bureau_returns_expected_keys():
    data = await fetch_credit_bureau(_COMPANY)
    for key in ("payment_history_score", "defaults_last_5_years",
                "credit_utilisation_pct", "court_judgements", "source"):
        assert key in data
    assert data["source"] == "credit_bureau_mock_v1"


async def test_hubspot_lead_returns_expected_keys():
    data = await fetch_hubspot_lead(_COMPANY)
    for key in ("meeting_outcome", "human_checkpoint_1_approved",
                "sales_notes", "hubspot_deal_stage", "source"):
        assert key in data
    assert data["source"] == "hubspot_mock_v1"
    assert data["meeting_outcome"] in ("approved_to_proceed", "declined_at_meeting")


# ── Value range checks ────────────────────────────────────────────────────────

async def test_credit_bureau_fico_in_range():
    data = await fetch_credit_bureau(_COMPANY)
    assert 300 <= data["payment_history_score"] <= 850


async def test_xero_debt_ratio_in_range():
    data = await fetch_xero_financials(_COMPANY)
    assert 0 <= data["debt_ratio"] <= 1


async def test_credit_utilisation_in_range():
    data = await fetch_credit_bureau(_COMPANY)
    assert 0 <= data["credit_utilisation_pct"] <= 1


# ── Seeded stability ──────────────────────────────────────────────────────────

async def test_seeded_values_stable_across_calls():
    # debt_ratio = total_debt / total_assets — both scale with revenue so the
    # jitter cancels out, making this value deterministic per company name.
    d1 = await fetch_xero_financials(_COMPANY)
    d2 = await fetch_xero_financials(_COMPANY)
    assert d1["debt_ratio"] == d2["debt_ratio"]


async def test_different_companies_produce_different_values():
    d1 = await fetch_xero_financials("Company Alpha")
    d2 = await fetch_xero_financials("Company Beta")
    assert d1["debt_ratio"] != d2["debt_ratio"]


async def test_hubspot_sentiment_stable():
    d1 = await fetch_hubspot_lead(_COMPANY)
    d2 = await fetch_hubspot_lead(_COMPANY)
    assert d1["meeting_outcome"] == d2["meeting_outcome"]
    assert d1["sales_rep_sentiment"] == d2["sales_rep_sentiment"]


# ── GoCardless ────────────────────────────────────────────────────────────────

async def test_gocardless_mandate_id_format():
    result = await simulate_gocardless_mandate(_COMPANY, 120_000)
    assert result["mandate_id"].startswith("MD")
    assert len(result["mandate_id"]) == 10  # "MD" + 8 hex chars


async def test_gocardless_weekly_payment_calculation():
    result = await simulate_gocardless_mandate(_COMPANY, 120_000)
    assert result["weekly_payment_usd"] == round(120_000 / 12, 2)
    assert result["repayment_weeks"] == 12
    assert result["status"] == "pending_customer_approval"


# ── Wise ──────────────────────────────────────────────────────────────────────

async def test_wise_transfer_id_format():
    result = await simulate_wise_payment_request(_COMPANY, 50_000)
    assert result["transfer_id"].startswith("TRF")


async def test_wise_fee_calculation():
    result = await simulate_wise_payment_request(_COMPANY, 50_000)
    assert result["wise_fee_usd"] == round(50_000 * 0.005, 2)
    assert result["amount_usd"] == 50_000
    assert result["status"] == "awaiting_human_approval"
    assert result["human_checkpoint_2"] == "supplier_payment_approval"
