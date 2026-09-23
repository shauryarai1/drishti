-- KAVACH — primary + other-person birth profiles
--
-- Apply after 0001, 0002 and 0003. ADDITIVE ONLY: it creates one new table, its
-- indexes, RLS and four ownership policies. It touches nothing else.
--
-- Security model:
--   * user_id references auth.users(id); rows die with the account.
--   * RLS is enabled AND forced, so no owner path can leak.
--   * Four policies, one per operation, each comparing auth.uid() to user_id.
--   * Nothing is granted to `anon`: an unauthenticated client reads nothing.
--   * At most ONE primary profile per user, enforced by a partial unique index
--     (database-level invariant, not just UI).
--   * No derived astrology is stored: natal positions are recalculated from the
--     authoritative engine, so stored values can never go stale.

create extension if not exists "pgcrypto";

create table if not exists public.birth_profiles (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users (id) on delete cascade,
  name text not null default '',
  birth_date text not null,
  birth_time text not null,
  birth_place_name text not null default '',
  latitude double precision,
  longitude double precision,
  timezone text not null default 'Asia/Kolkata',
  -- The account owner's own profile. Other-person profiles are is_primary=false.
  is_primary boolean not null default false,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists birth_profiles_user_created_idx
  on public.birth_profiles (user_id, created_at desc);

-- Maximum one primary profile per user.
create unique index if not exists birth_profiles_one_primary_idx
  on public.birth_profiles (user_id)
  where is_primary;

alter table public.birth_profiles enable row level security;
alter table public.birth_profiles force row level security;

-- Explicit grants: the browser client uses the authenticated role only.
revoke all on public.birth_profiles from anon;
grant select, insert, update, delete on public.birth_profiles to authenticated;

drop policy if exists "birth_profiles_select_own" on public.birth_profiles;
create policy "birth_profiles_select_own"
  on public.birth_profiles for select
  to authenticated
  using ((select auth.uid()) = user_id);

drop policy if exists "birth_profiles_insert_own" on public.birth_profiles;
create policy "birth_profiles_insert_own"
  on public.birth_profiles for insert
  to authenticated
  with check ((select auth.uid()) = user_id);

drop policy if exists "birth_profiles_update_own" on public.birth_profiles;
create policy "birth_profiles_update_own"
  on public.birth_profiles for update
  to authenticated
  using ((select auth.uid()) = user_id)
  with check ((select auth.uid()) = user_id);

drop policy if exists "birth_profiles_delete_own" on public.birth_profiles;
create policy "birth_profiles_delete_own"
  on public.birth_profiles for delete
  to authenticated
  using ((select auth.uid()) = user_id);

-- Reuse the updated_at trigger function created in 0001 (no duplicate function).
drop trigger if exists birth_profiles_touch_updated_at on public.birth_profiles;
create trigger birth_profiles_touch_updated_at
  before update on public.birth_profiles
  for each row execute function public.kavach_touch_updated_at();
