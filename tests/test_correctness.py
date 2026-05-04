from __future__ import annotations

import itertools
import random
from typing import Dict, List, Sequence, Set, Tuple

from src.io import parse_inline_dataset
from src.miner import MinerConfig, mine_hui_pr


def _bruteforce_hui(
    rows: Sequence[Dict[str, float]],
    profits: Dict[str, float],
    minutil: float,
) -> Set[Tuple[str, ...]]:
    items = sorted({i for tx in rows for i in tx})
    out: Set[Tuple[str, ...]] = set()
    for r in range(1, len(items) + 1):
        for comb in itertools.combinations(items, r):
            utility = 0.0
            for tx in rows:
                if all(i in tx for i in comb):
                    utility += sum(tx[i] * profits[i] for i in comb)
            if utility >= minutil:
                out.add(comb)
    return out


def test_paper_toy_example_contains_reported_huis() -> None:
    rows = [
        {"A": 3, "B": 3, "D": 1},
        {"A": 3, "B": 7, "C": 1, "E": 3},
        {"A": 4, "C": 3, "F": 1},
        {"C": 1, "D": 4, "E": 10},
        {"A": 4, "B": 4, "D": 2, "E": 6},
        {"A": 6, "B": 2, "D": 2, "E": 1},
    ]
    profits = {"A": 4, "B": 3, "C": 10, "D": 7, "E": 2, "F": 1}
    transactions = parse_inline_dataset(
        [[(k, v) for k, v in tx.items()] for tx in rows]
    )
    # Section 4 uses minutil = 48
    cfg = MinerConfig(minutil_ratio=48.0 / 282.0, mode="hui-pr")
    hui, _, _ = mine_hui_pr(transactions, profits, cfg)
    assert ("C", "D", "E") in hui
    assert ("C", "A") in hui or ("A", "C") in hui
    assert ("C", "B", "E", "A") in hui or ("A", "B", "C", "E") in hui


def test_matches_bruteforce_small_random_hui_pr() -> None:
    random.seed(7)
    items = ["A", "B", "C", "D"]
    profits = {i: random.randint(1, 10) for i in items}
    rows: List[Dict[str, float]] = []
    for _ in range(8):
        tx: Dict[str, float] = {}
        for item in items:
            if random.random() < 0.6:
                tx[item] = random.randint(1, 4)
        if tx:
            rows.append(tx)
    transactions = parse_inline_dataset(
        [[(k, v) for k, v in tx.items()] for tx in rows]
    )
    total_utility = sum(sum(q * profits[i] for i, q in tx.items()) for tx in rows)
    minutil = total_utility * 0.25
    expected = _bruteforce_hui(rows, profits, minutil)
    hui, _, _ = mine_hui_pr(transactions, profits, MinerConfig(minutil_ratio=0.25))
    assert hui == expected
