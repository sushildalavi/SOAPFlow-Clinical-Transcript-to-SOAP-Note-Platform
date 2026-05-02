#!/usr/bin/env python3
"""
Aggregate multiple batch_evaluate.py reports into one comparison table.

Usage:
    python evaluation/scripts/compare_runs.py \
        evaluation/reports/results_demo_baseline.json \
        evaluation/reports/results_ollama_qwen25_7b_full.json \
        --out evaluation/reports/comparison.md

Produces a Markdown table of (run, n, ROUGE-L, ROUGE-1, BLEU, sections, latency)
plus a per-source breakdown when --per-source data is present.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path


def _label_for(report: dict) -> str:
    cfg = report.get("configuration", {})
    mode = cfg.get("mode", "?")
    dataset = Path(cfg.get("dataset", "?")).name
    return f"{mode} ({dataset})"


def _row(report: dict) -> dict:
    cfg = report.get("configuration", {})
    agg = report.get("aggregate_statistics", {})
    return {
        "label": _label_for(report),
        "mode": cfg.get("mode", "?"),
        "dataset": cfg.get("dataset", "?"),
        "n": agg.get("total_examples", 0),
        "success": agg.get("successful_generations", 0),
        "rouge_l": agg.get("avg_rouge_l"),
        "rouge_1": agg.get("avg_rouge_1"),
        "bleu": agg.get("avg_bleu"),
        "sections": agg.get("avg_sections_populated"),
        "latency_ms": agg.get("avg_processing_time_ms"),
    }


def _fmt(v, digits=4) -> str:
    if v is None:
        return "—"
    if isinstance(v, float):
        return f"{v:.{digits}f}"
    return str(v)


def _render(rows: list[dict], reports: list[tuple[str, dict]]) -> str:
    lines = [
        f"# SOAPFlow evaluation comparison",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "## Aggregate metrics",
        "",
        "| Run | n | Success | ROUGE-L | ROUGE-1 | BLEU | Sections | Latency (ms) |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for r in rows:
        lines.append(
            f"| {r['label']} | {r['n']} | {r['success']}/{r['n']} | "
            f"{_fmt(r['rouge_l'])} | {_fmt(r['rouge_1'])} | {_fmt(r['bleu'])} | "
            f"{_fmt(r['sections'], 2)} | {_fmt(r['latency_ms'], 0)} |"
        )

    has_per_source = any("per_source_statistics" in rep for _, rep in reports)
    if has_per_source:
        lines += ["", "## Per-source ROUGE-L", "", "| Run | Source | n | ROUGE-L | ROUGE-1 | Sections |", "| --- | --- | ---: | ---: | ---: | ---: |"]
        for label, rep in reports:
            for src, stats in (rep.get("per_source_statistics") or {}).items():
                lines.append(
                    f"| {label} | {src} | {stats.get('successful', 0)}/{stats.get('total', 0)} | "
                    f"{_fmt(stats.get('avg_rouge_l'))} | {_fmt(stats.get('avg_rouge_1'))} | "
                    f"{_fmt(stats.get('avg_sections_populated'), 2)} |"
                )

    lines += ["", "## Reports", ""]
    for label, rep in reports:
        cfg = rep.get("configuration", {})
        lines.append(f"- **{label}** — `{cfg.get('dataset')}` ({cfg.get('total_examples')} examples)")

    return "\n".join(lines) + "\n"


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("reports", nargs="+", help="Paths to results_*.json files")
    p.add_argument("--out", default="evaluation/reports/comparison.md")
    args = p.parse_args()

    reports: list[tuple[str, dict]] = []
    rows: list[dict] = []
    for path in args.reports:
        rep = json.loads(Path(path).read_text())
        rows.append(_row(rep))
        reports.append((_label_for(rep), rep))

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(_render(rows, reports))
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
