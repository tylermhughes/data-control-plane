"""Example CI gate: refuse to train on a dataset version that isn't clean.

Fails (exit code 1) unless every batch in the dataset version
  - is accepted,
  - passed its automated checks, or was accepted anyway with a written override reason,
  - comes from a data source whose rights haven't expired.
A first, scriptable version of the "training gate" in docs/PRODUCT.md.

    export DCP_URL=http://localhost:8000 DCP_API_KEY=dcp_...
    uv run --project clients/cli python examples/quality_gate.py --dataset-version-id dsv_...
"""

import argparse
import datetime as dt
import os
import sys
from typing import Any

from dcp_client import AuthenticatedClient
from dcp_client.api.batches import get_batch
from dcp_client.api.data_sources import get_source
from dcp_client.api.datasets import get_dataset_version
from dcp_client.types import Unset


def ok(response: Any, what: str) -> Any:
    if int(response.status_code) >= 400:
        sys.exit(f"{what} failed (HTTP {int(response.status_code)}): {response.content.decode()}")
    return response.parsed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--dataset-version-id", required=True)
    args = parser.parse_args()
    client = AuthenticatedClient(
        base_url=os.environ.get("DCP_URL", "http://localhost:8000"),
        token=os.environ["DCP_API_KEY"],
    )

    version = ok(
        get_dataset_version.sync_detailed(args.dataset_version_id, client=client),
        "Reading the dataset version",
    )
    today = dt.date.today()
    problems: list[str] = []
    sources: dict[str, Any] = {}
    for batch_id in version.batch_ids:
        batch = ok(get_batch.sync_detailed(batch_id, client=client), f"Reading {batch_id}")
        status = str(batch.status.value if hasattr(batch.status, "value") else batch.status)
        if status != "accepted":
            problems.append(f"{batch_id}: is {status}, not accepted")
        quality = batch.quality
        failed = quality is not None and not isinstance(quality, Unset) and quality.failed_checks
        override = batch.override_reason if isinstance(batch.override_reason, str) else None
        if failed and not override:
            problems.append(f"{batch_id}: failed checks {quality.failed_checks} with no override")
        if batch.data_source_id not in sources:
            sources[batch.data_source_id] = ok(
                get_source.sync_detailed(batch.data_source_id, client=client), "Reading a source"
            )
        source = sources[batch.data_source_id]
        expires = source.rights_expires_at
        if isinstance(expires, dt.date) and expires < today:
            problems.append(f"{batch_id}: rights for {source.name} expired on {expires}")

    if problems:
        print(f"Gate FAILED for {version.id} ({len(problems)} problem(s)):")
        for problem in problems:
            print(f"  - {problem}")
        return 1
    print(f"Gate passed for {version.id}: {len(version.batch_ids)} batches, all clean.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
