import yaml

from app.export_openapi import render


def test_exported_spec_is_valid_yaml_with_health_routes() -> None:
    spec = yaml.safe_load(render())
    assert spec["openapi"].startswith("3.")
    assert {"/healthz", "/readyz"} <= set(spec["paths"])
