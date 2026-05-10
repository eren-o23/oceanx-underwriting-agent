# OceanX Underwriting Agent

## What this is
A Python CLI tool that acts as an AI underwriting agent for OceanX AI,
a trade finance company. Takes a customer application, simulates pulling
financial data, scores risk, and outputs a structured credit decision.

## Tech stack
- Python 3.11+
- Claude API (anthropic SDK) as the agent brain
- Mock JSON responses simulating CIN7, Xero, Apollo APIs
- Rich library for terminal output

## Key files
- main.py — entry point
- agent.py — the underwriting agent logic
- mock_apis.py — simulated API responses
- models.py — data models (Pydantic)
- report.py — output formatting

## Coding conventions
- Type hints everywhere
- Pydantic models for all data structures
- Functions over classes where possible
- Clear docstrings on every function
