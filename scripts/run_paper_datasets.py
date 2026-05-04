#!/usr/bin/env python3
"""
Run HUI-PR and HUI-PR* (Wu, Lin, Tamrakar, TKDD 2019, https://doi.org/10.1145/3363571)
on TKDD-style quantitative datasets. Threshold ratios match Table 7 in the paper
(Footmart → foodmart.txt).
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

# Allow running as `python scripts/run_paper_datasets.py` without installing the package.
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.io import parse_tkdd_quantitative_database, unit_profits_for_transactions
from src.metrics import Timer
from src.miner import MinerConfig, mine_hui_pr

# Table 7 — threshold ratio δ per dataset (Footmart file is foodmart here).
PAPER_THRESHOLDS: dict[str, list[float]] = {
    "chess": [0.25, 0.255, 0.26, 0.265, 0.27],
    "mushroom": [0.14, 0.1425, 0.145, 0.1475, 0.15],
    "connect": [0.289, 0.291, 0.293, 0.295, 0.297],
    "accidents": [0.131, 0.134, 0.137, 0.14, 0.143],
    "retail": [0.003, 0.004, 0.005, 0.006, 0.007],
    "foodmart": [0.0011, 0.0012, 0.0013, 0.0014, 0.0015],
}


def expand_threshold_midpoints(values: list[float]) -> list[float]:
    """Insert midpoints between consecutive paper thresholds for smoother curves."""
    v = sorted(values)
    out: list[float] = []
    for i in range(len(v) - 1):
        a, b = v[i], v[i + 1]
        out.append(a)
        mid = (a + b) / 2.0
        out.append(round(mid, 6))
    out.append(v[-1])
    return sorted({round(x, 6) for x in out})


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--datasets-dir",
        type=Path,
        default=_ROOT / "datasets",
        help="Directory containing *.txt quantitative databases",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=_ROOT / "results" / "paper_table7_runs.csv",
        help="Output CSV path",
    )
    parser.add_argument("--threads", type=int, default=1)
    parser.add_argument(
        "--no-tu-check",
        action="store_true",
        help="Skip TU == sum(quantities) validation",
    )
    parser.add_argument(
        "--datasets",
        default="",
        help="Comma-separated basenames (e.g. chess,retail); default = all known in PAPER_THRESHOLDS",
    )
    parser.add_argument(
        "--paper-thresholds-only",
        action="store_true",
        help="Use only the five Table-7 δ values per dataset (default adds midpoints for smoother curves).",
    )
    parser.add_argument(
        "--threshold-ratios",
        default="",
        metavar="LIST",
        help="Comma-separated δ values; overrides Table-7 grid for each selected dataset (e.g. 0.13,0.17).",
    )
    args = parser.parse_args()

    if args.datasets.strip():
        names = [x.strip() for x in args.datasets.split(",") if x.strip()]
    else:
        names = sorted(PAPER_THRESHOLDS.keys())

    args.out.parent.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, object]] = []

    for name in names:
        if name not in PAPER_THRESHOLDS:
            print(f"skip {name}: no Table-7 thresholds (add to PAPER_THRESHOLDS)", file=sys.stderr)
            continue
        path = args.datasets_dir / f"{name}.txt"
        if not path.is_file():
            print(f"skip {name}: missing {path}", file=sys.stderr)
            continue

        print(f"loading {path} ...", flush=True)
        tx = parse_tkdd_quantitative_database(
            str(path),
            validate_tu=not args.no_tu_check,
        )
        profits = unit_profits_for_transactions(tx)
        if args.threshold_ratios.strip():
            thresholds = sorted(
                {
                    float(x.strip())
                    for x in args.threshold_ratios.split(",")
                    if x.strip()
                }
            )
            if not thresholds:
                print(f"skip {name}: empty --threshold-ratios", file=sys.stderr)
                continue
        else:
            thresholds = PAPER_THRESHOLDS[name]
            if not args.paper_thresholds_only:
                thresholds = expand_threshold_midpoints(thresholds)

        for ratio in thresholds:
            for mode in ("hui-pr", "hui-pr-star"):
                cfg = MinerConfig(
                    minutil_ratio=ratio,
                    mode=mode,
                    n_threads=args.threads,
                )
                with Timer() as t:
                    hui, stats, minutil = mine_hui_pr(tx, profits, cfg)
                rows.append(
                    {
                        "dataset": name,
                        "mode": mode,
                        "threshold_ratio": ratio,
                        "minutil": minutil,
                        "transactions": len(tx),
                        "runtime_seconds": t.elapsed,
                        "hui_count": len(hui),
                        "candidates": stats.candidates,
                        "visited_transactions": stats.visited_transactions,
                        "upper_bound_calculations": stats.upper_bound_calculations,
                    }
                )
                print(
                    f"  {name} {mode} δ={ratio} | "
                    f"HUI={len(hui)} cand={stats.candidates} "
                    f"time={t.elapsed:.3f}s",
                    flush=True,
                )

    if not rows:
        print("No runs; nothing to write.", file=sys.stderr)
        sys.exit(1)

    with args.out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to {args.out}")


if __name__ == "__main__":
    main()
