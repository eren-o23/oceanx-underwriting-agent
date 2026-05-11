import pytest
import httpx
from unittest.mock import AsyncMock, patch

from main_api import _to_response, app
from models import (
    CustomerApplication,
    Decision,
    FinancialData,
    RiskRating,
    RiskScore,
    UnderwritingReport,
)


# ── Async test client (httpx 0.28+ / ASGITransport) ─────────────────────────

@pytest.fixture
async def client():
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as c:
        yield c


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_report(
    overall_score: int = 72,
    credit_limit: float = 150_000,
    decision: Decision = Decision.APPROVED,
    risk_rating: RiskRating = RiskRating.MEDIUM,
    flags: list[str] | None = None,
    hubspot_url: str = "https://app-eu1.hubspot.com/contacts/148454999/record/0-2/123",
) -> UnderwritingReport:
    return UnderwritingReport(
        application=CustomerApplication(
            name="Test Co", industry="Retail",
            annual_revenue=1_200_000, years_trading=5, country="New Zealand",
        ),
        financial_data=FinancialData(
            revenue_trend=0.08, debt_ratio=0.35,
            payment_history_score=70, bank_balance=200_000,
        ),
        risk_score=RiskScore(
            overall_score=overall_score,
            credit_limit_recommended=credit_limit,
            risk_rating=risk_rating,
            flags=flags or [],
        ),
        reasoning="Solid financial profile.",
        decision=decision,
        hubspot_created={"hubspot_url": hubspot_url},
    )


# ── _to_response: requires_human_review logic ─────────────────────────────────

def test_requires_review_when_score_below_45():
    resp = _to_response(_make_report(overall_score=44, credit_limit=50_000))
    assert resp.requires_human_review is True


def test_no_review_at_score_boundary_45():
    resp = _to_response(_make_report(overall_score=45, credit_limit=50_000))
    assert resp.requires_human_review is False


def test_requires_review_when_limit_above_250k():
    resp = _to_response(_make_report(overall_score=80, credit_limit=250_001))
    assert resp.requires_human_review is True


def test_no_review_at_limit_boundary_250k():
    resp = _to_response(_make_report(overall_score=80, credit_limit=250_000))
    assert resp.requires_human_review is False


def test_no_review_when_score_and_limit_both_ok():
    resp = _to_response(_make_report(overall_score=65, credit_limit=200_000))
    assert resp.requires_human_review is False


def test_requires_review_triggered_by_either_condition():
    assert _to_response(_make_report(overall_score=30, credit_limit=50_000)).requires_human_review
    assert _to_response(_make_report(overall_score=80, credit_limit=300_000)).requires_human_review


# ── _to_response: field mapping ───────────────────────────────────────────────

def test_to_response_maps_fields_correctly():
    resp = _to_response(_make_report(overall_score=72, credit_limit=150_000))
    assert resp.company_name == "Test Co"
    assert resp.overall_score == 72
    assert resp.credit_limit_recommended == 150_000
    assert resp.decision == "approved"
    assert resp.risk_rating == "medium"


def test_hubspot_url_extracted_from_hubspot_created():
    report = _make_report(hubspot_url="https://app-eu1.hubspot.com/contacts/148454999/record/0-2/999")
    assert _to_response(report).hubspot_url == (
        "https://app-eu1.hubspot.com/contacts/148454999/record/0-2/999"
    )


def test_hubspot_url_none_when_no_created_record():
    report = _make_report()
    report.hubspot_created = None
    assert _to_response(report).hubspot_url is None


# ── /underwrite endpoint ──────────────────────────────────────────────────────

async def test_underwrite_rejects_missing_company_name(client):
    resp = await client.post("/underwrite", json={"revenue": 500_000})
    assert resp.status_code == 422


async def test_underwrite_rejects_negative_revenue(client):
    resp = await client.post("/underwrite", json={"company_name": "Test Co", "revenue": -1})
    assert resp.status_code == 422


async def test_underwrite_rejects_zero_revenue(client):
    resp = await client.post("/underwrite", json={"company_name": "Test Co", "revenue": 0})
    assert resp.status_code == 422


@patch("main_api._AGENT")
async def test_underwrite_happy_path(mock_agent, client):
    mock_agent.underwrite = AsyncMock(return_value=_make_report())
    resp = await client.post("/underwrite", json={
        "company_name": "Test Co",
        "revenue": 1_200_000,
        "industry": "Retail",
        "years": 5,
        "country": "New Zealand",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["company_name"] == "Test Co"
    assert data["decision"] == "approved"
    assert data["requires_human_review"] is False
    assert data["overall_score"] == 72


@patch("main_api._AGENT")
async def test_underwrite_uses_defaults_for_optional_fields(mock_agent, client):
    mock_agent.underwrite = AsyncMock(return_value=_make_report())
    resp = await client.post("/underwrite", json={"company_name": "Minimal Co"})
    assert resp.status_code == 200
    call_app = mock_agent.underwrite.call_args[0][0]
    assert call_app.name == "Minimal Co"
    assert call_app.annual_revenue == 1_000_000  # default
    assert call_app.years_trading == 5            # default


@patch("main_api._AGENT")
async def test_underwrite_propagates_agent_exception(mock_agent, client):
    mock_agent.underwrite = AsyncMock(side_effect=RuntimeError("OpenAI timeout"))
    resp = await client.post("/underwrite", json={"company_name": "Test Co"})
    assert resp.status_code == 500
    assert "OpenAI timeout" in resp.json()["detail"]


# ── /demo endpoint ────────────────────────────────────────────────────────────

@patch("main_api._AGENT")
async def test_demo_returns_200(mock_agent, client):
    mock_agent.underwrite = AsyncMock(return_value=_make_report())
    resp = await client.get("/demo")
    assert resp.status_code == 200
    assert "company_name" in resp.json()


@patch("main_api._AGENT")
async def test_demo_cycles_through_profiles(mock_agent, client):
    mock_agent.underwrite = AsyncMock(return_value=_make_report())
    import main_api
    main_api._demo_index = 0

    names_seen = set()
    for _ in range(3):
        resp = await client.get("/demo")
        assert resp.status_code == 200
        names_seen.add(mock_agent.underwrite.call_args[0][0].name)

    assert len(names_seen) == 3
