"""Ask KAVACH internal Tarot engine: context, relevance, forcing and privacy."""

from __future__ import annotations

import re

from fastapi.testclient import TestClient

from main import app
from question_engine.engine import answer_question
from tarot.engine import read_question
from tarot.knowledge import CARDS

WHEN = "2026-09-20T14:15:00+05:30"
DELHI = (28.6139, 77.2090, "Asia/Kolkata", "New Delhi")
FORCED = ["three_of_wands", "the_star", "ace_of_pentacles"]


def test_seventy_eight_cards():
    suits = {}
    for card in CARDS.values():
        suits[card["suit"]] = suits.get(card["suit"], 0) + 1
    assert len(CARDS) == 78
    assert suits == {"Major": 22, "Wands": 14, "Cups": 14, "Swords": 14, "Pentacles": 14}


# --- 16: the SAME card must read differently per context ------------------
def test_forced_three_of_wands_across_contexts():
    exam = read_question("How will my exam go?", WHEN, force=FORCED)
    love = read_question("Will the girl I like accept me?", WHEN, force=FORCED)
    job = read_question("Should I take this job opportunity?", WHEN, force=FORCED)

    assert exam["context"]["domain"] == "education"
    assert love["context"]["domain"] == "love"
    assert job["context"]["domain"] == "career"

    answers = [exam["answer"], love["answer"], job["answer"]]
    assert len(set(answers)) == 3

    exam_text = exam["answer"].lower()
    assert "preparation" in exam_text and ("exam" in exam_text or "study" in exam_text)
    for banned in ("marriage", "romantic", "boss", "salary"):
        assert banned not in exam_text

    love_text = love["answer"].lower()
    assert "patience" in love_text and "space" in love_text
    for banned in ("exam", "salary", "boss", "preparation"):
        assert banned not in love_text

    job_text = job["answer"].lower()
    assert "opportunity" in job_text and ("grow" in job_text or "future" in job_text or "year" in job_text)
    for banned in ("marriage", "romantic", "exam"):
        assert banned not in job_text
    assert not re.search(r"\bher\b", job_text)


def test_same_card_keeps_its_own_grounding():
    exam = read_question("How will my exam go?", WHEN, force=FORCED)
    love = read_question("Will the girl I like accept me?", WHEN, force=FORCED)
    assert "positive mindset" in exam["answer"]
    assert "room for this to move forward" in love["answer"]


# --- 17: relevance --------------------------------------------------------
def test_evening_question_stays_about_the_period():
    result = read_question("How will my evening go?", WHEN)
    assert result["context"]["domain"] == "general_period"
    lowered = result["answer"].lower()
    for banned in ("marriage", "your boss", "salary", "exam", "partner"):
        assert banned not in lowered
    assert "evening" in lowered


def test_communication_question_has_no_money_or_job_reading():
    result = read_question("How can I improve communication with my friend?", WHEN)
    assert result["context"]["domain"] in ("friendship", "communication")
    lowered = result["answer"].lower()
    for banned in ("salary", "job", "money", "promotion"):
        assert banned not in lowered


def test_study_strategy_question_has_no_romantic_reading():
    result = read_question("Should I change my study strategy?", WHEN)
    assert result["context"]["domain"] == "education"
    lowered = result["answer"].lower()
    for banned in ("romantic", "marriage", "girlfriend", "partner"):
        assert banned not in lowered


def test_reply_question_has_no_career_reading():
    result = read_question("Will she reply?", WHEN)
    assert result["context"]["domain"] == "love"
    lowered = result["answer"].lower()
    for banned in ("boss", "promotion", "salary", "interview"):
        assert banned not in lowered


# --- 14: follow-up keeps the original subject -----------------------------
def test_follow_up_retains_the_previous_subject():
    first = answer_question("Will she reply?", WHEN, *DELHI)
    assert first["tarot"]["context"]["domain"] == "love"
    second = answer_question("Should I wait then?", "2026-09-20T14:16:00+05:30", *DELHI)
    assert second["tarot"]["context"]["domain"] == "love"
    assert "patience" in second["answer"].lower() or "wait" in second["answer"].lower()


# --- 11: cards never appear publicly -------------------------------------
def test_public_ask_returns_only_the_answer():
    client = TestClient(app)
    for question in ("How will my exam go?", "Will she reply?"):
        response = client.post("/api/ask", json={
            "question": question, "timestamp": WHEN, "latitude": 28.6139,
            "longitude": 77.209, "timezone": "Asia/Kolkata", "location_label": "New Delhi"})
        assert response.status_code == 200
        body = response.json()
        assert set(body) == {"status", "answered", "answer", "conversation_id"}
        blob = str(body).lower()
        for banned in ("card", "tarot", "spread", "upright", "reversed", "arcana",
                       "wands", "cups", "swords", "pentacles", "three of"):
            assert banned not in blob, banned


def test_dev_endpoint_exposes_the_audit():
    client = TestClient(app)
    response = client.post("/api/dev/kavach-tarot", json={
        "question": "How will my exam go?", "timestamp": WHEN, "latitude": 28.6139,
        "longitude": 77.209, "timezone": "Asia/Kolkata", "location_label": "New Delhi"})
    assert response.status_code == 200
    body = response.json()
    assert body["context"]["domain"] == "education"
    assert len(body["cards"]) == 3
    assert all(item["position"] for item in body["cards"])
    assert all(item["contextual_meaning"] for item in body["cards"])
    assert body["model"]["called"] is False
    assert body["private_context"]


def test_no_guaranteed_outcomes_in_tarot_answers():
    for question in ("How will my exam go?", "Will she accept me?", "Should I take this job?"):
        answer = read_question(question, WHEN)["answer"].lower()
        for banned in ("definitely", "100%", "certainly will", "guaranteed", "will happen"):
            assert banned not in answer
