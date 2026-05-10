import argparse
import asyncio

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from agent import UnderwritingAgent
from models import CustomerApplication
from report import print_human_checkpoint, print_report

console = Console()

_DEMO_PROFILES: list[tuple[str, str, CustomerApplication]] = [
    (
        "Profile 1 of 3  —  Low Risk",
        "green",
        CustomerApplication(
            name="Pacific Rim Trading Ltd",
            annual_revenue=2_400_000,
            industry="Food Import",
            years_trading=12,
            country="New Zealand",
        ),
    ),
    (
        "Profile 2 of 3  —  Medium Risk",
        "yellow",
        CustomerApplication(
            name="Apex Distribution Co",
            annual_revenue=380_000,
            industry="Electronics",
            years_trading=3,
            country="Australia",
        ),
    ),
    (
        "Profile 3 of 3  —  High Risk",
        "red",
        CustomerApplication(
            name="FastMove Logistics",
            annual_revenue=95_000,
            industry="General Trade",
            years_trading=1,
            country="United States",
        ),
    ),
]


async def _assess(agent: UnderwritingAgent, application: CustomerApplication) -> None:
    with console.status("[dim]Calling APIs and running credit analysis…[/dim]", spinner="dots"):
        report = await agent.underwrite(application)
    print_human_checkpoint(report)
    print_report(report)


async def _run_demo() -> None:
    agent = UnderwritingAgent()
    for i, (label, style, application) in enumerate(_DEMO_PROFILES):
        header = Text(justify="center")
        header.append(label + "\n", style=f"bold {style}")
        header.append(
            f"{application.name}  ·  ${application.annual_revenue:,.0f}  ·  "
            f"{application.industry}  ·  {application.years_trading} yr trading",
            style="dim white",
        )
        console.print(Panel(header, border_style=style, padding=(1, 4)))
        console.print()

        await _assess(agent, application)

        if i < len(_DEMO_PROFILES) - 1:
            await asyncio.sleep(2)


async def _run_single(application: CustomerApplication) -> None:
    agent = UnderwritingAgent()
    await _assess(agent, application)


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="underwrite",
        description="OceanX AI — AI-powered trade finance underwriting agent",
    )
    parser.add_argument(
        "--company",
        help="Company name to underwrite",
    )
    parser.add_argument(
        "--revenue",
        type=float,
        default=1_000_000,
        metavar="USD",
        help="Annual revenue in USD (default: 1,000,000)",
    )
    parser.add_argument(
        "--industry",
        default="General Trade",
        help="Industry type (default: General Trade)",
    )
    parser.add_argument(
        "--years",
        type=int,
        default=5,
        metavar="N",
        help="Years in business (default: 5)",
    )
    parser.add_argument(
        "--country",
        default="New Zealand",
        help="Country of operation (default: New Zealand)",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run three preset risk profiles (low / medium / high) back-to-back",
    )

    args = parser.parse_args()

    if args.demo:
        asyncio.run(_run_demo())
    elif args.company:
        application = CustomerApplication(
            name=args.company,
            annual_revenue=args.revenue,
            industry=args.industry,
            years_trading=args.years,
            country=args.country,
        )
        asyncio.run(_run_single(application))
    else:
        parser.error("--company is required (or use --demo to run the preset profiles)")


if __name__ == "__main__":
    main()
