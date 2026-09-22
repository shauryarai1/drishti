"""Regression tests for the three reported production bugs.

  BUG 1  Ask KAVACH latency cascade (NVIDIA hangs -> Gemini fallback unbounded)
  BUG 2  Current Hora showed the first morning Hora instead of the live one
  BUG 3  Daily Moon anchor / timezone

Deterministic: provider HTTP is mocked, "now" is frozen, no live quota used.
"""

from __future__ import annotations

import json
import pathlib
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import httpx
import pytest
from fastapi.testclient import TestClient

import chat.gemini as gemini
import chat.nvidia as nvidia
import main
from panchang import PanchangRequest, compute_panchang
from panchang import engine as panchang_engine

IST = ZoneInfo("Asia/Kolkata")
DELHI = dict(latitude=28.6139, longitude=77.209, timezone_name="Asia/Kolkata", label="Delhi")
RASHIS = ("Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
          "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces")


@pytest.fixture()
def frozen_now(monkeypatch):
    """Freeze the engine's live clock (single source of 'now')."""
    def freeze(moment: datetime):
        monkeypatch.setattr(panchang_engine, "_now", lambda tz: moment.astimezone(tz))
    return freeze


def _panchang(on_date: date):
    return compute_panchang(PanchangRequest(on_date=on_date, **DELHI))


# ============================ BUG 2: current Hora ============================
def test_current_hora_is_not_always_the_first_hora(frozen_now):
    frozen_now(datetime(2026, 9, 22, 11, 45, tzinfo=IST))
    hora = _panchang(date(2026, 9, 22))["hora"]
    current, first = hora["current"], hora["day"][0]

    assert current is not None
    assert current["start"] != first["start"], "midday must not report the sunrise Hora"
    # the reported interval genuinely contains the live local time
    start = datetime.fromisoformat(current["start"])
    end = datetime.fromisoformat(current["end"])
    assert start <= datetime(2026, 9, 22, 11, 45, tzinfo=IST) < end
    assert hora["current_is_live"] is True


@pytest.mark.parametrize("hour,minute", [(6, 0), (9, 30), (14, 0), (18, 0), (23, 30)])
def test_current_hora_tracks_the_local_clock(frozen_now, hour, minute):
    moment = datetime(2026, 9, 22, hour, minute, tzinfo=IST)
    frozen_now(moment)
    hora = _panchang(date(2026, 9, 22))["hora"]
    current = hora["current"]

    assert current is not None, f"no current Hora at {hour:02d}:{minute:02d}"
    start = datetime.fromisoformat(current["start"])
    end = datetime.fromisoformat(current["end"])
    assert start <= moment < end
    expected_part = "day" if 6 <= hour < 19 else "night"
    assert current["part"] in ("day", "night")
    if hour in (9, 14):
        assert current["part"] == "day"
    if hour == 23:
        assert current["part"] == "night"
    assert expected_part in ("day", "night")


def test_current_hora_at_exact_sunrise_is_the_first_hora(frozen_now):
    sunrise = datetime.fromisoformat(_panchang(date(2026, 9, 22))["sun_moon"]["sunrise"])
    frozen_now(sunrise)
    hora = _panchang(date(2026, 9, 22))["hora"]
    current, first = hora["current"], hora["day"][0]

    assert current["start"] == first["start"], "sunrise belongs to the first Hora (inclusive start)"
    assert current["planet"] == first["planet"]


def test_current_hora_at_an_exact_boundary_moves_to_the_next_slab(frozen_now):
    base = _panchang(date(2026, 9, 22))["hora"]
    boundary = datetime.fromisoformat(base["day"][3]["end"])  # end of the 4th Hora
    frozen_now(boundary)
    hora = _panchang(date(2026, 9, 22))["hora"]
    current = hora["current"]

    assert datetime.fromisoformat(current["start"]) == boundary, "an exact boundary starts the next Hora"
    assert current["planet"] == base["day"][4]["planet"]


def test_current_hora_just_before_sunset_is_still_a_day_hora(frozen_now):
    pan = _panchang(date(2026, 9, 22))
    sunset = datetime.fromisoformat(pan["sun_moon"]["sunset"])
    frozen_now(sunset - timedelta(seconds=1))
    hora = _panchang(date(2026, 9, 22))["hora"]

    assert hora["current"]["part"] == "day"
    assert hora["current"]["end"] == pan["sun_moon"]["sunset"]


def test_current_hora_at_sunset_is_the_first_night_hora(frozen_now):
    pan = _panchang(date(2026, 9, 22))
    sunset = datetime.fromisoformat(pan["sun_moon"]["sunset"])
    frozen_now(sunset)
    hora = _panchang(date(2026, 9, 22))["hora"]

    assert hora["current"]["part"] == "night"
    assert hora["current"]["start"] == pan["sun_moon"]["sunset"]


def test_night_hora_interval_crosses_midnight(frozen_now):
    """23:xx -> 00:xx must be one interval ending on the NEXT calendar day."""
    frozen_now(datetime(2026, 9, 21, 23, 30, tzinfo=IST))
    hora = _panchang(date(2026, 9, 21))["hora"]
    current = hora["current"]
    start = datetime.fromisoformat(current["start"])
    end = datetime.fromisoformat(current["end"])

    assert current["part"] == "night"
    assert end.date() > start.date(), "a late-night Hora must end on the following day"
    assert start <= datetime(2026, 9, 21, 23, 30, tzinfo=IST) < end


def test_after_midnight_before_sunrise_uses_the_previous_panchang_day(frozen_now):
    """00:xx belongs to the night Hora that began the previous evening."""
    frozen_now(datetime(2026, 9, 22, 0, 30, tzinfo=IST))
    pan = _panchang(date(2026, 9, 22))
    current = pan["hora"]["current"]
    sunrise = datetime.fromisoformat(pan["sun_moon"]["sunrise"])

    assert current is not None, "the Hora in progress after midnight must be reported"
    start = datetime.fromisoformat(current["start"])
    end = datetime.fromisoformat(current["end"])
    assert current["part"] == "night"
    # The ongoing night Hora started before today's sunrise and finishes before it.
    assert start < sunrise, "the interval belongs to the previous Panchang day"
    assert end <= sunrise
    assert start <= datetime(2026, 9, 22, 0, 30, tzinfo=IST) < end


def test_exactly_at_next_sunrise_belongs_to_the_new_day(frozen_now):
    pan = _panchang(date(2026, 9, 22))
    next_sunrise = datetime.fromisoformat(pan["sun_moon"]["next_sunrise"])
    frozen_now(next_sunrise)

    # The completed day has no current Hora...
    assert _panchang(date(2026, 9, 22))["hora"]["current"] is None
    # ...and the new Panchang day starts exactly at its first Hora.
    tomorrow = _panchang(next_sunrise.astimezone(IST).date())["hora"]
    assert tomorrow["current"]["start"] == pan["sun_moon"]["next_sunrise"]
    assert tomorrow["current"] == tomorrow["day"][0] or tomorrow["current"]["planet"] == tomorrow["day"][0]["planet"]


def test_selected_date_other_than_today_has_no_current_hora(frozen_now):
    frozen_now(datetime(2026, 9, 22, 11, 45, tzinfo=IST))
    for other in (date(2026, 9, 20), date(2026, 9, 25)):
        hora = _panchang(other)["hora"]
        assert hora["current"] is None, f"{other} must not claim a current Hora"
        assert hora["current_is_live"] is False
        assert len(hora["day"]) == 12 and len(hora["night"]) == 12, "full tables must remain"


def test_explicit_at_time_still_selects_that_instant():
    """Back-compat: an explicit at_time keeps the old, deterministic behaviour."""
    pan = compute_panchang(PanchangRequest(on_date=date(2026, 9, 22), at_time=__import__("datetime").time(11, 45), **DELHI))
    current = pan["hora"]["current"]
    start = datetime.fromisoformat(current["start"])
    end = datetime.fromisoformat(current["end"])
    assert start <= datetime(2026, 9, 22, 11, 45, tzinfo=IST) < end


def test_timezone_is_respected_for_the_current_hora(frozen_now):
    """The same instant picks each location's own local Hora."""
    instant = datetime(2026, 9, 22, 6, 30, tzinfo=ZoneInfo("UTC"))
    frozen_now(instant)

    kolkata = compute_panchang(PanchangRequest(
        on_date=instant.astimezone(IST).date(), latitude=22.5726, longitude=88.3639,
        timezone_name="Asia/Kolkata", label="Kolkata"))
    london = compute_panchang(PanchangRequest(
        on_date=instant.astimezone(ZoneInfo("Europe/London")).date(), latitude=51.5074,
        longitude=-0.1278, timezone_name="Europe/London", label="London"))

    for pan in (kolkata, london):
        current = pan["hora"]["current"]
        assert current is not None
        start = datetime.fromisoformat(current["start"])
        end = datetime.fromisoformat(current["end"])
        local_now = instant.astimezone(ZoneInfo(pan["request"]["timezone"]))
        assert start <= local_now < end, pan["request"]["timezone"]


# ============================ BUG 3: Daily Moon ==============================
def test_panchang_and_daily_agree_on_the_moon_rashi():
    from daily.engine import build_daily_prediction

    daily = build_daily_prediction({"date": "2026-09-22", "latitude": 28.6139, "longitude": 77.209,
                                    "timezone": "Asia/Kolkata", "place": "Delhi",
                                    "natal_moon": "Capricorn"})
    panchang = _panchang(date(2026, 9, 22))
    index = panchang["sun_moon_rashi"]["moon"]["index"]

    assert daily["dailyMoon"]["rashi"] == RASHIS[index], "Daily must use the authoritative Panchang Moon"
    assert daily["dailyMoon"]["sunrise"] == panchang["sun_moon"]["sunrise"]


def test_known_fixture_moon_rashi_is_capricorn():
    panchang = _panchang(date(2026, 9, 22))
    assert panchang["sun_moon_rashi"]["moon"]["name"] in ("Capricorn", "Makara")
    index = panchang["sun_moon_rashi"]["moon"]["index"]
    assert RASHIS[index] == "Capricorn"


def test_house_one_starts_at_the_calculated_moon_rashi():
    from daily.engine import build_daily_prediction

    daily = build_daily_prediction({"date": "2026-09-22", "latitude": 28.6139, "longitude": 77.209,
                                    "timezone": "Asia/Kolkata", "place": "Delhi"})
    anchor = daily["dailyMoon"]["rashi"]
    card = next(c for c in daily["signs"] if c["sign"] == anchor)

    assert card["activeHouse"] == 1, "the transit Moon's own rashi must be house 1"
    assert daily["basis"].endswith("transit_moon_as_house_1")


FORWARD_MAPPING = {
    "Aries": {"Aries": 1, "Taurus": 2, "Gemini": 3, "Cancer": 4, "Leo": 5, "Virgo": 6,
              "Libra": 7, "Scorpio": 8, "Sagittarius": 9, "Capricorn": 10,
              "Aquarius": 11, "Pisces": 12},
    "Capricorn": {"Capricorn": 1, "Aquarius": 2, "Pisces": 3, "Aries": 4, "Taurus": 5,
                  "Gemini": 6, "Cancer": 7, "Leo": 8, "Virgo": 9, "Libra": 10,
                  "Scorpio": 11, "Sagittarius": 12},
}


@pytest.mark.parametrize("anchor", ["Aries", "Capricorn"])
def test_house_mapping_is_forward_through_the_zodiac(anchor):
    """Transit Moon = H1, then the twelve signs run FORWARD through the zodiac."""
    from daily.engine import calculate_active_house

    for sign, expected in FORWARD_MAPPING[anchor].items():
        assert calculate_active_house(sign, anchor) == expected, f"{anchor} -> {sign}"

    anchor_index = RASHIS.index(anchor)
    for index, sign in enumerate(RASHIS):
        assert calculate_active_house(sign, anchor) == ((index - anchor_index) + 12) % 12 + 1


def test_house_mapping_is_forward_for_every_anchor():
    from daily.engine import calculate_active_house

    for anchor in RASHIS:
        houses = {sign: calculate_active_house(sign, anchor) for sign in RASHIS}
        assert sorted(houses.values()) == list(range(1, 13)), anchor
        assert houses[anchor] == 1, f"{anchor} must be house 1"
        anchor_index = RASHIS.index(anchor)
        for step in range(12):
            sign = RASHIS[(anchor_index + step) % 12]
            assert houses[sign] == step + 1, f"{anchor} -> {sign} should be house {step + 1}"


def test_reverse_mapping_is_not_used_any_more():
    """Guard against silently restoring the old reverse direction."""
    from daily.engine import calculate_active_house

    assert calculate_active_house("Aquarius", "Capricorn") == 2, "forward, not 12"
    assert calculate_active_house("Sagittarius", "Capricorn") == 12
    assert calculate_active_house("Aries", "Capricorn") == 4, "forward, not 10"


def test_moon_rashi_is_not_hardcoded():
    """A different day whose anchor differs must move house 1 accordingly."""
    from daily.engine import build_daily_prediction

    anchors = set()
    for offset in range(0, 6):
        day = date(2026, 9, 22) + timedelta(days=offset)
        daily = build_daily_prediction({"date": day.isoformat(), "latitude": 28.6139,
                                        "longitude": 77.209, "timezone": "Asia/Kolkata",
                                        "place": "Delhi"})
        anchor = daily["dailyMoon"]["rashi"]
        anchors.add(anchor)
        assert next(c for c in daily["signs"] if c["sign"] == anchor)["activeHouse"] == 1
    assert len(anchors) > 1, "the anchor must vary with the date (nothing hardcoded)"


def test_daily_respects_the_selected_timezone_for_the_local_date():
    from daily.engine import get_daily_moon_rashi

    for tz_name, lat, lon in (("Asia/Kolkata", 28.6139, 77.209),
                              ("Europe/London", 51.5074, -0.1278),
                              ("America/New_York", 40.7128, -74.006)):
        result = get_daily_moon_rashi({"latitude": lat, "longitude": lon, "timezone": tz_name,
                                       "place": "", "date": "2026-09-22"})
        panchang = compute_panchang(PanchangRequest(on_date=date(2026, 9, 22), latitude=lat,
                                                    longitude=lon, timezone_name=tz_name, label=""))
        index = panchang["sun_moon_rashi"]["moon"]["index"]
        assert result["rashi"] == RASHIS[index], tz_name
        assert result["sunrise"] == panchang["sun_moon"]["sunrise"], tz_name


def test_daily_frontend_sends_the_selected_city_timezone():
    root = pathlib.Path(__file__).resolve().parents[2]
    source = (root / "frontend-next" / "lib" / "daily.ts").read_text(encoding="utf-8")
    page = (root / "frontend-next" / "app" / "daily" / "page.tsx").read_text(encoding="utf-8")

    # Every city carries its own IANA timezone...
    assert source.count("{ label: '") == source.count("timezone: '"), "every city needs a timezone"
    assert source.count("timezone: '") >= 10
    assert "timezone: 'Europe/London'" in source
    assert "timezone: 'America/New_York'" in source
    assert "timezone: 'Australia/Sydney'" in source
    # ...and the page sends the selected city's zone, not a fixed one.
    assert "timezone: found.timezone" in page
    assert "timezone: 'Asia/Kolkata',\n        }));" not in page


# ============================ BUG 1: Ask KAVACH ==============================
ASK = {"timestamp": "2026-09-22T11:45:00+05:30", "latitude": 28.6139, "longitude": 77.209,
       "timezone": "Asia/Kolkata"}


@pytest.fixture()
def ask_env(monkeypatch):
    monkeypatch.setattr("chat.reading.sensitive_response", lambda _q: None)
    monkeypatch.setattr("chat.reading.build_reading",
                        lambda _q: (_ for _ in ()).throw(RuntimeError("no tarot in tests")))
    gemini.reset_health()


def _ask(client, conversation_id="bug1"):
    return client.post("/api/ask", json={**ASK, "question": "hello", "conversation_id": conversation_id})


def test_nvidia_success_returns_the_answer(ask_env):
    import chat.nvidia as nv
    original = nv.generate_reply_detailed
    nv.generate_reply_detailed = lambda *a, **k: {"text": "NVIDIA answered.", "model": nv.primary_model(),
                                                  "preferred": nv.primary_model(), "provider": "nvidia",
                                                  "attempts": [], "fallback": False}
    try:
        body = _ask(TestClient(main.app)).json()
    finally:
        nv.generate_reply_detailed = original
    assert body["answered"] is True and body["answer"] == "NVIDIA answered."


def test_nvidia_failure_reaches_gemini_and_returns_its_answer(ask_env, monkeypatch):
    monkeypatch.setattr("chat.nvidia.generate_reply_detailed",
                        lambda *a, **k: {"text": None, "model": None, "provider": "nvidia",
                                         "preferred": nvidia.primary_model(),
                                         "attempts": [{"model": "x", "reason": "transient_503"}],
                                         "fallback": True})
    monkeypatch.setattr("chat.gemini.generate_reply_detailed",
                        lambda *a, **k: {"text": "Gemini answered.", "model": "gemini-3.5-flash",
                                         "preferred": "gemini-3.6-flash", "provider": "gemini",
                                         "attempts": []})
    body = _ask(TestClient(main.app)).json()

    assert body["answered"] is True
    assert body["answer"] == "Gemini answered."


def test_all_providers_unavailable_gives_the_existing_friendly_message(ask_env, monkeypatch):
    monkeypatch.setattr("chat.nvidia.generate_reply_detailed",
                        lambda *a, **k: {"text": None, "model": None, "provider": "nvidia",
                                         "preferred": nvidia.primary_model(), "attempts": [], "fallback": True})
    monkeypatch.setattr("chat.gemini.generate_reply_detailed",
                        lambda *a, **k: {"text": None, "model": None, "provider": "gemini",
                                         "preferred": gemini.MODEL_PRIORITY[0], "attempts": []})
    body = _ask(TestClient(main.app)).json()

    assert body["answered"] is False
    assert body["answer"] == gemini.UNAVAILABLE_MESSAGE


def test_gemini_fallback_is_latency_bounded(monkeypatch):
    """A hanging/limited model must not burn the whole request."""
    monkeypatch.setenv("GEMINI_API_KEY", "test-sentinel")
    gemini.reset_health()

    assert gemini.PER_ATTEMPT_TIMEOUT <= 12.0
    assert gemini.TOTAL_BUDGET_SECONDS <= 24.0
    assert gemini.TOTAL_BUDGET_SECONDS < gemini.TIMEOUT_SECONDS

    calls = {"n": 0}

    def hanging_post(*args, **kwargs):
        calls["n"] += 1
        raise httpx.TimeoutException("hang")

    monkeypatch.setattr(gemini.httpx, "post", hanging_post)
    detail = gemini.generate_reply_detailed("hello", [])

    assert detail["text"] is None
    assert calls["n"] <= len(gemini.MODEL_PRIORITY)
    assert all(attempt["reason"] in ("timeout", "budget_exhausted") for attempt in detail["attempts"])

    health = gemini.model_health()
    cooled = [model for model, state in health.items() if state["cooldown_for"] > 0]
    assert cooled, "timed-out models must be parked so the next request is fast"


def test_gemini_rate_limited_models_are_parked_and_deprioritised(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-sentinel")
    gemini.reset_health()

    class Response:
        def __init__(self, status, payload=None, text=""):
            self.status_code = status
            self._payload = payload
            self.text = text

        def json(self):
            return self._payload if self._payload is not None else {"steps": []}

    primary, secondary = gemini.MODEL_PRIORITY[0], gemini.MODEL_PRIORITY[1]

    def scripted_post(*args, **kwargs):
        model = (kwargs.get("json") or {}).get("model")
        if model == primary:
            return Response(429, text="quota")
        return Response(200, {"steps": [{"type": "model_output",
                                         "content": [{"type": "text", "text": "answered"}]}]})

    monkeypatch.setattr(gemini.httpx, "post", scripted_post)
    detail = gemini.generate_reply_detailed("hello", [])

    assert detail["text"] == "answered"
    assert detail["model"] == secondary
    health = gemini.model_health()
    assert health[primary]["cooldown_for"] > 0, "a rate-limited model must be parked"
    assert gemini._ordered_models()[0] != primary, "a parked model must not be tried first next time"


def test_ordinary_ask_requests_are_not_rate_limited(monkeypatch, ask_env):
    monkeypatch.setenv("KAVACH_RATELIMIT", "1")
    import hardening

    hardening.LIMITER.reset()
    try:
        client = TestClient(main.app)
        for index in range(5):
            monkeypatch.setattr("chat.nvidia.generate_reply_detailed",
                                lambda *a, **k: {"text": "ok", "model": nvidia.primary_model(),
                                                 "preferred": nvidia.primary_model(), "provider": "nvidia",
                                                 "attempts": [], "fallback": False})
            assert _ask(client, f"normal-{index}").status_code == 200
    finally:
        hardening.LIMITER.reset()


def test_one_ask_request_still_archives_one_row(monkeypatch, ask_env):
    import archive

    class CountingStore:
        def __init__(self):
            self.inserts = 0

        def configured(self):
            return True

        def insert(self, row):
            self.inserts += 1
            return f"row-{self.inserts}"

        def verify_token(self, token):
            return None

    store = CountingStore()
    monkeypatch.setattr(archive, "store", store)
    monkeypatch.setattr("chat.nvidia.generate_reply_detailed",
                        lambda *a, **k: {"text": None, "provider": "nvidia",
                                         "preferred": nvidia.primary_model(), "attempts": [], "fallback": True})
    monkeypatch.setattr("chat.gemini.generate_reply_detailed",
                        lambda *a, **k: {"text": "Gemini answered.", "model": "gemini-3.5-flash",
                                         "preferred": "gemini-3.6-flash", "provider": "gemini", "attempts": []})

    _ask(TestClient(main.app), "archive-once")
    assert store.inserts == 1, "one user request (even with a fallback chain) is one archive row"


def test_ask_response_never_leaks_secrets(ask_env, monkeypatch):
    monkeypatch.setattr("chat.nvidia.generate_reply_detailed",
                        lambda *a, **k: {"text": "Fine.", "model": nvidia.primary_model(),
                                         "preferred": nvidia.primary_model(), "provider": "nvidia",
                                         "attempts": [], "fallback": False})
    body = json.dumps(_ask(TestClient(main.app)).json())
    assert set(json.loads(body).keys()) == {"status", "answered", "answer", "conversation_id"}
    for forbidden in ("Bearer", "nvapi-", "api_key", "reasoning"):
        assert forbidden not in body
