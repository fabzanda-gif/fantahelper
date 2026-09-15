-- fantahe1per: hardening RLS for the existing Streamlit app and future Next.js app.
-- Registered in Supabase migration history as 20260915211111.
--
-- Prerequisite before applying:
--   assign {"role":"admin"} in auth.users.raw_app_meta_data to every admin,
--   then refresh their Supabase sessions so the signed JWT contains the role.

begin;

-- The standings view must honor the caller and the RLS policies of its tables.
alter view public.league_standings_v set (security_invoker = true);

-- All public tables exposed through the Data API must use RLS.
alter table public.players enable row level security;
alter table public.rosters enable row level security;
alter table public.player_strategy_notes enable row level security;
alter table public.league_rounds enable row level security;
alter table public.league_fixtures enable row level security;
alter table public.lineup_submissions enable row level security;
alter table public.lineup_players enable row level security;
alter table public.player_round_scores enable row level security;
alter table public.league_scoring_rules enable row level security;

-- Remove broad grants. Anonymous users only need the team list during signup.
revoke all on table
  public.teams,
  public.players,
  public.rosters,
  public.user_team_assignments,
  public.user_strategy_settings,
  public.player_strategy_notes,
  public.league_rounds,
  public.league_fixtures,
  public.lineup_submissions,
  public.lineup_players,
  public.player_round_scores,
  public.league_scoring_rules,
  public.league_standings_v
from anon, authenticated;

grant select on table public.teams to anon;

grant select on table
  public.teams,
  public.players,
  public.rosters,
  public.player_strategy_notes,
  public.league_rounds,
  public.league_fixtures,
  public.lineup_submissions,
  public.lineup_players,
  public.player_round_scores,
  public.league_scoring_rules,
  public.league_standings_v
to authenticated;

grant insert, update on table
  public.user_team_assignments,
  public.user_strategy_settings
to authenticated;

grant select on table
  public.user_team_assignments,
  public.user_strategy_settings
to authenticated;

-- RLS remains the authorization layer for these grants. Only a signed admin
-- app_metadata claim can pass the write policies below.
grant insert, update, delete on table
  public.teams,
  public.players,
  public.rosters,
  public.player_strategy_notes,
  public.league_rounds,
  public.league_fixtures,
  public.lineup_submissions,
  public.lineup_players,
  public.player_round_scores,
  public.league_scoring_rules
to authenticated;

-- Optimize the existing ownership policies and preserve their behavior.
drop policy if exists "Users can read own team assignment" on public.user_team_assignments;
drop policy if exists "Users can create own team assignment" on public.user_team_assignments;
drop policy if exists "Users can update own team assignment" on public.user_team_assignments;

create policy "Users can read own team assignment"
on public.user_team_assignments for select
to authenticated
using ((select auth.uid()) = user_id);

create policy "Users can create own team assignment"
on public.user_team_assignments for insert
to authenticated
with check ((select auth.uid()) = user_id);

create policy "Users can update own team assignment"
on public.user_team_assignments for update
to authenticated
using ((select auth.uid()) = user_id)
with check ((select auth.uid()) = user_id);

drop policy if exists "Users can read own strategy" on public.user_strategy_settings;
drop policy if exists "Users can insert own strategy" on public.user_strategy_settings;
drop policy if exists "Users can update own strategy" on public.user_strategy_settings;

create policy "Users can read own strategy"
on public.user_strategy_settings for select
to authenticated
using ((select auth.uid()) = user_id);

create policy "Users can insert own strategy"
on public.user_strategy_settings for insert
to authenticated
with check ((select auth.uid()) = user_id);

create policy "Users can update own strategy"
on public.user_strategy_settings for update
to authenticated
using ((select auth.uid()) = user_id)
with check ((select auth.uid()) = user_id);

-- Allow safe re-application when the SQL was first run manually in Studio.
drop policy if exists "Authenticated users can read players" on public.players;
drop policy if exists "Authenticated users can read rosters" on public.rosters;
drop policy if exists "Authenticated users can read strategy notes" on public.player_strategy_notes;
drop policy if exists "Authenticated users can read league rounds" on public.league_rounds;
drop policy if exists "Authenticated users can read league fixtures" on public.league_fixtures;
drop policy if exists "Authenticated users can read lineup submissions" on public.lineup_submissions;
drop policy if exists "Authenticated users can read lineup players" on public.lineup_players;
drop policy if exists "Authenticated users can read player round scores" on public.player_round_scores;
drop policy if exists "Authenticated users can read scoring rules" on public.league_scoring_rules;

drop policy if exists "Admins can insert teams" on public.teams;
drop policy if exists "Admins can update teams" on public.teams;
drop policy if exists "Admins can delete teams" on public.teams;
drop policy if exists "Admins can insert players" on public.players;
drop policy if exists "Admins can update players" on public.players;
drop policy if exists "Admins can delete players" on public.players;
drop policy if exists "Admins can insert rosters" on public.rosters;
drop policy if exists "Admins can update rosters" on public.rosters;
drop policy if exists "Admins can delete rosters" on public.rosters;
drop policy if exists "Admins can insert strategy notes" on public.player_strategy_notes;
drop policy if exists "Admins can update strategy notes" on public.player_strategy_notes;
drop policy if exists "Admins can delete strategy notes" on public.player_strategy_notes;
drop policy if exists "Admins can insert league rounds" on public.league_rounds;
drop policy if exists "Admins can update league rounds" on public.league_rounds;
drop policy if exists "Admins can delete league rounds" on public.league_rounds;
drop policy if exists "Admins can insert league fixtures" on public.league_fixtures;
drop policy if exists "Admins can update league fixtures" on public.league_fixtures;
drop policy if exists "Admins can delete league fixtures" on public.league_fixtures;
drop policy if exists "Admins can insert lineup submissions" on public.lineup_submissions;
drop policy if exists "Admins can update lineup submissions" on public.lineup_submissions;
drop policy if exists "Admins can delete lineup submissions" on public.lineup_submissions;
drop policy if exists "Admins can insert lineup players" on public.lineup_players;
drop policy if exists "Admins can update lineup players" on public.lineup_players;
drop policy if exists "Admins can delete lineup players" on public.lineup_players;
drop policy if exists "Admins can insert player round scores" on public.player_round_scores;
drop policy if exists "Admins can update player round scores" on public.player_round_scores;
drop policy if exists "Admins can delete player round scores" on public.player_round_scores;
drop policy if exists "Admins can insert scoring rules" on public.league_scoring_rules;
drop policy if exists "Admins can update scoring rules" on public.league_scoring_rules;
drop policy if exists "Admins can delete scoring rules" on public.league_scoring_rules;

-- League members may read shared league data after authentication.
create policy "Authenticated users can read players"
on public.players for select to authenticated using (true);

create policy "Authenticated users can read rosters"
on public.rosters for select to authenticated using (true);

create policy "Authenticated users can read strategy notes"
on public.player_strategy_notes for select to authenticated using (true);

create policy "Authenticated users can read league rounds"
on public.league_rounds for select to authenticated using (true);

create policy "Authenticated users can read league fixtures"
on public.league_fixtures for select to authenticated using (true);

create policy "Authenticated users can read lineup submissions"
on public.lineup_submissions for select to authenticated using (true);

create policy "Authenticated users can read lineup players"
on public.lineup_players for select to authenticated using (true);

create policy "Authenticated users can read player round scores"
on public.player_round_scores for select to authenticated using (true);

create policy "Authenticated users can read scoring rules"
on public.league_scoring_rules for select to authenticated using (true);

-- Admin writes. Separate policies avoid duplicate SELECT policies, while
-- (select auth.jwt()) is evaluated once per statement by the planner.
create policy "Admins can insert teams" on public.teams for insert to authenticated
with check (((select auth.jwt()) -> 'app_metadata' ->> 'role') = 'admin');
create policy "Admins can update teams" on public.teams for update to authenticated
using (((select auth.jwt()) -> 'app_metadata' ->> 'role') = 'admin')
with check (((select auth.jwt()) -> 'app_metadata' ->> 'role') = 'admin');
create policy "Admins can delete teams" on public.teams for delete to authenticated
using (((select auth.jwt()) -> 'app_metadata' ->> 'role') = 'admin');

create policy "Admins can insert players" on public.players for insert to authenticated
with check (((select auth.jwt()) -> 'app_metadata' ->> 'role') = 'admin');
create policy "Admins can update players" on public.players for update to authenticated
using (((select auth.jwt()) -> 'app_metadata' ->> 'role') = 'admin')
with check (((select auth.jwt()) -> 'app_metadata' ->> 'role') = 'admin');
create policy "Admins can delete players" on public.players for delete to authenticated
using (((select auth.jwt()) -> 'app_metadata' ->> 'role') = 'admin');

create policy "Admins can insert rosters" on public.rosters for insert to authenticated
with check (((select auth.jwt()) -> 'app_metadata' ->> 'role') = 'admin');
create policy "Admins can update rosters" on public.rosters for update to authenticated
using (((select auth.jwt()) -> 'app_metadata' ->> 'role') = 'admin')
with check (((select auth.jwt()) -> 'app_metadata' ->> 'role') = 'admin');
create policy "Admins can delete rosters" on public.rosters for delete to authenticated
using (((select auth.jwt()) -> 'app_metadata' ->> 'role') = 'admin');

create policy "Admins can insert strategy notes" on public.player_strategy_notes for insert to authenticated
with check (((select auth.jwt()) -> 'app_metadata' ->> 'role') = 'admin');
create policy "Admins can update strategy notes" on public.player_strategy_notes for update to authenticated
using (((select auth.jwt()) -> 'app_metadata' ->> 'role') = 'admin')
with check (((select auth.jwt()) -> 'app_metadata' ->> 'role') = 'admin');
create policy "Admins can delete strategy notes" on public.player_strategy_notes for delete to authenticated
using (((select auth.jwt()) -> 'app_metadata' ->> 'role') = 'admin');

create policy "Admins can insert league rounds" on public.league_rounds for insert to authenticated
with check (((select auth.jwt()) -> 'app_metadata' ->> 'role') = 'admin');
create policy "Admins can update league rounds" on public.league_rounds for update to authenticated
using (((select auth.jwt()) -> 'app_metadata' ->> 'role') = 'admin')
with check (((select auth.jwt()) -> 'app_metadata' ->> 'role') = 'admin');
create policy "Admins can delete league rounds" on public.league_rounds for delete to authenticated
using (((select auth.jwt()) -> 'app_metadata' ->> 'role') = 'admin');

create policy "Admins can insert league fixtures" on public.league_fixtures for insert to authenticated
with check (((select auth.jwt()) -> 'app_metadata' ->> 'role') = 'admin');
create policy "Admins can update league fixtures" on public.league_fixtures for update to authenticated
using (((select auth.jwt()) -> 'app_metadata' ->> 'role') = 'admin')
with check (((select auth.jwt()) -> 'app_metadata' ->> 'role') = 'admin');
create policy "Admins can delete league fixtures" on public.league_fixtures for delete to authenticated
using (((select auth.jwt()) -> 'app_metadata' ->> 'role') = 'admin');

create policy "Admins can insert lineup submissions" on public.lineup_submissions for insert to authenticated
with check (((select auth.jwt()) -> 'app_metadata' ->> 'role') = 'admin');
create policy "Admins can update lineup submissions" on public.lineup_submissions for update to authenticated
using (((select auth.jwt()) -> 'app_metadata' ->> 'role') = 'admin')
with check (((select auth.jwt()) -> 'app_metadata' ->> 'role') = 'admin');
create policy "Admins can delete lineup submissions" on public.lineup_submissions for delete to authenticated
using (((select auth.jwt()) -> 'app_metadata' ->> 'role') = 'admin');

create policy "Admins can insert lineup players" on public.lineup_players for insert to authenticated
with check (((select auth.jwt()) -> 'app_metadata' ->> 'role') = 'admin');
create policy "Admins can update lineup players" on public.lineup_players for update to authenticated
using (((select auth.jwt()) -> 'app_metadata' ->> 'role') = 'admin')
with check (((select auth.jwt()) -> 'app_metadata' ->> 'role') = 'admin');
create policy "Admins can delete lineup players" on public.lineup_players for delete to authenticated
using (((select auth.jwt()) -> 'app_metadata' ->> 'role') = 'admin');

create policy "Admins can insert player round scores" on public.player_round_scores for insert to authenticated
with check (((select auth.jwt()) -> 'app_metadata' ->> 'role') = 'admin');
create policy "Admins can update player round scores" on public.player_round_scores for update to authenticated
using (((select auth.jwt()) -> 'app_metadata' ->> 'role') = 'admin')
with check (((select auth.jwt()) -> 'app_metadata' ->> 'role') = 'admin');
create policy "Admins can delete player round scores" on public.player_round_scores for delete to authenticated
using (((select auth.jwt()) -> 'app_metadata' ->> 'role') = 'admin');

create policy "Admins can insert scoring rules" on public.league_scoring_rules for insert to authenticated
with check (((select auth.jwt()) -> 'app_metadata' ->> 'role') = 'admin');
create policy "Admins can update scoring rules" on public.league_scoring_rules for update to authenticated
using (((select auth.jwt()) -> 'app_metadata' ->> 'role') = 'admin')
with check (((select auth.jwt()) -> 'app_metadata' ->> 'role') = 'admin');
create policy "Admins can delete scoring rules" on public.league_scoring_rules for delete to authenticated
using (((select auth.jwt()) -> 'app_metadata' ->> 'role') = 'admin');

commit;
