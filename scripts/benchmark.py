from __future__ import annotations

import argparse
import csv
from pathlib import Path

from src.io import parse_profit_table, parse_transactions
from src.metrics import Timer
from src.miner import MinerConfig, mine_hui_pr


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark HUI-PR modes across thresholds")
    parser.add_argument("--transactions", required=True)
    parser.add_argument("--profits", required=True)
    parser.add_argument("--thresholds", required=True, help="Comma-separated ratios")
    parser.add_argument("--out", default="benchmark.csv")
    parser.add_argument("--threads", type=int, default=1)
    args = parser.parse_args()

    tx = parse_transactions(args.transactions)
    profits = parse_profit_table(args.profits)
    thresholds = [float(x.strip()) for x in args.thresholds.split(",") if x.strip()]
    out_path = Path(args.out)

    rows = []
    for ratio in thresholds:
        for mode in ("hui-pr", "hui-pr-star"):
            cfg = MinerConfig(minutil_ratio=ratio, mode=mode, n_threads=args.threads)
            with Timer() as t:
                hui, stats, minutil = mine_hui_pr(tx, profits, cfg)
            rows.append(
                {
                    "mode": mode,
                    "threshold_ratio": ratio,
                    "minutil": minutil,
                    "runtime_seconds": t.elapsed,
                    "hui_count": len(hui),
                    "candidates": stats.candidates,
                    "visited_transactions": stats.visited_transactions,
                    "upper_bound_calculations": stats.upper_bound_calculations,
                }
            )

    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
