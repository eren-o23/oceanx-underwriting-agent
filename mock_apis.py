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
        "bureau_report_date": "2026-05-10",
        "source": "credit_bureau_mock_v1",
    }
