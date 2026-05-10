import asyncio
import json

from dotenv import load_dotenv
from openai import AsyncOpenAI
from pydantic import BaseModel, Field

load_dotenv()

from mock_apis import fetch_apollo_data, fetch_credit_bureau, fetch_xero_financials
from models import (
    CustomerApplication,
    Decision,
    FinancialData,
    RiskRating,
    RiskScore,
    UnderwritingReport,
)

_MODEL = "gpt-4o"

_SYSTEM = """\
You are a senior credit analyst at OceanX AI, a trade finance company that provides
working capital solutions to SMEs. Your task is to assess a credit application and
produce a structured, evidence-based credit decision.

## Scoring framework — produce an overall_score from 0 to 100 (higher = lower risk)

| Dimension           | Weight | Guidance                                                         |
|---------------------|--------|------------------------------------------------------------------|
| Revenue stability   |  25 %  | YoY trend; sustained growth scores high, contraction scores low  |
| Debt serviceability |  25 %  | debt_ratio < 0.4 → strong; 0.4–0.6 → moderate; > 0.6 → weak     |
| Payment history     |  25 %  | payment_history_score 750+ → excellent; 600–749 → fair; < 600 → poor |
| Industry risk       |  15 %  | Assess volatility of the sector; retail/F&B score lower than tech |
| Liquidity           |  10 %  | bank_balance vs. monthly obligations; runway matters              |

## Credit limit — set credit_limit_recommended between $10,000 and $500,000 USD

| Score band | Max credit limit  |
|------------|-------------------|
| 80 – 100   | $500,000          |
| 60 –  79   | $250,000          |
| 40 –  59   | $100,000          |
|  0 –  39   | $50,000 (or $0 if declined) |

## Risk rating thresholds

| Score band | risk_rating |
|------------|-------------|
| 75 – 100   | low         |
| 50 –  74   | medium      |
| 25 –  49   | high        |
|  0 –  24   | declined    |

## Decision rules

- **approved**: overall_score ≥ 60 and no critical flags
- **conditional**: overall_score 40–59, OR score ≥ 60 with notable flags (e.g. overdue invoices,
  high credit utilisation)
- **declined**: overall_score < 40, OR critical flags present (defaults in last 5 years,
  court judgements, debt_ratio > 0.8)

When declining, set credit_limit_recommended to 0 and risk_rating to "declined".

## Flags

Populate the flags list with short, factual strings describing material risk factors found
in the data (e.g. "3 defaults in last 5 years", "debt ratio 0.72 — above threshold",
"revenue declining 8 % YoY"). Leave the list empty if no significant flags are found.

## reasoning

Write 2–4 sentences summarising the key evidence behind the decision. Reference specific
numbers from the data. Be direct and professional.

Return only a valid JSON object matching the required schema. No preamble, no markdown.\
"""


class _CreditAnalysis(BaseModel):
    """Internal model — captures everything Claude returns before we split it into report fields."""

    overall_score: int = Field(..., ge=0, le=100)
    credit_limit_recommended: float = Field(..., ge=0)
    risk_rating: RiskRating
    flags: list[str] = Field(default_factory=list)
    reasoning: str = Field(..., description="2–4 sentence narrative explanation of the decision.")
    decision: Decision


def _build_prompt(
    application: CustomerApplication,
    apollo: dict,
    xero: dict,
    credit: dict,
) -> str:
    return (
        "Assess the following credit application. All monetary figures are in USD.\n\n"
        f"## Customer application\n{json.dumps(application.model_dump(), indent=2)}\n\n"
        f"## Company enrichment (Apollo)\n{json.dumps(apollo, indent=2)}\n\n"
        f"## Financial statements (Xero)\n{json.dumps(xero, indent=2)}\n\n"
        f"## Credit bureau report\n{json.dumps(credit, indent=2)}\n\n"
        "Produce your structured credit analysis."
    )


class UnderwritingAgent:
    """AI underwriting agent powered by GPT-4o."""

    def __init__(self) -> None:
        self._client = AsyncOpenAI()

    async def underwrite(self, application: CustomerApplication) -> UnderwritingReport:
        """Run a full underwriting assessment for the given application."""
        apollo_data, xero_data, credit_data = await asyncio.gather(
            fetch_apollo_data(application.name),
            fetch_xero_financials(application.name),
            fetch_credit_bureau(application.name),
        )

        raw_fico = credit_data["payment_history_score"]
        financial_data = FinancialData(
            revenue_trend=xero_data["revenue_trend"],
            debt_ratio=xero_data["debt_ratio"],
            payment_history_score=round((raw_fico - 300) / 5.5),
            bank_balance=xero_data["bank_balance_usd"],
        )

        response = await self._client.beta.chat.completions.parse(
            model=_MODEL,
            max_tokens=1024,
            messages=[
                {"role": "system", "content": _SYSTEM},
                {"role": "user", "content": _build_prompt(application, apollo_data, xero_data, credit_data)},
            ],
            response_format=_CreditAnalysis,
        )

        analysis: _CreditAnalysis = response.choices[0].message.parsed

        return UnderwritingReport(
            application=application,
            financial_data=financial_data,
            risk_score=RiskScore(
                overall_score=analysis.overall_score,
                credit_limit_recommended=analysis.credit_limit_recommended,
                risk_rating=analysis.risk_rating,
                flags=analysis.flags,
            ),
            reasoning=analysis.reasoning,
            decision=analysis.decision,
        )
