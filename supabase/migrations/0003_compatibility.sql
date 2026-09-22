-- KAVACH — marriage compatibility reports
--
-- Apply after 0001 and 0002. ADDITIVE ONLY: it widens two CHECK constraints so
-- the new `compatibility` product is a valid value.
--
-- It does NOT touch tables, columns, data, access rules or policies:
--   * `saved_readings` keeps RLS enabled AND forced, with the same four
--     ownership policies (auth.uid() = user_id) from 0001.
--   * `product_submissions` / `admin_users` keep their browser-side lockout and
--     RLS from 0002.
--   * Historical rows are unaffected; the widened constraint only ADMITS a new
--     value, it never invalidates an existing one.

alter table public.saved_readings
  drop constraint if exists saved_readings_type_check;
alter table public.saved_readings
  add constraint saved_readings_type_check
  check (type in ('kundli', 'daily', 'weekly', 'life_summary', 'dasha', 'ask', 'compatibility'));

alter table public.product_submissions
  drop constraint if exists product_submissions_product_check;
alter table public.product_submissions
  add constraint product_submissions_product_check
  check (product in ('kundli', 'reading', 'daily', 'weekly', 'life_summary', 'dasha', 'ask',
                     'panchang', 'compatibility'));
