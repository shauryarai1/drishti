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

# Astrology tools are PUBLIC: usable without an account. Accounts remain an
# optional convenience for saving readings and profiles.
PUBLIC_TOOLS = ("kundli", "reading", "results", "life-summary", "weekly-prediction",
                "compatibility", "ask", "yes-no", "panchang")
# Account management surfaces stay protected. They self-guard in the page (no
# route-level gate), so a signed-out visitor is asked to sign in, not blocked
# from the rest of the product.
ACCOUNT_ONLY = ("account", "history", "admin", "profile/setup")
# Public informational routes.
PUBLIC = ("services", "privacy", "terms", "login", "signup", "forgot-password",
          "reset-password", "profile")


def _read(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8")


def _layout(route: str) -> str:
    return _read(APP / route / "layout.tsx")


# --- route matrix ------------------------------------------------------------
def test_astrology_tools_have_no_login_or_profile_gate():
    for route in PUBLIC_TOOLS:
        layout = APP / route / "layout.tsx"
        if layout.exists():
            source = _read(layout)
            assert "GuardedLayout" not in source, route
            assert "RequireProfile" not in source, route
            assert "return children" in source, route


def test_account_only_routes_still_enforce_authentication():
    # No layout-level gate, but each page refuses to expose account data.
    history = _read(APP / "history" / "page.tsx")
    assert "useAuth" in history
    account = _read(APP / "account" / "page.tsx")
    assert "useAuth" in account
    setup = _read(APP / "profile" / "setup" / "page.tsx")
    assert "status !== 'signedIn'" in setup
    admin = _read(APP / "admin" / "page.tsx")
    assert "useAuth" in admin


def test_public_routes_have_no_guard():
    for route in PUBLIC:
        layout = APP / route / "layout.tsx"
        if layout.exists():
            assert "RequireProfile" not in _read(layout), route
        else:
            # No layout at all means no route-level gate.
            assert not layout.exists()


def test_tool_layouts_do_not_reimplement_or_use_the_guard():
    guard = _read(COMPONENTS / "RequireProfile.tsx")
    # The shared guard is preserved for any future account-only surface.
    assert "export function RequireProfile" in guard
    for route in PUBLIC_TOOLS:
        layout = APP / route / "layout.tsx"
        if not layout.exists():
            continue
        source = _read(layout)
        assert "from './RequireProfile'" not in source, f"{route} must not use the guard"
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


def test_require_profile_signed_out_resolves_to_the_sign_in_notice():
    guard = _read(COMPONENTS / "RequireProfile.tsx")
    # The session-loading branch must depend on the AUTH status only. Treating a
    # resolved signed-out state ('idle') as loading pinned users forever.
    assert "if (status === 'loading') {" in guard
    assert "state === 'idle'" not in guard.split("if (status === 'loading')")[1].split("}")[0]
    assert "SIGN IN" in guard
    assert "signin" not in guard.lower() or "loginHref" in guard


def test_auth_session_resolution_is_bounded():
    auth = _read(LIB / "auth.tsx")
    # A hung session lookup must not leave the app loading forever.
    assert "setTimeout" in auth
    assert "current === 'loading' ? 'signedOut' : current" in auth
    assert "clearTimeout(settle)" in auth


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
