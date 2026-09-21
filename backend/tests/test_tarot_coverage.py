"""Coverage: all 78 cards x orientations x core contexts resolve curated."""

from __future__ import annotations

import random

from fastapi.testclient import TestClient

from main import app
from tarot.engine import SOURCE_CURATED_DOMAIN, SOURCE_FALLBACK, read_question, draw_cards
from tarot.knowledge import CARDS

CONTEXTS = {
    "education_exam": "How will my exam go?",
    "love_attraction": "Will the girl I like accept me?",
    "career_opportunity": "Should I take this job opportunity?",
    "general_period": "How will my evening go?",
}
ORIENTATIONS = ("upright", "reversed")
CURATED = ("curated_context", "curated_domain")

LEAKS = {
    "education_exam": ("romantic", "marriage", "salary", "promotion", "girlfriend"),
    "love_attraction": ("exam", "salary", "promotion", "interview", "boss"),
    "career_opportunity": ("romantic", "marriage", "girlfriend", "boyfriend"),
    "general_period": ("romantic", "marriage", "salary", "promotion"),
}


def test_deck_is_exactly_78_unique_cards():
    assert len(CARDS) == 78
    assert len({card["name"] for card in CARDS.values()}) == 78


def test_every_card_and_orientation_resolves_in_every_core_context():
    failures = []
    fallbacks = []
    for card_id in sorted(CARDS):
        for orientation in ORIENTATIONS:
            for subcontext, question in CONTEXTS.items():
                result = read_question(question, force=[card_id], orientation=orientation)
                reading = result["readings"][0]
                # A card with nothing to say about this domain is dropped by
                # design (context overrides irrelevant meaning). What must never
                # happen is a generic fallback or off-domain leakage.
                if reading.get("reading") is None:
                    assert reading["source"] in (SOURCE_CURATED_DOMAIN, SOURCE_FALLBACK)
                    continue
                if reading["source"] not in CURATED:
                    fallbacks.append((card_id, orientation, subcontext, reading["source"]))
                text = reading["reading"].lower()
                for banned in LEAKS[subcontext]:
                    if banned in text:
                        failures.append((card_id, orientation, subcontext, banned))
    assert not failures, failures[:10]
    assert not fallbacks, fallbacks[:10]


def test_reversed_orientation_is_respected():
    upright = read_question("How will my exam go?", force=["the_sun"], orientation="upright")
    reversed_ = read_question("How will my exam go?", force=["the_sun"], orientation="reversed")
    assert upright["readings"][0]["orientation"] == "upright"
    assert reversed_["readings"][0]["orientation"] == "reversed"
    assert upright["readings"][0]["reading"] != reversed_["readings"][0]["reading"]


def test_scary_cards_stay_symbolic():
    for card_id in ("death", "the_devil", "the_tower", "ten_of_swords"):
        for question in CONTEXTS.values():
            text = read_question(question, force=[card_id])["readings"][0]["reading"].lower()
            for banned in ("death", "die", "fatal", "disaster", "abuse", "kill"):
                assert banned not in text, (card_id, banned)


# --- 16: the question never controls the draw ----------------------------
def test_question_does_not_control_card_selection():
    first = read_question("How will my exam go?", rng=random.Random(99))
    second = read_question("Will she accept me?", rng=random.Random(99))
    assert [card["card_id"] for card in first["cards"]] == [card["card_id"] for card in second["cards"]]
    assert [card["orientation"] for card in first["cards"]] == [card["orientation"] for card in second["cards"]]
    assert first["final_answer"] != second["final_answer"]


def test_draw_uses_full_deck_without_duplicates():
    rng = random.Random(1234)
    seen = set()
    for _ in range(500):
        cards = draw_cards(rng=rng)
        ids = [card["card_id"] for card in cards]
        assert len(set(ids)) == 3
        seen.update(ids)
    assert len(seen) > 60


def test_orientation_split_is_roughly_even():
    rng = random.Random(5)
    upright = sum(1 for _ in range(2000) for card in draw_cards(rng=rng) if card["orientation"] == "upright")
    ratio = upright / 6000
    assert 0.45 < ratio < 0.55


def test_simulation_reports_no_duplicates():
    from tarot.engine import simulate_draws
    report = simulate_draws(300, rng=random.Random(3))
    assert report["duplicate_spreads"] == 0
    assert report["total_cards"] == 900
    assert report["deck_size"] == 78


# --- public privacy ------------------------------------------------------
def test_public_api_never_exposes_cards():
    client = TestClient(app)
    for question in CONTEXTS.values():
        body = client.post("/api/ask", json={
            "question": question, "timestamp": "2026-09-20T14:15:00+05:30",
            "latitude": 28.6139, "longitude": 77.209,
            "timezone": "Asia/Kolkata", "location_label": "New Delhi"}).json()
        assert set(body) == {"status", "answered", "answer", "conversation_id"}
        blob = str(body).lower()
        for banned in ("card", "tarot", "spread", "upright", "reversed", "arcana",
                       "wands", "cups", "swords", "pentacles"):
            assert banned not in blob, banned


def test_dev_endpoint_returns_the_full_audit():
    client = TestClient(app)
    body = client.post("/api/dev/kavach-tarot", json={
        "question": "How will my exam go?", "force": ["three_of_wands"],
        "orientation": "upright"}).json()
    assert body["context"]["domain"] == "education"
    card = body["cards"][0]
    assert card["card_id"] == "three_of_wands"
    assert card["orientation"] == "upright"
    assert card["core_meaning"] and card["contextual_meaning"]
    assert card["source"] in CURATED
    assert body["model"]["called"] is False
