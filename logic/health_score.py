from typing import Dict, List


def compute_health_score(
    total_cash: float,
    current_broker_id: str,
    specs: Dict,
    comparison: Dict,
    mutual_fund_flags: List[str],
) -> Dict:
    score = 100
    penalties = {}

    # Find best sweep APY among all brokers
    best_sweep_apy = max(b["sweep_apy"] for b in specs.values())
    current_sweep_apy = specs[current_broker_id]["sweep_apy"]
    sweep_gap = best_sweep_apy - current_sweep_apy
    max_sweep_gap = best_sweep_apy  # gap when current APY = 0
    if max_sweep_gap > 0:
        sweep_penalty = round((sweep_gap / max_sweep_gap) * 30)
    else:
        sweep_penalty = 0
    score -= sweep_penalty
    penalties["cash_sweep"] = sweep_penalty

    # Options cost penalty
    best_options_fee = min(b["options_contract_fee"] for b in specs.values())
    current_options_fee = specs[current_broker_id]["options_contract_fee"]
    max_options_fee = max(b["options_contract_fee"] for b in specs.values())
    options_gap = current_options_fee - best_options_fee
    if max_options_fee - best_options_fee > 0:
        options_penalty = round((options_gap / (max_options_fee - best_options_fee)) * 20)
    else:
        options_penalty = 0
    score -= options_penalty
    penalties["options_cost"] = options_penalty

    # Maintenance fee penalty
    maintenance_fee = specs[current_broker_id]["annual_maintenance_fee"]
    maintenance_penalty = 15 if maintenance_fee > 0 else 0
    score -= maintenance_penalty
    penalties["maintenance_fee"] = maintenance_penalty

    # ACATS exit friction penalty (based on current broker's exit fee)
    acats_fee = specs[current_broker_id]["acats_exit_fee"]
    if acats_fee >= 75:
        acats_penalty = 10
    elif acats_fee >= 25:
        acats_penalty = 5
    else:
        acats_penalty = 0
    score -= acats_penalty
    penalties["acats_exit"] = acats_penalty

    # Mutual fund flags penalty
    fund_penalty = min(len(mutual_fund_flags) * 5, 25)
    score -= fund_penalty
    penalties["mutual_fund_flags"] = fund_penalty

    score = max(0, score)

    if score >= 85:
        band = "Optimized"
        band_color = "#10b981"
    elif score >= 70:
        band = "Adequate"
        band_color = "#f59e0b"
    elif score >= 50:
        band = "Needs Review"
        band_color = "#f97316"
    else:
        band = "High Leakage"
        band_color = "#ef4444"

    return {
        "score": score,
        "band": band,
        "band_color": band_color,
        "penalties": penalties,
    }
