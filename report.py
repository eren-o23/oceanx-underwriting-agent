from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

from models import Decision, UnderwritingReport

console = Console()

_DECISION_META: dict[Decision, tuple[str, str]] = {
    Decision.APPROVED: ("green", "✓  APPROVED"),
    Decision.CONDITIONAL: ("yellow", "~  REFER"),
    Decision.DECLINED: ("red", "✗  DECLINED"),
}


def _bar(score: int, width: int = 20) -> Text:
    """Block-character progress bar, coloured by score band."""
    filled = round(score * width / 100)
    color = "green" if score >= 70 else "yellow" if score >= 45 else "red"
    return Text(f"{'█' * filled}{'░' * (width - filled)}  {score:3d} / 100", style=color)


def _revenue_score(trend: float) -> int:
    """0 % growth → 50; clamp to [0, 100]."""
    return max(0, min(100, int(50 + trend * 100)))


def _debt_score(ratio: float) -> int:
    """0 debt → 100; fully leveraged → 0."""
    return max(0, min(100, int((1.0 - ratio) * 100)))


def _industry_score(industry: str) -> int:
    """Rough sector risk score derived from industry name keywords."""
    lower = industry.lower()
    high_risk = {"retail", "hospitality", "food", "beverage", "agriculture", "gaming", "fashion"}
    low_risk = {"tech", "software", "saas", "fintech", "health", "logistics"}
    if any(k in lower for k in high_risk):
        return 30
    if any(k in lower for k in low_risk):
        return 80
    return 55


def print_report(report: UnderwritingReport) -> None:
    """Print a fully formatted underwriting report to the terminal."""
    color, label = _DECISION_META[report.decision]
    app = report.application
    fd = report.financial_data
    rs = report.risk_score

    # ── Header panel ────────────────────────────────────────────────────────
    header = Text(justify="center")
    header.append(app.name + "\n", style="bold white")
    header.append(
        f"{app.industry}  ·  {app.country}  ·  "
        f"${app.annual_revenue:,.0f} revenue  ·  "
        f"{app.years_trading} yr{'s' if app.years_trading != 1 else ''} trading\n",
        style="dim",
    )
    header.append(f"\n{label}", style=f"bold {color}")
    console.print(
        Panel(
            header,
            title="[bold]OceanX AI — Underwriting Report[/bold]",
            border_style=color,
            padding=(1, 4),
        )
    )
    console.print()

    # ── Risk dimension table ─────────────────────────────────────────────────
    sign = "+" if fd.revenue_trend >= 0 else ""
    dimensions = [
        ("Revenue Stability",   f"{sign}{fd.revenue_trend * 100:.1f}% YoY",  _revenue_score(fd.revenue_trend)),
        ("Debt Serviceability", f"{fd.debt_ratio:.2f} ratio",                 _debt_score(fd.debt_ratio)),
        ("Payment History",     f"{fd.payment_history_score} / 100",          fd.payment_history_score),
        ("Industry Risk",       app.industry,                                   _industry_score(app.industry)),
    ]

    table = Table(
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan",
        title="Risk Dimensions",
        title_style="bold",
        padding=(0, 1),
    )
    table.add_column("Dimension",    style="dim",     width=22)
    table.add_column("Input Value",  justify="right", width=22)
    table.add_column("Derived Score",                 width=32)

    for dim, raw, score in dimensions:
        table.add_row(dim, raw, _bar(score))

    table.add_section()
    table.add_row(
        Text("Overall Score", style="bold"),
        Text(f"{rs.overall_score} / 100", style="bold"),
        _bar(rs.overall_score),
    )

    console.print(table)
    console.print()

    # ── Recommended credit limit ─────────────────────────────────────────────
    limit_line = Text()
    limit_line.append("  Recommended credit limit:  ", style="dim")
    if rs.credit_limit_recommended > 0:
        limit_line.append(f"${rs.credit_limit_recommended:,.0f}", style=f"bold {color}")
    else:
        limit_line.append("$0  (application declined)", style="bold red")
    console.print(limit_line)
    console.print()

    # ── Risk flags ───────────────────────────────────────────────────────────
    if rs.flags:
        console.print(Rule("[yellow]Risk Flags[/yellow]", style="yellow"))
        for flag in rs.flags:
            console.print(f"  [yellow]▲[/yellow]  {flag}")
        console.print()

    # ── Analyst reasoning ────────────────────────────────────────────────────
    console.print(Rule("Analyst Reasoning", style="dim"))
    console.print(f"\n  {report.reasoning}\n")


def print_human_checkpoint(report: UnderwritingReport) -> None:
    """Print a human-review warning panel when the report exceeds risk thresholds.

    Triggers when overall_score < 45 OR credit_limit_recommended > $250,000.
    Does nothing if neither condition is met.
    """
    rs = report.risk_score
    reasons: list[Text] = []

    if rs.overall_score < 45:
        line = Text()
        line.append("  • Low overall score: ", style="yellow")
        line.append(f"{rs.overall_score} / 100", style="bold yellow")
        line.append("  (threshold: 45)", style="dim")
        reasons.append(line)

    if rs.credit_limit_recommended > 250_000:
        line = Text()
        line.append("  • High credit limit recommended: ", style="yellow")
        line.append(f"${rs.credit_limit_recommended:,.0f}", style="bold yellow")
        line.append("  (threshold: $250,000)", style="dim")
        reasons.append(line)

    if not reasons:
        return

    body = Text()
    body.append("Flagged for the following reason(s):\n\n", style="dim")
    for reason in reasons:
        body.append_text(reason)
        body.append("\n")
    body.append("\nAgent has paused. Awaiting human approval before proceeding.", style="bold white")

    console.print(
        Panel(
            body,
            title="[bold yellow]⚠️  HUMAN REVIEW REQUIRED[/bold yellow]",
            border_style="yellow",
            padding=(1, 3),
        )
    )
    console.print()
