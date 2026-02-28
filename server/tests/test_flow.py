import os
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///./test_flow.db")

from app.main import app  # noqa: E402
from app.db.session import SessionLocal, engine, get_db  # noqa: E402
from app.models import Base  # noqa: E402

Base.metadata.create_all(bind=engine)


def override_get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_happy_path_flow():
    now = datetime.now(timezone.utc)

    # 1. Register watch
    resp = client.post("/v1/devices/watch/register", json={"device_id": "watch1", "bind_code": "BIND123"})
    assert resp.status_code == 201

    # 2. Pair phone with watch
    resp = client.post("/v1/binding/pair", json={"phone_device_id": "phone1", "bind_code": "BIND123"})
    assert resp.status_code == 200
    user_id = resp.json()["user_id"]

    # 3. Issue token for phone
    resp = client.post("/v1/auth/token", json={"device_id": "phone1", "device_type": "phone"})
    assert resp.status_code == 200
    token = resp.json()["access_token"]

    # 4. Create timeflow template
    template_payload = {
        "name": "25/5",
        "phases": [
            {"type": "study", "duration_sec": 1500},
            {"type": "break", "duration_sec": 300},
        ],
        "loop": {"mode": "repeat", "repeat": 2, "until_time": None},
    }
    resp = client.post("/v1/timeflows/templates", json=template_payload, headers=auth_headers(token))
    assert resp.status_code == 201
    template_id = resp.json()["id"]

    # 5. Upload focus session (idempotency not tested here)
    focus_payload = {
        "template_snapshot": template_payload,
        "started_at": now.isoformat(),
        "ended_at": (now + timedelta(minutes=30)).isoformat(),
        "ended_reason": "natural",
        "saved_confirmed": True,
    }
    resp = client.post("/v1/focus/sessions", json=focus_payload, headers=auth_headers(token))
    assert resp.status_code == 201
    session_id = resp.json()["session_id"]
    assert session_id

    # 6. Create card (active)
    card_payload = {"front": "front", "back": "back", "tags": ["tag1"], "status": "active"}
    resp = client.post("/v1/cards", json=card_payload, headers=auth_headers(token))
    assert resp.status_code == 201
    card_id = resp.json()["id"]

    # 7. Submit review event done
    event_payload = {
        "card_id": card_id,
        "event_type": "done",
        "occurred_at": now.isoformat(),
        "source": "phone",
    }
    resp = client.post("/v1/reviews/events", json=event_payload, headers=auth_headers(token))
    assert resp.status_code == 201

    # 8. Watch metrics
    resp = client.get("/v1/watch/review/metrics", headers=auth_headers(token))
    assert resp.status_code == 200
    metrics = resp.json()
    assert "today" in metrics

    # 9. Voice draft upload and fetch
    files = {"file": ("sample.wav", b"1234", "audio/wav")}
    resp = client.post("/v1/voice/drafts", files=files, headers=auth_headers(token))
    assert resp.status_code == 201
    draft_id = resp.json()["draft_id"]

    resp = client.get(f"/v1/voice/drafts/{draft_id}", headers=auth_headers(token))
    assert resp.status_code == 200

    # 10. Daily AI summary
    resp = client.post(
        "/v1/ai/summaries/daily",
        json={"date": now.date().isoformat()},
        headers=auth_headers(token),
    )
    assert resp.status_code == 200
    assert resp.json()["summary_id"]

    # 11. Export learning PDF
    resp = client.post("/v1/ai/exports/learning-pdf", headers=auth_headers(token))
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("application/pdf")
    assert resp.content.startswith(b"%PDF")
