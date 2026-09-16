"""Backend tests for jhax.ai co-pilot API"""
import os
import json
import time
import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL')
if not BASE_URL:
    # fallback read from frontend .env
    with open('/app/frontend/.env') as f:
        for line in f:
            if line.startswith('REACT_APP_BACKEND_URL='):
                BASE_URL = line.split('=', 1)[1].strip()
                break
BASE_URL = BASE_URL.rstrip('/')
API = f"{BASE_URL}/api"


@pytest.fixture(scope="session")
def restaurant_id():
    """Research a restaurant once and reuse."""
    payload = {"name": "TEST_Smoked Barrel", "location": "Austin, TX", "cuisine": "BBQ"}
    r = requests.post(f"{API}/restaurants/research", json=payload, timeout=120)
    assert r.status_code == 200, f"research failed: {r.status_code} {r.text[:400]}"
    data = r.json()
    assert data.get("id")
    return data["id"], data


# ---- Health ----
def test_root():
    r = requests.get(f"{API}/", timeout=10)
    assert r.status_code == 200
    assert "jhax" in r.json().get("message", "").lower()


# ---- Research ----
def test_research_shape(restaurant_id):
    rid, data = restaurant_id
    assert data["name"].startswith("TEST_")
    assert data.get("cuisine")
    assert data.get("price_tier")
    assert isinstance(data.get("competitors"), list) and len(data["competitors"]) >= 2
    assert isinstance(data.get("review_themes"), list) and len(data["review_themes"]) >= 3
    assert isinstance(data.get("local_context"), list) and len(data["local_context"]) >= 2
    assert data.get("menu_data") is not None
    assert data.get("positioning")


# ---- List / Get ----
def test_list_restaurants(restaurant_id):
    rid, _ = restaurant_id
    r = requests.get(f"{API}/restaurants", timeout=15)
    assert r.status_code == 200
    ids = [x["id"] for x in r.json()]
    assert rid in ids


def test_get_restaurant(restaurant_id):
    rid, _ = restaurant_id
    r = requests.get(f"{API}/restaurants/{rid}", timeout=15)
    assert r.status_code == 200
    body = r.json()
    assert "restaurant" in body and "messages" in body
    assert body["restaurant"]["id"] == rid


def test_get_restaurant_404():
    r = requests.get(f"{API}/restaurants/does-not-exist", timeout=10)
    assert r.status_code == 404


# ---- SSE helpers ----
def read_sse(resp, max_events=500):
    events = []
    for line in resp.iter_lines(decode_unicode=True):
        if not line:
            continue
        if line.startswith("data: "):
            payload = line[6:]
            try:
                ev = json.loads(payload)
            except json.JSONDecodeError:
                continue
            events.append(ev)
            if ev.get("type") == "done" or len(events) >= max_events:
                break
    return events


# ---- Snapshot stream ----
def test_snapshot_stream(restaurant_id):
    rid, _ = restaurant_id
    with requests.post(f"{API}/restaurants/{rid}/snapshot/stream", json={},
                       stream=True, timeout=120) as resp:
        assert resp.status_code == 200
        events = read_sse(resp)
    types = [e["type"] for e in events]
    assert "delta" in types, f"no delta events: {types[:5]}"
    assert types[-1] == "done"
    content = "".join(e.get("content", "") for e in events if e["type"] == "delta")
    assert len(content) > 50

    # verify persisted as snapshot
    r = requests.get(f"{API}/restaurants/{rid}", timeout=15)
    msgs = r.json()["messages"]
    snaps = [m for m in msgs if m.get("is_snapshot")]
    assert len(snaps) >= 1
    assert snaps[-1]["role"] == "assistant"


# ---- Chat stream + continuity ----
def test_chat_stream_and_continuity(restaurant_id):
    rid, _ = restaurant_id
    # first turn
    with requests.post(f"{API}/restaurants/{rid}/chat/stream",
                       json={"message": "Remember the number 4271. Reply with just 'ok'."},
                       stream=True, timeout=120) as resp:
        assert resp.status_code == 200
        events = read_sse(resp)
    assert events[-1]["type"] == "done"
    first_reply = "".join(e.get("content", "") for e in events if e["type"] == "delta")
    assert len(first_reply) > 0

    # follow-up references prior context
    with requests.post(f"{API}/restaurants/{rid}/chat/stream",
                       json={"message": "What number did I ask you to remember? Reply with just the digits."},
                       stream=True, timeout=120) as resp:
        assert resp.status_code == 200
        events2 = read_sse(resp)
    second_reply = "".join(e.get("content", "") for e in events2 if e["type"] == "delta")
    assert "4271" in second_reply, f"no continuity, got: {second_reply[:200]}"

    # verify messages persisted (both user and assistant)
    r = requests.get(f"{API}/restaurants/{rid}", timeout=15)
    msgs = r.json()["messages"]
    roles = [m["role"] for m in msgs]
    assert roles.count("user") >= 2
    assert roles.count("assistant") >= 3  # snapshot + 2 chat replies


# ---- Bug fix: chat stream with web_search tool (no reasoning_effort error) ----
def _existing_or_new_rid():
    r = requests.get(f"{API}/restaurants", timeout=15)
    if r.status_code == 200 and r.json():
        return r.json()[0]["id"]
    return None


REFUSAL_PHRASES = [
    "don't have",
    "do not have",
    "not in the loaded data",
    "won't guess",
    "will not guess",
]


def _assert_no_refusal(content: str, msg: str):
    low = content.lower()
    hits = [p for p in REFUSAL_PHRASES if p in low]
    assert not hits, f"[{msg}] refusal phrases found {hits} in: {content[:400]}"


@pytest.mark.parametrize("question,label", [
    ("what my business hours", "hours"),
    ("whats my address and phone", "address_phone"),
    ("how am I rated", "rating"),
])
def test_chat_stream_terse_factuals_trigger_web_search(question, label):
    """BUG FIX (v3): terse factual asks about the restaurant's OWN details must
    trigger web_search BEFORE any refusal, and return real facts."""
    rid = _existing_or_new_rid()
    if not rid:
        pytest.skip("no existing restaurant to reuse")

    with requests.post(f"{API}/restaurants/{rid}/chat/stream",
                       json={"message": question},
                       stream=True, timeout=240) as resp:
        assert resp.status_code == 200
        events = read_sse(resp, max_events=3000)

    types = [e["type"] for e in events]
    assert "error" not in types, f"[{label}] error events: {[e for e in events if e['type']=='error']}"
    assert types and types[-1] == "done", f"[{label}] did not end with done: {types[-5:]}"
    tool_evs = [e for e in events if e["type"] == "tool"]
    assert any(e.get("name") == "web_search" for e in tool_evs), \
        f"[{label}] no web_search tool event; got {tool_evs}"

    content = "".join(e.get("content", "") for e in events if e["type"] == "delta")
    assert len(content) > 60, f"[{label}] content too short: {content!r}"
    _assert_no_refusal(content, label)


def test_chat_stream_creative_ask_no_error():
    """Regression: creative ask streams a normal answer, no error events.
    web_search may or may not be called — both acceptable."""
    rid = _existing_or_new_rid()
    if not rid:
        pytest.skip("no existing restaurant to reuse")

    with requests.post(f"{API}/restaurants/{rid}/chat/stream",
                       json={"message": "draft me a short instagram caption for tonight"},
                       stream=True, timeout=180) as resp:
        assert resp.status_code == 200
        events = read_sse(resp, max_events=2000)

    types = [e["type"] for e in events]
    assert "error" not in types, f"error events: {[e for e in events if e['type']=='error']}"
    assert types[-1] == "done"
    content = "".join(e.get("content", "") for e in events if e["type"] == "delta")
    assert len(content) > 20, f"creative content too short: {content!r}"


def test_chat_stream_competitors_depth():
    """BUG FIX 2: competitor query must trigger web_search and mention multiple real names."""
    rid = _existing_or_new_rid()
    if not rid:
        pytest.skip("no existing restaurant to reuse")

    with requests.post(f"{API}/restaurants/{rid}/chat/stream",
                       json={"message": "Who are my nearby burger competitors? Search the web and list real named businesses."},
                       stream=True, timeout=180) as resp:
        assert resp.status_code == 200
        events = read_sse(resp, max_events=2000)

    types = [e["type"] for e in events]
    assert "error" not in types
    assert "tool" in types, f"expected web_search tool event; got {set(types)}"
    content = "".join(e.get("content", "") for e in events if e["type"] == "delta")
    assert len(content) > 200


def test_chat_stream_sources_event_shape():
    """NEW FEATURE 1: competitor question emits {type:sources, items:[{title,url},...]}."""
    rid = _existing_or_new_rid()
    if not rid:
        pytest.skip("no existing restaurant to reuse")

    with requests.post(f"{API}/restaurants/{rid}/chat/stream",
                       json={"message": "who are my nearby competitors?"},
                       stream=True, timeout=240) as resp:
        assert resp.status_code == 200
        events = read_sse(resp, max_events=3000)

    src_evs = [e for e in events if e.get("type") == "sources"]
    assert src_evs, f"no sources event in stream; types={[e['type'] for e in events]}"
    all_items = []
    for ev in src_evs:
        items = ev.get("items") or []
        assert isinstance(items, list), f"items not list: {items}"
        all_items.extend(items)
    assert all_items, "sources event(s) had no items"
    for it in all_items:
        assert isinstance(it, dict), f"item not object: {it!r}"
        assert "title" in it and "url" in it, f"item missing title/url: {it}"
        assert isinstance(it["title"], str) and isinstance(it["url"], str)
        assert it["url"].startswith("http"), f"bad url: {it['url']}"


def test_research_returns_4plus_competitors(restaurant_id):
    """Research endpoint returns >=4 real named competitors."""
    _, data = restaurant_id
    comps = data.get("competitors") or []
    assert len(comps) >= 4, f"only {len(comps)} competitors: {[c.get('name') for c in comps]}"
    names = [c.get("name", "") for c in comps]
    assert all(len(n) > 1 for n in names)


# ---- Delete ----
def test_delete_restaurant(restaurant_id):
    rid, _ = restaurant_id
    r = requests.delete(f"{API}/restaurants/{rid}", timeout=15)
    assert r.status_code == 200
    r2 = requests.get(f"{API}/restaurants/{rid}", timeout=10)
    assert r2.status_code == 404
