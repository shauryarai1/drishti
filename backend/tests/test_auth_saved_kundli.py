"""KAVACH Google auth + login-gated results + saved Kundlis.

Structural and behavioural guards for the auth/persistence integration. The
TypeScript modules that hold real logic (redirect safety, person names, pending
forms) are executed with Node so the behaviour is verified, not just grepped.
"""

from __future__ import annotations

import json
import pathlib
import shutil
import subprocess

import pytest

REPO = pathlib.Path(__file__).resolve().parents[2]
FRONTEND = REPO / "frontend-next"

AUTH_TS = FRONTEND / "lib" / "auth.tsx"
AUTH_PATHS = FRONTEND / "lib" / "authPaths.ts"
PERSON_NAME = FRONTEND / "lib" / "personName.ts"
PENDING = FRONTEND / "lib" / "pendingForms.ts"
GOOGLE_BUTTON = FRONTEND / "components" / "GoogleAuthButton.tsx"
RESULT_GATE = FRONTEND / "components" / "ResultGate.tsx"
LOGIN = FRONTEND / "app" / "login" / "page.tsx"
SIGNUP = FRONTEND / "app" / "signup" / "page.tsx"
KUNDLI = FRONTEND / "app" / "kundli" / "page.tsx"
READING = FRONTEND / "app" / "reading" / "page.tsx"
RESULTS = FRONTEND / "app" / "results" / "page.tsx"
LIFE_SUMMARY = FRONTEND / "app" / "life-summary" / "page.tsx"
YOUR_WEEK = FRONTEND / "app" / "your-week" / "page.tsx"
HISTORY = FRONTEND / "app" / "history" / "page.tsx"
BIRTH_DETAILS = FRONTEND / "components" / "BirthDetails.tsx"
MIGRATION = REPO / "supabase" / "migrations" / "0001_saved_readings.sql"


def _read(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8")


def _node(script_body: str, tmp_path: pathlib.Path) -> str:
    node = shutil.which("node")
    if not node:
        pytest.skip("node is not available")
    script = tmp_path / "check.mjs"
    script.write_text(script_body, encoding="utf-8")
    result = subprocess.run([node, str(script)], capture_output=True, text=True, timeout=90)
    assert result.returncode == 0, result.stderr
    return result.stdout


# --- Google auth -------------------------------------------------------------
def test_google_button_exists_and_uses_the_existing_supabase_layer():
    button = _read(GOOGLE_BUTTON)
    assert "CONTINUE WITH GOOGLE" in button
    assert "signInWithGoogle" in button
    assert "AuthOrDivider" in button  # the "OR" rule
    # No second auth system and no extra library.
    for banned in ("next-auth", "firebase", "@auth0", "passport", "gapi"):
        assert banned not in button, banned


def test_auth_uses_supabase_oauth_with_a_validated_return_path():
    auth = _read(AUTH_TS)
    assert "signInWithOAuth" in auth and "provider: 'google'" in auth
    assert "safeNextPath" in auth, "the return destination must be validated"
    # The public client only: no service-role key, no secret.
    for banned in ("SERVICE_ROLE", "service_role", "CLIENT_SECRET", "client_secret"):
        assert banned not in auth, banned


def test_login_and_signup_keep_email_password_and_add_google():
    for path in (LOGIN, SIGNUP):
        page = _read(path)
        assert "GoogleAuthButton" in page, path.name
        assert "AuthOrDivider" in page, path.name
        # Email/password remains.
        assert "signInWithPassword" not in page  # called through useAuth, not raw
        assert "type=\"password\"" in page or "type='password'" in page, path.name
        assert "AUTH_INPUT" in page, path.name


def test_supabase_client_still_uses_only_public_env():
    client = _read(FRONTEND / "lib" / "supabase.ts")
    assert "NEXT_PUBLIC_SUPABASE_URL" in client
    assert "NEXT_PUBLIC_SUPABASE_ANON_KEY" in client
    for banned in ("SERVICE_ROLE", "service_role"):
        assert banned not in client, banned


# --- redirect safety (executed) ---------------------------------------------
def test_redirect_guard_rejects_external_and_accepts_internal(tmp_path):
    module = AUTH_PATHS.as_uri()
    body = (
        'import { isSafeInternalPath, safeNextPath, DEFAULT_AUTH_DESTINATION } from "MODULE";\n'
        'const fail = (m) => { console.error("FAIL: " + m); process.exit(1); };\n'
        'for (const good of ["/kundli", "/reading", "/results", "/life-summary", "/account", "/history"]) {\n'
        '  if (!isSafeInternalPath(good)) fail("rejected internal path " + good);\n'
        '  if (safeNextPath(good) !== good) fail("safeNextPath changed " + good);\n'
        '}\n'
        'for (const bad of ["https://evil.example", "//evil.example", "javascript:alert(1)",\n'
        '  "/javascript:alert(1)", "http://evil.example/kundli", "/kundli\\\\..", "/kundli\\n",\n'
        '  "kundli", "", null, undefined, "/etc/passwd", "/unknown-product"]) {\n'
        '  if (isSafeInternalPath(bad)) fail("accepted unsafe path " + JSON.stringify(bad));\n'
        '  if (safeNextPath(bad) !== DEFAULT_AUTH_DESTINATION) fail("unsafe path not defaulted: " + bad);\n'
        '}\n'
        'console.log("REDIRECT_OK");\n'.replace("MODULE", module)
    )
    assert "REDIRECT_OK" in _node(body, tmp_path)


# --- person name (executed) -------------------------------------------------
def test_person_name_validation_and_unicode(tmp_path):
    module = PERSON_NAME.as_uri()
    body = (
        'import { normalisePersonName, isValidPersonName, displayPersonName, UNNAMED_KUNDLI, PERSON_NAME_MAX } from "MODULE";\n'
        'const fail = (m) => { console.error("FAIL: " + m); process.exit(1); };\n'
        'if (normalisePersonName("  Trishna Rai  ") !== "Trishna Rai") fail("trim");\n'
        'if (isValidPersonName("   ")) fail("whitespace-only must be invalid");\n'
        'if (isValidPersonName("")) fail("empty must be invalid");\n'
        'if (!isValidPersonName("Trishna Rai")) fail("normal name");\n'
        'if (normalisePersonName("\\u0924\\u094d\\u0930\\u093f\\u0937\\u094d\\u0923\\u093e") !== "\\u0924\\u094d\\u0930\\u093f\\u0937\\u094d\\u0923\\u093e") fail("hindi");\n'
        'if (!isValidPersonName("\\u0906\\u0930\\u094d\\u092f\\u0928")) fail("hindi valid");\n'
        'if (!isValidPersonName("Jos\\u00e9 \\u00d1")) fail("accented");\n'
        'if (normalisePersonName("a\\u0000b\\n c") !== "a b c") fail("control chars");\n'
        'if (normalisePersonName("x".repeat(500)).length !== PERSON_NAME_MAX) fail("max length");\n'
        'if (displayPersonName("") !== UNNAMED_KUNDLI) fail("unnamed fallback");\n'
        'if (displayPersonName(null) !== UNNAMED_KUNDLI) fail("null fallback");\n'
        'if (displayPersonName("Trishna") !== "Trishna") fail("display");\n'
        'console.log("NAME_OK");\n'.replace("MODULE", module)
    )
    assert "NAME_OK" in _node(body, tmp_path)


# --- pending forms ----------------------------------------------------------
def test_pending_forms_are_safe_without_a_browser(tmp_path):
    """No window/storage: must never throw, and must resolve to 'no pending form'."""
    module = PENDING.as_uri()
    body = (
        'import { savePendingForm, readPendingForm, takePendingForm, clearPendingForm } from "MODULE";\n'
        'const fail = (m) => { console.error("FAIL: " + m); process.exit(1); };\n'
        'savePendingForm("kundli", { name: "Trishna", date: "2026-09-22", time: "15:53", place: "Delhi" });\n'
        'if (readPendingForm("kundli") !== null) fail("must be null without storage");\n'
        'if (takePendingForm("reading") !== null) fail("take must be null without storage");\n'
        'clearPendingForm("life_summary");\n'
        'console.log("PENDING_OK");\n'.replace("MODULE", module)
    )
    assert "PENDING_OK" in _node(body, tmp_path)


def test_pending_forms_store_only_birth_fields_and_expire():
    source = _read(PENDING)
    # Namespaced per product, sessionStorage only, and it expires.
    assert "kavach_pending_v1" in source
    assert "sessionStorage" in source
    assert "MAX_AGE_MS" in source and "30 * 60 * 1000" in source
    # Allow-listed fields only.
    assert "ALLOWED_FIELDS" in source
    for field in ("'date'", "'time'", "'place'", "'latitude'", "'longitude'", "'timezone'", "'name'"):
        assert field in source, field
    # Never any credential material.
    for banned in ("password", "access_token", "refresh_token", "user_id", "secret", "apikey",
                   "authorization"):
        assert banned not in source.lower(), banned
    # Nothing goes in the URL.
    assert "searchParams" not in source and "location.href" not in source


# --- result gate ------------------------------------------------------------
def test_result_gate_copy_and_buttons():
    gate = _read(RESULT_GATE)
    assert "SAVE & VIEW YOUR READING" in gate
    assert "Sign in to view your personalized result and keep it safely in My KAVACH." in gate
    assert "GoogleAuthButton" in gate
    assert "CONTINUE WITH EMAIL" in gate
    assert "loginHref" in gate


@pytest.mark.parametrize("path", [KUNDLI, RESULTS, LIFE_SUMMARY, YOUR_WEEK])
def test_personalized_results_are_not_hidden_behind_login(path):
    source = _read(path)
    # Guest access: the result is shown without an account.
    assert "ResultGate" not in source, f"{path.name} must not hide its result behind sign-in"


@pytest.mark.parametrize("page", ["yes-no", "panchang", "services"])
def test_public_pages_remain_public(page):
    source = _read(FRONTEND / "app" / page / "page.tsx")
    for banned in ("ResultGate", "useAuth", "pendingForms", "loginHref"):
        assert banned not in source, f"{page} must stay public ({banned})"


def test_ask_kavach_is_untouched_by_this_work():
    source = _read(FRONTEND / "app" / "ask" / "page.tsx")
    for banned in ("ResultGate", "pendingForms", "GoogleAuthButton", "signInWithGoogle"):
        assert banned not in source, banned


# --- guest can fill AND reveal ----------------------------------------------
def test_guest_can_generate_the_kundli():
    source = _read(KUNDLI)
    # The form is offered to a guest, and the calculation runs for everyone.
    assert "showName" in source and "requireName" in source
    assert "await fetchKundli(payload)" in source
    # generate() never bounces to login: the only login redirect in the page is
    # the optional "Save to history" action, which is not part of calculation.
    generate_block = source.split("const generate = async", 1)[1].split("const saveToHistory", 1)[0]
    assert "loginHref" not in generate_block
    assert "savePendingForm" not in generate_block


def test_public_tools_no_longer_store_a_pending_form_for_login():
    for path in (KUNDLI, READING, LIFE_SUMMARY, YOUR_WEEK):
        source = _read(path)
        assert "savePendingForm" not in source, path.name
        assert "takePendingForm" not in source, path.name


def test_guest_your_week_result_is_public():
    source = _read(YOUR_WEEK)
    assert "ResultGate" not in source
    assert "savePendingForm('your_week'" not in source
    assert "takePendingForm('your_week')" not in source
    assert "loginHref('/your-week')" not in source
    # The weekly calculation runs for a guest.
    assert "await fetchWeekly(" in source


def test_your_week_pending_state_cannot_collide_with_reading():
    week = _read(YOUR_WEEK)
    # It must never reuse KAVACH Reading's pending key.
    assert "savePendingForm('reading'" not in week
    assert "takePendingForm('reading')" not in week

    pending = _read(PENDING)
    # Each product has its own key, so the stored entries cannot collide.
    assert "storageKey(product)" in pending
    for product in ("'kundli'", "'reading'", "'life_summary'", "'your_week'"):
        assert product in pending, product
    assert "your_week:" in pending, "your_week needs its own allow-list entry"


def test_weekly_calculation_request_is_unchanged():
    """The gate must not alter the weekly request the calculation receives."""
    source = _read(YOUR_WEEK)
    assert "fetchWeekly(" in source
    assert "birth: { date: birthDate" in source and "forecast: { startDate" in source
    weekly_lib = _read(FRONTEND / "lib" / "weekly.ts")
    assert "fetchWeekly" in weekly_lib
    for banned in ("ResultGate", "pendingForms", "useAuth"):
        assert banned not in weekly_lib, banned


def test_person_name_field_is_required_for_new_kundlis():
    source = _read(BIRTH_DETAILS)
    assert "Enter person's name" in source
    assert "person-name-input" in source
    assert "isValidPersonName" in source
    assert "requireName" in source
    assert "normalisePersonName" in source


# --- saving -----------------------------------------------------------------
def test_successful_kundli_is_saved_automatically_for_the_session_user():
    source = _read(KUNDLI)
    assert "saveKundliReading(user.id" in source, "ownership comes from the session user"
    assert "void autoSave(natal, details)" in source
    # Never trust a browser-supplied id.
    for banned in ("user_id", "userId", "localStorage", "searchParams.get('user"):
        assert banned not in source, banned


def test_duplicate_saves_are_prevented():
    source = _read(KUNDLI)
    assert "savedSignatureRef" in source
    assert "if (savedSignatureRef.current === signature) return;" in source
    # A failed save may be retried, a successful one is not repeated.
    assert "savedSignatureRef.current = null" in source


def test_failed_generation_is_not_saved():
    source = _read(KUNDLI)
    # autoSave is only reached after a successful natal fetch.
    fetch_index = source.index("const natal = await fetchKundli(payload)")
    save_index = source.index("void autoSave(natal, details)")
    catch_index = source.index("setError(exc instanceof Error ? exc.message : 'We could not generate")
    assert fetch_index < save_index < catch_index


def test_history_identifies_kundlis_by_person_with_a_fallback():
    source = _read(HISTORY)
    assert "personLabel" in source
    assert "displayPersonName" in source
    assert "Unnamed Kundli" not in source  # the fallback text lives in personName.ts


def test_saved_kundli_is_reopened_from_the_snapshot_not_recalculated():
    source = _read(KUNDLI)
    assert "getReading(user.id, savedId)" in source
    assert "reading.result_data as KundliResponse" in source
    assert "never recalculated" in source


# --- security / database ----------------------------------------------------
def test_rls_and_ownership_are_unchanged():
    sql = _read(MIGRATION)
    assert "enable row level security" in sql
    assert "force row level security" in sql
    assert "auth.uid()" in sql
    assert "revoke all on public.saved_readings from anon" in sql
    for op in ("select", "insert", "update", "delete"):
        assert f"for {op}" in sql, op


def test_no_new_dependencies_were_added():
    package = json.loads(_read(FRONTEND / "package.json"))
    deps = {**package.get("dependencies", {}), **package.get("devDependencies", {})}
    assert "@supabase/supabase-js" in deps
    for banned in ("next-auth", "@auth0/nextjs-auth0", "firebase", "passport", "grant", "simple-oauth2"):
        assert banned not in deps, banned


def test_no_secrets_reachable_from_the_browser():
    for path in (AUTH_TS, GOOGLE_BUTTON, RESULT_GATE, PENDING, PERSON_NAME):
        source = _read(path)
        for banned in ("SERVICE_ROLE", "service_role", "GROQ_API_KEY", "GEMINI_API_KEY",
                       "GEOAPIFY_API_KEY", "client_secret"):
            assert banned not in source, f"{path.name} exposes {banned}"
