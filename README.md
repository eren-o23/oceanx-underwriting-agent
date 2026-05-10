# OceanX AI — Underwriting Agent

## What This Does

This is an AI-powered credit underwriting agent built for OceanX AI, a trade finance company that provides working capital to SMEs engaged in cross-border trade. When a business applies for a credit facility, the agent pulls financial and company data from three external sources in parallel, passes the full picture to GPT-4o with a structured scoring framework, and returns a credit decision — approved, conditional, or declined — along with a recommended credit limit, a risk rating, and a written analyst rationale. The entire assessment takes a few seconds rather than hours.

The system is designed around the principle that AI should automate everything it can do reliably, while humans retain control at the points where judgement or accountability matter most. A human checkpoint fires automatically when the overall risk score falls below 45 or the recommended credit limit exceeds $250,000 — flagging the application for manual review before any commitment is made. This mirrors OceanX's broader operating model: agents handle the analytical heavy lifting, humans make the capital decisions.

## Demo

```bash
pip install -r requirements.txt
echo 'OPENAI_API_KEY=sk-...' > .env
uvicorn main_api:app --reload
```

Then open [http://localhost:8000](http://localhost:8000) in your browser. Use the form to assess any company, or click **Run Demo** to cycle through three preset risk profiles (low, medium, high).

To use the CLI instead:

```bash
python main.py --demo
python main.py --company "Apex Distribution Co" --revenue 380000 --industry Electronics --years 3
```

## Architecture

| File | Purpose |
|---|---|
| `agent.py` | Core underwriting logic. Calls the three mock APIs in parallel, normalises the data, sends it to GPT-4o with a structured system prompt, parses the response into a typed `UnderwritingReport`, and enforces the human checkpoint rules. |
| `mock_apis.py` | Simulates three external data sources — Apollo (company enrichment), Xero (financial statements), and a credit bureau — with stable per-company randomisation via MD5 seed, plus live jitter to make demos feel real. Each call has a 0.5s simulated latency. |
| `models.py` | Pydantic v2 data models for the full underwriting pipeline: `CustomerApplication`, `FinancialData`, `RiskScore`, `UnderwritingReport`, and the `RiskRating` / `Decision` enums. All fields are validated at the boundary. |
| `report.py` | Terminal output using the Rich library. `print_report()` renders a formatted credit memo with a header panel, risk dimension table, score bars, flag list, and analyst reasoning. `print_human_checkpoint()` prints an amber warning panel when thresholds are breached. |
| `main_api.py` | FastAPI server exposing `POST /underwrite` and `GET /demo`. Handles CORS, serves the frontend as a static file, and computes `requires_human_review` server-side so the frontend can render the review banner without reimplementing threshold logic. |
| `static/index.html` | Single-file web frontend — no frameworks, no build step. Two-column layout with a credit application form on the left and an animated results panel on the right. Includes an Export PDF button that generates a one-page credit memo client-side using jsPDF. |

## How It Works

1. **Input received** — a `CustomerApplication` is submitted via the web form or CLI, containing company name, annual revenue, industry, years trading, and country.

2. **Three parallel API calls** — `asyncio.gather()` fires `fetch_apollo_data`, `fetch_xero_financials`, and `fetch_credit_bureau` simultaneously. Apollo returns company enrichment (employee count, founding year, description). Xero returns revenue trend, debt ratio, and bank balance. The credit bureau returns a FICO-style payment history score (300–850), which is normalised to 0–100 before use.

3. **Data passed to GPT-4o** — all inputs are assembled into a structured prompt and sent to `gpt-4o` via the OpenAI `beta.chat.completions.parse()` endpoint, with a Pydantic model as the `response_format`. This guarantees a typed, validated response with no prompt engineering needed to extract JSON.

4. **Risk scored across five dimensions** — the model scores revenue stability, debt serviceability, payment history, industry risk, and liquidity against the weighting table in the system prompt. Hard score caps are enforced for weak-profile signals: revenue under $100k, one year or less trading, negative net profit, or credit utilisation above 80% each impose a ceiling below 45, preventing those applications from scoring into the approved band.

5. **Human checkpoint evaluated** — once the report is returned, `requires_human_review` is set to `true` if `overall_score < 45` or `credit_limit_recommended > $250,000`. In the web UI this renders an amber banner before the result. In the CLI it prints a warning panel. In the PDF export it appears as a flagged section within the credit memo.

6. **Decision rendered and PDF available** — the full report is displayed in the UI with a decision badge (Approved / Refer / Declined), credit limit, animated score bars per dimension, risk flags, and analyst reasoning. Clicking **Export PDF** generates a formatted one-page credit memorandum client-side, named `OceanX-{Company}-{Date}.pdf`, suitable for an internal credit file.

## Risk Scoring Model

| Dimension | Data Source | Weight | Scoring Guidance |
|---|---|---|---|
| Revenue Stability | Xero (`revenue_trend`) | 25% | YoY growth positive → high score; contraction → low score; anchored at 0% = 50 |
| Debt Serviceability | Xero (`debt_ratio`) | 25% | Below 0.4 → strong; 0.4–0.6 → moderate; above 0.6 → weak; above 0.8 → critical flag |
| Payment History | Credit Bureau (`payment_history_score`) | 25% | Normalised FICO 300–850 to 0–100; 75+ excellent, 50–74 fair, below 50 poor |
| Industry Risk | Application (`industry`) | 15% | Retail / F&B / agriculture → higher risk; tech / SaaS / health → lower risk |
| Liquidity | Xero (`bank_balance_usd`) | 10% | Bank balance relative to monthly revenue obligations; runway assessed contextually |

Score bands map to decisions: 80–100 → Approved up to $500k; 60–79 → Approved up to $250k; 40–59 → Conditional up to $100k; below 40 → Declined.

## Scaling to Full Multi-Agent System

This underwriting agent is Step 3 in OceanX's nine-step end-to-end workflow and is designed to slot directly into a broader multi-agent architecture. The **Master Supervisor Agent** would orchestrate the full pipeline, passing control to this agent once a human sales meeting is complete and consuming its credit decision to gate downstream steps. The **Customer Acquisition Agent** — running outreach across Instantly, Dripify, Apollo, and HubSpot — would hand off qualified leads to the Supervisor, which then triggers underwriting. Once a credit limit is set here, the **Contract and Structuring Agent** uses it to generate a pricing proposal and DocuSign contract. The **Operations Agent** ingests the signed contract to create products and purchase orders in CIN7 and raise invoices and bills in Xero. The **Payment Agent** triggers GoCardless direct debits against the approved credit limit and reconciles collections in Xero. The **Logistics Agent** tracks shipment milestones and updates order status in real time. The **Inventory Agent** syncs warehouse WMS data into CIN7 as goods arrive. The **Collections Agent** monitors outstanding balances against the credit limit set by this agent and escalates delays — making the credit decision made here the single source of truth for exposure management across the entire system.

## Tech Stack

- **Python 3.11+** — runtime
- **FastAPI + Uvicorn** — HTTP API and static file server
- **OpenAI GPT-4o** — credit analysis via structured output (`beta.chat.completions.parse`)
- **Pydantic v2** — data validation and schema enforcement throughout
- **Rich** — terminal report formatting (CLI mode)
- **jsPDF** — client-side PDF generation (no server dependency)
- **Plain HTML / CSS / JS** — single-file frontend, no framework, no build step
- **python-dotenv** — environment variable management

## Assignment Context

Built as part of the OceanX AI intern automation assignment, May 2026, demonstrating the underwriting agent component of OceanX's broader nine-agent trade finance automation system.
