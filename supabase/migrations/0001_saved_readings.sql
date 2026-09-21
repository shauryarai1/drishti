-- KAVACH — private reading history
--
-- Apply this to the Supabase project (SQL editor, or `supabase db push`).
-- It is additive and non-destructive: it creates one new table, one helper
-- function and one trigger. It does not touch, drop or reset anything else.
--
-- Security model:
--   * user_id references auth.users(id); rows die with the account.
--   * Row level security is enabled AND forced, so no table owner path leaks.
--   * Four policies, one per operation, each comparing auth.uid() to user_id.
--   * Nothing is granted to `anon`: an unauthenticated client can read nothing.

create extension if not exists "pgcrypto";

create table if not exists public.saved_readings (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users (id) on delete cascade,
  type text not null
    check (type in ('kundli', 'daily', 'weekly', 'life_summary', 'dasha', 'ask')),
  title text not null default '',
  input_data jsonb not null default '{}'::jsonb,
  result_data jsonb,
  schema_version integer not null default 1,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists saved_readings_user_created_idx
  on public.saved_readings (user_id, created_at desc);

alter table public.saved_readings enable row level security;
alter table public.saved_readings force row level security;

-- Explicit grants: the browser client uses the authenticated role only.
revoke all on public.saved_readings from anon;
grant select, insert, update, delete on public.saved_readings to authenticated;

drop policy if exists "saved_readings_select_own" on public.saved_readings;
create policy "saved_readings_select_own"
  on public.saved_readings for select
  to authenticated
  using ((select auth.uid()) = user_id);

drop policy if exists "saved_readings_insert_own" on public.saved_readings;
create policy "saved_readings_insert_own"
  on public.saved_readings for insert
  to authenticated
  with check ((select auth.uid()) = user_id);

drop policy if exists "saved_readings_update_own" on public.saved_readings;
create policy "saved_readings_update_own"
  on public.saved_readings for update
  to authenticated
  using ((select auth.uid()) = user_id)
  with check ((select auth.uid()) = user_id);

drop policy if exists "saved_readings_delete_own" on public.saved_readings;
create policy "saved_readings_delete_own"
  on public.saved_readings for delete
  to authenticated
  using ((select auth.uid()) = user_id);

create or replace function public.kavach_touch_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

drop trigger if exists saved_readings_touch_updated_at on public.saved_readings;
create trigger saved_readings_touch_updated_at
  before update on public.saved_readings
  for each row execute function public.kavach_touch_updated_at();
