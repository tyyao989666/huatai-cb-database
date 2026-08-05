-- Run this once in Supabase SQL Editor.  Users can only see their own rows.
create table if not exists public.saved_screens (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  name text not null check (char_length(name) between 1 and 80),
  payload jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (user_id, name)
);

create table if not exists public.watchlist (
  user_id uuid not null references auth.users(id) on delete cascade,
  bond_code text not null,
  added_at timestamptz not null default now(),
  primary key (user_id, bond_code)
);

create or replace function public.set_updated_at()
returns trigger language plpgsql security invoker as $$
begin new.updated_at = now(); return new; end;
$$;

drop trigger if exists set_saved_screens_updated_at on public.saved_screens;
create trigger set_saved_screens_updated_at
before update on public.saved_screens
for each row execute function public.set_updated_at();

alter table public.saved_screens enable row level security;
alter table public.watchlist enable row level security;

drop policy if exists "Users manage own screens" on public.saved_screens;
create policy "Users manage own screens" on public.saved_screens
for all to authenticated using ((select auth.uid()) = user_id) with check ((select auth.uid()) = user_id);

drop policy if exists "Users manage own watchlist" on public.watchlist;
create policy "Users manage own watchlist" on public.watchlist
for all to authenticated using ((select auth.uid()) = user_id) with check ((select auth.uid()) = user_id);
