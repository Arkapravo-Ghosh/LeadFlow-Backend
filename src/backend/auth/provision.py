"""Administrator-only CLI: passwords are entered privately, never CLI arguments."""

import argparse
import sys
from getpass import getpass

from sqlalchemy import select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from backend.auth.models import User
from backend.auth.passwords import hash_password, normalize_username
from backend.db.session import get_engine
from backend.leads.models import Lead


def create_user(
    session: Session, username: str, password: str, *, claim_unowned: bool = False
) -> User:
    username = normalize_username(username)
    if session.scalar(select(User.id).where(User.username == username)):
        raise ValueError("That username is already in use.")
    user = User(username=username, password_hash=hash_password(password))
    session.add(user)
    session.flush()
    if claim_unowned:
        # Migration leaves legacy rows hidden. Never transfer another user's leads.
        session.execute(
            update(Lead).where(Lead.owner_id.is_(None)).values(owner_id=user.id)
        )
    session.commit()
    return user


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a LeadFlow account privately.")
    parser.add_argument(
        "--claim-unowned",
        action="store_true",
        help="Assign legacy unowned leads to this account.",
    )
    args = parser.parse_args()
    if not sys.stdin.isatty():
        raise SystemExit(
            "Use an interactive terminal; passwords must not be piped or passed as arguments."
        )
    username = input("Username: ")
    password = getpass("Password (12–128 characters): ")
    if password != getpass("Confirm password: "):
        raise SystemExit("Passwords did not match; no account created.")
    try:
        with Session(get_engine()) as session:
            create_user(session, username, password, claim_unowned=args.claim_unowned)
    except ValueError as error:
        raise SystemExit(str(error)) from None
    except SQLAlchemyError:
        raise SystemExit(
            "Account creation failed; check database availability and retry."
        ) from None
    print("Account created. Sign in through the frontend.")
