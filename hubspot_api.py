import os
from datetime import datetime, timezone

import httpx

_BASE = "https://api.hubapi.com"
_PORTAL_ID = "148454999"

_LEAD_STATUS_MAP = {
    "approved": "CONNECTED",
    "conditional": "IN_PROGRESS",
    "declined": "UNQUALIFIED",
}


async def create_hubspot_company(
    name: str,
    annual_revenue: float,
    country: str,
    decision: str,
    credit_limit: float,
    risk_rating: str,
    overall_score: int,
    reasoning: str,
    industry: str = "",
) -> dict:
    """Create a HubSpot company record and attach a decision note."""
    api_key = os.getenv("HUBSPOT_API_KEY")
    if not api_key:
        return {"skipped": True, "reason": "HUBSPOT_API_KEY not configured"}

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    lead_status = _LEAD_STATUS_MAP.get(decision, "IN_PROGRESS")
    description = (
        f"OceanX Credit Decision: {decision.upper()} | "
        f"Score: {overall_score}/100 | "
        f"Limit: ${credit_limit:,.0f} | "
        f"Risk: {risk_rating}"
    )
    note_body = (
        f"OceanX AI Underwriting Decision\n"
        f"Decision: {decision.upper()}\n"
        f"Overall Score: {overall_score}/100\n"
        f"Risk Rating: {risk_rating}\n"
        f"Credit Limit Recommended: ${credit_limit:,.2f}\n\n"
        f"Reasoning:\n{reasoning}"
    )

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            company_resp = await client.post(
                f"{_BASE}/crm/v3/objects/companies",
                headers=headers,
                json={
                    "properties": {
                        "name": name,
                        "annualrevenue": str(int(annual_revenue)),
                        "country": country,
                        "description": description,
                        "hs_lead_status": lead_status,
                    }
                },
            )
            company_resp.raise_for_status()
            company = company_resp.json()
            company_id = company["id"]

            note_resp = await client.post(
                f"{_BASE}/crm/v3/objects/notes",
                headers=headers,
                json={
                    "properties": {
                        "hs_note_body": note_body,
                        "hs_timestamp": datetime.now(timezone.utc).strftime(
                            "%Y-%m-%dT%H:%M:%S.000Z"
                        ),
                    },
                    "associations": [
                        {
                            "to": {"id": company_id},
                            "types": [
                                {
                                    "associationCategory": "HUBSPOT_DEFINED",
                                    "associationTypeId": 185,
                                }
                            ],
                        }
                    ],
                },
            )

            hubspot_url = f"https://app-eu1.hubspot.com/contacts/{_PORTAL_ID}/record/0-2/{company_id}"

            return {
                "company_id": company_id,
                "company_name": name,
                "hubspot_url": hubspot_url,
                "lead_status": lead_status,
                "decision_recorded": decision,
                "credit_limit_usd": credit_limit,
                "overall_score": overall_score,
                "note_created": note_resp.status_code == 201,
                "source": "hubspot_live_v1",
            }

    except httpx.HTTPStatusError as exc:
        return {
            "error": f"HubSpot API {exc.response.status_code}: {exc.response.text[:300]}",
            "source": "hubspot_live_v1",
        }
    except httpx.RequestError as exc:
        return {
            "error": f"HubSpot request failed: {exc!s}",
            "source": "hubspot_live_v1",
        }
