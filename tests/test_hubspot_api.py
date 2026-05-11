import pytest
import httpx
from unittest.mock import AsyncMock, MagicMock, patch

from hubspot_api import create_hubspot_company

_KWARGS = dict(
    name="Test Co",
    annual_revenue=1_000_000,
    country="New Zealand",
    decision="approved",
    credit_limit=50_000,
    risk_rating="low",
    overall_score=75,
    reasoning="Strong financials across all dimensions.",
)


def _mock_client(company_id: str = "12345678", note_status: int = 201):
    """Return a mock httpx.AsyncClient with canned company + note responses."""
    company_resp = MagicMock()
    company_resp.json.return_value = {"id": company_id}
    company_resp.raise_for_status = MagicMock()

    note_resp = MagicMock()
    note_resp.status_code = note_status

    client = AsyncMock()
    client.post = AsyncMock(side_effect=[company_resp, note_resp])
    return client


def _patch_client(mock_client):
    ctx = MagicMock()
    ctx.__aenter__ = AsyncMock(return_value=mock_client)
    ctx.__aexit__ = AsyncMock(return_value=False)
    return patch("hubspot_api.httpx.AsyncClient", return_value=ctx)


# ── Skip when no key ──────────────────────────────────────────────────────────

async def test_skips_when_no_api_key(monkeypatch):
    monkeypatch.delenv("HUBSPOT_API_KEY", raising=False)
    result = await create_hubspot_company(**_KWARGS)
    assert result["skipped"] is True


# ── URL construction ──────────────────────────────────────────────────────────

async def test_url_format(monkeypatch):
    monkeypatch.setenv("HUBSPOT_API_KEY", "pat-eu1-test")
    with _patch_client(_mock_client("99887766")):
        result = await create_hubspot_company(**_KWARGS)
    assert result["hubspot_url"] == (
        "https://app-eu1.hubspot.com/contacts/148454999/record/0-2/99887766"
    )
    assert result["company_id"] == "99887766"


# ── Lead status mapping ───────────────────────────────────────────────────────

@pytest.mark.parametrize("decision,expected_status", [
    ("approved",    "CONNECTED"),
    ("conditional", "IN_PROGRESS"),
    ("declined",    "UNQUALIFIED"),
])
async def test_lead_status_mapping(monkeypatch, decision, expected_status):
    monkeypatch.setenv("HUBSPOT_API_KEY", "pat-eu1-test")
    kwargs = {**_KWARGS, "decision": decision}
    with _patch_client(_mock_client()):
        result = await create_hubspot_company(**kwargs)
    assert result["lead_status"] == expected_status


# ── Note creation flag ────────────────────────────────────────────────────────

async def test_note_created_true_when_201(monkeypatch):
    monkeypatch.setenv("HUBSPOT_API_KEY", "pat-eu1-test")
    with _patch_client(_mock_client(note_status=201)):
        result = await create_hubspot_company(**_KWARGS)
    assert result["note_created"] is True


async def test_note_created_false_when_403(monkeypatch):
    monkeypatch.setenv("HUBSPOT_API_KEY", "pat-eu1-test")
    with _patch_client(_mock_client(note_status=403)):
        result = await create_hubspot_company(**_KWARGS)
    # A 403 on the note (missing scope) should not crash — just sets note_created False
    assert result["note_created"] is False


# ── Error handling ────────────────────────────────────────────────────────────

async def test_http_error_returns_error_dict(monkeypatch):
    monkeypatch.setenv("HUBSPOT_API_KEY", "pat-eu1-test")

    bad_response = MagicMock()
    bad_response.status_code = 401
    bad_response.text = "Unauthorized"

    client = AsyncMock()
    client.post = AsyncMock(
        side_effect=httpx.HTTPStatusError(
            "401", request=MagicMock(), response=bad_response
        )
    )
    with _patch_client(client):
        result = await create_hubspot_company(**_KWARGS)

    assert "error" in result
    assert "401" in result["error"]
    assert result["source"] == "hubspot_live_v1"


async def test_request_error_returns_error_dict(monkeypatch):
    monkeypatch.setenv("HUBSPOT_API_KEY", "pat-eu1-test")

    client = AsyncMock()
    client.post = AsyncMock(
        side_effect=httpx.RequestError("connection refused", request=MagicMock())
    )
    with _patch_client(client):
        result = await create_hubspot_company(**_KWARGS)

    assert "error" in result
    assert "connection refused" in result["error"]
