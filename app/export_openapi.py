"""Print the OpenAPI spec as YAML: uv run python -m app.export_openapi > openapi.yaml"""

import sys

import yaml

from app.main import app


def render() -> str:
    return yaml.safe_dump(app.openapi(), sort_keys=False, allow_unicode=True)


if __name__ == "__main__":
    sys.stdout.write(render())
