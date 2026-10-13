"""Operations commands. Run as a one-off job, never from the web process.

python -m app.cli migrate              # alembic upgrade head, then seed the catalog
python -m app.cli seed                 # seed the catalog only
python -m app.cli seed-pack            # Knowledge Pack v1.0 (thousands of resources)
python -m app.cli write-pack           # emit seed-data JSON files from the compiler
python -m app.cli grant-admin <clerk_id> --reason "first admin"
python -m app.cli reapply-erasures     # after a database restore
"""

from __future__ import annotations

import argparse
import sys


def migrate() -> None:
    from alembic import command
    from alembic.config import Config

    command.upgrade(Config("alembic.ini"), "head")
    seed()


def seed() -> None:
    from app.core.config import get_settings
    from app.core.database import session_scope
    from app.seed import seed_catalog

    with session_scope() as session:
        seed_catalog(session, demo_accounts=not get_settings().production)


def seed_pack() -> None:
    from app.core.database import session_scope
    from app.seed import seed_catalog
    from app.seed_pack import seed_knowledge_pack

    with session_scope() as session:
        seed_catalog(session, demo_accounts=False)
        counts = seed_knowledge_pack(session)
    print("Knowledge Pack v1.0 seeded:", counts)


def write_pack() -> None:
    from pathlib import Path

    from app.domain.knowledge.seed_files import write_seed_files

    root = Path(__file__).resolve().parents[2] / "seed-data"
    written = write_seed_files(root)
    print(f"Wrote {len(written)} files under {root}")


def grant_admin(clerk_id: str, reason: str) -> int:
    """Bootstrap or recover an admin. Roles never come from identity-provider metadata."""

    from app.core.database import session_scope
    from app.repositories.sql import SqlRepository

    with session_scope() as session:
        repo = SqlRepository(session)
        user = repo.user_by_clerk_id(clerk_id)
        if user is None:
            print(
                f"No user with clerk id {clerk_id}. They must sign in once first.", file=sys.stderr
            )
            return 1
        previous = user.role
        user.role = "admin"
        repo.audit(
            None,
            "user.role",
            "user",
            str(user.id),
            {"from": previous, "to": "admin", "reason": reason[:500], "via": "cli"},
        )
    print(f"{clerk_id} is now an admin.")
    return 0


def reapply_erasures() -> int:
    """Erase again every learner a restored backup brought back (Runbook §11.9)."""

    from sqlalchemy import select

    from app.core.config import get_settings
    from app.core.database import session_scope
    from app.models import AuditEvent, User
    from app.services import privacy

    settings = get_settings()
    with session_scope() as session:
        erased = set(
            session.scalars(
                select(AuditEvent.entity_id).where(AuditEvent.action == "privacy.erasure")
            )
        )
        restored = [
            user for user in session.scalars(select(User)) if privacy.subject_hash(user) in erased
        ]
        for user in restored:
            privacy.erase(session, settings, user, initiated_by="restore", delete_identity=False)
    print(f"Re-erased {len(restored)} restored account(s).")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="app.cli")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("migrate")
    commands.add_parser("seed")
    commands.add_parser("seed-pack")
    commands.add_parser("write-pack")
    grant = commands.add_parser("grant-admin")
    grant.add_argument("clerk_id")
    grant.add_argument("--reason", required=True)
    commands.add_parser("reapply-erasures")
    args = parser.parse_args(argv)
    if args.command == "migrate":
        migrate()
        return 0
    if args.command == "seed":
        seed()
        return 0
    if args.command == "seed-pack":
        seed_pack()
        return 0
    if args.command == "write-pack":
        write_pack()
        return 0
    if args.command == "reapply-erasures":
        return reapply_erasures()
    return grant_admin(args.clerk_id, args.reason)


if __name__ == "__main__":
    raise SystemExit(main())
