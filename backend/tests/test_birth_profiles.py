"""Birth profiles: schema/RLS invariants + access-layer safety.

Database-level checks inspect the migration SQL (the Supabase project applies
migrations outside the test suite); the frontend checks lock the access layer's
ownership and privacy rules. Nothing here tests astrology.
"""

from __future__ import annotations

import pathlib
import re

REPO = pathlib.Path(__file__).resolve().parents[2]
MIGRATION = REPO / "supabase" / "migrations" / "0004_birth_profiles.sql"
LIB = REPO / "frontend-next" / "lib" / "profiles.ts"


def _sql() -> str:
    return MIGRATION.read_text(encoding="utf-8")


def _lib() -> str:
    return LIB.read_text(encoding="utf-8")


# --- migration: additive + ownership ----------------------------------------
def test_migration_is_additive_and_does_not_touch_history():
    sql = _sql()
    assert "create table if not exists public.birth_profiles" in sql
    for banned in ("drop table", "alter table public.saved_readings",
                   "alter table public.product_submissions", "delete from"):
        assert banned not in sql.lower(), banned
    # The three earlier migrations are untouched.
    for name in ("0001_saved_readings.sql", "0002_product_submissions.sql",
                 "0003_compatibility.sql"):
        assert "birth_profiles" not in (REPO / "supabase" / "migrations" / name).read_text(encoding="utf-8")


def test_rls_is_enabled_and_forced_with_no_anonymous_access():
    sql = _sql()
    assert "enable row level security" in sql
    assert "force row level security" in sql
    assert "revoke all on public.birth_profiles from anon" in sql
    assert "grant select, insert, update, delete on public.birth_profiles to authenticated" in sql
    assert "to anon" not in sql.split("create policy")[1], "no anon policy"


def test_every_policy_is_owned_by_auth_uid():
    sql = _sql()
    for op in ("select", "insert", "update", "delete"):
        assert f'for {op}' in sql, op
    assert sql.count("(select auth.uid()) = user_id") >= 4
    # INSERT must also constrain the written row.
    assert "with check ((select auth.uid()) = user_id)" in sql
    assert "using ((select auth.uid()) = user_id)" in sql


def test_max_one_primary_profile_is_enforced_in_the_database():
    sql = _sql()
    assert "create unique index if not exists birth_profiles_one_primary_idx" in sql
    assert "on public.birth_profiles (user_id)" in sql
    assert "where is_primary" in sql


def test_user_id_owns_rows_and_dies_with_the_account():
    sql = _sql()
    assert "user_id uuid not null references auth.users (id) on delete cascade" in sql


def test_no_derived_astrology_is_stored():
    """Moon Rashi / Janma Nakshatra must be recalculated, never cached stale."""
    sql = _sql().lower()
    for banned in ("nakshatra", "moon_rashi", "moon_sign", "lagna", "rashi"):
        assert banned not in sql, banned


# --- access layer: ownership + privacy --------------------------------------
def test_every_operation_is_scoped_to_the_session_user():
    lib = _lib()
    assert ".eq('user_id', userId)" in lib
    assert "user_id: userId" in lib
    # A browser-supplied identity is never trusted for writes.
    assert "auth.uid()" not in lib  # that is the database's job


def test_primary_invariants_are_respected_by_the_access_layer():
    lib = _lib()
    # Only the one-time setup creates a primary; other people are never primary.
    assert lib.count("is_primary: true") >= 1
    assert "is_primary: false" in lib
    assert "export async function createPrimaryProfile" in lib
    assert "export async function createOtherPerson" in lib
    # Editing never changes primary status, and deleting refuses the primary.
    assert ".eq('is_primary', false)" in lib, "other-person delete must exclude the primary"
    # Promotion demotes first so the unique index is never violated.
    promotion = lib.split("export async function makePrimary")[1]
    assert promotion.index("is_primary: false") < promotion.index("is_primary: true")


def test_profile_errors_are_generic_and_never_leak_internals():
    lib = _lib()
    for banned in ("error.message", "error.details", "error.hint", "error.code", "console."):
        assert banned not in lib, banned
    assert "Please try again." in lib


def test_birth_details_are_never_persisted_client_side_or_logged():
    lib = _lib()
    for banned in ("localStorage", "sessionStorage", "analytics", "trackEvent",
                   "console.log", "console.error", "URLSearchParams", "location.href"):
        assert banned not in lib, banned


def test_no_service_role_or_secret_in_the_frontend_layer():
    lib = _lib()
    for banned in ("SERVICE_ROLE", "service_role", "sb_secret", "GROQ_API_KEY",
                   "GEMINI_API_KEY", "GEOAPIFY_API_KEY"):
        assert banned not in lib, banned


def test_profiles_use_the_existing_supabase_session_client():
    lib = _lib()
    assert "from './supabase'" in lib and "getSupabase" in lib
    assert "createClient" not in lib, "must reuse the shared browser client"
