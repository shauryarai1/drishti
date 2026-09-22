"""KAVACH Services / Private Consultation: structure, pricing and safety guards.

The consultation and pooja offerings are additive frontend files. These tests
lock down the commercial promises: exact prices, correctly encoded WhatsApp
messages, no payment gateway, no fear-based or scarcity copy, and a commercial
layer that is independent of the astrology engines.
"""

from __future__ import annotations

import json
import pathlib
import shutil
import subprocess

import pytest

REPO = pathlib.Path(__file__).resolve().parents[2]
FRONTEND = REPO / "frontend-next"

SERVICES_PAGE = FRONTEND / "app" / "services" / "page.tsx"
CATALOGUE = FRONTEND / "lib" / "services.ts"
ANALYTICS = FRONTEND / "lib" / "analytics.ts"
BOOKING_BUTTON = FRONTEND / "components" / "ServiceBookingButton.tsx"
POOJA_CARD = FRONTEND / "components" / "PoojaPackageCard.tsx"
SERVICES_CTA = FRONTEND / "components" / "ServicesCTA.tsx"
PAGE_VIEW = FRONTEND / "components" / "AnalyticsPageView.tsx"

NEW_FILES = [SERVICES_PAGE, CATALOGUE, ANALYTICS, BOOKING_BUTTON, POOJA_CARD, SERVICES_CTA, PAGE_VIEW]

# Deliberately never used anywhere in the new commercial layer.
PAYMENT_TERMS = ("razorpay", "stripe", "payment gateway", "payment_gateway", "cvv",
                 "card number", "card_number", "checkout", "upi id", "payu", "phonepe")

# Sales pressure, fear and fabricated urgency.
FEAR_TERMS = ("book now", "hurry", "limited time", "only today", "act fast", "don't miss",
              "dont miss", "best seller", "bestseller", "countdown", "offer ends",
              "danger detected", "your planet is dangerous", "must purchase", "you must",
              "mandatory", "required", "fear")


def _read(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8")


def test_new_files_exist():
    for path in NEW_FILES:
        assert path.exists(), f"missing {path}"


# --- the real catalogue, executed -------------------------------------------------
def test_catalogue_prices_and_whatsapp_encoding(tmp_path):
    node = shutil.which("node")
    if not node:
        pytest.skip("node is not available")

    module = CATALOGUE.as_uri()
    script = tmp_path / "check_services.mjs"
    script.write_text(
        'import { CONSULTATION, POOJA_PACKAGES, SERVICES, bookingUrl, whatsappUrl,\n'
        '  WHATSAPP_NUMBER, WHATSAPP_BASE_URL, PLANETARY_FOCUS } from "MODULE";\n'
        'const fail = (m) => { console.error("FAIL: " + m); process.exit(1); };\n'
        'const rupee = "\\u20b9";\n'
        'if (WHATSAPP_NUMBER !== "919911233375") fail("whatsapp number");\n'
        'if (WHATSAPP_BASE_URL !== "https://wa.me/919911233375") fail("whatsapp base");\n'
        'const ids = SERVICES.map((s) => s.id).join(",");\n'
        'if (ids !== "consultation,pooja_2100,pooja_5100,pooja_11000") fail("service ids: " + ids);\n'
        'if (CONSULTATION.priceInr !== 1100 || CONSULTATION.priceLabel !== rupee + "1,100") fail("consultation price");\n'
        'const expected = [[2100, "2,100"], [5100, "5,100"], [11000, "11,000"]];\n'
        'POOJA_PACKAGES.forEach((s, i) => {\n'
        '  if (s.priceInr !== expected[i][0] || s.priceLabel !== rupee + expected[i][1]) fail("pooja price " + i);\n'
        '});\n'
        'const messages = [\n'
        '  "Hi, I\'d like to book a KAVACH Private Consultation for " + rupee + "1,100.",\n'
        '  "Hi, I\'d like to enquire about the KAVACH " + rupee + "2,100 Pooja & Mantra Jaap service.",\n'
        '  "Hi, I\'d like to enquire about the KAVACH " + rupee + "5,100 Pooja & Mantra Jaap service.",\n'
        '  "Hi, I\'d like to enquire about the KAVACH " + rupee + "11,000 Pooja & Mantra Jaap service.",\n'
        '];\n'
        'SERVICES.forEach((s, i) => { if (s.whatsappMessage !== messages[i]) fail("message " + i + ": " + s.whatsappMessage); });\n'
        'const urls = [\n'
        '  "https://wa.me/919911233375?text=Hi%2C%20I\'d%20like%20to%20book%20a%20KAVACH%20Private%20Consultation%20for%20%E2%82%B91%2C100.",\n'
        '  "https://wa.me/919911233375?text=Hi%2C%20I\'d%20like%20to%20enquire%20about%20the%20KAVACH%20%E2%82%B92%2C100%20Pooja%20%26%20Mantra%20Jaap%20service.",\n'
        '  "https://wa.me/919911233375?text=Hi%2C%20I\'d%20like%20to%20enquire%20about%20the%20KAVACH%20%E2%82%B95%2C100%20Pooja%20%26%20Mantra%20Jaap%20service.",\n'
        '  "https://wa.me/919911233375?text=Hi%2C%20I\'d%20like%20to%20enquire%20about%20the%20KAVACH%20%E2%82%B911%2C000%20Pooja%20%26%20Mantra%20Jaap%20service.",\n'
        '];\n'
        'SERVICES.forEach((s, i) => { if (bookingUrl(s) !== urls[i]) fail("url " + i + ": " + bookingUrl(s)); });\n'
        'const blob = JSON.stringify({ messages, urls, custom: whatsappUrl("a b&c") }).toLowerCase();\n'
        'for (const banned of ["date of birth", "time of birth", "place of birth", "latitude", "longitude", "dob", "birth details"]) {\n'
        '  if (blob.includes(banned)) fail("personal data in url: " + banned);\n'
        '}\n'
        'for (const url of urls) { if (url.includes(" ") || url.includes(rupee)) fail("unencoded url"); }\n'
        'if (whatsappUrl("a b&c") !== "https://wa.me/919911233375?text=a%20b%26c") fail("custom encoding");\n'
        'if (PLANETARY_FOCUS.length !== 9) fail("planetary focus");\n'
        'console.log("SERVICES_OK");\n'.replace("MODULE", module),
        encoding="utf-8",
    )

    result = subprocess.run([node, str(script)], capture_output=True, text=True, timeout=90)
    assert result.returncode == 0, result.stderr
    assert "SERVICES_OK" in result.stdout


def test_catalogue_source_prices_are_exact():
    source = _read(CATALOGUE)
    for price in (1100, 2100, 5100, 11000):
        assert f"priceInr: {price}" in source, price
    # Pre-formatted labels so display never varies by locale.
    for label in (r"\u20b91,100", r"\u20b92,100", r"\u20b95,100", r"\u20b911,000"):
        assert label in source, label


# --- no payment gateway ----------------------------------------------------------
def test_no_payment_gateway_was_added():
    for path in NEW_FILES:
        lowered = _read(path).lower()
        for term in PAYMENT_TERMS:
            assert term not in lowered, f"{path.name} references {term}"


def test_no_payment_dependency_was_added():
    package = json.loads(_read(FRONTEND / "package.json"))
    deps = {**package.get("dependencies", {}), **package.get("devDependencies", {})}
    for banned in ("razorpay", "stripe", "@stripe/stripe-js", "payu", "phonepe"):
        assert banned not in deps, banned


# --- no fear, no scarcity, no fabricated differentiation -------------------------
def test_no_fear_or_scarcity_copy():
    for path in NEW_FILES:
        lowered = _read(path).lower()
        for term in FEAR_TERMS:
            assert term not in lowered, f"{path.name} contains {term!r}"


def test_recommendation_wording_is_calm():
    page = _read(SERVICES_PAGE)
    assert "may be suggested" in page
    assert "suggested" in page
    assert "voluntarily" in page, "the user must choose to enquire, not be pushed"


def test_page_carries_the_responsible_disclaimer():
    page = _read(SERVICES_PAGE)
    assert "matters of personal belief" in page
    assert "not be treated as guaranteed outcomes" in page
    assert "professional medical, legal or" in page


# --- the commercial layer cannot influence the astrology engines -----------------
def test_commercial_layer_is_independent_of_the_engines():
    page = _read(SERVICES_PAGE)
    for forbidden in ("lib/api", "yesno", "kundli", "panchang", "life_summary", "chat"):
        assert forbidden not in page, f"services page must not touch {forbidden}"


def test_engines_contain_no_monetization_references():
    """A reading can never be influenced by the commercial layer."""
    for name in ("engine.py", "interpretation.py", "relationships.py", "safety.py", "numbers.py"):
        source = _read(REPO / "backend" / "yesno" / name).lower()
        for banned in ("whatsapp", "consultation", "pooja", "price", "payment", "book", "services"):
            assert banned not in source, f"yesno/{name} references {banned}"


# --- reusable CTA and analytics readiness ---------------------------------------
def test_reusable_services_cta_exists_and_result_pages_are_untouched():
    cta = _read(SERVICES_CTA)
    assert 'href="/services"' in cta
    assert "services_cta_view" in cta
    assert "services_cta_click" in cta

    # Approved integration: Header and Footer link to /services.
    assert "/services" in _read(FRONTEND / "components" / "Header.tsx")
    assert "/services" in _read(FRONTEND / "components" / "Footer.tsx")

    # The CTA is deliberately NOT placed on any result page yet.
    for page in ("app/ask/page.tsx", "app/results/page.tsx", "app/life-summary/page.tsx",
                 "app/daily/page.tsx", "app/your-week/page.tsx", "app/yes-no/page.tsx"):
        assert "ServicesCTA" not in _read(FRONTEND / page), page


def test_analytics_events_are_declared_and_no_provider_added():
    analytics = _read(ANALYTICS)
    for event in ("services_page_view", "consultation_booking_click", "pooja_2100_booking_click",
                  "pooja_5100_booking_click", "pooja_11000_booking_click",
                  "services_cta_view", "services_cta_click"):
        assert event in analytics, event

    source = _read(ANALYTICS).lower()
    for provider in ("gtag(", "googletagmanager", "posthog", "mixpanel", "plausible", "segment"):
        assert provider not in source, provider

    package = json.loads(_read(FRONTEND / "package.json"))
    deps = {**package.get("dependencies", {}), **package.get("devDependencies", {})}
    for banned in ("@vercel/analytics", "posthog-js", "mixpanel", "@segment/analytics-next", "react-ga"):
        assert banned not in deps, banned


# --- responsive behaviour --------------------------------------------------------
def test_pooja_packages_stack_on_mobile():
    page = _read(SERVICES_PAGE)
    assert "grid-cols-1 gap-6 lg:grid-cols-3" in page, "packages must stack until the large breakpoint"


def test_booking_targets_are_comfortable_on_touch():
    for path in (BOOKING_BUTTON, SERVICES_CTA):
        assert "min-h-[48px]" in _read(path), path.name
