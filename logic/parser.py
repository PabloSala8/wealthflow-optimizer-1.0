import csv
import io
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import pandas as pd
from utils.ai_advisor import map_headers_with_ai


@dataclass
class PortfolioData:
    holdings: List[Dict] = field(default_factory=list)
    total_market_value: float = 0.0
    total_cash: float = 0.0
    total_options_contracts: int = 0
    raw_headers: List[str] = field(default_factory=list)
    header_mapping: Dict = field(default_factory=dict)


def load_and_normalize(csv_path: str) -> PortfolioData:
    df = pd.read_csv(csv_path)
    raw_headers = list(df.columns)
    sample_row = dict(zip(raw_headers, df.iloc[0].tolist())) if len(df) > 0 else {}

    header_mapping = map_headers_with_ai(raw_headers, sample_row)

    # Build reverse mapping: raw -> canonical
    rename_map = {raw: canonical for raw, canonical in header_mapping.items() if canonical}
    df_normalized = df.rename(columns=rename_map)

    holdings = []
    total_cash = 0.0
    total_market_value = 0.0
    total_options_contracts = 0

    for _, row in df_normalized.iterrows():
        holding = {}
        for canonical_col in ["ticker", "market_value", "cash_sweep", "num_options_contracts",
                               "account_type", "quantity", "avg_cost", "asset_class", "sector", "notes"]:
            holding[canonical_col] = row.get(canonical_col, None)

        # Coerce numeric fields
        market_value = _to_float(holding.get("market_value"))
        num_contracts = _to_int(holding.get("num_options_contracts"))

        holding["market_value"] = market_value
        holding["num_options_contracts"] = num_contracts

        # Detect cash from dedicated column or from asset_class = cash
        asset_class = str(holding.get("asset_class") or "").strip().lower()
        if asset_class == "cash":
            cash_sweep = market_value
        else:
            cash_sweep = _to_float(holding.get("cash_sweep"))
        holding["cash_sweep"] = cash_sweep

        total_market_value += market_value
        total_cash += cash_sweep
        total_options_contracts += num_contracts

        holdings.append(holding)

    return PortfolioData(
        holdings=holdings,
        total_market_value=round(total_market_value, 2),
        total_cash=round(total_cash, 2),
        total_options_contracts=total_options_contracts,
        raw_headers=raw_headers,
        header_mapping=header_mapping,
    )


def _to_float(val) -> float:
    try:
        return float(val) if val is not None else 0.0
    except (ValueError, TypeError):
        return 0.0


def _to_int(val) -> int:
    try:
        return int(val) if val is not None else 0
    except (ValueError, TypeError):
        return 0
