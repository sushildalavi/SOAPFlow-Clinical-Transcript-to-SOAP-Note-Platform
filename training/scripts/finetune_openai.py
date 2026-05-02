#!/usr/bin/env python3
"""
Fine-tune a GPT model on SOAPFlow SOAP note generation data.
Integrates with MLflow for experiment tracking and model registry.

Prerequisites:
    pip install openai mlflow
    export OPENAI_API_KEY=sk-...
    mlflow server --host 0.0.0.0 --port 5000  (optional, uses local tracking otherwise)

Usage:
    # Upload data and start fine-tuning job
    python training/scripts/finetune_openai.py --data data/training.jsonl

    # Check status of a running job
    python training/scripts/finetune_openai.py --check --job-id ftjob-abc123

    # List all fine-tuning jobs
    python training/scripts/finetune_openai.py --list
"""
import argparse
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

CONFIG_PATH = Path(__file__).parent.parent / "configs" / "openai_finetune.json"
MLFLOW_TRACKING_URI = os.environ.get("MLFLOW_TRACKING_URI", "http://localhost:5000")


def load_config() -> dict:
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            return json.load(f)
    return {}


def upload_training_file(client, data_path: str) -> str:
    print(f"Uploading training file: {data_path}")
    with open(data_path, "rb") as f:
        response = client.files.create(file=f, purpose="fine-tune")
    file_id = response.id
    print(f"  Uploaded: {file_id}")
    print("  Waiting for file processing...")
    while True:
        file_status = client.files.retrieve(file_id)
        if file_status.status == "processed":
            break
        elif file_status.status == "error":
            raise RuntimeError(f"File processing failed: {file_status.status_details}")
        time.sleep(5)
    print(f"  File ready: {file_id}")
    return file_id


def start_finetune(client, file_id: str, config: dict) -> str:
    model = config.get("model", "gpt-4o-mini-2024-07-18")
    suffix = config.get("suffix", "soapflow")
    epochs = config.get("n_epochs", 3)

    print(f"Starting fine-tune: model={model}, suffix={suffix}, epochs={epochs}")
    job = client.fine_tuning.jobs.create(
        training_file=file_id,
        model=model,
        suffix=suffix,
        hyperparameters={"n_epochs": epochs},
    )
    print(f"  Job ID: {job.id} | Status: {job.status}")
    return job.id


def track_with_mlflow(job_id: str, config: dict, data_path: str, client) -> None:
    """Log fine-tuning run to MLflow experiment tracker."""
    try:
        import mlflow
        mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
        mlflow.set_experiment("soapflow-finetuning")

        with mlflow.start_run(run_name=f"openai-finetune-{job_id[:8]}"):
            # Log hyperparameters
            mlflow.log_params({
                "model": config.get("model", "gpt-4o-mini-2024-07-18"),
                "n_epochs": config.get("n_epochs", 3),
                "suffix": config.get("suffix", "soapflow"),
                "job_id": job_id,
                "data_path": data_path,
            })

            # Count training examples
            with open(data_path) as f:
                n_examples = sum(1 for _ in f)
            mlflow.log_metric("training_examples", n_examples)

            # Poll for completion and log final metrics
            print("Tracking job with MLflow...")
            while True:
                job = client.fine_tuning.jobs.retrieve(job_id)
                mlflow.log_metric("job_running", 1 if job.status == "running" else 0)

                if job.status == "succeeded":
                    mlflow.log_param("fine_tuned_model", job.fine_tuned_model)
                    mlflow.log_metric("job_succeeded", 1)
                    mlflow.set_tag("fine_tuned_model", job.fine_tuned_model)
                    print(f"\nMLflow run complete. Fine-tuned model: {job.fine_tuned_model}")
                    break
                elif job.status in ("failed", "cancelled"):
                    mlflow.log_metric("job_succeeded", 0)
                    mlflow.set_tag("failure_reason", str(job.error))
                    break

                time.sleep(60)

    except Exception as e:
        print(f"  MLflow tracking failed (non-critical): {e}")


def check_job(client, job_id: str) -> None:
    job = client.fine_tuning.jobs.retrieve(job_id)
    print(f"Job: {job_id}\n  Status: {job.status}\n  Model: {job.model}")
    if job.fine_tuned_model:
        print(f"  Fine-tuned model: {job.fine_tuned_model}")
        print(f"\n  Add to backend/.env:\n  OPENAI_MODEL={job.fine_tuned_model}")
    if job.error:
        print(f"  Error: {job.error}")
    events = client.fine_tuning.jobs.list_events(fine_tuning_job_id=job_id, limit=5)
    print("\nRecent events:")
    for event in reversed(events.data):
        print(f"  [{event.created_at}] {event.message}")


def list_jobs(client) -> None:
    jobs = client.fine_tuning.jobs.list(limit=20)
    print(f"Fine-tuning jobs ({len(jobs.data)} shown):")
    for job in jobs.data:
        ft = f" -> {job.fine_tuned_model}" if job.fine_tuned_model else ""
        print(f"  {job.id} | {job.status} | {job.model}{ft}")


def main():
    parser = argparse.ArgumentParser(description="Fine-tune GPT model for SOAP generation")
    parser.add_argument("--data", help="Path to training JSONL file")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--job-id", help="Fine-tuning job ID")
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--mlflow", action="store_true", help="Track run with MLflow")
    args = parser.parse_args()

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY not set.")
        sys.exit(1)

    try:
        from openai import OpenAI
    except ImportError:
        print("Error: pip install openai")
        sys.exit(1)

    client = OpenAI(api_key=api_key)
    config = load_config()

    if args.list:
        list_jobs(client)
        return

    if args.check:
        if not args.job_id:
            print("Error: --job-id required with --check")
            sys.exit(1)
        check_job(client, args.job_id)
        return

    if not args.data or not Path(args.data).exists():
        print(f"Error: --data file not found: {args.data}")
        sys.exit(1)

    with open(args.data) as f:
        count = sum(1 for _ in f)
    print(f"Training examples: {count}")
    if count < 10:
        print("Warning: OpenAI recommends at least 10 examples.")

    file_id = upload_training_file(client, args.data)
    job_id = start_finetune(client, file_id, config)
    print(f"\nJob started: {job_id}")
    print(f"Check: python training/scripts/finetune_openai.py --check --job-id {job_id}")

    if args.mlflow:
        track_with_mlflow(job_id, config, args.data, client)


if __name__ == "__main__":
    main()
