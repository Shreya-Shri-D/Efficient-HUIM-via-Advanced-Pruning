#!/usr/bin/env python3
"""Emit results/dashboard.html from results/paper_table7_merged.csv (or --csv path)."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def load_rows(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--csv",
        type=Path,
        default=_ROOT / "results" / "paper_table7_merged.csv",
    )
    ap.add_argument(
        "--out",
        type=Path,
        default=_ROOT / "results" / "dashboard.html",
    )
    args = ap.parse_args()

    rows = load_rows(args.csv)
    for r in rows:
        r["threshold_ratio"] = float(r["threshold_ratio"])
        r["minutil"] = float(r["minutil"])
        r["runtime_seconds"] = float(r["runtime_seconds"])
        r["hui_count"] = int(r["hui_count"])
        r["candidates"] = int(r["candidates"])
        r["visited_transactions"] = int(r["visited_transactions"])
        r["upper_bound_calculations"] = int(r["upper_bound_calculations"])
        r["transactions"] = int(r["transactions"])

    payload = json.dumps(rows, separators=(",", ":"))
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>HUI-PR · TKDD 2019 benchmark dashboard</title>
  <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet" />
  <style>
    :root {{
      --bg0: #0a0e17;
      --bg1: #111827;
      --card: #161f2f;
      --border: #243044;
      --text: #e8edf5;
      --muted: #8b9cb3;
      --accent: #22d3ee;
      --accent2: #fbbf24;
      --pr: #38bdf8;
      --star: #f472b6;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--bg0);
      color: var(--text);
      font-family: "IBM Plex Sans", system-ui, sans-serif;
      min-height: 100vh;
      background-image:
        radial-gradient(ellipse 120% 80% at 50% -30%, rgba(34, 211, 238, 0.12), transparent),
        radial-gradient(ellipse 80% 50% at 100% 100%, rgba(244, 114, 182, 0.08), transparent);
    }}
    .wrap {{ max-width: 1400px; margin: 0 auto; padding: 2rem 1.5rem 4rem; }}
    header {{
      margin-bottom: 2rem;
      padding-bottom: 1.5rem;
      border-bottom: 1px solid var(--border);
    }}
    h1 {{
      font-weight: 600;
      font-size: 1.75rem;
      letter-spacing: -0.02em;
      margin: 0 0 0.5rem;
      background: linear-gradient(135deg, var(--text) 0%, var(--accent) 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }}
    .sub {{
      color: var(--muted);
      font-size: 0.95rem;
      line-height: 1.5;
      max-width: 52rem;
    }}
    .sub code {{
      font-family: "IBM Plex Mono", monospace;
      font-size: 0.85em;
      color: var(--accent);
      background: var(--bg1);
      padding: 0.1em 0.35em;
      border-radius: 4px;
    }}
    .kpis {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
      gap: 1rem;
      margin-bottom: 2rem;
    }}
    .kpi {{
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 1.1rem 1.25rem;
    }}
    .kpi .v {{ font-size: 1.65rem; font-weight: 600; font-family: "IBM Plex Mono", monospace; color: var(--accent); }}
    .kpi .l {{ font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.08em; color: var(--muted); margin-top: 0.35rem; }}
    .grid {{ display: grid; gap: 1.25rem; }}
    @media (min-width: 900px) {{
      .grid-2 {{ grid-template-columns: 1fr 1fr; }}
    }}
    .panel {{
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 1rem 1rem 0.5rem;
      overflow: hidden;
    }}
    .panel h2 {{
      font-size: 0.8rem;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.1em;
      color: var(--muted);
      margin: 0 0 0.5rem 1rem;
    }}
    .plot {{ width: 100%; height: 380px; }}
    .plot.tall {{ height: 440px; }}
    .plot.plot-3d {{ height: 520px; min-height: 420px; }}
    .plot.plot-parcoords {{ height: 340px; min-height: 300px; }}
    .legend-note {{
      font-size: 0.8rem;
      color: var(--muted);
      margin: 0.5rem 1rem 1rem;
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <header>
      <h1>High-utility itemset mining — benchmark lens</h1>
      <p class="sub">
        Interactive view of HUI-PR vs HUI-PR* runs (Wu, Lin, Tamrakar, <em>ACM TKDD</em> 2019,
        <code>10.1145/3363571</code>).
      </p>
    </header>
    <div class="kpis" id="kpis"></div>
    <div class="grid">
      <div class="panel"><h2>Runtime vs minimum utility threshold (δ)</h2><div id="g1" class="plot tall"></div></div>
      <div class="panel"><h2>Search effort — candidates explored</h2><div id="g2" class="plot tall"></div></div>
    </div>
    <div class="grid grid-2" style="margin-top:1.25rem">
      <div class="panel"><h2>Runtime ratio (HUI-PR* / HUI-PR)</h2><div id="g3" class="plot"></div><p class="legend-note">&gt;1 means the stricter bound costs more time on that slice (matches paper’s observation for HUI-PR*).</p></div>
      <div class="panel"><h2>Bubble map — candidates × time (size = #HUIs)</h2><div id="g4" class="plot"></div></div>
    </div>
    <div class="panel" style="margin-top:1.25rem"><h2>Upper-bound calculations (work proxy)</h2><div id="g5" class="plot"></div></div>
    <h2 style="margin:2.25rem 0 0.75rem;font-size:0.85rem;font-weight:600;letter-spacing:0.14em;text-transform:uppercase;color:var(--muted);border-bottom:1px solid var(--border);padding-bottom:0.5rem;">More views</h2>
    <div class="grid grid-2" style="margin-top:0.75rem">
      <div class="panel"><h2>Δ Runtime heatmap — HUI-PR* vs HUI-PR (%)</h2><div id="g6" class="plot tall"></div><p class="legend-note">Green: * faster · Red: * slower · White: tie. Empty = no paired run at that δ.</p></div>
      <div class="panel"><h2>3D search landscape</h2><div id="g7" class="plot plot-3d"></div><p class="legend-note">Rotate (drag), zoom (scroll). Axes: candidates, visited tx, runtime. Hue = dataset.</p></div>
    </div>
    <div class="panel" style="margin-top:1.25rem"><h2>Parallel coordinates — brush ranges to filter runs</h2><div id="g8" class="plot plot-parcoords"></div><p class="legend-note">Drag vertical axis edges to constrain; color encodes δ (warmer = looser threshold).</p></div>
    <div class="panel" style="margin-top:1.25rem"><h2>Sunburst — HUI counts by dataset &amp; mode</h2><div id="g9" class="plot" style="height:480px"></div></div>
  </div>
  <script>
    const RAW = {payload};
    const layoutBase = {{
      paper_bgcolor: 'rgba(0,0,0,0)',
      plot_bgcolor: 'rgba(0,0,0,0)',
      font: {{ family: 'IBM Plex Sans, sans-serif', color: '#e8edf5', size: 12 }},
      xaxis: {{ gridcolor: '#243044', zeroline: false, linecolor: '#243044', tickcolor: '#8b9cb3' }},
      yaxis: {{ gridcolor: '#243044', zeroline: false, linecolor: '#243044', tickcolor: '#8b9cb3' }},
      legend: {{ bgcolor: 'rgba(22,31,47,0.9)', borderwidth: 0, font: {{ size: 11 }} }},
      margin: {{ t: 28, r: 20, b: 48, l: 56 }},
      hovermode: 'closest',
    }};
    const paletteDs = ['#22d3ee', '#a78bfa', '#fbbf24', '#34d399', '#fb7185', '#94a3b8'];

    const datasets = [...new Set(RAW.map(r => r.dataset))].sort();
    const kpis = document.getElementById('kpis');
    kpis.innerHTML = [
      {{ v: datasets.length, l: 'Datasets' }},
      {{ v: RAW.length, l: 'Total runs' }},
      {{ v: (RAW.reduce((s,r) => s + r.hui_count, 0)).toLocaleString(), l: 'HUIs (sum over runs)' }},
    ].map(k => `<div class="kpi"><div class="v">${{k.v}}</div><div class="l">${{k.l}}</div></div>`).join('');

    function tracesByDataset(mode, ykey) {{
      const label = mode === 'hui-pr' ? 'HUI-PR' : 'HUI-PR*';
      return datasets.map((ds, i) => {{
        const sub = RAW.filter(r => r.dataset === ds && r.mode === mode).sort((a,b) => a.threshold_ratio - b.threshold_ratio);
        const c = paletteDs[i % paletteDs.length];
        return {{
          x: sub.map(r => r.threshold_ratio),
          y: sub.map(r => r[ykey]),
          name: ds + ' · ' + label,
          type: 'scatter',
          mode: 'lines+markers',
          line: {{
            color: c,
            width: mode === 'hui-pr' ? 2.4 : 2,
            shape: 'linear',
            dash: mode === 'hui-pr-star' ? 'dot' : 'solid',
          }},
          marker: {{
            size: mode === 'hui-pr' ? 7 : 6,
            color: c,
            symbol: mode === 'hui-pr-star' ? 'diamond' : 'circle',
            line: {{ width: 0 }},
          }},
          legendgroup: ds + '|' + mode,
          showlegend: true,
          hovertemplate: '<b>' + ds + '</b> (' + label + ')<br>δ=%{{x}}<br>%{{y}}<extra></extra>',
        }};
      }});
    }}

    const t1pr = tracesByDataset('hui-pr', 'runtime_seconds');
    const t1st = tracesByDataset('hui-pr-star', 'runtime_seconds');
    Plotly.newPlot('g1', [...t1pr, ...t1st], {{
      ...layoutBase,
      xaxis: {{ ...layoutBase.xaxis, title: 'Threshold ratio δ' }},
      yaxis: {{ ...layoutBase.yaxis, title: 'Runtime (s)', type: 'linear' }},
      title: '',
    }}, {{ responsive: true, displaylogo: false }});

    const t2pr = tracesByDataset('hui-pr', 'candidates');
    const t2st = tracesByDataset('hui-pr-star', 'candidates');
    Plotly.newPlot('g2', [...t2pr, ...t2st], {{
      ...layoutBase,
      xaxis: {{ ...layoutBase.xaxis, title: 'Threshold ratio δ' }},
      yaxis: {{ ...layoutBase.yaxis, title: 'Candidates', type: 'linear' }},
    }}, {{ responsive: true, displaylogo: false }});

    const ratioRows = [];
    for (const ds of datasets) {{
      const pr = RAW.filter(r => r.dataset === ds && r.mode === 'hui-pr');
      for (const a of pr) {{
        const b = RAW.find(r => r.dataset === ds && r.mode === 'hui-pr-star' && r.threshold_ratio === a.threshold_ratio);
        if (b && a.runtime_seconds > 0) ratioRows.push({{ dataset: ds, x: a.threshold_ratio, ratio: b.runtime_seconds / a.runtime_seconds }});
      }}
    }}
    const t3 = datasets.map(ds => {{
      const sub = ratioRows.filter(r => r.dataset === ds);
      return {{
        x: sub.map(r => r.x),
        y: sub.map(r => r.ratio),
        name: ds,
        type: 'scatter',
        mode: 'lines+markers',
        line: {{ width: 2 }},
        marker: {{ size: 8 }},
      }};
    }});
    Plotly.newPlot('g3', t3, {{
      ...layoutBase,
      shapes: [{{
        type: 'line', x0: Math.min(...ratioRows.map(r=>r.x)), x1: Math.max(...ratioRows.map(r=>r.x)), y0: 1, y1: 1,
        line: {{ color: '#8b9cb3', width: 1, dash: 'dash' }}
      }}],
      xaxis: {{ ...layoutBase.xaxis, title: 'δ' }},
      yaxis: {{ ...layoutBase.yaxis, title: 'Time ratio', rangemode: 'tozero' }},
    }}, {{ responsive: true, displaylogo: false }});

    const t4 = RAW.map((r, i) => ({{
      x: [r.candidates],
      y: [r.runtime_seconds],
      text: [`${{r.dataset}} ${{r.mode}} δ=${{r.threshold_ratio}}<br>HUIs: ${{r.hui_count}}`],
      name: r.dataset + ' ' + r.mode,
      type: 'scatter',
      mode: 'markers',
      marker: {{
        size: Math.max(6, Math.min(40, 8 + Math.sqrt(r.hui_count) * 1.2)),
        color: paletteDs[datasets.indexOf(r.dataset) % paletteDs.length],
        opacity: r.mode === 'hui-pr-star' ? 0.85 : 0.55,
        line: {{ width: r.mode === 'hui-pr-star' ? 2 : 0, color: '#fff' }},
      }},
      showlegend: false,
      hovertemplate: '%{{text}}<br>candidates: %{{x}}<br>runtime: %{{y:.3f}}s<extra></extra>',
    }}));
    Plotly.newPlot('g4', t4, {{
      ...layoutBase,
      xaxis: {{ ...layoutBase.xaxis, title: 'Candidates', type: 'log' }},
      yaxis: {{ ...layoutBase.yaxis, title: 'Runtime (s)', type: 'log' }},
    }}, {{ responsive: true, displaylogo: false }});

    const t5pr = tracesByDataset('hui-pr', 'upper_bound_calculations');
    const t5st = tracesByDataset('hui-pr-star', 'upper_bound_calculations');
    Plotly.newPlot('g5', [...t5pr, ...t5st], {{
      ...layoutBase,
      xaxis: {{ ...layoutBase.xaxis, title: 'Threshold ratio δ' }},
      yaxis: {{ ...layoutBase.yaxis, title: 'Upper-bound calculations', type: 'linear' }},
    }}, {{ responsive: true, displaylogo: false }});

    const allDelta = [...new Set(RAW.map(r => r.threshold_ratio))].sort((a, b) => a - b);
    const zHeat = datasets.map(ds =>
      allDelta.map(d => {{
        const pr = RAW.find(r => r.dataset === ds && r.mode === 'hui-pr' && Math.abs(r.threshold_ratio - d) < 1e-12);
        const st = RAW.find(r => r.dataset === ds && r.mode === 'hui-pr-star' && Math.abs(r.threshold_ratio - d) < 1e-12);
        if (!pr || !st || pr.runtime_seconds <= 1e-9) return null;
        return 100 * (st.runtime_seconds / pr.runtime_seconds - 1);
      }})
    );
    Plotly.newPlot('g6', [{{
      type: 'heatmap',
      z: zHeat,
      x: allDelta.map(d => String(d)),
      y: datasets,
      hovertemplate: '%{{y}} · δ=%{{x}}<br>Δ runtime: %{{z:.2f}}%<extra></extra>',
      colorscale: [
        [0, 'rgb(52, 211, 153)'],
        [0.45, 'rgb(30, 58, 72)'],
        [0.5, 'rgb(22, 31, 47)'],
        [0.55, 'rgb(58, 42, 52)'],
        [1, 'rgb(251, 113, 133)'],
      ],
      zmid: 0,
      colorbar: {{ title: '% slower<br>for *', titleside: 'right', tickfont: {{ size: 10 }} }},
      xgap: 2,
      ygap: 2,
    }}], {{
      ...layoutBase,
      margin: {{ ...layoutBase.margin, l: 88 }},
      xaxis: {{ ...layoutBase.xaxis, title: 'Threshold δ', side: 'bottom' }},
      yaxis: {{ ...layoutBase.yaxis, title: '', autorange: 'reversed' }},
    }}, {{ responsive: true, displaylogo: false }});

    const t7 = datasets.map((ds, i) => {{
      const sub = RAW.filter(r => r.dataset === ds);
      const c = paletteDs[i % paletteDs.length];
      return {{
        type: 'scatter3d',
        mode: 'markers',
        name: ds,
        x: sub.map(r => Math.log10(r.candidates + 1)),
        y: sub.map(r => Math.log10(r.visited_transactions + 1)),
        z: sub.map(r => r.runtime_seconds),
        marker: {{
          size: sub.map(r => 5 + Math.min(9, Math.sqrt(r.hui_count + 1))),
          color: c,
          symbol: sub.map(r => (r.mode === 'hui-pr-star' ? 'diamond' : 'circle')),
          line: {{ width: 0.35, color: 'rgba(255,255,255,0.25)' }},
          opacity: 0.92,
        }},
        text: sub.map(r => r.mode + ' · δ=' + r.threshold_ratio + '<br>HUIs: ' + r.hui_count),
        hovertemplate: '<b>' + ds + '</b><br>%{{text}}<br>log₁₀(cand+1)=%{{x:.3f}}<br>log₁₀(vis+1)=%{{y:.3f}}<br>runtime=%{{z:.3f}}s<extra></extra>',
      }};
    }});
    Plotly.newPlot('g7', t7, {{
      paper_bgcolor: 'rgba(0,0,0,0)',
      plot_bgcolor: 'rgba(0,0,0,0)',
      font: {{ family: 'IBM Plex Sans, sans-serif', color: '#e8edf5', size: 11 }},
      scene: {{
        xaxis: {{ title: 'log₁₀(candidates+1)', gridcolor: '#243044', backgroundcolor: 'rgba(17,24,39,0.4)' }},
        yaxis: {{ title: 'log₁₀(visited tx+1)', gridcolor: '#243044', backgroundcolor: 'rgba(17,24,39,0.4)' }},
        zaxis: {{ title: 'Runtime (s)', gridcolor: '#243044', backgroundcolor: 'rgba(17,24,39,0.4)' }},
        camera: {{ eye: {{ x: 1.55, y: 1.45, z: 0.85 }} }},
      }},
      margin: {{ t: 24, r: 12, b: 12, l: 12 }},
      legend: {{ bgcolor: 'rgba(22,31,47,0.85)', orientation: 'h', y: 1.02, x: 0.5, xanchor: 'center' }},
      annotations: [{{
        text: '○ HUI-PR  ·  ◇ HUI-PR*',
        xref: 'paper',
        yref: 'paper',
        x: 0.5,
        y: 1.08,
        showarrow: false,
        font: {{ color: '#8b9cb3', size: 11 }},
        xanchor: 'center',
      }}],
    }}, {{ responsive: true, displaylogo: false }});

    const dMin = Math.min(...RAW.map(r => r.threshold_ratio));
    const dMax = Math.max(...RAW.map(r => r.threshold_ratio));
    const dSpan = dMax - dMin || 1;
    const lineColor = RAW.map(r => (r.threshold_ratio - dMin) / dSpan);
    Plotly.newPlot('g8', [{{
      type: 'parcoords',
      line: {{
        color: lineColor,
        colorscale: [[0, '#22d3ee'], [0.5, '#a78bfa'], [1, '#fb7185']],
        showscale: true,
        colorbar: {{ title: 'δ (norm)', titleside: 'right', tickfont: {{ size: 10 }} }},
      }},
      dimensions: [
        {{ label: 'δ', values: RAW.map(r => r.threshold_ratio) }},
        {{ label: 'Runtime (s)', values: RAW.map(r => r.runtime_seconds) }},
        {{ label: 'log₁₀ cand', values: RAW.map(r => Math.log10(r.candidates + 1)) }},
        {{ label: 'log₁₀ visited', values: RAW.map(r => Math.log10(r.visited_transactions + 1)) }},
        {{ label: 'log₁₀ UB calc', values: RAW.map(r => Math.log10(r.upper_bound_calculations + 1)) }},
        {{ label: 'HUIs', values: RAW.map(r => r.hui_count) }},
      ],
    }}], {{
      paper_bgcolor: 'rgba(0,0,0,0)',
      plot_bgcolor: 'rgba(0,0,0,0)',
      font: {{ family: 'IBM Plex Sans, sans-serif', color: '#e8edf5', size: 11 }},
      margin: {{ t: 36, r: 28, b: 24, l: 24 }},
    }}, {{ responsive: true, displaylogo: false }});

    const sbIds = ['root'];
    const sbLabels = ['Σ |HUI| (all δ grid points)'];
    const sbParents = [''];
    const sbValues = [0];
    let rootSum = 0;
    for (const ds of datasets) {{
      for (const mode of ['hui-pr', 'hui-pr-star']) {{
        const id = ds + '|' + mode;
        sbIds.push(id);
        sbLabels.push(ds + ' · ' + (mode === 'hui-pr' ? 'HUI-PR' : 'HUI-PR*'));
        sbParents.push('root');
        let v = 0;
        for (const r of RAW) if (r.dataset === ds && r.mode === mode) v += r.hui_count;
        sbValues.push(v);
        rootSum += v;
      }}
    }}
    sbValues[0] = rootSum;
    Plotly.newPlot('g9', [{{
      type: 'sunburst',
      ids: sbIds,
      labels: sbLabels,
      parents: sbParents,
      values: sbValues,
      marker: {{ line: {{ width: 1.5, color: '#0a0e17' }} }},
      insidetextorientation: 'radial',
      hovertemplate: '<b>%{{label}}</b><br>Σ HUIs (over grid): %{{value}}<br>%{{percentParent}} of parent<extra></extra>',
    }}], {{
      paper_bgcolor: 'rgba(0,0,0,0)',
      font: {{ family: 'IBM Plex Sans, sans-serif', color: '#e8edf5', size: 12 }},
      margin: {{ t: 12, r: 12, b: 12, l: 12 }},
      sunburstcolorway: paletteDs,
    }}, {{ responsive: true, displaylogo: false }});
  </script>
</body>
</html>
"""

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(html, encoding="utf-8")
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
