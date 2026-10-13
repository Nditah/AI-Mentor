"""Access control, XP integrity, webhooks, erasure, and redirect checks (TestPlan §2.6)."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import re
import time
import uuid
from contextlib import contextmanager
from datetime import UTC, datetime

import pytest

from app.api.deps import settings_dep
from app.core.config import get_settings
from app.core.database import session_scope
from app.models import Conversation, User, XpEvent
from app.repositories.sql import SqlRepository

STAFF = {"X-Dev-User-Id": "demo-admin"}
CLERK_SECRET = "whsec_" + base64.b64encode(b"clerk-test-secret-0123456789").decode()
STRIPE_SECRET = "whsec_stripe_test"


@contextmanager
def settings(client, **changes):
    patched = get_settings().model_copy(update=changes)
    client.app.dependency_overrides[settings_dep] = lambda: patched
    try:
        yield patched
    finally:
        client.app.dependency_overrides.pop(settings_dep, None)


def _user(clerk_id: str) -> User:
    with session_scope() as session:
        user = SqlRepository(session).user_by_clerk_id(clerk_id)
        assert user is not None
        session.expunge(user)
        return user


def _quiz(client, headers) -> dict:
    created = client.post(
        "/api/v1/quiz/generate",
        headers=headers,
        json={"concept_slug": "agent-environment", "difficulty": "beginner"},
    )
    assert created.status_code == 200
    return created.json()


def test_errors_are_problem_details(student) -> None:
    client, headers = student
    missing = client.get(f"/api/v1/conversations/{uuid.uuid4()}", headers=headers)
    assert missing.status_code == 404
    assert missing.headers["content-type"].startswith("application/problem+json")
    body = missing.json()
    assert {"type", "title", "status", "detail", "instance", "trace_id"} <= set(body)
    assert body["status"] == 404
    invalid = client.post("/api/v1/chat", headers=headers, json={"message": ""})
    assert invalid.status_code == 422
    assert invalid.json()["errors"][0]["path"].endswith("message")


def test_security_headers(client) -> None:
    response = client.get("/health")
    assert response.headers["content-security-policy"].startswith("default-src 'none'")
    assert response.headers["x-frame-options"] == "DENY"
    assert re.fullmatch(r"[0-9a-f]{32}", response.headers["x-request-id"])


def test_learner_cannot_reach_another_learners_records(client) -> None:
    owner = {"X-Dev-User-Id": f"owner-{uuid.uuid4().hex[:8]}"}
    other = {"X-Dev-User-Id": f"other-{uuid.uuid4().hex[:8]}"}
    chat = client.post("/api/v1/chat", headers=owner, json={"message": "Teach me MDPs"}).json()
    upload = client.post(
        "/api/v1/research/documents",
        headers=owner,
        files={"file": ("a.md", b"Private notes about reward shaping.", "text/markdown")},
    ).json()
    quiz = _quiz(client, owner)
    client.post("/api/v1/flashcards/generate", headers=owner, json={"concept_slug": "bellman"})
    card = client.get("/api/v1/flashcards/due", headers=owner).json()[0]

    assert (
        client.get(f"/api/v1/conversations/{chat['conversation_id']}", headers=other).status_code
        == 404
    )
    follow_up = client.post(
        "/api/v1/chat",
        headers=other,
        json={"message": "continue", "conversation_id": chat["conversation_id"]},
    )
    assert follow_up.status_code == 404
    analysis = client.post(
        "/api/v1/research/analyze",
        headers=other,
        json={"document_id": upload["id"], "question": "What is in it?"},
    )
    assert analysis.status_code == 404
    answer = {"question_id": quiz["questions"][0]["id"], "response": "B"}
    graded = client.post(
        f"/api/v1/quiz/{quiz['id']}/grade", headers=other, json={"answers": [answer]}
    )
    assert graded.status_code == 404
    review = client.post(
        f"/api/v1/flashcards/{card['id']}/review", headers=other, json={"rating": 5}
    )
    assert review.status_code == 404


def test_every_admin_route_refuses_a_student(client, student) -> None:
    _client, headers = student
    routes = [
        (method.upper(), path)
        for path, operations in client.app.openapi()["paths"].items()
        if path.startswith("/api/v1/admin")
        for method in operations
    ]
    assert len(routes) >= 15
    for method, path in routes:
        url = re.sub(r"\{[^}]+\}", str(uuid.uuid4()), path)
        response = client.request(method, url, headers=headers, json={})
        assert response.status_code == 403, (method, path, response.status_code)


def test_quiz_is_submitted_once_and_earns_xp_once(student) -> None:
    client, headers = student
    quiz = _quiz(client, headers)
    answers = {"answers": [{"question_id": quiz["questions"][0]["id"], "response": "B"}]}
    first = client.post(f"/api/v1/quiz/{quiz['id']}/grade", headers=headers, json=answers)
    assert first.status_code == 200
    xp = client.get("/api/v1/me", headers=headers).json()["xp"]
    again = client.post(f"/api/v1/quiz/{quiz['id']}/grade", headers=headers, json=answers)
    assert again.status_code == 409
    assert client.get("/api/v1/me", headers=headers).json()["xp"] == xp


def test_lesson_and_analysis_xp_follow_the_table(student) -> None:
    client, headers = student
    first = client.post("/api/v1/progress/lessons/agent-environment/complete", headers=headers)
    assert first.status_code == 200
    client.post("/api/v1/progress/lessons/agent-environment/complete", headers=headers)
    assert client.get("/api/v1/me", headers=headers).json()["xp"] == 40

    document = client.post(
        "/api/v1/research/documents",
        headers=headers,
        files={"file": ("n.md", b"Policy gradients estimate the gradient.", "text/markdown")},
    ).json()
    for _ in range(3):
        client.post(
            "/api/v1/research/analyze",
            headers=headers,
            json={"document_id": document["id"], "question": "What is estimated?"},
        )
    assert client.get("/api/v1/me", headers=headers).json()["xp"] == 50


def test_chat_counts_for_the_streak_only(student) -> None:
    client, headers = student
    client.post("/api/v1/chat", headers=headers, json={"message": "Teach me Q-learning"})
    me = client.get("/api/v1/me", headers=headers).json()
    assert me["xp"] == 0
    assert me["streak_days"] == 1


def test_xp_ledger_rejects_a_duplicate_source(student) -> None:
    client, headers = student
    client.get("/api/v1/me", headers=headers)
    user = _user(headers["X-Dev-User-Id"])
    with session_scope() as session:
        repo = SqlRepository(session)
        kwargs = dict(
            user_id=user.id,
            source_type="lesson",
            source_id="same",
            requested=40,
            granted=40,
            local_date=datetime.now(UTC).date(),
        )
        assert repo.add_xp_event(**kwargs) is True
        assert repo.add_xp_event(**kwargs) is False
        assert session.query(XpEvent).filter_by(user_id=user.id).count() == 1


def test_lab_is_closed_when_disabled(student) -> None:
    client, headers = student
    with settings(client, lab_enabled=False):
        response = client.post("/api/v1/lab/run", headers=headers, json={"code": "print(1)"})
        assert response.status_code == 503
        quiz = client.post(
            "/api/v1/quiz/generate",
            headers=headers,
            json={"concept_slug": "q-learning", "difficulty": "intermediate"},
        )
        if quiz.status_code == 200:
            assert all(item["kind"] != "coding" for item in quiz.json()["questions"])


@pytest.mark.parametrize(
    "url",
    [
        "http://localhost:3000.evil.example/pay",
        "http://localhost:3000@evil.example/pay",
        "https://localhost:3000/pay",
        "javascript:alert(1)",
        "//evil.example/",
    ],
)
def test_billing_return_url_must_match_an_origin_exactly(student, url) -> None:
    client, headers = student
    response = client.post(
        "/api/v1/billing/checkout",
        headers=headers,
        json={"tier": "pro", "success_url": url, "cancel_url": "http://localhost:3000/"},
    )
    assert response.status_code == 400


def test_admin_cannot_change_their_own_role(client) -> None:
    me = client.get("/api/v1/me", headers=STAFF).json()
    response = client.patch(
        f"/api/v1/admin/users/{me['id']}", headers=STAFF, json={"role": "student"}
    )
    assert response.status_code == 409


def test_role_changes_are_audited(client, student) -> None:
    _client, headers = student
    target = client.get("/api/v1/me", headers=headers).json()
    changed = client.patch(
        f"/api/v1/admin/users/{target['id']}",
        headers=STAFF,
        json={"role": "instructor", "reason": "Course author"},
    )
    assert changed.status_code == 200
    audit = client.get("/api/v1/admin/audit", headers=STAFF).json()
    entry = next(item for item in audit if item["entity_id"] == target["id"])
    assert entry["detail"]["from"] == "student"
    assert entry["detail"]["to"] == "instructor"


def test_leaderboard_is_pseudonymous_and_learners_only(client, student) -> None:
    _client, headers = student
    client.post("/api/v1/progress/lessons/agent-environment/complete", headers=headers)
    client.post("/api/v1/progress/lessons/agent-environment/complete", headers=STAFF)
    board = client.get("/api/v1/leaderboard").json()
    names = {item["display_name"] for item in board}
    assert all(name.startswith("Learner-") or re.fullmatch(r"\w{3,24}", name) for name in names)
    staff = client.get("/api/v1/me", headers=STAFF).json()
    assert staff["display_name"] not in names

    client.patch("/api/v1/me", headers=headers, json={"handle": f"h{uuid.uuid4().hex[:8]}"})
    mine = client.get("/api/v1/me", headers=headers).json()
    assert (
        mine["handle"]
        in {item["display_name"] for item in client.get("/api/v1/leaderboard").json()}
        or len(board) >= 10
    )
    client.patch("/api/v1/me", headers=headers, json={"leaderboard_opt_out": True})
    after = {item["display_name"] for item in client.get("/api/v1/leaderboard").json()}
    assert mine["handle"] not in after


def test_profile_validation(student) -> None:
    client, headers = student
    assert (
        client.patch("/api/v1/me", headers=headers, json={"timezone": "Mars/Base"}).status_code
        == 422
    )
    assert client.patch("/api/v1/me", headers=headers, json={"locale": "de"}).status_code == 422
    ok = client.patch(
        "/api/v1/me", headers=headers, json={"timezone": "Africa/Lagos", "country_code": "NG"}
    )
    assert ok.status_code == 200
    assert ok.json()["timezone"] == "Africa/Lagos"
    handle = f"taken{uuid.uuid4().hex[:6]}"
    assert client.patch("/api/v1/me", headers=headers, json={"handle": handle}).status_code == 200
    other = {"X-Dev-User-Id": f"user-{uuid.uuid4().hex[:12]}"}
    assert (
        client.patch("/api/v1/me", headers=other, json={"handle": handle.upper()}).status_code
        == 409
    )


def test_export_and_self_service_erasure(student) -> None:
    client, headers = student
    client.post("/api/v1/chat", headers=headers, json={"message": "Teach me MDPs"})
    client.post(
        "/api/v1/research/documents",
        headers=headers,
        files={"file": ("p.md", b"Private paper notes on value iteration.", "text/markdown")},
    )
    exported = client.get("/api/v1/me/export", headers=headers).json()
    assert exported["conversations"][0]["messages"]
    assert exported["documents"]
    user_id = uuid.UUID(exported["profile"]["id"])

    assert client.delete("/api/v1/me", headers=headers).status_code == 204
    with session_scope() as session:
        assert session.get(User, user_id) is None
        assert session.query(Conversation).filter_by(user_id=user_id).count() == 0
    audit = client.get("/api/v1/admin/audit", headers=STAFF).json()
    digest = hashlib.sha256(user_id.bytes).hexdigest()
    assert any(
        item["action"] == "privacy.erasure" and item["entity_id"] == digest for item in audit
    )

    from app.cli import reapply_erasures

    with session_scope() as session:
        session.add(User(id=user_id, clerk_id=headers["X-Dev-User-Id"], email="", display_name="R"))
    assert reapply_erasures() == 0
    with session_scope() as session:
        assert session.get(User, user_id) is None


def _clerk_post(client, event: dict, event_id: str):
    from svix.webhooks import Webhook

    payload = json.dumps(event)
    stamp = datetime.now(UTC)
    signature = Webhook(CLERK_SECRET).sign(event_id, stamp, payload)
    return client.post(
        "/api/v1/webhooks/clerk",
        content=payload,
        headers={
            "svix-id": event_id,
            "svix-timestamp": str(int(stamp.timestamp())),
            "svix-signature": signature,
            "content-type": "application/json",
        },
    )


def test_clerk_webhook_ignores_role_metadata_and_erases_on_delete(client) -> None:
    clerk_id = f"user_{uuid.uuid4().hex[:10]}"
    created = {
        "type": "user.created",
        "data": {
            "id": clerk_id,
            "first_name": "Ada",
            "email_addresses": [{"id": "e1", "email_address": f"{clerk_id}@example.test"}],
            "primary_email_address_id": "e1",
            "public_metadata": {"role": "admin"},
        },
    }
    with settings(client, clerk_webhook_secret=CLERK_SECRET):
        assert _clerk_post(client, created, "msg_1" + clerk_id).status_code == 200
        replay = _clerk_post(client, created, "msg_1" + clerk_id)
        assert replay.json()["outcome"] == "duplicate"
        assert _user(clerk_id).role == "student"

        forged = client.post(
            "/api/v1/webhooks/clerk",
            content=json.dumps(created),
            headers={"svix-id": "x", "svix-timestamp": "1", "svix-signature": "v1,bad"},
        )
        assert forged.status_code == 400

        deleted = {"type": "user.deleted", "data": {"id": clerk_id, "deleted": True}}
        assert _clerk_post(client, deleted, "msg_2" + clerk_id).status_code == 200
    with session_scope() as session:
        assert SqlRepository(session).user_by_clerk_id(clerk_id) is None


def _stripe_post(client, event: dict):
    payload = json.dumps(event)
    stamp = int(time.time())
    digest = hmac.new(
        STRIPE_SECRET.encode(), f"{stamp}.{payload}".encode(), hashlib.sha256
    ).hexdigest()
    return client.post(
        "/api/v1/webhooks/stripe",
        content=payload,
        headers={"stripe-signature": f"t={stamp},v1={digest}", "content-type": "application/json"},
    )


def test_stripe_webhook_is_idempotent_and_ordered(student) -> None:
    client, headers = student
    clerk_id = headers["X-Dev-User-Id"]
    client.get("/api/v1/me", headers=headers)
    now = int(time.time())

    def event(event_id: str, kind: str, created: int, status: str) -> dict:
        return {
            "id": event_id,
            "object": "event",
            "type": kind,
            "created": created,
            "data": {
                "object": {
                    "object": "subscription",
                    "customer": f"cus_{clerk_id}",
                    "status": status,
                    "metadata": {"clerk_id": clerk_id},
                    "items": {"data": [{"price": {"id": "price_research"}}]},
                }
            },
        }

    with settings(
        client,
        stripe_secret_key="sk_test_x",
        stripe_webhook_secret=STRIPE_SECRET,
        stripe_price_research="price_research",
    ):
        newer = event(f"evt_new_{clerk_id}", "customer.subscription.updated", now, "active")
        older = event(f"evt_old_{clerk_id}", "customer.subscription.updated", now - 60, "past_due")
        assert _stripe_post(client, newer).json()["outcome"] == "applied"
        assert _stripe_post(client, newer).json()["outcome"] == "duplicate"
        assert _stripe_post(client, older).json()["outcome"] == "stale"
        bad = client.post(
            "/api/v1/webhooks/stripe",
            content=json.dumps(newer),
            headers={"stripe-signature": f"t={now},v1=deadbeef"},
        )
        assert bad.status_code == 400
    user = _user(clerk_id)
    assert user.subscription_status == "active"
    assert user.subscription_tier == "research"


def test_request_context_is_transaction_local() -> None:
    from sqlalchemy import text

    from app.core.database import bind_request_context

    with session_scope() as session:
        bind_request_context(session, current_user_id="00000000-0000-0000-0000-000000000001")
        if session.get_bind().dialect.name != "postgresql":
            return
        value = session.execute(text("SELECT current_setting('app.current_user_id', true)"))
        assert value.scalar() == "00000000-0000-0000-0000-000000000001"
        session.commit()
        after = session.execute(text("SELECT current_setting('app.current_user_id', true)"))
        assert after.scalar() in ("", None)
