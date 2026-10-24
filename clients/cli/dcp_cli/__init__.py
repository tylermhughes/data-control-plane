"""dcp: the Data Control Plane command line, built on the generated dcp-client.

    export DCP_URL=http://localhost:8000 DCP_API_KEY=dcp_...
    dcp list                                   # every command
    dcp projects list-projects
    dcp batches list-batches --status failed --limit 10
    dcp projects create-project --body '{"name": "Vision"}'
    dcp batches accept-batch --batch-id bat_... --body-file accept.json

Commands come straight from the API (one per endpoint), so new endpoints appear here
automatically after the client is regenerated. Output is the API's JSON; the exit code is 0
for success and 1 for an error response.
"""

from __future__ import annotations

import argparse
import datetime as dt
import enum
import importlib
import inspect
import json
import os
import pkgutil
import sys
import types
import typing
from collections.abc import Callable
from pathlib import Path
from typing import Any

import dcp_client.api as api_package
from dcp_client import AuthenticatedClient, Client
from dcp_client.types import Unset

HIDDEN = {"client", "body"}


def operations() -> dict[str, dict[str, types.ModuleType]]:
    """{group: {command: module}}, e.g. {"batches": {"list-batches": <module>}}."""
    found: dict[str, dict[str, types.ModuleType]] = {}
    for group in pkgutil.iter_modules(api_package.__path__):
        package = importlib.import_module(f"{api_package.__name__}.{group.name}")
        for op in pkgutil.iter_modules(package.__path__):
            module = importlib.import_module(f"{package.__name__}.{op.name}")
            if hasattr(module, "sync_detailed"):
                commands = found.setdefault(group.name.replace("_", "-"), {})
                commands[op.name.replace("_", "-")] = module
    return found


def _types_of(annotation: Any) -> list[Any]:
    """The useful types in an annotation like `None | str | Unset`."""
    args = typing.get_args(annotation) or (annotation,)
    return [a for a in args if a not in (type(None), Unset)]


def _converter(annotation: Any) -> Callable[[str], Any]:
    for kind in _types_of(annotation):
        if inspect.isclass(kind) and issubclass(kind, enum.Enum):
            return kind
        if kind is bool:
            return lambda v: v.lower() in ("1", "true", "yes")
        if kind is int:
            return int
        if kind is float:
            return float
        if kind is dt.datetime:
            return dt.datetime.fromisoformat
        if kind is dt.date:
            return dt.date.fromisoformat
    return str


def _body_class(hints: dict[str, Any]) -> Any:
    for kind in _types_of(hints.get("body", type(None))):
        if hasattr(kind, "from_dict"):
            return kind
    return None


def _build_command(sub: argparse._SubParsersAction, name: str, module: types.ModuleType) -> None:
    function = module.sync_detailed
    hints = typing.get_type_hints(function)
    doc = (inspect.getdoc(function) or "").split("\n\n")[0]
    parser = sub.add_parser(name, help=doc, description=doc)
    parser.set_defaults(_module=module, _hints=hints)
    for param in inspect.signature(function).parameters.values():
        if param.name in HIDDEN:
            continue
        required = param.default is inspect.Parameter.empty
        parser.add_argument(
            f"--{param.name.replace('_', '-')}",
            dest=param.name,
            type=_converter(hints.get(param.name)),
            required=required,
            help="required" if required else None,
        )
    if _body_class(hints) is not None:
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument("--body", help="Request body as JSON")
        group.add_argument("--body-file", type=Path, help="Request body from a JSON file")


def make_client() -> Client:
    url = os.environ.get("DCP_URL", "http://localhost:8000")
    key = os.environ.get("DCP_API_KEY")
    if key:
        return AuthenticatedClient(base_url=url, token=key, timeout=60)
    return Client(base_url=url, timeout=60)


def main(argv: list[str] | None = None) -> int:
    ops = operations()
    parser = argparse.ArgumentParser(prog="dcp", description=__doc__.split("\n\n")[0])
    groups = parser.add_subparsers(dest="group", metavar="GROUP")
    groups.add_parser("list", help="List every command")
    for group, commands in sorted(ops.items()):
        group_parser = groups.add_parser(group, help=f"{len(commands)} commands")
        sub = group_parser.add_subparsers(dest="command", metavar="COMMAND", required=True)
        for name, module in sorted(commands.items()):
            _build_command(sub, name, module)
    args = parser.parse_args(argv)

    if args.group in (None, "list"):
        for group, commands in sorted(ops.items()):
            print(f"{group}: " + ", ".join(sorted(commands)))
        return 0

    skip = {"group", "command", "body", "body_file"}
    kwargs = {
        k: v
        for k, v in vars(args).items()
        if not k.startswith("_") and k not in skip and v is not None
    }
    body_cls = _body_class(args._hints)
    if body_cls is not None:
        raw = args.body if args.body is not None else args.body_file.read_text()
        kwargs["body"] = body_cls.from_dict(json.loads(raw))

    response = args._module.sync_detailed(client=make_client(), **kwargs)
    content = response.content.decode() if response.content else ""
    try:
        print(json.dumps(json.loads(content), indent=2))
    except ValueError:
        print(content or f"HTTP {int(response.status_code)}")
    return 0 if int(response.status_code) < 400 else 1


if __name__ == "__main__":
    sys.exit(main())
