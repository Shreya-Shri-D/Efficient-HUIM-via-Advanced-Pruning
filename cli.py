from __future__ import annotations

import argparse
import json

from src.io import parse_profit_table, parse_transactions
from src.metrics import RunMetrics, Timer, write_metrics_json
from src.miner import MinerConfig, mine_hui_pr


def main() -> None:
    parser = argparse.ArgumentParser(description="HUI-PR / HUI-PR* miner")
    parser.add_argument("--transactions", required=True, help="Path to transactions file")
    parser.add_argument("--profits", required=True, help="Path to item profits file")
    parser.add_argument("--minutil-ratio", required=True, type=float, help="Threshold ratio")
    parser.add_argument(
        "--mode",
        choices=["hui-pr", "hui-pr-star"],
        default="hui-pr",
        help="Algorithm mode",
    )
    parser.add_argument("--threads", type=int, default=1, help="Preprocess thread count")
    parser.add_argument("--no-merge", action="store_true", help="Disable transaction merging")
    parser.add_argument("--out", default="hui_results.json", help="Output json path")
    parser.add_argument("--metrics-out", default="", help="Optional metrics json path")
    args = parser.parse_args()

    transactions = parse_transactions(args.transactions)
    profits = parse_profit_table(args.profits)
    cfg = MinerConfig(
        minutil_ratio=args.minutil_ratio,
        mode=args.mode,
        use_transaction_merge=not args.no_merge,
        n_threads=args.threads,
    )

    with Timer() as timer:
        hui, stats, minutil = mine_hui_pr(transactions, profits, cfg)

    payload = {
        "mode": args.mode,
        "minutil_ratio": args.minutil_ratio,
        "minutil": minutil,
        "hui_count": len(hui),
        "hui": [list(x) for x in sorted(hui)],
        "stats": {
            "candidates": stats.candidates,
            "visited_transactions": stats.visited_transactions,
            "upper_bound_calculations": stats.upper_bound_calculations,
            "runtime_seconds": timer.elapsed,
        },
    }
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    if args.metrics_out:
        write_metrics_json(
            args.metrics_out,
            RunMetrics(
                runtime_seconds=timer.elapsed,
                candidates=stats.candidates,
                visited_transactions=stats.visited_transactions,
                upper_bound_calculations=stats.upper_bound_calculations,
                hui_count=len(hui),
            ),
        )


if __name__ == "__main__":
    main()
