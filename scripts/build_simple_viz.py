#!/usr/bin/env python3
"""Emit results/simple_viz.html — minimal benchmark charts from merged CSV."""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]


def load_rows(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--csv", type=Path, default=_ROOT / "results" / "paper_table7_merged.csv")
    ap.add_argument("--out", type=Path, default=_ROOT / "results" / "simple_viz.html")
    args = ap.parse_args()

    rows = load_rows(args.csv)
    for r in rows:
        r["threshold_ratio"] = float(r["threshold_ratio"])
        r["runtime_seconds"] = float(r["runtime_seconds"])
        r["hui_count"] = int(r["hui_count"])

    datasets = sorted({r["dataset"] for r in rows})
    by_ds_mode: dict[tuple[str, str], list[float]] = defaultdict(list)
    for r in rows:
        by_ds_mode[(r["dataset"], r["mode"])].append(r["runtime_seconds"])

    pr_means: list[float] = []
    star_means: list[float] = []
    time_ratios: list[float | None] = []

    for ds in datasets:
        pr_times = by_ds_mode.get((ds, "hui-pr"), [])
        st_times = by_ds_mode.get((ds, "hui-pr-star"), [])
        pr_means.append(sum(pr_times) / len(pr_times) if pr_times else 0.0)
        star_means.append(sum(st_times) / len(st_times) if st_times else 0.0)

        # paired ratio: match same δ
        pr_by_d = {r["threshold_ratio"]: r["runtime_seconds"] for r in rows if r["dataset"] == ds and r["mode"] == "hui-pr"}
        ratios = []
        for r in rows:
            if r["dataset"] != ds or r["mode"] != "hui-pr-star":
                continue
            d = r["threshold_ratio"]
            if d in pr_by_d and pr_by_d[d] > 1e-9:
                ratios.append(r["runtime_seconds"] / pr_by_d[d])
        time_ratios.append(sum(ratios) / len(ratios) if ratios else None)

    line_payload: dict[str, dict[str, list]] = {}
    for ds in datasets:
        pr_pts = sorted(
            (r["threshold_ratio"], r["runtime_seconds"])
            for r in rows
            if r["dataset"] == ds and r["mode"] == "hui-pr"
        )
        st_pts = sorted(
            (r["threshold_ratio"], r["runtime_seconds"])
            for r in rows
            if r["dataset"] == ds and r["mode"] == "hui-pr-star"
        )
        line_payload[ds] = {
            "d_pr": [p[0] for p in pr_pts],
            "t_pr": [p[1] for p in pr_pts],
            "d_st": [p[0] for p in st_pts],
            "t_st": [p[1] for p in st_pts],
        }

    total_hui = sum(r["hui_count"] for r in rows)
    total_wall = sum(r["runtime_seconds"] for r in rows)

    lines_main = {ds: v for ds, v in line_payload.items() if ds != "accidents"}
    lines_acc = {ds: v for ds, v in line_payload.items() if ds == "accidents"}

    chart_data = {
        "datasets": datasets,
        "pr_means": pr_means,
        "star_means": star_means,
        "time_ratios": time_ratios,
        "lines_main": lines_main,
        "lines_accidents": lines_acc,
        "kpis": {
            "datasets": len(datasets),
            "runs": len(rows),
            "total_hui": total_hui,
            "total_wall_s": total_wall,
        },
    }
    payload = json.dumps(chart_data, separators=(",", ":"))

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>HUI-PR benchmark · summary</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link href="https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,400;0,9..40,600;0,9..40,700;1,9..40,400&display=swap" rel="stylesheet" />
  <style>
    :root {{
      --bg: #0c1222;
      --card: #141c2f;
      --line: #2a3650;
      --text: #eef2f8;
      --muted: #8b9bb8;
      --pr: #38bdf8;
      --star: #e879f9;
      --accent: #fbbf24;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: "DM Sans", system-ui, sans-serif;
      background: var(--bg);
      color: var(--text);
      min-height: 100vh;
      background-image: radial-gradient(ellipse 100% 60% at 50% -20%, rgba(56, 189, 248, 0.14), transparent);
    }}
    .wrap {{ max-width: 1040px; margin: 0 auto; padding: 2.5rem 1.25rem 3rem; }}
    header {{ margin-bottom: 2rem; }}
    h1 {{
      font-size: 1.85rem;
      font-weight: 700;
      letter-spacing: -0.03em;
      margin: 0 0 0.35rem;
    }}
    .lead {{ color: var(--muted); font-size: 1rem; line-height: 1.55; max-width: 36rem; margin: 0; }}
    .kpis {{
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 0.85rem;
      margin: 2rem 0;
    }}
    @media (min-width: 640px) {{ .kpis {{ grid-template-columns: repeat(4, 1fr); }} }}
    .kpi {{
      background: var(--card);
      border: 1px solid var(--line);
      border-radius: 14px;
      padding: 1.15rem 1.2rem;
    }}
    .kpi .n {{ font-size: 1.5rem; font-weight: 700; color: var(--pr); letter-spacing: -0.02em; }}
    .kpi .lbl {{ font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.12em; color: var(--muted); margin-top: 0.4rem; }}
    section {{
      background: var(--card);
      border: 1px solid var(--line);
      border-radius: 16px;
      padding: 1.25rem 1.25rem 1.5rem;
      margin-bottom: 1.25rem;
    }}
    section h2 {{
      font-size: 0.72rem;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.14em;
      color: var(--muted);
      margin: 0 0 1rem;
    }}
    .chart-wrap {{ position: relative; height: 280px; }}
    .chart-wrap.tall {{ height: 300px; }}
    .split {{ display: grid; gap: 1rem; }}
    @media (min-width: 720px) {{ .split {{ grid-template-columns: 1.4fr 1fr; }} }}
    .note {{ font-size: 0.8rem; color: var(--muted); margin-top: 0.75rem; line-height: 1.45; }}
    footer {{ margin-top: 2rem; font-size: 0.75rem; color: var(--muted); }}
  </style>
</head>
<body>
  <div class="wrap">
    <header>
      <h1>High-utility mining benchmark</h1>
      <p class="lead">HUI-PR vs HUI-PR* on TKDD-style runs. Averages are taken over every threshold δ in your results file for each dataset.</p>
    </header>
    <div class="kpis" id="kpis"></div>
    <section>
      <h2>Average runtime by dataset</h2>
      <div class="chart-wrap tall"><canvas id="c1"></canvas></div>
      <p class="note">Lower is faster. Comparing the two pruning strategies at the same δ grid.</p>
    </section>
    <section>
      <h2>Mean runtime ratio (HUI-PR* ÷ HUI-PR)</h2>
      <div class="chart-wrap"><canvas id="c2"></canvas></div>
      <p class="note">Above 1: HUI-PR* slower on matched δ. Green: faster or equal.</p>
    </section>
    <section>
      <h2>Runtime vs δ</h2>
      <div class="split">
        <div class="chart-wrap tall"><canvas id="c3"></canvas></div>
        <div class="chart-wrap tall"><canvas id="c4"></canvas></div>
      </div>
      <p class="note">Left: Table-7-style grids · Right: accidents (your custom δ). Solid = HUI-PR, dashed = HUI-PR*.</p>
    </section>
    <footer>Source: paper_table7_merged.csv · Chart.js</footer>
  </div>
  <script>
    const DATA = {payload};
    const prColor = 'rgba(56, 189, 248, 0.9)';
    const starColor = 'rgba(232, 121, 249, 0.9)';
    const grid = 'rgba(139, 155, 184, 0.25)';
    const text = '#eef2f8';
    const muted = '#8b9bb8';

    const kpis = document.getElementById('kpis');
    const k = DATA.kpis;
    const fmt = (n) => n >= 1e6 ? (n/1e6).toFixed(2) + 'M' : n >= 1e3 ? (n/1e3).toFixed(1) + 'k' : n.toLocaleString();
    kpis.innerHTML = [
      {{ n: k.datasets, l: 'Datasets' }},
      {{ n: k.runs, l: 'Total runs' }},
      {{ n: fmt(k.total_hui), l: 'HUIs (sum)' }},
      {{ n: k.total_wall_s.toFixed(0) + ' s', l: 'Wall time (sum)' }},
    ].map(x => `<div class="kpi"><div class="n">${{x.n}}</div><div class="lbl">${{x.l}}</div></div>`).join('');

    new Chart(document.getElementById('c1'), {{
      type: 'bar',
      data: {{
        labels: DATA.datasets,
        datasets: [
          {{ label: 'HUI-PR', data: DATA.pr_means, backgroundColor: prColor, borderRadius: 6, borderSkipped: false }},
          {{ label: 'HUI-PR*', data: DATA.star_means, backgroundColor: starColor, borderRadius: 6, borderSkipped: false }},
        ],
      }},
      options: {{
        responsive: true,
        maintainAspectRatio: false,
        plugins: {{
          legend: {{ labels: {{ color: text }}, position: 'top' }},
        }},
        scales: {{
          x: {{
            grid: {{ color: grid }},
            ticks: {{ color: muted, maxRotation: 45 }},
          }},
          y: {{
            beginAtZero: true,
            title: {{ display: true, text: 'Seconds (mean)', color: muted }},
            grid: {{ color: grid }},
            ticks: {{ color: muted }},
          }},
        }},
      }},
    }});

    const ratioLabels = [];
    const ratioVals = [];
    DATA.datasets.forEach((ds, i) => {{
      const v = DATA.time_ratios[i];
      if (v != null) {{ ratioLabels.push(ds); ratioVals.push(v); }}
    }});
    new Chart(document.getElementById('c2'), {{
      type: 'bar',
      data: {{
        labels: ratioLabels,
        datasets: [{{
          label: 'HUI-PR* / HUI-PR',
          data: ratioVals,
          backgroundColor: ratioVals.map(v => v > 1 ? 'rgba(251, 191, 36, 0.75)' : 'rgba(52, 211, 153, 0.65)'),
          borderRadius: 6,
          borderSkipped: false,
        }}],
      }},
      options: {{
        indexAxis: 'y',
        responsive: true,
        maintainAspectRatio: false,
        plugins: {{ legend: {{ display: false }} }},
        scales: {{
          x: {{
            grid: {{ color: grid }},
            ticks: {{ color: muted }},
            title: {{ display: true, text: 'Ratio', color: muted }},
          }},
          y: {{
            grid: {{ color: grid }},
            ticks: {{ color: muted }},
          }},
        }},
      }},
    }});

    function lineDatasets(linesObj) {{
      const out = [];
      const palette = ['#38bdf8', '#fbbf24', '#34d399', '#fb7185', '#a78bfa', '#e879f9'];
      let pi = 0;
      for (const ds of Object.keys(linesObj).sort()) {{
        const L = linesObj[ds];
        const c = palette[pi++ % palette.length];
        out.push({{
          label: ds + ' · PR',
          data: L.d_pr.map((d, i) => ({{ x: d, y: L.t_pr[i] }})),
          borderColor: c,
          backgroundColor: c,
          tension: 0.25,
          pointRadius: 3,
          borderWidth: 2.5,
        }});
        out.push({{
          label: ds + ' · PR*',
          data: L.d_st.map((d, i) => ({{ x: d, y: L.t_st[i] }})),
          borderColor: c,
          borderDash: [7, 5],
          tension: 0.25,
          pointRadius: 2,
          borderWidth: 2,
        }});
      }}
      return out;
    }}

    const lineOpts = {{
      responsive: true,
      maintainAspectRatio: false,
      interaction: {{ mode: 'nearest', intersect: false }},
      plugins: {{
        legend: {{
          labels: {{ color: text, boxWidth: 10, font: {{ size: 10 }} }},
          position: 'bottom',
        }},
      }},
      scales: {{
        x: {{
          type: 'linear',
          title: {{ display: true, text: 'δ', color: muted }},
          grid: {{ color: grid }},
          ticks: {{ color: muted }},
        }},
        y: {{
          beginAtZero: true,
          title: {{ display: true, text: 'Seconds', color: muted }},
          grid: {{ color: grid }},
          ticks: {{ color: muted }},
        }},
      }},
    }};

    new Chart(document.getElementById('c3'), {{
      type: 'line',
      data: {{ datasets: lineDatasets(DATA.lines_main) }},
      options: lineOpts,
    }});
    new Chart(document.getElementById('c4'), {{
      type: 'line',
      data: {{ datasets: lineDatasets(DATA.lines_accidents) }},
      options: lineOpts,
    }});
  </script>
</body>
</html>
"""

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(html, encoding="utf-8")
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
