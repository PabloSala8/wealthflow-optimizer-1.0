import json
from dataclasses import dataclass
from typing import Dict, List, Optional


def load_broker_specs(path: str) -> Dict:
    with open(path, "r") as f:
        data = json.load(f)
    return {b["id"]: b for b in data["brokers"]}


def calculate_sweep_opportunity_loss(
    total_cash: float,
    current_broker_id: str,
    target_broker_id: str,
    specs: Dict,
) -> Dict:
    current = specs[current_broker_id]
    target = specs[target_broker_id]
    current_apy = current["sweep_apy"]
    target_apy = target["sweep_apy"]
    basis_point_delta = round((target_apy - current_apy) * 10000, 2)
    annual_loss_usd = round(total_cash * (target_apy - current_apy), 2)
    monthly_loss_usd = round(annual_loss_usd / 12, 2)
    return {
        "current_apy": current_apy,
        "target_apy": target_apy,
        "basis_point_delta": basis_point_delta,
        "annual_loss_usd": annual_loss_usd,
        "monthly_loss_usd": monthly_loss_usd,
    }


def calculate_options_cost_delta(
    total_contracts: int,
    current_id: str,
    target_id: str,
    specs: Dict,
) -> Dict:
    current_fee = specs[current_id]["options_contract_fee"]
    target_fee = specs[target_id]["options_contract_fee"]
    annual_savings_usd = round((current_fee - target_fee) * total_contracts, 2)
    return {
        "current_fee_per_contract": current_fee,
        "target_fee_per_contract": target_fee,
        "annual_savings_usd": annual_savings_usd,
    }


def calculate_mutual_fund_flags(holdings: List[Dict]) -> List[str]:
    flagged = []
    for h in holdings:
        asset_class = str(h.get("asset_class", "")).lower()
        ticker = str(h.get("ticker", ""))
        if asset_class == "mutual_fund":
            flagged.append(ticker)
    return flagged


def calculate_breakeven_months(exit_fee: float, monthly_savings: float) -> float:
    if monthly_savings <= 0:
        return float("inf")
    return round(exit_fee / monthly_savings, 1)


def generate_full_comparison(portfolio: Dict, current_broker_id: str, specs: Dict) -> Dict:
    total_cash = portfolio.get("total_cash", 0.0)
    total_contracts = portfolio.get("total_options_contracts", 0)
    holdings = portfolio.get("holdings", [])
    mutual_fund_flags = calculate_mutual_fund_flags(holdings)
    current_broker = specs[current_broker_id]
    results = {}
    for target_id, target_broker in specs.items():
        sweep = calculate_sweep_opportunity_loss(total_cash, current_broker_id, target_id, specs)
        options = calculate_options_cost_delta(total_contracts, current_broker_id, target_id, specs)
        maintenance_delta = current_broker["annual_maintenance_fee"] - target_broker["annual_maintenance_fee"]
        total_annual_savings = round(
            sweep["annual_loss_usd"] + options["annual_savings_usd"] + maintenance_delta, 2
        )
        monthly_savings = round(total_annual_savings / 12, 2)
        exit_fee = target_broker["acats_exit_fee"]
        breakeven = calculate_breakeven_months(exit_fee, monthly_savings)
        results[target_id] = {
            "broker_name": target_broker["name"],
            "sweep": sweep,
            "options": options,
            "maintenance_delta_usd": maintenance_delta,
            "total_annual_savings_usd": total_annual_savings,
            "monthly_savings_usd": monthly_savings,
            "acats_exit_fee": exit_fee,
            "breakeven_months": breakeven,
            "mutual_fund_flags": mutual_fund_flags,
        }
    return results
