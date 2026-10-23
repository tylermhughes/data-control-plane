"""The docs page should show realistic examples, not placeholder 'string' values."""

from typing import Any

import yaml

from app.export_openapi import render


def test_every_request_body_has_a_realistic_example() -> None:
    spec: dict[str, Any] = yaml.safe_load(render())
    schemas = spec["components"]["schemas"]
    for path, methods in spec["paths"].items():
        for method, op in methods.items():
            content = op.get("requestBody", {}).get("content", {}).get("application/json")
            if not content:
                continue
            name = content["schema"]["$ref"].rsplit("/", 1)[-1]
            examples = schemas[name].get("examples")
            assert examples, f"{method.upper()} {path}: {name} has no example"
            assert "string" not in str(examples), f"{name} example uses placeholder 'string'"
