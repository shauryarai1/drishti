"""Profile / auth route wiring.

The gating is implemented with App Router layout files, so these tests assert
the route matrix from the real files rather than from brittle page strings, plus
the guard's behaviour contract and the profile UI rules.
"""

from __future__ import annotations

import pathlib

REPO = pathlib.Path(__file__).resolve().parents[2]
APP = REPO / "frontend-next" / "app"
COMPONENTS = REPO / "frontend-next" / "components"
LIB = REPO / "frontend-next" / "lib"

# Login + Primary Profile.
TWO_GATE = ("kundli", "reading", "results", "life-summary", "your-week", "compatibility")
# Login only - the feature must not use profile astrology.
LOGIN_ONLY = ("ask", "yes-no", "panchang")
# Public.
PUBLIC = ("services", "privacy", "terms", "login", "signup", "forgot-password",
          "reset-password", "profile")


def _read(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8")


def _layout(route: str) -> str:
    return _read(APP / route / "layout.tsx")


# --- route matrix ------------------------------------------------------------
def test_personal_tools_require_login_and_primary_profile():
    for route in TWO_GATE:
        source = _layout(route)
        assert "GuardedLayout" in source, route
        assert "requireProfile={false}" not in source, f"{route} must require a Primary Profile"


def test_ask_yes_no_panchang_are_login_only_and_use_no_profile():
    for route in LOGIN_ONLY:
        source = _layout(route)
        assert "GuardedLayout requireProfile={false}" in source, route


def test_daily_requires_login_and_primary_profile():
    page = _read(APP / "daily" / "page.tsx")
    assert "RequireProfile" in page
    assert "requireProfile={false}" not in page


def test_public_routes_have_no_guard():
    for route in PUBLIC:
        layout = APP / route / "layout.tsx"
        if layout.exists():
            assert "RequireProfile" not in _read(layout), route
        else:
            # No layout at all means no route-level gate.
            assert not layout.exists()


def test_shared_guard_is_reused_not_duplicated():
    guard = _read(COMPONENTS / "RequireProfile.tsx")
    assert "export function RequireProfile" in guard
    for route in TWO_GATE + LOGIN_ONLY:
        source = _layout(route)
        assert "from './RequireProfile'" not in source, f"{route} must use the shared wrapper"
        assert "getPrimaryProfile" not in source, f"{route} must not reimplement the guard"


# --- guard contract ----------------------------------------------------------
def test_guard_distinguishes_missing_profile_from_load_failure():
    guard = _read(COMPONENTS / "RequireProfile.tsx")
    assert "'missing'" in guard and "'error'" in guard
    assert "setState('error')" in guard
    # A failed load shows RETRY and never redirects to setup: the redirect is
    # keyed to the missing state only.
    assert "if (state === 'missing') router.replace" in guard
    assert "RETRY" in guard
    assert "state === 'error'" in guard


def test_guard_preserves_the_validated_return_path():
    guard = _read(COMPONENTS / "RequireProfile.tsx")
    assert "safeNextPath" in guard
    assert "loginHref(pathname)" in guard
    # No raw redirect from an unvalidated value.
    assert "window.location.href = next" not in guard


def test_setup_page_never_requires_a_primary_profile():
    setup = _read(APP / "profile" / "setup" / "page.tsx")
    assert "RequireProfile" not in setup, "setup must not guard itself (redirect loop)"
    assert "createPrimaryProfile" in setup
    assert "getPrimaryProfile" in setup, "an existing Primary must not be re-created"
    assert "safeNextPath" in setup


# --- profile UI rules --------------------------------------------------------
def test_no_make_primary_or_delete_primary_in_the_product_ui():
    for path in list(COMPONENTS.glob("*.tsx")) + [APP / "profile" / "setup" / "page.tsx"]:
        source = _read(path)
        assert "makePrimary" not in source, path.name
        assert "Delete Primary" not in source, path.name


def test_other_people_are_created_non_primary():
    lib = _read(LIB / "profiles.ts")
    assert "export async function createOtherPerson" in lib
    other = lib.split("export async function createOtherPerson")[1].split("export async function")[0]
    assert "is_primary: false" in other
    assert "is_primary: true" not in other


def test_primary_edit_cannot_change_primary_status():
    lib = _read(LIB / "profiles.ts")
    update = lib.split("export async function updateProfile")[1].split("export async function")[0]
    assert "is_primary" not in update
    assert "clean(input)" in update


# --- Daily wiring ------------------------------------------------------------
def test_daily_defaults_to_primary_and_offers_every_profile():
    page = _read(APP / "daily" / "page.tsx")
    assert "listProfiles" in page
    assert "find((profile) => profile.is_primary)" in page
    assert "PersonSelector" in page
    assert "profiles={profiles}" in page


def test_daily_derives_real_natal_values_and_sends_them():
    page = _read(APP / "daily" / "page.tsx")
    assert "deriveNatal(" in page
    assert "natal_moon: natalRef.current.moonRashi" in page
    assert "natal_nakshatra: natalRef.current.janmaNakshatra" in page
    # Never fabricate natal data when derivation fails.
    assert "natalRef.current = null" in page


def test_natal_values_come_from_the_existing_authoritative_engine():
    natal = _read(LIB / "natal.ts")
    assert "api.getInterpretation" in natal, "reuse the existing chart path"
    assert "moonRashi" in natal and "janmaNakshatra" in natal
    # No new astronomy and no Rashi -> Nakshatra lookup.
    for banned in ("swisseph", "swe.", "RASHI_NAKSHATRA", "rashiToNakshatra"):
        assert banned not in natal, banned


def test_daily_switching_is_latest_wins_and_keeps_its_location_separate():
    page = _read(APP / "daily" / "page.tsx")
    assert "natalRequestIdRef" in page
    assert "if (requestId !== natalRequestIdRef.current) return;" in page
    # The selected Daily city is never replaced by the birth place.
    assert "cityRef" in page
    assert "birth_place_name" not in page


def test_daily_keeps_midnight_rollover():
    page = _read(APP / "daily" / "page.tsx")
    assert "localCalendarDate" in page and "dayRef" in page


# --- Daily personalisation acceptance (11A-11I) ------------------------------
def test_daily_never_falls_back_to_another_person_or_a_saved_reading():
    page = _read(APP / "daily" / "page.tsx")
    # The Primary is required: no `?? list[0]` (first other person) fallback.
    assert "?? list[0]" not in page
    assert "list.find((profile) => profile.is_primary)" in page
    # No fallback to a saved Kundli / reading / cached person anywhere.
    for banned in ("getSavedKundli", "latestKundli", "savedReading", "getHistory", "listReadings"):
        assert banned not in page, banned
    # A missing primary, a load failure and a derivation failure all surface a
    # retry instead of borrowing someone else's data.
    assert "setProfileError(" in page
    assert "profileError" in page
    assert "retryProfile" in page


def test_daily_reverts_the_selector_when_a_switch_cannot_be_calculated():
    page = _read(APP / "daily" / "page.tsx")
    assert "const previousId = selectedId;" in page
    assert "setSelectedId(previousId);" in page


def test_daily_is_login_only_and_never_creates_an_anonymous_profile():
    page = _read(APP / "daily" / "page.tsx")
    assert "<RequireProfile>" in page
    # No session-only birth profile: Daily never writes or creates a profile.
    assert "createPrimaryProfile" not in page
    assert "createOtherPerson" not in page
    assert "sessionStorage" not in page
    assert "birth_profiles" not in page


def test_daily_sends_both_natal_values_and_no_manual_nakshatra_input():
    page = _read(APP / "daily" / "page.tsx")
    assert "natal_moon: natalRef.current.moonRashi" in page
    assert "natal_nakshatra: natalRef.current.janmaNakshatra" in page
    # Nothing asks the user to type a Rashi / Nakshatra / Lagna.
    lowered = page.lower()
    assert "janma nakshatra" not in lowered or "input" not in lowered
    assert "rashi</label>" not in lowered
    # The birth place is never sent as the Daily location.
    assert "birth_place_name" not in page


def test_daily_defaults_to_primary_every_fresh_visit():
    page = _read(APP / "daily" / "page.tsx")
    # Selection is component state only - never persisted as a default.
    assert "setSelectedId(primary.id)" in page
    for banned in ("localStorage.setItem('kavach_daily_person", "selectedId").setItem"):
        assert banned not in page, banned


def test_other_person_uses_the_same_natal_pipeline_as_primary():
    page = _read(APP / "daily" / "page.tsx")
    # One derivation path used by both bootstrap and selection.
    assert page.count("await deriveNatal(") == 2


# --- account profile management ---------------------------------------------
def test_account_page_mounts_the_profiles_manager():
    account = _read(APP / "account" / "page.tsx")
    assert "BirthProfilesManager" in account
    assert "userId={user.id}" in account


def test_profiles_manager_can_edit_primary_and_crud_other_people():
    manager = _read(COMPONENTS / "BirthProfilesManager.tsx")
    assert "updateProfile(" in manager, "Primary edit uses the shared update path"
    assert "createOtherPerson(" in manager, "Add uses the non-primary creator"
    assert "deleteOtherPerson(" in manager, "Delete uses the other-person-only deleter"
    # Edit is offered for the Primary too, but it is never deletable/promotable.
    assert "openEdit(primary)" in manager
    assert "profile.is_primary) return;" in manager, "delete refuses the Primary"
    assert "makePrimary" not in manager
    assert "is_primary:" not in manager, "the manager never sets primary status"


def test_profiles_manager_does_not_persist_birth_data_in_the_browser():
    manager = _read(COMPONENTS / "BirthProfilesManager.tsx")
    for banned in ("localStorage", "sessionStorage", "URLSearchParams", "console.",
                   "trackEvent", "dataLayer"):
        assert banned not in manager, banned


# --- privacy -----------------------------------------------------------------
def test_birth_profiles_are_not_persisted_in_the_browser_or_urls():
    for name in ("profiles.ts", "natal.ts"):
        source = _read(LIB / name)
        for banned in ("localStorage", "sessionStorage", "URLSearchParams", "location.href",
                       "console.", "trackEvent"):
            assert banned not in source, (name, banned)


def test_no_service_role_or_secret_in_the_profile_flow():
    for path in (LIB / "profiles.ts", LIB / "natal.ts", COMPONENTS / "RequireProfile.tsx",
                 COMPONENTS / "GuardedLayout.tsx", APP / "profile" / "setup" / "page.tsx"):
        source = _read(path)
        for banned in ("SERVICE_ROLE", "service_role", "sb_secret", "GROQ_API_KEY",
                       "GEMINI_API_KEY", "GEOAPIFY_API_KEY"):
            assert banned not in source, (path.name, banned)
