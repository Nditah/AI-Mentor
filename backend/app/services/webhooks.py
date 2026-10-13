"""Provider webhooks. Each event applies once, and an older event never overwrites a newer one."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models import User
from app.repositories.sql import SqlRepository, aware
from app.services import privacy

STRIPE_EVENTS = {
    "checkout.session.completed",
    "customer.subscription.created",
    "customer.subscription.updated",
    "customer.subscription.deleted",
}


def apply_stripe(session: Session, settings: Settings, event: dict) -> str:
    repo = SqlRepository(session)
    kind = str(event.get("type", ""))
    if not repo.record_webhook("stripe", str(event["id"]), kind):
        return "duplicate"
    if kind not in STRIPE_EVENTS:
        return "ignored"
    data = (event.get("data") or {}).get("object") or {}
    metadata = data.get("metadata") or {}
    clerk_id = metadata.get("clerk_id") or data.get("client_reference_id")
    customer = data.get("customer")
    account = repo.user_by_clerk_id(clerk_id) if clerk_id else None
    if account is None and customer:
        account = session.scalar(select(User).where(User.stripe_customer_id == str(customer)))
    if account is None:
        return "unmatched"
    occurred = datetime.fromtimestamp(int(event["created"]), UTC)
    if account.subscription_event_at and aware(account.subscription_event_at) > occurred:
        return "stale"
    account.subscription_event_at = occurred
    if customer:
        account.stripe_customer_id = str(customer)
    if kind == "checkout.session.completed":
        paid = data.get("payment_status") in {"paid", "no_payment_required"}
        account.subscription_status = "active" if paid else "incomplete"
        account.subscription_tier = _tier(metadata.get("tier"))
    elif kind == "customer.subscription.deleted":
        account.subscription_status = "canceled"
        account.subscription_tier = "free"
    else:
        account.subscription_status = str(data.get("status") or "incomplete")
        account.subscription_tier = _tier_for_price(settings, data) or account.subscription_tier
    return "applied"


def apply_clerk(session: Session, settings: Settings, event_id: str, event: dict) -> str:
    """Profile sync and erasure. Roles never come from Clerk metadata (SEC-02)."""

    repo = SqlRepository(session)
    kind = str(event.get("type", ""))
    if not repo.record_webhook("clerk", event_id, kind):
        return "duplicate"
    data = event.get("data") or {}
    clerk_id = data.get("id")
    if not clerk_id:
        return "ignored"
    if kind in {"user.created", "user.updated"}:
        repo.sync_identity(clerk_id=clerk_id, email=_primary_email(data), display_name=_name(data))
        return "applied"
    if kind == "user.deleted":
        account = repo.user_by_clerk_id(clerk_id)
        if account is None:
            return "applied"
        privacy.erase(session, settings, account, initiated_by="clerk", delete_identity=False)
        return "applied"
    return "ignored"


def _primary_email(data: dict) -> str | None:
    emails = data.get("email_addresses") or []
    primary = data.get("primary_email_address_id")
    for item in emails:
        if item.get("id") == primary:
            return item.get("email_address")
    return emails[0].get("email_address") if emails else None


def _name(data: dict) -> str | None:
    parts = (data.get("first_name"), data.get("last_name"))
    return " ".join(part for part in parts if part) or None


def _tier(value: object) -> str:
    return value if value in {"pro", "research"} else "free"  # type: ignore[return-value]


def _tier_for_price(settings: Settings, subscription: dict) -> str | None:
    items = ((subscription.get("items") or {}).get("data")) or []
    for item in items:
        price = (item.get("price") or {}).get("id")
        if price and price == settings.stripe_price_research:
            return "research"
        if price and price == settings.stripe_price_pro:
            return "pro"
    return None
