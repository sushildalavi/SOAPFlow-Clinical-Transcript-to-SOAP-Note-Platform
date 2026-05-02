#!/usr/bin/env python3
"""
Prepare training data for fine-tuning a SOAP note generation model.

This script:
1. Loads examples from the synthetic dataset (or other adapters)
2. Generates SOAP notes via the SOAPFlow API for examples that lack reference notes
3. Formats everything into OpenAI fine-tuning JSONL format
4. Saves to the specified output file

Usage:
    python training/scripts/prepare_dataset.py --output data/training.jsonl --count 100
    python training/scripts/prepare_dataset.py --source synthetic --output data/train.jsonl
    python training/scripts/prepare_dataset.py --generate-missing --api-url http://localhost:8000
"""
import argparse
import json
import sys
from pathlib import Path

import httpx

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scribe_datasets.adapters import get_adapter
from scribe_datasets.adapters.base import SOAPExample

SYSTEM_PROMPT = """You are SOAPFlow, an expert clinical documentation AI assistant. Your task is to convert raw doctor-patient conversation transcripts into structured, professional SOAP notes.

Return ONLY valid JSON with keys: subjective, objective, assessment, plan."""


def example_to_finetune_message(example: SOAPExample) -> dict | None:
    """Convert a SOAPExample to OpenAI fine-tuning chat format."""
    if not example.transcript or not example.soap_note:
        return None

    soap = example.soap_note
    # Validate soap has all sections
    for key in ["subjective", "objective", "assessment", "plan"]:
        if not soap.get(key):
            return None

    return {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Please generate a structured SOAP note from the following transcript:\n\n"
                    f"---TRANSCRIPT START---\n{example.transcript}\n---TRANSCRIPT END---\n\n"
                    f"Return ONLY the JSON object with keys: subjective, objective, assessment, plan."
                ),
            },
            {
                "role": "assistant",
                "content": json.dumps(
                    {
                        "subjective": soap["subjective"],
                        "objective": soap["objective"],
                        "assessment": soap["assessment"],
                        "plan": soap["plan"],
                    },
                    ensure_ascii=False,
                ),
            },
        ]
    }


def _normalize_api_url(api_url: str) -> str:
    return api_url.rstrip("/")


def generate_soap_via_api(
    client: httpx.Client,
    transcript: str,
    api_url: str,
) -> dict | None:
    """Call the SOAPFlow API to generate a SOAP note for a transcript."""
    try:
        response = client.post(
            f"{api_url}/api/v1/generate",
            json={"transcript": transcript, "mode": "demo"},
        )
        response.raise_for_status()
        data = response.json()
        return data.get("soap_note")
    except Exception as e:
        print(f"  Warning: API call failed: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(description="Prepare SOAPFlow fine-tuning dataset")
    parser.add_argument("--source", default="synthetic", help="Dataset adapter name")
    parser.add_argument("--output", default="data/training.jsonl", help="Output JSONL file path")
    parser.add_argument("--count", type=int, default=None, help="Limit number of examples")
    parser.add_argument("--generate-missing", action="store_true", help="Generate SOAP notes for examples without reference notes")
    parser.add_argument("--api-url", default="http://localhost:8000", help="SOAPFlow API URL for generation")
    parser.add_argument("--validate", action="store_true", help="Validate output format after generation")
    args = parser.parse_args()
    api_url = _normalize_api_url(args.api_url)

    print(f"Loading adapter: {args.source}")
    adapter = get_adapter(args.source)
    adapter.load()
    print(f"  Loaded {len(adapter)} examples")

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    written = 0
    skipped = 0
    generated = 0

    with httpx.Client(timeout=httpx.Timeout(30.0, connect=10.0)) as client, open(output_path, "w") as f:
        for i, example in enumerate(adapter):
            if args.count and written >= args.count:
                break

            if not example.soap_note and args.generate_missing:
                print(f"  Generating SOAP for example {example.id}...")
                soap = generate_soap_via_api(client, example.transcript, api_url)
                if soap:
                    example.soap_note = soap
                    generated += 1

            message = example_to_finetune_message(example)
            if message:
                f.write(json.dumps(message, ensure_ascii=False) + "\n")
                written += 1
            else:
                skipped += 1

            if (i + 1) % 10 == 0:
                print(f"  Processed {i + 1} examples...")

    print(f"\nDone!")
    print(f"  Written: {written} examples")
    print(f"  Skipped: {skipped} examples (missing data)")
    if generated > 0:
        print(f"  Generated: {generated} SOAP notes via API")
    print(f"  Output: {output_path}")

    # Validate format
    if args.validate:
        print("\nValidating output format...")
        with open(output_path) as f:
            for line in f:
                obj = json.loads(line)
                assert "messages" in obj
                assert len(obj["messages"]) == 3
                assert obj["messages"][0]["role"] == "system"
        print("  Validation passed!")


if __name__ == "__main__":
    main()
