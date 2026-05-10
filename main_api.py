import asyncio

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from agent import UnderwritingAgent
from models import CustomerApplication, UnderwritingReport

app = FastAPI(title="OceanX AI Underwriting Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

_AGENT = UnderwritingAgent()

_DEMO_PROFILES: list[CustomerApplication] = [
    CustomerApplication(
        name="Pacific Rim Trading Ltd",
        annual_revenue=2_400_000,
        industry="Food Import",
        years_trading=12,
        country="New Zealand",
    ),
    CustomerApplication(
        name="Apex Distribution Co",
        annual_revenue=380_000,
        industry="Electronics",
        years_trading=3,
        country="Australia",
    ),
    CustomerApplication(
        name="FastMove Logistics",
        annual_revenue=95_000,
        industry="General Trade",
        years_trading=1,
        country="United States",
    ),
]

_demo_index = 0


class UnderwriteRequest(BaseModel):
    company_name: str
    revenue: float = Field(default=1_000_000, gt=0)
    industry: str = "General Trade"
    years: int = Field(default=5, ge=0)
    country: str = "New Zealand"


class UnderwriteResponse(BaseModel):
    company_name: str
    industry: str
    annual_revenue: float
    years_trading: int
    country: str
    revenue_trend: float
    debt_ratio: float
    payment_history_score: int
    bank_balance: float
    overall_score: int
    credit_limit_recommended: float
    risk_rating: str
    flags: list[str]
    reasoning: str
    decision: str
    requires_human_review: bool


def _to_response(report: UnderwritingReport) -> UnderwriteResponse:
    rs = report.risk_score
    requires_review = rs.overall_score < 45 or rs.credit_limit_recommended > 250_000
    return UnderwriteResponse(
        company_name=report.application.name,
        industry=report.application.industry,
        annual_revenue=report.application.annual_revenue,
        years_trading=report.application.years_trading,
        country=report.application.country,
        revenue_trend=report.financial_data.revenue_trend,
        debt_ratio=report.financial_data.debt_ratio,
        payment_history_score=report.financial_data.payment_history_score,
        bank_balance=report.financial_data.bank_balance,
        overall_score=rs.overall_score,
        credit_limit_recommended=rs.credit_limit_recommended,
        risk_rating=rs.risk_rating.value,
        flags=rs.flags,
        reasoning=report.reasoning,
        decision=report.decision.value,
        requires_human_review=requires_review,
    )


@app.get("/")
async def root() -> FileResponse:
    return FileResponse("static/index.html")


@app.post("/underwrite", response_model=UnderwriteResponse)
async def underwrite(req: UnderwriteRequest) -> UnderwriteResponse:
    application = CustomerApplication(
        name=req.company_name,
        annual_revenue=req.revenue,
        industry=req.industry,
        years_trading=req.years,
        country=req.country,
    )
    try:
        report = await _AGENT.underwrite(application)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return _to_response(report)


@app.get("/demo", response_model=UnderwriteResponse)
async def demo() -> UnderwriteResponse:
    global _demo_index
    application = _DEMO_PROFILES[_demo_index % len(_DEMO_PROFILES)]
    _demo_index += 1
    try:
        report = await _AGENT.underwrite(application)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return _to_response(report)
