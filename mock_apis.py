import asyncio
import hashlib
import random
from typing import Any


def _seeded(company_name: str) -> random.Random:
    """Return a Random instance seeded from the company name for consistent per-company values."""
    seed = int(hashlib.md5(company_name.lower().encode()).hexdigest(), 16) % (2**32)
    return random.Random(seed)


async def fetch_apollo_data(company_name: str) -> dict[str, Any]:
    """Simulate Apollo.io enrichment — company firmographics and contact info."""
    await asyncio.sleep(0.5)
    rng = _seeded(company_name)

    industries = ["Manufacturing", "Retail", "Logistics", "Agriculture", "Technology", "Food & Beverage"]
    countries = ["New Zealand", "Australia", "United Kingdom", "United States", "Canada"]
    headcount_bands = ["1-10", "11-50", "51-200", "201-500", "500+"]

    base_revenue = rng.randint(500_000, 50_000_000)
    jitter = random.uniform(0.95, 1.05)  # live-feeling variation each run

    return {
        "company_name": company_name,
        "industry": rng.choice(industries),
        "country": rng.choice(countries),
        "employee_headcount": rng.choice(headcount_bands),
        "estimated_annual_revenue_usd": round(base_revenue * jitter, -3),
        "years_in_business": rng.randint(1, 30),
        "linkedin_employees": rng.randint(5, 600),
        "funding_rounds": rng.randint(0, 4),
        "technologies_used": rng.sample(
            ["Shopify", "Xero", "Salesforce", "HubSpot", "NetSuite", "QuickBooks", "SAP"], k=rng.randint(1, 4)
        ),
        "source": "apollo_mock_v1",
    }


async def fetch_xero_financials(company_name: str) -> dict[str, Any]:
    """Simulate Xero accounting data — P&L, balance sheet, and cash position."""
    await asyncio.sleep(0.5)
    rng = _seeded(company_name)

    base_revenue = rng.randint(400_000, 40_000_000)
    revenue_jitter = random.uniform(0.93, 1.07)
    current_revenue = round(base_revenue * revenue_jitter, -2)

    prior_revenue = round(base_revenue * rng.uniform(0.75, 1.15), -2)
    revenue_trend = round((current_revenue - prior_revenue) / prior_revenue, 4)

    gross_margin = rng.uniform(0.25, 0.65)
    operating_expenses = round(current_revenue * rng.uniform(0.15, 0.40), -2)
    net_profit = round(current_revenue * gross_margin - operating_expenses, -2)

    total_assets = round(current_revenue * rng.uniform(0.8, 2.0), -2)
    total_debt = round(total_assets * rng.uniform(0.10, 0.75), -2)
    debt_ratio = round(total_debt / total_assets, 4)

    bank_balance_jitter = random.uniform(0.90, 1.10)
    bank_balance = round(current_revenue * rng.uniform(0.05, 0.30) * bank_balance_jitter, -2)

    return {
        "company_name": company_name,
        "current_annual_revenue_usd": current_revenue,
        "prior_year_revenue_usd": prior_revenue,
        "revenue_trend": revenue_trend,
        "gross_margin": round(gross_margin, 4),
        "operating_expenses_usd": operating_expenses,
        "net_profit_usd": net_profit,
        "total_assets_usd": total_assets,
        "total_debt_usd": total_debt,
        "debt_ratio": debt_ratio,
        "bank_balance_usd": bank_balance,
        "overdue_invoices_count": rng.randint(0, 12),
        "average_debtor_days": rng.randint(15, 90),
        "source": "xero_mock_v1",
    }


async def fetch_credit_bureau(company_name: str) -> dict[str, Any]:
    """Simulate credit bureau data — payment history, defaults, and trade credit."""
    await asyncio.sleep(0.5)
    rng = _seeded(company_name)

    base_score = rng.randint(450, 850)
    score_jitter = random.randint(-15, 15)  # small live-run variation
    payment_history_score = max(300, min(850, base_score + score_jitter))

    defaults = rng.randint(0, 3)
    late_payments_12m = rng.randint(0, defaults * 4 + rng.randint(0, 5))

    return {
        "company_name": company_name,
        "payment_history_score": payment_history_score,
        "defaults_last_5_years": defaults,
        "late_payments_last_12_months": late_payments_12m,
        "trade_credit_lines_active": rng.randint(1, 10),
        "largest_credit_line_usd": round(rng.randint(10_000, 500_000), -3),
        "credit_utilisation_pct": round(rng.uniform(0.05, 0.90), 2),
        "court_judgements": rng.randint(0, min(defaults, 2)),
        "bureau_report_date": "2026-05-11",
        "source": "credit_bureau_mock_v1",
    }


async def fetch_hubspot_lead(company_name: str) -> dict[str, Any]:
    """Simulate HubSpot CRM record — lead source, meeting outcome, and sales rep notes."""
    await asyncio.sleep(0.5)
    rng = _seeded(company_name)

    lead_sources = [
        "Cold Email (Instantly)", "LinkedIn (Dripify)", "Apollo Outreach",
        "Referral", "Trade Show", "Corporate Finance Broker",
    ]
    sales_reps = ["Sarah Chen", "Marcus Williams", "Priya Patel", "Tom Nguyen"]
    meeting_dates = ["2026-04-22", "2026-04-28", "2026-05-01", "2026-05-05", "2026-05-08"]

    sentiment_score = rng.randint(1, 10)

    positive_notes = [
        f"Strong demand for trade credit. {company_name} imports regularly from Asia — good volume.",
        f"Founder has 10+ years in the industry. Clear growth plan with existing retail partners.",
        f"Existing relationship with major retailers. Credit line would unlock their next buying cycle.",
    ]
    cautious_notes = [
        f"Early-stage business. Limited trading history but founder is credible and well-connected.",
        f"Some concerns raised around cash flow — team mentioned delayed receivables from key client.",
    ]
    critical_notes = [
        f"High leverage flagged during meeting. Owner acknowledged difficulty servicing current debt.",
    ]

    if sentiment_score >= 7:
        notes = rng.choice(positive_notes)
        outcome = "approved_to_proceed"
        sentiment = "positive"
    elif sentiment_score >= 3:
        notes = rng.choice(cautious_notes)
        outcome = "approved_to_proceed"
        sentiment = "cautious"
    else:
        notes = rng.choice(critical_notes)
        outcome = "declined_at_meeting"
        sentiment = "negative"

    return {
        "company_name": company_name,
        "lead_source": rng.choice(lead_sources),
        "assigned_rep": rng.choice(sales_reps),
        "meeting_date": rng.choice(meeting_dates),
        "meeting_outcome": outcome,
        "human_checkpoint_1_completed": True,
        "human_checkpoint_1_approved": outcome == "approved_to_proceed",
        "sales_rep_sentiment": sentiment,
        "sales_notes": notes,
        "hubspot_deal_stage": "underwriting" if outcome == "approved_to_proceed" else "closed_lost",
        "source": "hubspot_mock_v1",
    }


async def simulate_gocardless_mandate(company_name: str, credit_limit: float) -> dict[str, Any]:
    """Simulate GoCardless direct debit mandate for an approved credit facility."""
    await asyncio.sleep(0.3)
    mandate_id = "MD" + hashlib.md5(company_name.encode()).hexdigest()[:8].upper()
    weekly_payment = round(credit_limit / 12, 2)

    return {
        "mandate_id": mandate_id,
        "company_name": company_name,
        "status": "pending_customer_approval",
        "credit_limit_usd": credit_limit,
        "payment_schedule": "weekly",
        "weekly_payment_usd": weekly_payment,
        "repayment_weeks": 12,
        "mandate_url": f"https://pay.gocardless.com/obauth/{mandate_id.lower()}",
        "created_at": "2026-05-11T09:00:00Z",
        "source": "gocardless_mock_v1",
    }


async def simulate_wise_payment_request(company_name: str, amount: float) -> dict[str, Any]:
    """Simulate Wise supplier payment — marked awaiting human approval (second human checkpoint)."""
    await asyncio.sleep(0.3)
    rng = _seeded(company_name)

    transfer_id = "TRF" + hashlib.md5((company_name + str(amount)).encode()).hexdigest()[:8].upper()
    supplier_countries = ["China", "Taiwan", "South Korea", "Vietnam", "India", "Germany"]
    currencies = ["USD", "EUR", "CNY", "SGD", "AUD"]

    return {
        "transfer_id": transfer_id,
        "company_name": company_name,
        "status": "awaiting_human_approval",
        "human_checkpoint_2": "supplier_payment_approval",
        "supplier_country": rng.choice(supplier_countries),
        "amount_usd": amount,
        "currency": rng.choice(currencies),
        "wise_fee_usd": round(amount * 0.005, 2),
        "estimated_arrival": "1–2 business days",
        "exchange_rate_locked": True,
        "approval_required_from": "operations_team",
        "created_at": "2026-05-11T09:01:00Z",
        "source": "wise_mock_v1",
    }
