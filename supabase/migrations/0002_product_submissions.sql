-- KAVACH — owner-visible archive of product submissions
--
-- Apply after 0001. Additive and non-destructive: it creates two new tables.
--
-- Security model:
--   * This archive is NOT user history. `saved_readings` (0001) is untouched.
--   * Neither `anon` nor `authenticated` is granted anything on these tables, so
--     no browser client (guest or signed in) can read or write them at all.
--   * Only the trusted FastAPI server reaches them, using the service-role key,
--     which is server-side only and never shipped to the frontend.
--   * RLS is enabled and forced as defence in depth should a grant ever appear.

create table if not exists public.product_submissions (
  id uuid primary key default gen_random_uuid(),
  created_at timestamptz not null default now(),
  completed_at timestamptz,
  user_id uuid references auth.users (id) on delete set null,
  visitor_session_id text,
  product text not null
    check (product in ('kundli', 'reading', 'daily', 'weekly', 'life_summary', 'dasha', 'ask', 'panchang')),
  status text not null default 'SUCCEEDED'
    check (status in ('SUCCEEDED', 'FAILED')),
  input_data jsonb not null default '{}'::jsonb,
  result_data jsonb,
  error_category text,
  schema_version integer not null default 1
);

create index if not exists product_submissions_created_idx
  on public.product_submissions (created_at desc);
create index if not exists product_submissions_product_created_idx
  on public.product_submissions (product, created_at desc);
create index if not exists product_submissions_user_created_idx
  on public.product_submissions (user_id, created_at desc);

alter table public.product_submissions enable row level security;
alter table public.product_submissions force row level security;

-- No browser-side access: the server is the only writer and reader.
revoke all on public.product_submissions from anon;
revoke all on public.product_submissions from authenticated;

-- Explicit admin registry. Membership is data, never a frontend flag.
create table if not exists public.admin_users (
  user_id uuid primary key references auth.users (id) on delete cascade,
  created_at timestamptz not null default now(),
  note text
);

alter table public.admin_users enable row level security;
alter table public.admin_users force row level security;

revoke all on public.admin_users from anon;
revoke all on public.admin_users from authenticated;

-- Register the owner as an administrator (replace the UUID with the owner's
-- auth.users id, found in Supabase → Authentication → Users):
--   insert into public.admin_users (user_id, note)
--   values ('00000000-0000-0000-0000-000000000000', 'KAVACH owner')
--   on conflict (user_id) do nothing;
