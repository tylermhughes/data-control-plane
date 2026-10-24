import yaml

from app.export_openapi import render


def test_exported_spec_is_valid_yaml_with_health_routes() -> None:
    spec = yaml.safe_load(render())
    assert spec["openapi"].startswith("3.")
    assert {"/healthz", "/readyz"} <= set(spec["paths"])


def test_operation_ids_are_unique_and_readable() -> None:
    spec = yaml.safe_load(render())
    ids = [op["operationId"] for ops in spec["paths"].values() for op in ops.values()]
    assert len(ids) == len(set(ids)), "operation ids must be unique (they name client methods)"
    assert all("_v1_" not in i for i in ids)
