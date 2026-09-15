-- Manual rollback for 20260915211111_rls_hardening.sql
-- Stored outside migrations so Supabase CLI never applies it automatically.
-- This restores the previous permissive and insecure access model.

begin;

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

drop policy if exists "Authenticated users can read players" on public.players;
drop policy if exists "Authenticated users can read rosters" on public.rosters;
drop policy if exists "Authenticated users can read strategy notes" on public.player_strategy_notes;
drop policy if exists "Authenticated users can read league rounds" on public.league_rounds;
drop policy if exists "Authenticated users can read league fixtures" on public.league_fixtures;
drop policy if exists "Authenticated users can read lineup submissions" on public.lineup_submissions;
drop policy if exists "Authenticated users can read lineup players" on public.lineup_players;
drop policy if exists "Authenticated users can read player round scores" on public.player_round_scores;
drop policy if exists "Authenticated users can read scoring rules" on public.league_scoring_rules;

alter table public.players disable row level security;
alter table public.rosters disable row level security;
alter table public.player_strategy_notes disable row level security;
alter table public.league_rounds disable row level security;
alter table public.league_fixtures disable row level security;
alter table public.lineup_submissions disable row level security;
alter table public.lineup_players disable row level security;
alter table public.player_round_scores disable row level security;
alter table public.league_scoring_rules disable row level security;

alter view public.league_standings_v set (security_invoker = false);

grant all on table
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
to anon, authenticated;

-- Restore the original, functionally equivalent ownership policies.
drop policy if exists "Users can read own team assignment" on public.user_team_assignments;
drop policy if exists "Users can create own team assignment" on public.user_team_assignments;
drop policy if exists "Users can update own team assignment" on public.user_team_assignments;

create policy "Users can read own team assignment"
on public.user_team_assignments for select
to authenticated using (auth.uid() = user_id);

create policy "Users can create own team assignment"
on public.user_team_assignments for insert
to authenticated with check (auth.uid() = user_id);

create policy "Users can update own team assignment"
on public.user_team_assignments for update
to authenticated
using (auth.uid() = user_id)
with check (auth.uid() = user_id);

drop policy if exists "Users can read own strategy" on public.user_strategy_settings;
drop policy if exists "Users can insert own strategy" on public.user_strategy_settings;
drop policy if exists "Users can update own strategy" on public.user_strategy_settings;

create policy "Users can read own strategy"
on public.user_strategy_settings for select
to authenticated using (auth.uid() = user_id);

create policy "Users can insert own strategy"
on public.user_strategy_settings for insert
to authenticated with check (auth.uid() = user_id);

create policy "Users can update own strategy"
on public.user_strategy_settings for update
to authenticated
using (auth.uid() = user_id)
with check (auth.uid() = user_id);

commit;
