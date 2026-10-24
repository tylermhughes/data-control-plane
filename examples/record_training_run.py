"""Example for a training pipeline: after training on new data, tell DCP what it achieved.

Freezes the next dataset version from accepted batches, records the eval result (with a link
to the run), and prints what the diagnosis now recommends. Run it as the last CI step of a
training job, so the portfolio and diagnosis stay current without anyone typing numbers.

    export DCP_URL=http://localhost:8000 DCP_API_KEY=dcp_...
    uv run --project clients/cli python examples/record_training_run.py \\
        --dataset-id dst_... --batch-ids bat_1,bat_2 --value 0.861 \\
        --run-url https://wandb.ai/acme/damage-det/runs/abc123
"""

import argparse
import os
import sys
from typing import Any

from dcp_client import AuthenticatedClient
from dcp_client.api.datasets import create_dataset_version, get_dataset
from dcp_client.api.eval_results import record_eval
from dcp_client.api.recommendations import diagnosis
from dcp_client.models import DatasetVersionCreate, EvalResultCreate


def ok(response: Any, what: str) -> Any:
    if int(response.status_code) >= 400:
        sys.exit(f"{what} failed (HTTP {int(response.status_code)}): {response.content.decode()}")
    return response.parsed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--dataset-id", required=True)
    parser.add_argument("--batch-ids", default="", help="Comma-separated accepted batches to add")
    parser.add_argument("--value", type=float, required=True, help="Main eval metric value")
    parser.add_argument("--run-url", help="Link to the training/eval run")
    parser.add_argument("--run-name", default="")
    args = parser.parse_args()

    client = AuthenticatedClient(
        base_url=os.environ.get("DCP_URL", "http://localhost:8000"),
        token=os.environ["DCP_API_KEY"],
    )
    batch_ids = [b for b in args.batch_ids.split(",") if b]
    version = ok(
        create_dataset_version.sync_detailed(
            args.dataset_id,
            client=client,
            body=DatasetVersionCreate(batch_ids=batch_ids),
            idempotency_key=f"train-{args.dataset_id}-{args.run_name or args.value}",
        ),
        "Creating the dataset version",
    )
    print(f"Dataset version {version.version} ({version.id}): {len(version.batch_ids)} batches")

    result = ok(
        record_eval.sync_detailed(
            client=client,
            body=EvalResultCreate(
                dataset_version_id=version.id,
                value=args.value,
                run_name=args.run_name,
                external_run_url=args.run_url,
            ),
        ),
        "Recording the eval result",
    )
    print(f"Recorded {result.metric} = {result.value}")

    dataset = ok(get_dataset.sync_detailed(args.dataset_id, client=client), "Reading the dataset")
    report = ok(
        diagnosis.sync_detailed(dataset.capability_id, client=client), "Reading the diagnosis"
    )
    print(f"Diagnosis: {report.recommendation} - {report.summary}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
