"""API fuzz testing with Schemathesis: generated requests for every operation in the spec.

Each operation gets a handful of generated requests (valid and invalid). The checks fail on
any server error (5xx) and on responses that don't match openapi.yaml: undocumented status
codes, wrong content types, or bodies that don't fit the documented schema.
"""

from typing import Any

import schemathesis
from hypothesis import HealthCheck, settings
from schemathesis.specs.openapi.checks import negative_data_rejection

from app.main import app
from tests.conftest import MakeKey

schema = schemathesis.openapi.from_asgi("/openapi.json", app)

FUZZ_SETTINGS = settings(
    max_examples=15,
    deadline=None,
    suppress_health_check=[
        HealthCheck.function_scoped_fixture,
        HealthCheck.too_slow,
        HealthCheck.filter_too_much,
    ],
)


@schema.parametrize()
@FUZZ_SETTINGS
def test_api_conforms_to_its_spec(case: Any, make_key: MakeKey) -> None:
    headers = case.headers or {}
    if "Authorization" not in headers:
        headers = {**headers, **make_key()}
    # negative_data_rejection is off on purpose: DCP ignores unknown query parameters (so older
    # and newer scripts keep working), which that check treats as invalid input. Request
    # bodies are validated strictly (extra fields refused) and covered by the API tests.
    case.call_and_validate(headers=headers, excluded_checks=[negative_data_rejection])
