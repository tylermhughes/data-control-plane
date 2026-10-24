from typing import Any

from fastapi.testclient import TestClient

from tests.helpers import Headers, Setup, post_ok


def accepted_batch(s: Setup, alloc_id: str, accepted: int = 900, **extra: Any) -> Any:
    batch = s.batch(alloc_id, **extra)
    return post_ok(
        s.client, f"/v1/batches/{batch['id']}/accept", s.admin, {"accepted_count": accepted}
    )


def dataset(s: Setup, name: str = "damage-det") -> Any:
    return post_ok(
        s.client, "/v1/datasets", s.admin, {"capability_id": s.capability_id, "name": name}
    )


def version(s: Setup, dataset_id: str, **body: Any) -> Any:
    return post_ok(s.client, f"/v1/datasets/{dataset_id}/versions", s.admin, body)


def test_versions_build_on_the_previous_one(client: TestClient, admin: Headers) -> None:
    s = Setup(client, admin)
    alloc = s.active_allocation()
    a = accepted_batch(s, alloc["id"], spend="1000")
    b = accepted_batch(s, alloc["id"], spend="500")
    ds = dataset(s)
    assert (ds["id"][:4], ds["latest_version"], ds["project_id"]) == ("dst_", 0, s.project_id)

    v1 = version(s, ds["id"], batch_ids=[a["id"]])
    assert (v1["version"], v1["baseline_version_id"], v1["batch_ids"]) == (1, None, [a["id"]])

    v2 = version(s, ds["id"], batch_ids=[b["id"]])
    assert v2["version"] == 2
    assert v2["baseline_version_id"] == v1["id"]
    assert v2["batch_ids"] == sorted([a["id"], b["id"]])  # kept the baseline's batches
    assert v2["totals"][0]["spend"] == "1500.00"
    assert v2["new_vs_baseline"][0] == {
        "unit": "images",
        "currency": "USD",
        "batch_count": 1,
        "accepted_count": 900,
        "spend": "500.00",
    }
    assert client.get(f"/v1/datasets/{ds['id']}", headers=admin).json()["latest_version"] == 2


def test_baseline_choices(client: TestClient, admin: Headers) -> None:
    s = Setup(client, admin)
    alloc = s.active_allocation()
    a, b = accepted_batch(s, alloc["id"]), accepted_batch(s, alloc["id"])
    first = dataset(s, "first")
    v1 = version(s, first["id"], batch_ids=[a["id"]])

    no_baseline = version(s, first["id"], batch_ids=[b["id"]], baseline_version_id=None)
    assert (no_baseline["baseline_version_id"], no_baseline["batch_ids"]) == (None, [b["id"]])

    other = dataset(s, "second")
    cross = version(s, other["id"], batch_ids=[b["id"]], baseline_version_id=v1["id"])
    assert cross["baseline_version_id"] == v1["id"]
    assert cross["batch_ids"] == sorted([a["id"], b["id"]])

    only_new = version(
        s,
        first["id"],
        batch_ids=[b["id"]],
        baseline_version_id=v1["id"],
        include_baseline_batches=False,
    )
    assert only_new["batch_ids"] == [b["id"]]


def test_only_accepted_batches_from_this_project(client: TestClient, admin: Headers) -> None:
    s = Setup(client, admin)
    alloc = s.active_allocation()
    received = s.batch(alloc["id"])
    ds = dataset(s)
    path = f"/v1/datasets/{ds['id']}/versions"
    bad = client.post(path, headers=admin, json={"batch_ids": [received["id"]]})
    assert bad.status_code == 422
    assert "only accepted batches" in bad.json()["detail"]
    assert client.post(path, headers=admin, json={"batch_ids": []}).status_code == 422

    other = Setup(client, admin, "Other")
    foreign = accepted_batch(other, other.active_allocation()["id"])
    assert client.post(path, headers=admin, json={"batch_ids": [foreign["id"]]}).status_code == 422


def test_baseline_must_be_for_the_same_capability(client: TestClient, admin: Headers) -> None:
    s = Setup(client, admin)
    alloc = s.active_allocation()
    a = accepted_batch(s, alloc["id"])
    v1 = version(s, dataset(s)["id"], batch_ids=[a["id"]])
    other_cap = post_ok(
        client,
        "/v1/capabilities",
        admin,
        {
            "project_id": s.project_id,
            "name": "Labels",
            "eval_metric": "read accuracy",
            "value_per_point": "1",
            "currency": "USD",
        },
    )
    ds = post_ok(
        client, "/v1/datasets", admin, {"capability_id": other_cap["id"], "name": "labels"}
    )
    response = client.post(
        f"/v1/datasets/{ds['id']}/versions",
        headers=admin,
        json={"batch_ids": [a["id"]], "baseline_version_id": v1["id"]},
    )
    assert response.status_code == 422


def test_manifest_lists_every_file(client: TestClient, admin: Headers) -> None:
    s = Setup(client, admin)
    alloc = s.active_allocation()
    files = [
        {"uri": "s3://intake/a/1.jsonl", "format": "jsonl", "record_count": 500},
        {"uri": "s3://intake/a/2.jsonl", "format": "jsonl", "record_count": 500},
    ]
    a = accepted_batch(s, alloc["id"], artifacts=files)
    v1 = version(s, dataset(s)["id"], batch_ids=[a["id"]])
    manifest = client.get(f"/v1/dataset-versions/{v1['id']}/manifest", headers=admin).json()
    assert (manifest["batch_count"], manifest["file_count"]) == (1, 2)
    assert manifest["files"][0]["uri"] == "s3://intake/a/1.jsonl"
    assert manifest["files"][0]["source_kind"] == "human_vendor"
    assert manifest["files"][0]["spec_version_id"] == s.v1


def test_delete_rules(client: TestClient, admin: Headers) -> None:
    s = Setup(client, admin)
    alloc = s.active_allocation()
    a = accepted_batch(s, alloc["id"])
    ds = dataset(s)
    v1 = version(s, ds["id"], batch_ids=[a["id"]])
    v2 = version(s, ds["id"])  # same batches, baseline v1

    assert client.delete(f"/v1/datasets/{ds['id']}", headers=admin).status_code == 409
    baseline = client.delete(f"/v1/dataset-versions/{v1['id']}", headers=admin)
    assert baseline.status_code == 409
    assert v2["id"] in baseline.json()["detail"]
    ev = post_ok(client, "/v1/eval-results", admin, {"dataset_version_id": v2["id"], "value": 0.8})
    assert client.delete(f"/v1/dataset-versions/{v2['id']}", headers=admin).status_code == 409
    assert client.delete(f"/v1/capabilities/{s.capability_id}", headers=admin).status_code == 409

    client.delete(f"/v1/eval-results/{ev['id']}", headers=admin)
    assert client.delete(f"/v1/dataset-versions/{v2['id']}", headers=admin).status_code == 204
    assert client.delete(f"/v1/dataset-versions/{v1['id']}", headers=admin).status_code == 204
    assert client.delete(f"/v1/datasets/{ds['id']}", headers=admin).status_code == 204


def test_eval_result_defaults(client: TestClient, admin: Headers) -> None:
    s = Setup(client, admin)
    a = accepted_batch(s, s.active_allocation()["id"])
    v1 = version(s, dataset(s)["id"], batch_ids=[a["id"]])

    main = post_ok(
        client, "/v1/eval-results", admin, {"dataset_version_id": v1["id"], "value": 0.857}
    )
    assert (main["metric"], main["higher_is_better"]) == ("recall@0.5", True)
    assert main["capability_id"] == s.capability_id

    slice_without_direction = client.post(
        "/v1/eval-results",
        headers=admin,
        json={"dataset_version_id": v1["id"], "metric": "false alarms per image", "value": 0.27},
    )
    assert slice_without_direction.status_code == 422
    slice_ok = post_ok(
        client,
        "/v1/eval-results",
        admin,
        {
            "dataset_version_id": v1["id"],
            "metric": "false alarms per image",
            "value": 0.27,
            "higher_is_better": False,
            "external_run_url": "https://wandb.ai/acme/runs/1",
        },
    )
    assert slice_ok["higher_is_better"] is False
    listed = client.get(f"/v1/eval-results?dataset_version_id={v1['id']}", headers=admin).json()
    assert len(listed["data"]) == 2
