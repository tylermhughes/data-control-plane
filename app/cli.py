"""Server-side admin commands. Run inside the api container:

    docker compose exec api python -m app.cli create-admin-key [--name NAME]

Prints the new key to the terminal only (never to the server log).
"""

import argparse
import sys

from sqlalchemy.orm import Session

from app.db import get_engine
from app.schemas.api_keys import ApiKeyCreate
from app.services import api_keys
from app.services.principal import CLI


def create_admin_key(name: str) -> str:
    with Session(get_engine(), expire_on_commit=False) as session:
        key, secret = api_keys.create_key(
            session, CLI, ApiKeyCreate(name=name, role="admin", access="write")
        )
        session.commit()
        return f"{key.id}\n{secret}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.cli", description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    create = commands.add_parser("create-admin-key", help="Create an admin API key.")
    create.add_argument("--name", default="admin", help="A label for the key (default: admin).")
    args = parser.parse_args(argv)

    if args.command == "create-admin-key":
        key_id, secret = create_admin_key(args.name).split("\n")
        print(f"Created admin API key {key_id} ({args.name}).")
        print("Copy it now. It will not be shown again:\n")
        print(f"    {secret}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
