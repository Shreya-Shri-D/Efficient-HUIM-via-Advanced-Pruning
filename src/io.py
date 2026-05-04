from __future__ import annotations

from typing import Dict, List, Sequence, Set, Tuple

from .model import RawTransaction


def parse_profit_table(path: str) -> Dict[str, float]:
    """
    Expected format per line:
      item profit
    or
      item,profit
    """
    profits: Dict[str, float] = {}
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "," in line:
                item, profit = [p.strip() for p in line.split(",", 1)]
            else:
                item, profit = line.split()
            profits[item] = float(profit)
    return profits


def parse_transactions(path: str) -> List[RawTransaction]:
    """
    Expected format per line:
      item:qty item:qty ...
    or comma-separated tokens:
      item:qty,item:qty,...
    """
    transactions: List[RawTransaction] = []
    with open(path, "r", encoding="utf-8") as f:
        for tid, line in enumerate(f, start=1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            tokens = line.replace(",", " ").split()
            qmap: Dict[str, float] = {}
            for token in tokens:
                item, qty = token.split(":")
                qmap[item] = float(qty)
            transactions.append(RawTransaction(tid=tid, quantities=qmap))
    return transactions


def parse_inline_dataset(
    rows: List[List[Tuple[str, float]]],
) -> List[RawTransaction]:
    transactions: List[RawTransaction] = []
    for tid, row in enumerate(rows, start=1):
        quantities = {item: qty for item, qty in row}
        transactions.append(RawTransaction(tid=tid, quantities=quantities))
    return transactions


def parse_tkdd_quantitative_database(
    path: str,
    *,
    validate_tu: bool = True,
    tu_tolerance: float = 1e-3,
) -> List[RawTransaction]:
    """
    TKDD / SPMF-style quantitative database used in Wu et al. (2019):
    each line is ``i1 i2 ... ik : TU : q1 q2 ... qk`` (space-separated).
    Items are string tokens; quantities are internal utilities. With unit
    profit 1, TU equals the sum of quantities (as in the public benchmarks).
    """
    transactions: List[RawTransaction] = []
    with open(path, "r", encoding="utf-8") as f:
        for tid, line in enumerate(f, start=1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split(":")
            if len(parts) != 3:
                raise ValueError(
                    f"{path}:{tid}: expected 'items : TU : quantities', got {len(parts)} fields"
                )
            items = parts[0].split()
            tu = float(parts[1])
            quantities = [float(x) for x in parts[2].split()]
            if len(items) != len(quantities):
                raise ValueError(
                    f"{path}:{tid}: {len(items)} items but {len(quantities)} quantities"
                )
            if validate_tu and items:
                s = sum(quantities)
                if abs(s - tu) > tu_tolerance:
                    raise ValueError(
                        f"{path}:{tid}: TU {tu} != sum(quantities) {s} (diff {abs(s - tu)})"
                    )
            qmap = {item: qty for item, qty in zip(items, quantities)}
            transactions.append(RawTransaction(tid=tid, quantities=qmap))
    return transactions


def unit_profits_for_transactions(
    transactions: Sequence[RawTransaction],
) -> Dict[str, float]:
    """External utility 1 for every item (standard for these benchmarks)."""
    items: Set[str] = set()
    for t in transactions:
        items.update(t.quantities.keys())
    return {i: 1.0 for i in items}
