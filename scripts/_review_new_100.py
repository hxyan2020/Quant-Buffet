"""Review new_100 drafts for completeness, QB-only code, metrics, lab readiness."""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POSTS = ROOT / "backtest" / "drafts" / "new_100" / "posts"
CODE = ROOT / "backtest" / "drafts" / "new_100" / "code"
CURVES = ROOT / "backtest" / "drafts" / "new_100" / "equity_curves"
SUMMARY = ROOT / "backtest" / "drafts" / "new_100" / "backtest_summary.json"

QC_MARKERS = (
    "quantconnect",
    "algorithmimports",
    "add_equity",
    "addequity",
    "qcalgorithm",
    "self.securities",
    "lean ",
)

QB_MARKERS = (
    "from backtest.data import",
    "from backtest.engine import",
    "from backtest.metrics import",
    "PortfolioEngine",
    "make_on_day",
    "ASSETS",
)

SECTIONS = (
    "STRATEGY IN A NUTSHELL",
    "ECONOMIC RATIONALE",
    "SOURCE PAPER",
    "BACKTEST PERFORMANCE",
    "PYTHON CODE",
)


def main() -> None:
    posts = list(POSTS.glob("*.json"))
    codes = {p.stem for p in CODE.glob("*.py")}
    curves = {p.stem for p in CURVES.glob("*.json")}
    summary = json.loads(SUMMARY.read_text(encoding="utf-8")) if SUMMARY.exists() else {}

    issues = []
    qc_hits = []
    missing_sections = Counter()
    missing_metrics = 0
    missing_code = 0
    missing_curve = 0
    missing_paper = 0
    qb_ok = 0
    templates = Counter()
    fidelity = Counter()
    off_topic = []

    for f in posts:
        d = json.loads(f.read_text(encoding="utf-8"))
        slug = d.get("slug") or f.stem
        html = d.get("contentHtml") or ""
        py_html = d.get("pythonCodeHtml") or ""
        py_file = CODE / f"{slug}.py"
        py = py_file.read_text(encoding="utf-8") if py_file.exists() else ""
        blob = f"{py}\n{py_html}".lower()

        templates[d.get("template") or "?"] += 1
        fidelity[d.get("fidelity") or "?"] += 1

        for sec in SECTIONS:
            if sec.lower() not in html.lower() and sec.lower() not in (d.get("economicRationale") or "").lower():
                # python/backtest may live in dedicated fields
                if sec == "PYTHON CODE" and py_html:
                    continue
                if sec == "BACKTEST PERFORMANCE" and d.get("annualisedReturn"):
                    continue
                if sec == "ECONOMIC RATIONALE" and d.get("economicRationale"):
                    continue
                missing_sections[sec] += 1

        if not d.get("annualisedReturn") or not d.get("sharpeRatio"):
            missing_metrics += 1
            issues.append(f"metrics:{slug}")
        if slug not in codes:
            missing_code += 1
            issues.append(f"codefile:{slug}")
        if slug not in curves:
            missing_curve += 1
        if not d.get("paperTitle") or not d.get("academicLink"):
            missing_paper += 1

        if any(m in blob for m in QC_MARKERS):
            qc_hits.append(slug)
        if all(m.lower() in blob for m in ("from backtest.data import", "portfolioengine", "make_on_day")):
            qb_ok += 1
        elif "portfolioengine" in blob and "make_on_day" in blob:
            qb_ok += 1
        else:
            issues.append(f"qb_contract:{slug}")

        title = (d.get("title") or "") + " " + (d.get("paperTitle") or "")
        if re.search(r"optical angular|spin and orbital|climate risks for institutional|air-sea fluxes", title, re.I):
            off_topic.append(slug)

    print("=== NEW 100 REVIEW ===")
    print("posts", len(posts))
    print("code_files", len(codes))
    print("equity_curves", len(curves))
    print("summary_ok", summary.get("ok"), "errors", summary.get("errors"))
    print("median_cagr", summary.get("median_cagr"), "median_sharpe", summary.get("median_sharpe"))
    print("templates", dict(templates))
    print("fidelity", dict(fidelity))
    print("qb_ok", qb_ok)
    print("qc_hits", qc_hits)
    print("missing_metrics", missing_metrics)
    print("missing_code", missing_code)
    print("missing_curve", missing_curve)
    print("missing_paper", missing_paper)
    print("missing_sections", dict(missing_sections))
    print("off_topic_candidates", off_topic)
    print("issue_count", len(issues))
    for x in issues[:20]:
        print(" ", x)


if __name__ == "__main__":
    main()
