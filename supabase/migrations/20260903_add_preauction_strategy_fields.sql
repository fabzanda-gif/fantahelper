begin;

alter table public.player_strategy_notes
    add column if not exists source_role text,
    add column if not exists suggested_price integer,
    add column if not exists average_auction_percent numeric(6,3),
    add column if not exists source_quote integer;

alter table public.player_strategy_notes
    drop constraint if exists player_strategy_notes_source_role_check,
    add constraint player_strategy_notes_source_role_check
        check (source_role is null or source_role in ('P', 'D', 'C', 'A')),
    drop constraint if exists player_strategy_notes_suggested_price_check,
    add constraint player_strategy_notes_suggested_price_check
        check (suggested_price is null or suggested_price >= 0),
    drop constraint if exists player_strategy_notes_average_auction_percent_check,
    add constraint player_strategy_notes_average_auction_percent_check
        check (
            average_auction_percent is null
            or average_auction_percent between 0 and 100
        ),
    drop constraint if exists player_strategy_notes_source_quote_check,
    add constraint player_strategy_notes_source_quote_check
        check (source_quote is null or source_quote >= 0);

comment on column public.player_strategy_notes.suggested_price is
    'Spesa strategica suggerita in crediti, separata dal listino canonico del giocatore.';
comment on column public.player_strategy_notes.average_auction_percent is
    'Prezzo medio d asta espresso come percentuale del budget iniziale.';

commit;
