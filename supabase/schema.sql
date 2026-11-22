-- Run this once in Supabase: Dashboard -> SQL Editor -> New query -> paste -> Run.

create table if not exists public.tickets (
  id                  bigint generated always as identity primary key,
  name                text        not null check (char_length(name) between 1 and 100),
  email               text        not null check (char_length(email) <= 254),
  message             text        not null check (char_length(message) between 10 and 2000),
  category            text        not null default 'UNCLEAR',
  category_confidence real        not null default 0,
  priority            text        not null default 'low'  check (priority in ('low','medium','high')),
  status              text        not null default 'open' check (status in ('open','in_progress','resolved','closed')),
  draft_status        text        not null default 'pending' check (draft_status in ('pending','ready','no_match','failed')),
  draft_reply         text,
  draft_sources       jsonb,
  draft_flags         jsonb,
  created_at          timestamptz not null default now(),
  updated_at          timestamptz not null default now()
);

create index if not exists tickets_category_idx on public.tickets (category);
create index if not exists tickets_status_idx   on public.tickets (status);
create index if not exists tickets_created_idx  on public.tickets (created_at desc);

create or replace function public.set_updated_at() returns trigger as $$
begin new.updated_at = now(); return new; end; $$ language plpgsql;

drop trigger if exists tickets_set_updated_at on public.tickets;
create trigger tickets_set_updated_at before update on public.tickets
  for each row execute function public.set_updated_at();

-- Security: RLS ON and NO policies => the public (anon) key can not read or write tickets.
-- Only the backend, using the SERVICE ROLE key (bypasses RLS), can access this table.
alter table public.tickets enable row level security;
