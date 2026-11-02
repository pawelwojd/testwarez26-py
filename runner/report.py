"""Render a RunSummary as a single self-contained HTML report (no external assets)."""

from __future__ import annotations

import html
from collections import OrderedDict
from pathlib import Path

from runner.runner import RunSummary

# outcome -> (label, icon, css var). Status colours are never colour-alone: always icon + label.
OUTCOMES = OrderedDict([
    ("passed", ("Passed", "✓", "--status-good")),
    ("failed", ("Failed", "✕", "--status-critical")),
    ("error", ("Error", "!", "--status-serious")),
    ("skipped", ("Skipped", "–", "--status-muted")),
])

CSS = """
.viz-root{color-scheme:light;
  --surface-0:#f3f2ee;--surface-1:#fcfcfb;--text-primary:#0b0b0b;--text-secondary:#52514e;
  --text-muted:#7a7974;--grid:#e1e0d9;--axis:#c3c2b7;--border:rgba(11,11,11,.10);
  --series-1:#2a78d6;--status-good:#0ca30c;--status-critical:#d03b3b;--status-serious:#ec835a;
  --status-muted:#a3a29b;--track:#ecebe6}
@media (prefers-color-scheme:dark){.viz-root{color-scheme:dark;
  --surface-0:#111110;--surface-1:#1a1a19;--text-primary:#f0efec;--text-secondary:#c3c2b7;
  --text-muted:#8f8e88;--grid:#2c2c2a;--axis:#383835;--border:rgba(255,255,255,.10);
  --series-1:#3987e5;--status-muted:#6b6a65;--track:#252523}}
*{box-sizing:border-box}
body{margin:0;font:14px/1.45 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif}
.viz-root{background:var(--surface-0);color:var(--text-primary);min-height:100vh;padding:32px}
.wrap{max-width:1100px;margin:0 auto;display:grid;gap:20px}
header h1{margin:0 0 4px;font-size:22px}
.meta{color:var(--text-secondary);font-size:13px;display:flex;gap:16px;flex-wrap:wrap}
.badge{display:inline-flex;align-items:center;gap:6px;font-weight:600;padding:2px 10px;border-radius:999px;
  border:1px solid var(--border);background:var(--surface-1)}
.dot{width:10px;height:10px;border-radius:3px;display:inline-block;flex:none}
.card{background:var(--surface-1);border:1px solid var(--border);border-radius:12px;padding:20px}
.card h2{margin:0 0 14px;font-size:15px}
.tiles{display:grid;grid-template-columns:repeat(6,1fr);gap:12px}
.tile{background:var(--surface-1);border:1px solid var(--border);border-radius:12px;padding:14px 16px}
.tile .k{color:var(--text-secondary);font-size:12px;display:flex;align-items:center;gap:6px}
.tile .v{font-size:28px;font-weight:650;font-variant-numeric:tabular-nums;margin-top:2px}
.legend{display:flex;gap:16px;flex-wrap:wrap;color:var(--text-secondary);font-size:12px;margin-bottom:12px}
.legend span{display:inline-flex;align-items:center;gap:6px}
.stack{display:flex;gap:2px;height:14px;border-radius:4px;overflow:hidden;background:var(--track)}
.stack.big{height:28px}
.seg{height:100%;min-width:3px;cursor:default}
.seg:hover{filter:brightness(1.12)}
.rows{display:grid;grid-template-columns:200px 1fr 64px;gap:10px 14px;align-items:center}
.rows .lbl{font-size:13px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.rows .num{font-size:12px;color:var(--text-secondary);text-align:right;font-variant-numeric:tabular-nums}
.bar{height:14px;background:var(--series-1);border-radius:0 4px 4px 0;min-width:2px}
.bar:hover{filter:brightness(1.12)}
.axisrow{border-left:1px solid var(--axis)}
table{width:100%;border-collapse:collapse;font-size:13px}
th{text-align:left;color:var(--text-secondary);font-weight:500;padding:8px;border-bottom:1px solid var(--axis)}
td{padding:8px;border-bottom:1px solid var(--grid);vertical-align:top}
td.dur{text-align:right;font-variant-numeric:tabular-nums;color:var(--text-secondary)}
.pill{display:inline-flex;align-items:center;gap:6px;font-weight:600;white-space:nowrap}
.pill i{font-style:normal;width:18px;height:18px;border-radius:5px;display:inline-grid;place-items:center;
  color:#fff;font-size:11px}
code{font:12px ui-monospace,SFMono-Regular,Menlo,monospace}
details summary{cursor:pointer;color:var(--text-secondary)}
pre{white-space:pre-wrap;background:var(--surface-0);padding:10px;border-radius:8px;
  font:12px/1.4 ui-monospace,SFMono-Regular,Menlo,monospace;max-height:320px;overflow:auto}
.filters{display:flex;gap:8px;margin-bottom:12px;flex-wrap:wrap}
.filters button{font:inherit;font-size:12px;padding:4px 12px;border-radius:999px;cursor:pointer;
  border:1px solid var(--border);background:var(--surface-1);color:var(--text-primary)}
.filters button[aria-pressed=true]{background:var(--text-primary);color:var(--surface-1)}
#tip{position:fixed;pointer-events:none;background:var(--text-primary);color:var(--surface-1);
  font-size:12px;padding:6px 9px;border-radius:6px;opacity:0;transition:opacity .08s;z-index:10;white-space:pre}
@media (max-width:800px){.tiles{grid-template-columns:repeat(3,1fr)}.rows{grid-template-columns:120px 1fr 52px}}
"""

JS = """
const tip=document.getElementById('tip');
document.querySelectorAll('[data-tip]').forEach(el=>{
  el.addEventListener('mousemove',e=>{tip.textContent=el.dataset.tip;tip.style.opacity=1;
    tip.style.left=Math.min(e.clientX+12,innerWidth-tip.offsetWidth-8)+'px';tip.style.top=(e.clientY+14)+'px'});
  el.addEventListener('mouseleave',()=>tip.style.opacity=0);
});
document.querySelectorAll('.filters button').forEach(b=>b.addEventListener('click',()=>{
  document.querySelectorAll('.filters button').forEach(x=>x.setAttribute('aria-pressed',x===b));
  const f=b.dataset.filter;
  document.querySelectorAll('tbody tr').forEach(r=>r.hidden=!(f==='all'||r.dataset.outcome===f));
}));
"""


def _e(text) -> str:
    return html.escape(str(text))


def _stack(counts: dict[str, int], label: str, big: bool = False) -> str:
    total = sum(counts.values()) or 1
    segs = []
    for key, (name, _icon, var) in OUTCOMES.items():
        n = counts.get(key, 0)
        if not n:
            continue
        pct = 100 * n / total
        segs.append(f'<div class="seg" style="flex:{n} 1 0;background:var({var})" '
                    f'data-tip="{_e(label)}\n{name}: {n} ({pct:.0f}%)"></div>')
    cls = "stack big" if big else "stack"
    return f'<div class="{cls}" role="img" aria-label="{_e(label)}">{"".join(segs)}</div>'


def _legend() -> str:
    items = "".join(f'<span><i class="dot" style="background:var({var})"></i>{icon} {name}</span>'
                    for name, icon, var in OUTCOMES.values())
    return f'<div class="legend">{items}</div>'


def render_html(summary: RunSummary, title: str = "SWAPI Starship Test Report", base_url: str = "") -> str:
    totals = {k: summary.count(k) for k in OUTCOMES}
    pass_rate = 100 * totals["passed"] / summary.total if summary.total else 0.0
    ok = summary.successful
    status_badge = (f'<span class="badge"><i class="dot" style="background:var(--status-good)"></i>✓ All checks passed</span>'
                    if ok else
                    f'<span class="badge"><i class="dot" style="background:var(--status-critical)"></i>✕ Run failed</span>')

    # --- stat tiles -------------------------------------------------------
    tiles = [f'<div class="tile"><div class="k">Total tests</div><div class="v">{summary.total}</div></div>']
    for key, (name, icon, var) in OUTCOMES.items():
        tiles.append(f'<div class="tile"><div class="k"><i class="dot" style="background:var({var})"></i>'
                     f'{icon} {name}</div><div class="v">{totals[key]}</div></div>')
    tiles.append(f'<div class="tile"><div class="k">Pass rate</div><div class="v">{pass_rate:.0f}%</div></div>')

    # --- per-suite breakdown ---------------------------------------------
    suites: "OrderedDict[str, dict[str, int]]" = OrderedDict()
    for r in summary.records:
        suites.setdefault(r.suite, {k: 0 for k in OUTCOMES})[r.outcome] += 1
    suite_rows = "".join(
        f'<div class="lbl" title="{_e(s)}">{_e(s)}</div>{_stack(c, s)}'
        f'<div class="num">{c["passed"]}/{sum(c.values())}</div>'
        for s, c in suites.items()
    )

    # --- slowest tests (single series -> no legend) ------------------------
    slow = sorted(summary.records, key=lambda r: r.duration, reverse=True)[:10]
    max_d = max((r.duration for r in slow), default=0) or 1
    slow_rows = "".join(
        f'<div class="lbl" title="{_e(r.test_id)}">{_e(r.name)}</div>'
        f'<div class="axisrow"><div class="bar" style="width:{100 * r.duration / max_d:.1f}%" '
        f'data-tip="{_e(r.suite)}.{_e(r.name)}\n{r.duration * 1000:.0f} ms"></div></div>'
        f'<div class="num">{r.duration * 1000:.0f} ms</div>'
        for r in slow
    )

    # --- results table ----------------------------------------------------
    rows = []
    for r in summary.records:
        name, icon, var = OUTCOMES[r.outcome]
        details = (f'<details><summary>Show details</summary><pre>{_e(r.details)}</pre></details>'
                   if r.details else "")
        desc = f'<div style="color:var(--text-secondary)">{_e(r.description)}</div>' if r.description else ""
        rows.append(
            f'<tr data-outcome="{r.outcome}">'
            f'<td><span class="pill"><i style="background:var({var})">{icon}</i>{name}</span></td>'
            f'<td>{_e(r.suite)}<div style="color:var(--text-muted);font-size:12px">{_e(r.module)}</div></td>'
            f'<td><code>{_e(r.name)}</code>{desc}{details}</td>'
            f'<td class="dur">{r.duration * 1000:.0f} ms</td></tr>'
        )
    filter_buttons = '<button data-filter="all" aria-pressed="true">All</button>' + "".join(
        f'<button data-filter="{k}" aria-pressed="false">{icon} {name} ({totals[k]})</button>'
        for k, (name, icon, _v) in OUTCOMES.items() if totals[k]
    )

    meta = [f"Started {summary.started_at:%Y-%m-%d %H:%M:%S}", f"Duration {summary.duration:.2f}s"]
    if base_url:
        meta.append(f"Target {_e(base_url)}")

    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{_e(title)}</title><style>{CSS}</style></head>
<body><div class="viz-root"><div class="wrap">
<header><h1>{_e(title)}</h1><div class="meta">{status_badge}{''.join(f'<span>{m}</span>' for m in meta)}</div></header>
<div class="tiles">{''.join(tiles)}</div>
<section class="card"><h2>Overall results</h2>{_legend()}{_stack(totals, "All tests", big=True)}</section>
<section class="card"><h2>Results by test suite</h2>{_legend()}<div class="rows">{suite_rows}</div></section>
<section class="card"><h2>Slowest tests (duration)</h2><div class="rows">{slow_rows}</div></section>
<section class="card"><h2>All tests</h2><div class="filters">{filter_buttons}</div>
<table><thead><tr><th>Status</th><th>Suite</th><th>Test</th><th style="text-align:right">Duration</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table></section>
</div><div id="tip" role="tooltip"></div></div>
<script>{JS}</script>
</body></html>"""


def write_report(summary: RunSummary, path: str | Path, **kwargs) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_html(summary, **kwargs), encoding="utf-8")
    return path
