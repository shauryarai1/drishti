"""Structural security guardrails for accounts + private reading history.

Scope of these tests: the artefacts this repository actually controls — the RLS
migration SQL, environment handling, and the browser data-access layer.

They do NOT prove live row level security behaviour: that can only be verified
against a real Supabase project (see the final report). Nothing here fakes it.
"""

from __future__ import annotations

import pathlib
import re

REPO = pathlib.Path(__file__).resolve().parents[2]
FRONTEND = REPO / "frontend-next"
MIGRATION = REPO / "supabase" / "migrations" / "0001_saved_readings.sql"


def sql_lower() -> str:
    return MIGRATION.read_text(encoding="utf-8").lower()


def frontend_sources():
    for path in FRONTEND.rglob("*.ts*"):
        if "node_modules" in path.parts or ".next" in path.parts:
            continue
        yield path


def strip_comments(text: str) -> str:
    """Prose may mention secrets; only real code should fail these checks."""
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    text = re.sub(r"//.*", "", text)
    return text


def test_migration_file_exists_and_targets_expected_table():
    assert MIGRATION.is_file(), "missing saved_readings migration"
    assert "create table if not exists public.saved_readings" in sql_lower()


def test_table_has_extensible_history_model():
    body = sql_lower()
    for column in (
        "id uuid primary key",
        "user_id uuid not null",
        "type text not null",
        "title text not null",
        "input_data jsonb not null",
        "result_data jsonb",
        "schema_version integer not null",
        "created_at timestamptz not null",
        "updated_at timestamptz not null",
    ):
        assert column in body, column


def test_type_is_constrained_to_known_reading_types():
    body = sql_lower()
    assert "check (type in" in body
    for reading_type in ("kundli", "daily", "weekly", "life_summary", "dasha", "ask"):
        assert f"'{reading_type}'" in body


def test_user_id_is_owned_by_auth_users_and_cascades():
    body = sql_lower()
    assert "references auth.users (id)" in body or "references auth.users(id)" in body
    assert "on delete cascade" in body


def test_row_level_security_is_enabled_and_forced():
    body = sql_lower()
    assert "alter table public.saved_readings enable row level security" in body
    assert "force row level security" in body


def test_four_policies_exist_one_per_operation():
    body = sql_lower()
    for operation in ("for select", "for insert", "for update", "for delete"):
        assert operation in body
    assert len(re.findall(r"create policy", body)) == 4


def test_every_policy_compares_authenticated_identity_to_row_ownership():
    body = sql_lower()
    policies = re.findall(r"create policy.*?;", body, flags=re.DOTALL)
    assert len(policies) == 4
    for policy in policies:
        assert "auth.uid()" in policy, policy
        assert "user_id" in policy, policy


def test_insert_and_update_policies_validate_the_written_owner():
    body = sql_lower()
    assert body.count("with check") >= 2


def test_no_public_or_anon_read_path():
    body = sql_lower()
    for forbidden in ("using (true)", "using(true)", "to anon", "to public", "for select using (true)"):
        assert forbidden not in body, forbidden
    assert "revoke all on public.saved_readings from anon" in body
    assert "grant select, insert, update, delete on public.saved_readings to authenticated" in body


def test_migration_is_non_destructive():
    body = sql_lower()
    for destructive in (
        "drop table",
        "truncate",
        "delete from",
        "disable row level security",
        "alter table public.saved_readings drop",
    ):
        assert destructive not in body, destructive


def test_frontend_never_references_a_service_role_key():
    offenders = []
    for path in frontend_sources():
        code = strip_comments(path.read_text(encoding="utf-8", errors="ignore")).lower()
        if "service_role" in code or "service-role" in code or "supabase_service" in code:
            offenders.append(str(path))
    assert offenders == [], offenders


def test_only_public_supabase_variables_are_read_in_the_browser_client():
    code = strip_comments((FRONTEND / "lib" / "supabase.ts").read_text(encoding="utf-8"))
    assert "NEXT_PUBLIC_SUPABASE_URL" in code
    assert "NEXT_PUBLIC_SUPABASE_ANON_KEY" in code
    assert "process.env.SUPABASE" not in code
    assert "SERVICE" not in code.upper()
    assert "SECRET" not in code.upper()


def test_history_layer_scopes_every_query_to_the_signed_in_user():
    source = (FRONTEND / "lib" / "history.ts").read_text(encoding="utf-8")
    assert "HISTORY_TABLE" in source
    chunks = source.split("HISTORY_TABLE)")
    assert len(chunks) >= 5, "expected list/get/save/rename/delete paths"
    for chunk in chunks[1:]:
        statement = chunk.split(";")[0]
        assert "user_id" in statement, statement


def test_auth_layer_never_stores_credentials_itself():
    for name in ("auth.tsx", "supabase.ts", "history.ts"):
        source = (FRONTEND / "lib" / name).read_text(encoding="utf-8").lower()
        assert "localstorage" not in source, name
        assert "password_hash" not in source, name
        assert "bcrypt" not in source, name


def test_supabase_env_example_names_have_no_values():
    example = (FRONTEND / ".env.example").read_text(encoding="utf-8")
    supabase_lines = [line.strip() for line in example.splitlines() if "SUPABASE" in line]
    assert "NEXT_PUBLIC_SUPABASE_URL=" in supabase_lines
    assert "NEXT_PUBLIC_SUPABASE_ANON_KEY=" in supabase_lines
    for line in supabase_lines:
        assert line.endswith("="), f"a value was committed: {line}"


def test_no_server_secret_names_in_frontend_env_example():
    example = (FRONTEND / ".env.example").read_text(encoding="utf-8").upper()
    for forbidden in ("SERVICE_ROLE", "SECRET", "DATABASE_URL", "GEMINI"):
        assert forbidden not in example, forbidden


def test_env_files_are_gitignored():
    ignore = (REPO / ".gitignore").read_text(encoding="utf-8")
    assert ".env" in ignore
    assert ".env.*" in ignore
    assert "!.env.example" in ignore
