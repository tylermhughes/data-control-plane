"""M5/M6 end to end: the north-star demo script itself, run through the API and the worker."""

import importlib.util
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.worker.__main__ import run_once
from tests.helpers import Headers

SCRIPT = Path(__file__).parents[2] / "scripts" / "demo.py"


def load_demo() -> Any:
    spec = importlib.util.spec_from_file_location("demo", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_north_star_demo(client: TestClient, admin: Headers, data_dir: Path, db: Session) -> None:
    demo = load_demo()

    def api(method: str, path: str, body: Any = None) -> Any:
        run_once(db)  # the worker: runs queued checks between API calls, as in Docker
        response = client.request(method, path, json=body, headers=admin)
        assert response.status_code < 400, f"{method} {path}: {response.text}"
        return response.json() if response.content else None

    lines: list[str] = []
    result = demo.run(
        api, webhook_port=None, say=lines.append, data_dir=data_dir, uri_root=str(data_dir)
    )
    report = result["portfolio"]

    [cap] = report["by_capability"]
    assert cap["spend"] == [{"currency": "USD", "amount": "13400.00"}]  # 6200 + 6600 + 600
    assert cap["usable_units"] == [{"unit": "images", "count": 10100}]  # 3800 + 3700 + 2600
    assert cap["cost_per_usable_unit"][0]["amount"] == "1.3267"
    assert cap["eval_change_points"] == 4.5  # (0.857 − 0.812) / 0.01
    assert cap["spend_on_scored_versions"] == [{"currency": "USD", "amount": "7200.00"}]
    assert cap["points_per_10k"] == 6.25  # 4.5 / 7,200 × 10,000
    assert cap["value"] == "112500.00"  # 4.5 × 25,000
    assert cap["roi"] == 15.62  # 112,500 / 7,200

    kinds = {row["kind"]: row for row in report["by_source_kind"]}
    human, enterprise = kinds["human_vendor"], kinds["enterprise_workflow"]
    assert (human["is_estimate"], human["attribution_method"]) == (True, "accepted_units_share")
    # v2 added Mercor (3,700 accepted) and Returns photos (2,600): 4.5 points split 37:26.
    assert human["eval_change_points"] == round(4.5 * 3700 / 6300, 4)
    assert enterprise["eval_change_points"] == round(4.5 * 2600 / 6300, 4)
    assert human["points_per_10k"] == round(4.5 * 3700 / 6300 / 6600 * 10_000, 4)
    assert human["spend"] == [{"currency": "USD", "amount": "12800.00"}]  # Surge + Mercor

    text = "\n".join(lines)
    assert "Surge: passed (checks passed)" in text
    assert (
        "Mercor: accepted by mercor-qa (checks passed: 0 repeated within this batch; 50 already"
        in text
    )
    assert "Returns photos: passed (checks passed: 12 of 3,000 records don't match" in text
    assert "30 repeated within this batch" in text
    assert "no value for agreement" in text
    assert "Surge batch gaps: ['package_type=shrink_wrapped: 29% vs 35% target']" in text
    assert "Whole request gaps: none (within tolerance)" in text
