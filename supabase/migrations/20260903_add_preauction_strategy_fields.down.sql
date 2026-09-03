begin;

alter table public.player_strategy_notes
    drop constraint if exists player_strategy_notes_source_role_check,
    drop constraint if exists player_strategy_notes_suggested_price_check,
    drop constraint if exists player_strategy_notes_average_auction_percent_check,
    drop constraint if exists player_strategy_notes_source_quote_check,
    drop column if exists source_role,
    drop column if exists suggested_price,
    drop column if exists average_auction_percent,
    drop column if exists source_quote;

commit;
