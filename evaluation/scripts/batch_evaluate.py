#!/usr/bin/env python3
"""
Batch evaluation script for SOAPFlow.

Generates SOAP notes for a dataset of transcripts, scores them against
reference notes (if available), and produces a detailed evaluation report.

Usage:
    # Evaluate on synthetic dataset examples
    python evaluation/scripts/batch_evaluate.py \
        --dataset data/synthetic/synthetic_soap_examples.json \
        --output evaluation/reports/results.json \
        --api-url http://localhost:8000

    # Evaluate specific mode
    python evaluation/scripts/batch_evaluate.py \
        --dataset data/synthetic/synthetic_soap_examples.json \
        --mode demo \
        --output evaluation/reports/demo_results.json
"""
import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import httpx


def _normalize_api_url(api_url: str) -> str:
    return api_url.rstrip("/")


def generate_soap(
    client: httpx.Client,
    transcript: str,
    api_url: str,
    mode: str = "demo",
) -> dict | None:
    """Call SOAPFlow API to generate a SOAP note."""
    try:
        response = client.post(
            f"{api_url}/api/v1/generate",
            json={"transcript": transcript, "mode": mode, "include_raw_json": True},
        )
        response.raise_for_status()
        data = response.json()
        return {
            "soap_note": data.get("soap_note"),
            "metadata": data.get("metadata"),
            "warnings": data.get("warnings", []),
        }
    except Exception as e:
        return {"error": str(e)}


def evaluate_note(
    client: httpx.Client,
    transcript: str,
    generated: dict,
    reference: dict | None,
    api_url: str,
) -> dict | None:
    """Call the /evaluate endpoint to score a generated note."""
    try:
        payload = {
            "transcript": transcript,
            "generated_note": generated,
        }
        if reference:
            payload["reference_note"] = reference

        response = client.post(
            f"{api_url}/api/v1/evaluate",
            json=payload,
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}


def _avg(xs: list[float]) -> float | None:
    return round(sum(xs) / len(xs), 4) if xs else None


def compute_aggregate_stats(results: list[dict]) -> dict:
    """Compute aggregate statistics across all evaluation results."""
    successful = [r for r in results if not r.get("error")]
    with_reference = [r for r in successful if r.get("evaluation") and r["evaluation"].get("scores", {}).get("rouge_l") is not None]

    stats = {
        "total_examples": len(results),
        "successful_generations": len(successful),
        "failed_generations": len(results) - len(successful),
        "generation_success_rate": len(successful) / max(len(results), 1),
    }

    # Aggregate ROUGE scores if available
    if with_reference:
        rouge_l_scores = [r["evaluation"]["scores"]["rouge_l"] for r in with_reference if r["evaluation"]["scores"].get("rouge_l") is not None]
        rouge_1_scores = [r["evaluation"]["scores"]["rouge_1"] for r in with_reference if r["evaluation"]["scores"].get("rouge_1") is not None]
        bleu_scores = [r["evaluation"]["scores"]["bleu"] for r in with_reference if r["evaluation"]["scores"].get("bleu") is not None]

        if rouge_l_scores:
            stats["avg_rouge_l"] = round(sum(rouge_l_scores) / len(rouge_l_scores), 4)
            stats["max_rouge_l"] = round(max(rouge_l_scores), 4)
            stats["min_rouge_l"] = round(min(rouge_l_scores), 4)
        if rouge_1_scores:
            stats["avg_rouge_1"] = round(sum(rouge_1_scores) / len(rouge_1_scores), 4)
        if bleu_scores:
            stats["avg_bleu"] = round(sum(bleu_scores) / len(bleu_scores), 4)

    # Average sections populated
    sections = [r["generation"]["metadata"]["sections_populated"] for r in successful if r.get("generation") and r["generation"].get("metadata")]
    if sections:
        stats["avg_sections_populated"] = round(sum(sections) / len(sections), 2)

    # Average processing time
    times = [r["generation"]["metadata"]["processing_time_ms"] for r in successful if r.get("generation") and r["generation"].get("metadata")]
    if times:
        stats["avg_processing_time_ms"] = round(sum(times) / len(times), 2)

    # Warning counts
    warning_counts = []
    for r in successful:
        if r.get("generation") and r["generation"].get("warnings"):
            warning_counts.append(len(r["generation"]["warnings"]))
    if warning_counts:
        stats["avg_warnings_per_note"] = round(sum(warning_counts) / len(warning_counts), 2)

    return stats


def _load_dataset(path: str) -> list[dict]:
    """Load examples from JSON or JSONL. Normalizes to {id, transcript, reference_soap, source}."""
    p = Path(path)
    suffix = p.suffix.lower()
    raw: list[dict] = []
    if suffix == ".jsonl":
        with p.open() as f:
            for line in f:
                line = line.strip()
                if line:
                    raw.append(json.loads(line))
    else:
        with p.open() as f:
            raw = json.load(f)

    normalized = []
    for i, item in enumerate(raw):
        ex_id = item.get("id") or f"ex_{i:04d}"
        transcript = item.get("transcript") or ""
        reference = item.get("reference_soap") or item.get("soap_note")
        normalized.append(
            {
                "id": ex_id,
                "transcript": transcript,
                "reference_soap": reference,
                "source": item.get("source") or item.get("metadata", {}).get("source") or "unknown",
                "chief_complaint": item.get("chief_complaint")
                or (item.get("metadata") or {}).get("chief_complaint"),
            }
        )
    return normalized


def compute_per_source_stats(results: list[dict]) -> dict:
    by_source: dict[str, list[dict]] = {}
    for r in results:
        by_source.setdefault(r.get("source", "unknown"), []).append(r)
    out: dict[str, dict] = {}
    for src, rows in by_source.items():
        ok = [r for r in rows if not r.get("error")]
        rouge_l = [
            r["evaluation"]["scores"].get("rouge_l")
            for r in ok
            if r.get("evaluation") and r["evaluation"].get("scores", {}).get("rouge_l") is not None
        ]
        rouge_1 = [
            r["evaluation"]["scores"].get("rouge_1")
            for r in ok
            if r.get("evaluation") and r["evaluation"].get("scores", {}).get("rouge_1") is not None
        ]
        bleu = [
            r["evaluation"]["scores"].get("bleu")
            for r in ok
            if r.get("evaluation") and r["evaluation"].get("scores", {}).get("bleu") is not None
        ]
        sections = [
            r["generation"]["metadata"]["sections_populated"]
            for r in ok
            if r.get("generation") and r["generation"].get("metadata")
        ]
        out[src] = {
            "total": len(rows),
            "successful": len(ok),
            "avg_rouge_l": _avg(rouge_l),
            "avg_rouge_1": _avg(rouge_1),
            "avg_bleu": _avg(bleu),
            "avg_sections_populated": _avg(sections),
        }
    return out


def main():
    parser = argparse.ArgumentParser(description="Batch evaluate SOAPFlow SOAP generation")
    parser.add_argument("--dataset", required=True, help="Path to dataset JSON or JSONL file")
    parser.add_argument("--output", default="evaluation/reports/results.json", help="Output report path")
    parser.add_argument("--api-url", default="http://localhost:8000", help="SOAPFlow API URL")
    parser.add_argument("--mode", default="demo", choices=["demo", "openai", "anthropic", "ollama", "groq", "mlx"], help="Generation mode")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of examples to evaluate")
    parser.add_argument("--no-evaluate", action="store_true", help="Skip evaluation step (generation only)")
    parser.add_argument("--per-source", action="store_true", help="Break out metrics per dataset source")
    parser.add_argument("--timeout", type=float, default=300.0, help="HTTP timeout per request in seconds")
    args = parser.parse_args()
    api_url = _normalize_api_url(args.api_url)

    print(f"Loading dataset: {args.dataset}")
    examples = _load_dataset(args.dataset)
    print(f"  Found {len(examples)} examples")

    if args.limit:
        examples = examples[:args.limit]
        print(f"  Limited to {len(examples)} examples")

    results = []
    print(f"\nGenerating SOAP notes using mode: {args.mode}")
    print(f"API: {api_url}\n")

    with httpx.Client(timeout=httpx.Timeout(args.timeout, connect=10.0)) as client:
        for i, example in enumerate(examples):
            example_id = example.get("id", f"ex_{i:04d}")
            transcript = example.get("transcript", "")
            reference_soap = example.get("reference_soap")
            source = example.get("source", "unknown")

            print(f"[{i+1}/{len(examples)}] {example_id} ({source}) — {example.get('chief_complaint', '')}".rstrip(" —"))

            if not transcript or len(transcript) < 50:
                print(f"  Skipping: transcript too short")
                results.append({"id": example_id, "source": source, "error": "Transcript too short"})
                continue

            gen_result = generate_soap(client, transcript, api_url, args.mode)
            if gen_result.get("error"):
                print(f"  Generation failed: {gen_result['error']}")
                results.append({"id": example_id, "source": source, "error": gen_result["error"]})
                continue

            print(f"  Generated in {gen_result['metadata']['processing_time_ms']:.0f}ms ({gen_result['metadata']['sections_populated']}/4 sections)")

            result = {
                "id": example_id,
                "source": source,
                "chief_complaint": example.get("chief_complaint"),
                "generation": gen_result,
                "has_reference": reference_soap is not None,
            }

            if not args.no_evaluate:
                eval_result = evaluate_note(
                    client,
                    transcript,
                    gen_result["soap_note"],
                    reference_soap,
                    api_url,
                )
                if eval_result and not eval_result.get("error"):
                    result["evaluation"] = eval_result
                    scores = eval_result.get("scores", {})
                    rouge_l = scores.get("rouge_l")
                    heuristic = (scores.get("section_scores") or {}).get("heuristic_completeness")
                    score_str = f"ROUGE-L={rouge_l:.3f}" if rouge_l else f"Heuristic={heuristic:.2f}" if heuristic else "N/A"
                    print(f"  Score: {score_str}")

            results.append(result)
            time.sleep(0.1)

    # Compute aggregate statistics
    stats = compute_aggregate_stats(results)
    per_source = compute_per_source_stats(results) if args.per_source else None

    # Build report
    report = {
        "generated_at": datetime.now().isoformat(),
        "configuration": {
            "dataset": args.dataset,
            "mode": args.mode,
            "api_url": api_url,
            "total_examples": len(results),
        },
        "aggregate_statistics": stats,
        "results": results,
    }
    if per_source:
        report["per_source_statistics"] = per_source

    # Save report
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*50}")
    print(f"EVALUATION COMPLETE")
    print(f"{'='*50}")
    print(f"Total examples:    {stats['total_examples']}")
    print(f"Successful:        {stats['successful_generations']}")
    if "avg_rouge_l" in stats:
        print(f"Avg ROUGE-L:       {stats['avg_rouge_l']:.4f}")
    if "avg_sections_populated" in stats:
        print(f"Avg sections:      {stats['avg_sections_populated']:.1f}/4")
    if "avg_processing_time_ms" in stats:
        print(f"Avg time:          {stats['avg_processing_time_ms']:.0f}ms")
    if per_source:
        print(f"\nPer-source breakdown:")
        for src, s in per_source.items():
            r = s.get("avg_rouge_l")
            print(
                f"  {src:<18} n={s['successful']}/{s['total']:<5}"
                + (f"  ROUGE-L={r:.3f}" if r is not None else "")
            )
    print(f"\nReport saved: {output_path}")


if __name__ == "__main__":
    main()
