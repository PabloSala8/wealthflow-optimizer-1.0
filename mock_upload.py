#!/usr/bin/env python3
"""CLI pipeline tester — no Flask required."""

import os
import sys

# Allow running from project root
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from logic.parser import load_and_normalize
from logic.fees import load_broker_specs, generate_full_comparison
from logic.health_score import compute_health_score
from utils.ai_advisor import generate_executive_summary
from tabulate import tabulate


def main():
    print("\n=== WealthFlow Optimizer — CLI Pipeline Test ===\n")

    specs = load_broker_specs(config.BROKER_SPECS_PATH)
    broker_list = list(specs.keys())
    print("Available brokers:")
    for i, bid in enumerate(broker_list):
        print(f"  [{i+1}] {bid} — {specs[bid]['name']}")

    choice = input("\nEnter your current broker ID (e.g. schwab): ").strip().lower()
    if choice not in specs:
        print(f"Error: '{choice}' not found. Choose from: {broker_list}")
        sys.exit(1)

    print(f"\nParsing {config.SAMPLE_PORTFOLIO_PATH} ...")
    portfolio = load_and_normalize(config.SAMPLE_PORTFOLIO_PATH)
    print(f"  Rows loaded:           {len(portfolio.holdings)}")
    print(f"  Total market value:    ${portfolio.total_market_value:,.2f}")
    print(f"  Total cash (sweep):    ${portfolio.total_cash:,.2f}")
    print(f"  Total options contracts: {portfolio.total_options_contracts}")
    print(f"  Header mapping:        {portfolio.header_mapping}")

    portfolio_dict = {
        "total_cash": portfolio.total_cash,
        "total_options_contracts": portfolio.total_options_contracts,
        "holdings": portfolio.holdings,
    }

    print("\nCalculating fee comparisons...")
    comparison = generate_full_comparison(portfolio_dict, choice, specs)

    mutual_fund_flags = comparison[list(comparison.keys())[0]]["mutual_fund_flags"]
    health = compute_health_score(
        total_cash=portfolio.total_cash,
        current_broker_id=choice,
        specs=specs,
        comparison=comparison,
        mutual_fund_flags=mutual_fund_flags,
    )
    print(f"\nHealth Score: {health['score']}/100 — {health['band']}")
    print(f"Penalties: {health['penalties']}")

    # Build comparison table
    rows = []
    for bid, data in comparison.items():
        rows.append([
            data["broker_name"],
            f"{data['sweep']['target_apy']*100:.2f}%",
            f"${data['sweep']['annual_loss_usd']:+,.2f}",
            f"${data['options']['annual_savings_usd']:+,.2f}",
            f"${data['total_annual_savings_usd']:+,.2f}",
            f"${data['acats_exit_fee']:.0f}",
            f"{data['breakeven_months']}" if data['breakeven_months'] != float('inf') else "N/A",
        ])

    headers = ["Broker", "Sweep APY", "Sweep Δ/yr", "Options Δ/yr", "Total Savings/yr", "Exit Fee", "Breakeven (mo)"]
    print("\n" + tabulate(rows, headers=headers, tablefmt="rounded_outline"))

    if mutual_fund_flags:
        print(f"\nFlagged mutual funds (may have transfer restrictions): {', '.join(mutual_fund_flags)}")

    # Find best broker
    best_id = max(
        [bid for bid in comparison if bid != choice],
        key=lambda b: comparison[b]["total_annual_savings_usd"]
    )
    best = comparison[best_id]

    ask_ai = input("\nGenerate AI executive summary? [y/N]: ").strip().lower()
    if ask_ai == "y":
        print("\nGenerating summary...")
        aum = portfolio.total_market_value + portfolio.total_cash
        summary = generate_executive_summary(
            aum=aum,
            health_score=health["score"],
            health_band=health["band"],
            sweep_loss_annual=best["sweep"]["annual_loss_usd"],
            sweep_bps=best["sweep"]["basis_point_delta"],
            best_broker_name=best["broker_name"],
            annual_savings=best["total_annual_savings_usd"],
            acats_breakeven_months=best["breakeven_months"],
            current_broker_name=specs[choice]["name"],
        )
        print("\n--- Executive Summary ---")
        print(summary)
        print("-------------------------")

    print("\nPipeline test complete.\n")


if __name__ == "__main__":
    main()
