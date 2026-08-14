from __future__ import annotations

import os
import random
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from supabase import Client, create_client


# ============================================================
# CONFIGURAZIONE
# ============================================================

st.set_page_config(page_title="RCD Escanol Auction Center", layout="wide")

ROLE_LIMITS: dict[str, int] = {
    "P": 3,
    "D": 8,
    "C": 8,
    "A": 6,
}
TOTAL_SLOTS_PER_TEAM = sum(ROLE_LIMITS.values())

ROLE_LABELS = {
    "Tutti i ruoli": "ALL",
    "Portieri (P)": "P",
    "Difensori (D)": "D",
    "Centrocampisti (C)": "C",
    "Attaccanti (A)": "A",
}

PLAYER_FIELDS = (
    "id, name, role, team_nfl, list_price, status_titolarita, "
    "rigorista, affidabilita_fisica, propensione_cartellini, "
    "slot_fantacalcio, primo_anno_serie_a"
)

RATING_CONFIG = {
    "base": 6.5,
    "list_price_bonus": (
        (30, 3.5),
        (20, 2.5),
        (10, 1.0),
        (5, 0.5),
    ),
    "titolare": 1.5,
    "riserva": -1.5,
    "rigorista": 1.5,
    "cartellini": -0.3,
    "rookie": -0.2,
    "preferito": 0.8,
}

TEAM_MAP = {
    "Napoli": "NAP", "Juventus": "JUV", "Milan": "MIL", "Inter": "INT",
    "Roma": "ROM", "Lazio": "LAZ", "Atalanta": "ATA", "Fiorentina": "FIO",
    "Torino": "TOR", "Bologna": "BOL", "Genoa": "GEN", "Sassuolo": "SAS",
    "Udinese": "UDI", "Cagliari": "CAG", "Verona": "VER", "Lecce": "LEC",
    "Cremonese": "CRE", "Parma": "PAR", "Como": "COM", "Pisa": "PIS",
}

DATA_DIR = Path(__file__).resolve().parent
STATS_FILE = DATA_DIR / "player_aggregated_stats.csv"
SEASON_FILE = DATA_DIR / "season-2526.csv"

SOUND_URLS = {
    "massive": "https://www.myinstants.com/media/sounds/john-cena-sound-effect.mp3",
    "great": "https://www.myinstants.com/media/sounds/ta-da.mp3",
    "normal": "https://www.myinstants.com/media/sounds/plop.mp3",
}


@dataclass
class AuctionState:
    bought_player_ids: set[Any]
    team_role_totals: dict[str, dict[str, int]]
    team_total_bought: dict[str, int]
    team_players_map: dict[str, list[dict[str, Any]]]
    team_purchases_map: dict[str, list[dict[str, Any]]]


# ============================================================
# DATABASE
# ============================================================

@st.cache_resource
def get_supabase() -> Client:
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_KEY"],
    )


supabase = get_supabase()


@st.cache_data(ttl=5)
def load_teams() -> list[dict[str, Any]]:
    return (
        supabase.table("teams")
        .select("id, name, remaining_budget, initial_budget")
        .execute()
        .data
    )


@st.cache_data(ttl=5)
def load_rosters() -> list[dict[str, Any]]:
    return (
        supabase.table("rosters")
        .select(
            "purchase_price, teams(name), "
            "players(id, name, role, team_nfl, list_price, status_titolarita, "
            "rigorista, affidabilita_fisica, propensione_cartellini, "
            "slot_fantacalcio, primo_anno_serie_a)"
        )
        .execute()
        .data
    )


@st.cache_data(ttl=5)
def load_players(
    role: str = "ALL",
    team_nfl: str = "ALL",
) -> list[dict[str, Any]]:
    query = supabase.table("players").select(PLAYER_FIELDS)

    if role != "ALL":
        query = query.eq("role", role)

    if team_nfl != "ALL":
        query = query.eq("team_nfl", team_nfl)

    return query.order("name").execute().data


def invalidate_data_cache() -> None:
    load_teams.clear()
    load_rosters.clear()
    load_players.clear()
    load_external_data.clear()


# ============================================================
# UI / AUDIO
# ============================================================

def play_sound(sound_url: str) -> None:
    components.html(
        f"""
        <audio autoplay>
            <source src="{sound_url}" type="audio/mp3">
        </audio>
        """,
        height=0,
        width=0,
    )


def default_team_index(team_names: list[str], preferred: str = "Escanyol") -> int:
    if not team_names:
        return 0
    return team_names.index(preferred) if preferred in team_names else 0


# ============================================================
# DATI ESTERNI / NORMALIZZAZIONE
# ============================================================

def normalize_string(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    value = unicodedata.normalize("NFKD", value)
    value = "".join(c for c in value if not unicodedata.combining(c))
    value = re.sub(r"[^a-zA-Z0-9\\s]", "", value)
    return re.sub(r"\\s+", " ", value).strip().lower()


@st.cache_data(ttl=300)
def load_external_data() -> tuple[pd.DataFrame, dict[str, dict[str, float]]]:
    stats = pd.DataFrame()
    mods: dict[str, dict[str, float]] = {}

    if STATS_FILE.exists():
        try:
            stats = pd.read_csv(STATS_FILE)
            if "clean_name" not in stats.columns and "name" in stats.columns:
                stats["clean_name"] = stats["name"].map(normalize_string)
            elif "clean_name" in stats.columns:
                stats["clean_name"] = stats["clean_name"].map(normalize_string)
        except (OSError, pd.errors.ParserError) as exc:
            st.warning(f"Impossibile leggere {STATS_FILE.name}: {exc}")

    if not SEASON_FILE.exists():
        return stats, mods

    try:
        df = pd.read_csv(SEASON_FILE)
        required = {"HomeTeam", "AwayTeam", "FTHG", "FTAG"}
        if not required.issubset(df.columns):
            return stats, mods

        home = (
            df.groupby("HomeTeam")
            .agg(GF=("FTHG", "sum"), GA=("FTAG", "sum"), M=("FTHG", "count"))
            .reset_index()
            .rename(columns={"HomeTeam": "Team"})
        )
        away = (
            df.groupby("AwayTeam")
            .agg(GF=("FTAG", "sum"), GA=("FTHG", "sum"), M=("FTAG", "count"))
            .reset_index()
            .rename(columns={"AwayTeam": "Team"})
        )
        ts = pd.merge(home, away, on="Team", how="outer").fillna(0)
        ts["Matches"] = ts["M_x"] + ts["M_y"]
        ts["TotalGF"] = ts["GF_x"] + ts["GF_y"]
        ts["TotalGA"] = ts["GA_x"] + ts["GA_y"]
        total_matches = ts["Matches"].sum()
        if total_matches <= 0:
            return stats, mods

        avg_gf = ts["TotalGF"].sum() / total_matches
        avg_ga = ts["TotalGA"].sum() / total_matches

        for _, row in ts.iterrows():
            if row["Matches"] <= 0:
                continue
            code = TEAM_MAP.get(str(row["Team"]), str(row["Team"]).upper()[:3])
            mods[code] = {
                "att": round(((row["TotalGF"] / row["Matches"]) - avg_gf) * 0.8, 2),
                "def": round((avg_ga - (row["TotalGA"] / row["Matches"])) * 0.9, 2),
            }
    except (OSError, pd.errors.ParserError, KeyError, ZeroDivisionError) as exc:
        st.warning(f"Impossibile elaborare {SEASON_FILE.name}: {exc}")

    return stats, mods


STATS, MODS = load_external_data()


# ============================================================
# RATING
# ============================================================

def calculate_player_rating_detailed(
    player: dict[str, Any],
    preferred_players: set[Any] | None = None,
) -> dict[str, Any]:
    preferred_players = preferred_players or set()
    role = player.get("role", "D")
    player_name = normalize_string(player.get("name", ""))

    base = 5.0
    real_stats = False
    goals = assists = matches = 0

    if not STATS.empty and player_name and "clean_name" in STATS.columns:
        exact = STATS[STATS["clean_name"] == player_name]
        match = exact
        if match.empty:
            escaped = re.escape(player_name)
            match = STATS[STATS["clean_name"].str.contains(escaped, na=False, regex=True)]
        if not match.empty:
            row = match.iloc[0]
            goals = int(row.get("goals", 0) or 0)
            assists = int(row.get("assists", 0) or 0)
            matches = int(row.get("matches", 0) or 0)
            if matches > 3:
                base = float(row.get("avg_vote", 6.0) or 6.0)
                if role in {"A", "C"}:
                    base += goals * 0.12 + assists * 0.08
                else:
                    base += goals * 0.15 + assists * 0.10
                real_stats = True

    if not real_stats:
        fallback = {"A": 5.0, "P": 5.0, "C": 4.8, "D": 4.5}.get(role, 4.5)
        base = fallback + (float(player.get("list_price") or 1) * 0.04)

    titolarita_mod = {
        "Titolare": 0.4,
        "Ballottaggio": -0.3,
        "Riserva": -1.5,
    }.get(player.get("status_titolarita"), 0.0)

    team_mods = MODS.get(player.get("team_nfl"), {"att": 0.0, "def": 0.0})
    team_mod = team_mods["att"] if role in {"A", "C"} else team_mods["def"]

    rigorista_mod = 0.8 if player.get("rigorista") else 0.0
    cartellini_mod = -0.3 if player.get("propensione_cartellini") == "A rischio malus" else 0.0
    rookie_mod = -0.3 if player.get("primo_anno_serie_a") else 0.0
    preferred_mod = 0.5 if player.get("id") in preferred_players else 0.0

    final = round(
        max(
            1.0,
            min(
                10.0,
                base
                + titolarita_mod
                + team_mod
                + rigorista_mod
                + cartellini_mod
                + rookie_mod
                + preferred_mod,
            ),
        ),
        1,
    )

    if (
        (cartellini_mod < 0 or rookie_mod < 0 or player.get("status_titolarita") in {"Ballottaggio", "Riserva"})
        and final >= 10.0
    ):
        final = 9.0

    return {
        "final_rating": final,
        "base": round(base, 2),
        "team_mod": team_mod,
        "tit": titolarita_mod,
        "rig": rigorista_mod,
        "cart": cartellini_mod,
        "rook": rookie_mod,
        "pref": preferred_mod,
        "g": goals,
        "a": assists,
        "m": matches,
    }


def calculate_player_rating(
    player: dict[str, Any],
    preferred_players: set[Any] | None = None,
) -> float:
    return calculate_player_rating_detailed(
        player,
        preferred_players,
    )["final_rating"]


# ============================================================
# STATO ASTA
# ============================================================

def build_auction_state(
    teams: list[dict[str, Any]],
    rosters: list[dict[str, Any]],
) -> AuctionState:
    bought_player_ids: set[Any] = set()
    team_role_totals = {
        team["name"]: {role: 0 for role in ROLE_LIMITS}
        for team in teams
    }
    team_total_bought = {team["name"]: 0 for team in teams}
    team_players_map = {team["name"]: [] for team in teams}
    team_purchases_map = {team["name"]: [] for team in teams}

    for roster in rosters:
        player = roster.get("players")
        team = roster.get("teams")

        if not player or not team:
            continue

        player_id = player.get("id")
        team_name = team.get("name")
        role = player.get("role")

        if player_id is not None:
            bought_player_ids.add(player_id)

        if team_name not in team_players_map:
            continue

        team_players_map[team_name].append(player)
        team_purchases_map[team_name].append(roster)

        if role in ROLE_LIMITS:
            team_role_totals[team_name][role] += 1
            team_total_bought[team_name] += 1

    return AuctionState(
        bought_player_ids=bought_player_ids,
        team_role_totals=team_role_totals,
        team_total_bought=team_total_bought,
        team_players_map=team_players_map,
        team_purchases_map=team_purchases_map,
    )


def calculate_team_ratings(
    state: AuctionState,
    preferred_players: set[Any],
) -> dict[str, float]:
    return {
        team_name: (
            sum(
                calculate_player_rating(player, preferred_players)
                for player in players
            )
            / len(players)
            if players
            else 0.0
        )
        for team_name, players in state.team_players_map.items()
    }


def calculate_completed_roles(
    state: AuctionState,
) -> list[str]:
    completed = []

    for role, limit in ROLE_LIMITS.items():
        if all(
            counts[role] >= limit
            for counts in state.team_role_totals.values()
        ):
            completed.append(role)

    return completed


def is_auction_finished(state: AuctionState) -> bool:
    return all(
        bought >= TOTAL_SLOTS_PER_TEAM
        for bought in state.team_total_bought.values()
    )


# ============================================================
# ANALISI SQUADRA
# ============================================================

def get_credit_rank(
    teams_df: pd.DataFrame,
    team_name: str,
) -> tuple[int, int]:
    sorted_df = (
        teams_df.sort_values("remaining_budget", ascending=False)
        .reset_index(drop=True)
    )
    row = sorted_df[sorted_df["name"] == team_name]

    if row.empty:
        return 0, 0

    return int(row.index[0] + 1), int(row.iloc[0]["remaining_budget"])


def get_team_risk_counts(players: list[dict[str, Any]]) -> dict[str, int]:
    movement_players = [
        player for player in players
        if player.get("role") != "P"
    ]

    club_counts: dict[str, int] = {}
    for player in movement_players:
        club = player.get("team_nfl")
        if club:
            club_counts[club] = club_counts.get(club, 0) + 1

    return {
        "max_block": max(club_counts.values(), default=0),
        "ballottaggio": sum(
            player.get("status_titolarita") == "Ballottaggio"
            for player in players
        ),
        "cartellini": sum(
            player.get("propensione_cartellini") == "A rischio malus"
            for player in players
        ),
        "rookie": sum(
            bool(player.get("primo_anno_serie_a"))
            for player in players
        ),
    }


def risk_label(
    count: int,
    good_threshold: int,
    warning_threshold: int,
    good: str,
    warning: str,
    bad: str,
) -> str:
    if count < good_threshold:
        return good
    if count < warning_threshold:
        return warning
    return bad


def render_team_analysis(
    teams_df: pd.DataFrame,
    state: AuctionState,
    ratings: dict[str, float],
) -> None:
    st.sidebar.divider()
    st.sidebar.subheader("🔮 Analisi Asta & Valutazione")

    team_names = teams_df["name"].tolist()
    if not team_names:
        st.sidebar.info("Nessuna squadra configurata.")
        return

    selected_team = st.sidebar.selectbox(
        "Analizza squadra",
        team_names,
        index=default_team_index(team_names),
        key="sidebar_team_analysis",
    )

    players = state.team_players_map.get(selected_team, [])
    bought_count = len(players)
    credit_rank, budget = get_credit_rank(teams_df, selected_team)
    slots_left = max(0, TOTAL_SLOTS_PER_TEAM - bought_count)

    if players:
        avg_score = ratings[selected_team]
        rating_position = sorted(
            ratings,
            key=ratings.get,
            reverse=True,
        ).index(selected_team) + 1

        st.sidebar.metric(
            "Rating Rosa",
            f"{avg_score:.1f} / 10.0",
            delta=f"Posizione: {rating_position}/{len(ratings)}",
            delta_color="off",
        )

        if avg_score >= 8:
            st.sidebar.success("Rosa da Scudetto!")
        elif avg_score >= 6.5:
            st.sidebar.info("Rosa competitiva.")
        else:
            st.sidebar.warning("Rosa da rinforzare.")
    else:
        st.sidebar.metric("Rating Rosa", "N/D")
        st.sidebar.info("Assegna giocatori per calcolare il rating.")

    st.sidebar.markdown(
        f"💰 **Posizione Crediti:** {credit_rank}° su {len(team_names)} "
        f"({budget} cr residui)"
    )

    if slots_left:
        avg_spendable = budget / slots_left
        st.sidebar.caption(
            f"Spesa media potenziale: **{avg_spendable:.1f} cr/slot** "
            f"({slots_left} slot liberi)"
        )

    st.sidebar.markdown("---")
    st.sidebar.markdown("**📊 Cruscotto Rischi Rosa:**")

    risks = get_team_risk_counts(players)

    block_status = (
        "👍 Ottimale" if risks["max_block"] < 4
        else "👎 Rischio Blocco"
    )
    st.sidebar.write(
        f"🚨 **Blocco Squadra:** {risks['max_block']} max | {block_status}"
    )

    ballot_status = risk_label(
        risks["ballottaggio"], 3, 6,
        "👍 Ottimale", "🟡 Moderato", "👎 Troppi",
    )
    st.sidebar.write(
        f"⚠️ **Ballottaggi:** {risks['ballottaggio']} giocatori | "
        f"{ballot_status}"
    )

    card_status = risk_label(
        risks["cartellini"], 2, 4,
        "👍 Pulita", "🟡 Attenzione", "👎 Troppi Malus",
    )
    st.sidebar.write(
        f"🟨 **A rischio malus:** {risks['cartellini']} | {card_status}"
    )

    rookie_status = risk_label(
        risks["rookie"], 2, 4,
        "👍 Esperti", "🟡 Equilibrato", "👎 Troppi Rookie",
    )
    st.sidebar.write(
        f"👶 **Primo anno in A:** {risks['rookie']} | {rookie_status}"
    )


# ============================================================
# TOP 5
# ============================================================

def render_top5(
    role: str,
    bought_player_ids: set[Any],
    preferred_players: set[Any],
) -> None:
    st.sidebar.subheader("🔥 Top 5 Liberi (Ranking)")

    players = load_players(role=role)

    available = [
        player for player in players
        if player["id"] not in bought_player_ids
    ]

    available.sort(
        key=lambda player: calculate_player_rating(
            player,
            preferred_players,
        ),
        reverse=True,
    )

    with st.sidebar.container(border=True):
        if not available:
            st.info("Nessun giocatore disponibile.")
            return

        for index, player in enumerate(available[:5], start=1):
            rating = calculate_player_rating(player, preferred_players)
            star = " ⭐" if player["id"] in preferred_players else ""

            st.markdown(
                f"**{index}. {player['name']}**{star} "
                f"`[{player['role']}]` ({player['team_nfl']}) — "
                f"⭐️ **{rating}** | 💎 **{player['list_price']} cr**"
            )


# ============================================================
# AUTOCOMPILAZIONE
# ============================================================

def simulate_autofill(
    teams: list[dict[str, Any]],
    state: AuctionState,
    role_filter: str,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    players = load_players()
    free_players = [
        player for player in players
        if player["id"] not in state.bought_player_ids
    ]

    if role_filter != "Tutti":
        free_players = [
            player for player in free_players
            if player["role"] == role_filter
        ]

    random.shuffle(free_players)

    sim_bought = state.team_total_bought.copy()
    sim_roles = {
        team: counts.copy()
        for team, counts in state.team_role_totals.items()
    }
    sim_budgets = {
        team["name"]: int(team["remaining_budget"])
        for team in teams
    }
    team_id_map = {
        team["name"]: team["id"]
        for team in teams
    }

    inserts = []

    for player in free_players:
        role = player["role"]
        if role not in ROLE_LIMITS:
            continue

        valid_teams = [
            team_name
            for team_name in sim_bought
            if (
                sim_bought[team_name] < TOTAL_SLOTS_PER_TEAM
                and sim_roles[team_name][role] < ROLE_LIMITS[role]
            )
        ]

        if not valid_teams:
            continue

        def team_score(team_name: str) -> float:
            slots_left = TOTAL_SLOTS_PER_TEAM - sim_bought[team_name]
            return (
                sim_budgets[team_name] / slots_left
                if slots_left > 0
                else -1
            )

        chosen_team = max(valid_teams, key=team_score)
        slots_left = TOTAL_SLOTS_PER_TEAM - sim_bought[chosen_team]
        current_budget = sim_budgets[chosen_team]

        base_price = max(1, int(player.get("list_price") or 1))

        if slots_left == 1:
            purchase_price = max(1, current_budget)
        else:
            avg_allowed = current_budget / slots_left
            purchase_price = max(
                1,
                int((base_price + avg_allowed) / 2),
            )

            max_allowed = current_budget - (slots_left - 1)
            purchase_price = min(
                purchase_price,
                max(1, int(max_allowed)),
            )

        inserts.append(
            {
                "team_id": team_id_map[chosen_team],
                "player_id": player["id"],
                "purchase_price": purchase_price,
            }
        )

        sim_bought[chosen_team] += 1
        sim_roles[chosen_team][role] += 1
        sim_budgets[chosen_team] -= purchase_price

    return inserts, sim_budgets


def perform_autofill(
    teams: list[dict[str, Any]],
    state: AuctionState,
    role_filter: str,
) -> bool:
    inserts, budgets = simulate_autofill(
        teams,
        state,
        role_filter,
    )

    if not inserts:
        return False

    supabase.table("rosters").insert(inserts).execute()

    team_id_map = {
        team["name"]: team["id"]
        for team in teams
    }

    for team_name, budget in budgets.items():
        supabase.table("teams").update(
            {"remaining_budget": max(0, int(budget))}
        ).eq(
            "id",
            team_id_map[team_name],
        ).execute()

    return True


# ============================================================
# ADMIN
# ============================================================

def reset_auction(teams_df: pd.DataFrame) -> None:
    supabase.table("rosters").delete().gt("purchase_price", -1).execute()

    for _, row in teams_df.iterrows():
        supabase.table("teams").update(
            {"remaining_budget": int(row["initial_budget"])}
        ).eq("id", row["id"]).execute()


def render_admin_tools(
    teams_df: pd.DataFrame,
    state: AuctionState,
) -> None:
    st.sidebar.divider()
    st.sidebar.subheader("🛠️ Strumenti Mockup & Admin")

    role_filter = st.sidebar.selectbox(
        "Completa ruolo (Mockup)",
        ["Tutti"] + list(ROLE_LIMITS),
    )

    if st.sidebar.button("🎲 Autocompila rose (Intermedio)"):
        if perform_autofill(
            teams_df.to_dict("records"),
            state,
            role_filter,
        ):
            st.sidebar.success("Rose autocompilate con successo!")
            invalidate_data_cache()
            st.rerun()
        else:
            st.sidebar.warning(
                "Nessun inserimento possibile o limiti già raggiunti."
            )

    if st.sidebar.button(
        "🗑️ Svuota tutte le rose (Reset)",
        type="primary",
    ):
        st.session_state["confirm_reset"] = True

    if st.session_state.get("confirm_reset"):
        st.sidebar.warning(
            "Questa operazione cancellerà tutti gli acquisti e "
            "ripristinerà i budget iniziali."
        )

        confirm_col, cancel_col = st.sidebar.columns(2)

        with confirm_col:
            if st.button("Conferma reset", key="confirm_reset_button"):
                reset_auction(teams_df)
                st.session_state["confirm_reset"] = False
                invalidate_data_cache()
                st.sidebar.success("Asta resettata.")
                st.rerun()

        with cancel_col:
            if st.button("Annulla", key="cancel_reset_button"):
                st.session_state["confirm_reset"] = False
                st.rerun()


# ============================================================
# ACQUISTO MANUALE
# ============================================================

def execute_purchase(
    teams_df: pd.DataFrame,
    state: AuctionState,
    selected_player: dict[str, Any],
    purchase_price: int,
    target_team: str,
) -> tuple[bool, str]:
    team_row = teams_df[teams_df["name"] == target_team]

    if team_row.empty:
        return False, "Seleziona una squadra valida."

    team = team_row.iloc[0]
    role = selected_player["role"]
    role_count = state.team_role_totals[target_team][role]
    role_limit = ROLE_LIMITS.get(role, TOTAL_SLOTS_PER_TEAM)

    if role_count >= role_limit:
        return (
            False,
            f"❌ Limite raggiunto! {target_team} ha completato "
            f"il ruolo {role} ({role_count}/{role_limit}).",
        )

    if state.team_total_bought[target_team] >= TOTAL_SLOTS_PER_TEAM:
        return (
            False,
            f"❌ La squadra {target_team} ha completato la rosa "
            f"({TOTAL_SLOTS_PER_TEAM}/{TOTAL_SLOTS_PER_TEAM}).",
        )

    current_budget = int(team["remaining_budget"])

    if purchase_price > current_budget:
        return (
            False,
            f"❌ Budget insufficiente per {target_team}: "
            f"{current_budget} crediti residui.",
        )

    supabase.table("rosters").insert(
        {
            "team_id": team["id"],
            "player_id": selected_player["id"],
            "purchase_price": purchase_price,
        }
    ).execute()

    supabase.table("teams").update(
        {"remaining_budget": current_budget - purchase_price}
    ).eq("id", team["id"]).execute()

    return True, ""


def render_manual_purchase(
    teams_df: pd.DataFrame,
    state: AuctionState,
    current_role: str,
) -> None:
    if is_auction_finished(state):
        return

    team_filter = "ALL"
    if current_role != "ALL":
        players_for_filter = load_players(role=current_role)
    else:
        players_for_filter = load_players()

    available_nfl_teams = sorted(
        {
            player["team_nfl"]
            for player in players_for_filter
            if player.get("team_nfl")
        }
    )

    col_r, col_t = st.columns(2)

    with col_t:
        nfl_filter_label = st.selectbox(
            "2. Filtra per Squadra Serie A (Opzionale)",
            ["Tutte le squadre"] + available_nfl_teams,
        )
        team_filter = (
            "ALL"
            if nfl_filter_label == "Tutte le squadre"
            else nfl_filter_label
        )

    players = load_players(
        role=current_role,
        team_nfl=team_filter,
    )

    available_players = [
        player
        for player in players
        if player["id"] not in state.bought_player_ids
    ]

    if not available_players:
        st.warning(
            "Nessun giocatore disponibile trovato con questi filtri."
        )
        return

    player_options = {
        (
            f"{player['name']} [{player['role']}] "
            f"({player['team_nfl']} - Listino: {player['list_price']})"
        ): player
        for player in available_players
    }

    col1, col2, col3 = st.columns([3, 1, 2])

    with col1:
        selected_label = st.selectbox(
            "3. Seleziona Giocatore",
            list(player_options),
        )
        selected_player = player_options[selected_label]

    with col2:
        default_price = max(
            1,
            int(selected_player.get("list_price") or 1),
        )
        purchase_price = st.number_input(
            "4. Costo",
            min_value=1,
            max_value=500,
            value=default_price,
        )

    with col3:
        role = selected_player["role"]
        active_teams = [
            team_name
            for team_name in teams_df["name"].tolist()
            if (
                state.team_total_bought[team_name] < TOTAL_SLOTS_PER_TEAM
                and state.team_role_totals[team_name][role]
                < ROLE_LIMITS[role]
            )
        ]

        team_names = (
            active_teams
            if active_teams
            else teams_df["name"].tolist()
        )

        target_team = st.selectbox(
            "5. Squadra Acquirente",
            team_names,
            index=default_team_index(team_names),
        )

    if not st.button("Conferma Acquisto", type="primary"):
        return

    success, error = execute_purchase(
        teams_df,
        state,
        selected_player,
        int(purchase_price),
        target_team,
    )

    if not success:
        st.error(error)
        return

    rating = calculate_player_rating(
        selected_player,
        st.session_state.preferred_players,
    )

    if target_team == "Escanyol":
        if rating >= 8.5:
            st.balloons()
            st.snow()
            play_sound(SOUND_URLS["massive"])
            st.success(
                f"🔥 MASSIVE COLPO! Hai preso **{selected_player['name']}** "
                f"(Rating {rating})! AND HIS NAME IS JOHN CENA! 🎺🎺🎺"
            )
        elif rating >= 7.5:
            st.balloons()
            play_sound(SOUND_URLS["great"])
            st.success(
                f"🎉 Ottimo innesto! **{selected_player['name']}** "
                f"con rating {rating}. Gran bel colpo per l'Escanyol! 🌟"
            )
        else:
            play_sound(SOUND_URLS["normal"])
            st.info(
                f"✅ Operazione conclusa: preso "
                f"**{selected_player['name']}** a {purchase_price} crediti."
            )
    else:
        st.success(
            f"✅ Acquistato **{selected_player['name']}** "
            f"[{selected_player['role']}] a **{purchase_price}** crediti "
            f"per **{target_team}**!"
        )

    invalidate_data_cache()
    st.rerun()


# ============================================================
# PANORAMICA SQUADRE
# ============================================================

def build_team_alerts(
    players: list[dict[str, Any]],
    bought: int,
) -> list[dict[str, str]]:
    alerts: list[dict[str, str]] = []

    club_players: dict[str, list[str]] = {}
    for player in players:
        if player.get("role") == "P":
            continue

        club = player.get("team_nfl")
        if club:
            club_players.setdefault(club, []).append(
                f"{player.get('name')} [{player.get('role')}]"
            )

    for club, names in club_players.items():
        if len(names) >= 4:
            alerts.append(
                {
                    "text": (
                        f"🚨 **Rischio Blocco:** {len(names)} "
                        f"giocatori di movimento su {club}"
                    ),
                    "help": (
                        f"Giocatori di movimento del club {club}:\n- "
                        + "\n- ".join(names)
                    ),
                }
            )

    ballotaggio = [
        f"{player.get('name')} [{player.get('role')}]"
        for player in players
        if player.get("status_titolarita") == "Ballottaggio"
    ]
    if bought >= 5 and len(ballotaggio) >= bought * 0.4:
        alerts.append(
            {
                "text": f"⚠️ **Troppi Ballottaggi:** {len(ballotaggio)} giocatori",
                "help": "Giocatori in ballottaggio:\n- "
                + "\n- ".join(ballotaggio),
            }
        )

    cartellini = [
        f"{player.get('name')} [{player.get('role')}]"
        for player in players
        if player.get("propensione_cartellini") == "A rischio malus"
    ]
    if len(cartellini) >= 3:
        alerts.append(
            {
                "text": f"🟨 **Rischio Malus:** {len(cartellini)} a rischio cartellino",
                "help": "Giocatori a rischio malus:\n- "
                + "\n- ".join(cartellini),
            }
        )

    rookies = [
        f"{player.get('name')} [{player.get('role')}]"
        for player in players
        if player.get("primo_anno_serie_a")
    ]
    if len(rookies) >= 3:
        alerts.append(
            {
                "text": f"👶 **Rischio Rookie:** {len(rookies)} al primo anno in A",
                "help": "Giocatori al primo anno in Serie A:\n- "
                + "\n- ".join(rookies),
            }
        )

    return alerts


def render_team_overview(
    teams_df: pd.DataFrame,
    state: AuctionState,
    ratings: dict[str, float],
) -> None:
    st.divider()
    st.subheader("📊 Panoramica Squadre & Alert Strategici")

    if teams_df.empty:
        st.info("Nessuna squadra configurata.")
        return

    summaries = []

    for _, team in teams_df.iterrows():
        name = team["name"]
        remaining_budget = int(team["remaining_budget"])
        players = state.team_players_map[name]
        bought = state.team_total_bought[name]
        spent = sum(
            purchase.get("purchase_price", 0)
            for purchase in state.team_purchases_map[name]
        )

        slots_left = max(0, TOTAL_SLOTS_PER_TEAM - bought)
        avg_price = (
            round(remaining_budget / slots_left, 1)
            if slots_left
            else 0
        )
        avg_spent = (
            round(spent / bought, 1)
            if bought
            else 0.0
        )

        alerts = build_team_alerts(players, bought)

        top_players = sum(
            player.get("slot_fantacalcio") == "1° Slot"
            or (player.get("list_price") or 0) >= 25
            for player in players
        )

        if bought == 0:
            status = "📭 Rosa ancora vuota."
        else:
            count = len(alerts)
            risk_text = (
                "pochi rischi"
                if count == 0
                else "1 rischio potenziale"
                if count == 1
                else f"{count} criticità da monitorare"
            )
            status = (
                f"✨ Rating: **{ratings[name]:.1f}** "
                f"({top_players} Top) — {risk_text}."
            )

        summaries.append(
            {
                "team": team,
                "bought": bought,
                "slots_left": slots_left,
                "avg_price": avg_price,
                "avg_spent": avg_spent,
                "role_counts": state.team_role_totals[name],
                "alerts": alerts,
                "status": status,
            }
        )

    summaries.sort(
        key=lambda item: (
            -item["avg_price"],
            -int(item["team"]["remaining_budget"]),
            item["team"]["name"],
        )
    )

    for start in range(0, len(summaries), 4):
        cols = st.columns(4)

        for offset, col in enumerate(cols):
            if start + offset >= len(summaries):
                continue

            item = summaries[start + offset]
            team = item["team"]
            name = team["name"]
            bought = item["bought"]
            remaining = int(team["remaining_budget"])
            initial = max(1, int(team["initial_budget"]))
            roles = item["role_counts"]

            role_string = (
                f"**P** {roles['P']}/{ROLE_LIMITS['P']} | "
                f"**D** {roles['D']}/{ROLE_LIMITS['D']} | "
                f"**C** {roles['C']}/{ROLE_LIMITS['C']} | "
                f"**A** {roles['A']}/{ROLE_LIMITS['A']}"
            )

            with col:
                title = (
                    f"**{name}** — ⭐️ {ratings[name]:.1f}"
                    if bought
                    else f"**{name}**"
                )
                st.markdown(title)

                if bought < TOTAL_SLOTS_PER_TEAM:
                    delta = (
                        f"{item['avg_spent']} cr/giocatore"
                        if bought
                        else "N/A"
                    )
                    st.metric(
                        "Budget",
                        f"{remaining} cr",
                        delta=delta,
                        delta_color="off",
                    )
                    st.markdown(role_string)
                    st.text(
                        f"Media max/giocatore: {item['avg_price']} cr"
                    )
                    st.progress(
                        max(0.0, min(1.0, remaining / initial))
                    )
                else:
                    st.success(
                        f"✅ Rosa Completata "
                        f"({TOTAL_SLOTS_PER_TEAM}/{TOTAL_SLOTS_PER_TEAM})"
                    )

                st.markdown(f"*{item['status']}*")

                for alert in item["alerts"]:
                    st.markdown(
                        alert["text"],
                        help=alert["help"],
                    )

                st.markdown("---")


# ============================================================
# TAB 2 — ROSE E PAGELLE
# ============================================================

def build_roster_dataframe(
    rosters: list[dict[str, Any]],
    preferred_players: set[Any],
) -> pd.DataFrame:
    rows = []

    for roster in rosters:
        team = roster.get("teams")
        player = roster.get("players")

        if not team or not player:
            continue

        list_price = player.get("list_price") or 1

        rows.append(
            {
                "⭐ Preferito": player["id"] in preferred_players,
                "Squadra": team["name"],
                "Giocatore": player["name"],
                "Ruolo": player["role"],
                "Rating": calculate_player_rating(
                    player,
                    preferred_players,
                ),
                "Club Serie A": player.get("team_nfl"),
                "Listino": list_price,
                "Pagato": roster.get("purchase_price", 0),
                "Differenza": (
                    roster.get("purchase_price", 0) - list_price
                ),
                "Slot": player.get(
                    "slot_fantacalcio",
                    "Scommessa",
                ),
                "Titolarità": player.get(
                    "status_titolarita",
                    "Titolare",
                ),
                "Rigorista": "Sì" if player.get("rigorista") else "No",
                "Fisico": player.get(
                    "affidabilita_fisica",
                    "Integro",
                ),
                "Cartellini": player.get(
                    "propensione_cartellini",
                    "Normale",
                ),
                "1° Anno A": (
                    "Sì"
                    if player.get("primo_anno_serie_a")
                    else "No"
                ),
                "_player_id": player["id"],
            }
        )

    return pd.DataFrame(rows)


def calculate_auction_grades(
    teams: list[dict[str, Any]],
    state: AuctionState,
    ratings: dict[str, float],
) -> pd.DataFrame:
    grades = []

    for team in teams:
        name = team["name"]
        players = state.team_players_map[name]
        purchases = state.team_purchases_map[name]

        if not players:
            grades.append(
                {
                    "Squadra": name,
                    "Voto Asta": 0.0,
                    "Rating Medio": 0.0,
                    "Bilancio Crediti (Listino - Speso)": 0,
                    "Criticità Rilevate": 0,
                }
            )
            continue

        total_listino = sum(
            player.get("list_price") or 1
            for player in players
        )
        total_speso = sum(
            purchase.get("purchase_price", 0)
            for purchase in purchases
        )

        savings = total_listino - total_speso
        savings_bonus = max(
            -2.0,
            min(2.0, savings / 15.0),
        )

        alerts = build_team_alerts(
            players,
            len(players),
        )
        criticality = len(alerts)

        grade = (
            ratings[name] * 0.7
            + 5.0 * 0.3
            + savings_bonus
            - criticality * 0.4
        )
        grade = round(max(0.0, min(10.0, grade)), 1)

        grades.append(
            {
                "Squadra": name,
                "Voto Asta": grade,
                "Rating Medio": round(ratings[name], 1),
                "Bilancio Affari (Listino - Speso)": savings,
                "Criticità Rilevate": criticality,
            }
        )

    return (
        pd.DataFrame(grades)
        .sort_values("Voto Asta", ascending=False)
        .reset_index(drop=True)
        .rename_axis("Posizione")
    )


def render_rosters_tab(
    teams: list[dict[str, Any]],
    teams_df: pd.DataFrame,
    rosters: list[dict[str, Any]],
    state: AuctionState,
    ratings: dict[str, float],
) -> None:
    st.subheader("📋 Tutte le Rose & Pagelle Post-Asta")
    st.markdown(
        "In questa sezione puoi visionare tutte le rose completate e "
        "l'**Analisi Voto Asta** basata su ranking, risparmio/overpaying "
        "sui listini e criticità complessive."
    )

    if not rosters:
        st.info("Nessun giocatore ancora acquistato in questa sessione d'asta.")
        return

    df_rosters = build_roster_dataframe(
        rosters,
        st.session_state.preferred_players,
    )

    team_names = teams_df["name"].tolist()
    filter_options = ["Tutte"] + team_names

    selected_filter = st.selectbox(
        "Filtra per Squadra",
        filter_options,
        index=default_team_index(filter_options),
        key="table_team_filter_tab2",
    )

    display_df = df_rosters.copy()
    if selected_filter != "Tutte":
        display_df = display_df[
            display_df["Squadra"] == selected_filter
        ]

    edited_df = st.data_editor(
        display_df,
        column_config={
            "_player_id": None,
            "⭐ Preferito": st.column_config.CheckboxColumn(
                "⭐ Preferito",
                help="Dai un bonus di rating al giocatore.",
                default=False,
            ),
        },
        use_container_width=True,
        hide_index=True,
    )

    for _, row in edited_df.iterrows():
        player_id = row["_player_id"]
        if row["⭐ Preferito"]:
            st.session_state.preferred_players.add(player_id)
        else:
            st.session_state.preferred_players.discard(player_id)

    st.divider()
    st.subheader("🏆 Classifica e Voto Asta per Squadra")
    st.markdown(
        "Il voto dell'asta unisce: **1)** Rating medio della rosa, "
        "**2)** Gestione economica, **3)** Penalizzazione per criticità "
        "e rischi rosa."
    )

    grades_df = calculate_auction_grades(
        teams,
        state,
        ratings,
    )
    st.dataframe(
        grades_df,
        use_container_width=True,
    )


# ============================================================
# TAB 3 — TUTTI I GIOCATORI / RATING
# ============================================================

def render_all_players_tab() -> None:
    st.subheader("⭐️ Tutti i Giocatori — Rating Dettagliato")
    st.caption(
        "Il rating combina statistiche stagionali, listino, titolarità, "
        "modificatore squadra, rigoristi, rischio cartellini, rookie e preferiti."
    )

    all_players = load_players()
    if not all_players:
        st.info("Nessun giocatore trovato nel database.")
        return

    rows = []
    bought_ids = set()
    for roster in load_rosters():
        player = roster.get("players")
        if player and player.get("id") is not None:
            bought_ids.add(player["id"])

    for player in all_players:
        details = calculate_player_rating_detailed(
            player,
            st.session_state.preferred_players,
        )
        rows.append(
            {
                "⭐ Preferito": player["id"] in st.session_state.preferred_players,
                "Giocatore": player.get("name", ""),
                "Ruolo": player.get("role", ""),
                "Rating ⭐️": details["final_rating"],
                "Base/Fantamedia": details["base"],
                "Mod Squadra": details["team_mod"],
                "Titolarità": details["tit"],
                "Rigorista": details["rig"],
                "Cartellini": details["cart"],
                "Rookie": details["rook"],
                "Gol": details["g"],
                "Ass": details["a"],
                "Presenze": details["m"],
                "Club": player.get("team_nfl", ""),
                "Listino": player.get("list_price", 0),
                "Stato": "Acquistato" if player["id"] in bought_ids else "Libero",
                "_player_id": player["id"],
            }
        )

    df = pd.DataFrame(rows)

    col1, col2, col3 = st.columns(3)
    with col1:
        role_filter = st.selectbox(
            "Filtra per Ruolo",
            ["Tutti", "P", "D", "C", "A"],
            key="tab3_role_filter",
        )
    with col2:
        status_filter = st.selectbox(
            "Filtra per Stato",
            ["Tutti", "Libero", "Acquistato"],
            key="tab3_status_filter",
        )
    with col3:
        search_name = st.text_input(
            "Cerca Giocatore",
            key="tab3_search_name",
        )

    filtered = df.copy()
    if role_filter != "Tutti":
        filtered = filtered[filtered["Ruolo"] == role_filter]
    if status_filter != "Tutti":
        filtered = filtered[filtered["Stato"] == status_filter]
    if search_name:
        needle = re.escape(search_name)
        filtered = filtered[
            filtered["Giocatore"].astype(str).str.contains(
                needle,
                case=False,
                na=False,
                regex=True,
            )
        ]

    filtered = filtered.sort_values(
        ["Rating ⭐️", "Giocatore"],
        ascending=[False, True],
    )

    st.dataframe(
        filtered.drop(columns=["_player_id"]),
        use_container_width=True,
        hide_index=True,
        column_config={
            "⭐ Preferito": st.column_config.CheckboxColumn(
                "⭐ Preferito",
                help="Aggiunge +0.5 al rating del giocatore.",
            ),
            "Rating ⭐️": st.column_config.NumberColumn(
                "Rating ⭐️",
                format="%.1f",
            ),
        },
    )


# ============================================================
# MAIN
# ============================================================

def main() -> None:
    st.title("⚽ RCD Escanol - Live Auction Assistant")

    teams = load_teams()
    rosters = load_rosters()

    teams_df = pd.DataFrame(teams)
    state = build_auction_state(teams, rosters)

    if "preferred_players" not in st.session_state:
        st.session_state.preferred_players = set()

    preferred_players = st.session_state.preferred_players
    ratings = calculate_team_ratings(
        state,
        preferred_players,
    )

    completed_roles = calculate_completed_roles(state)
    auction_finished = is_auction_finished(state)

    available_role_labels = {
        label: role
        for label, role in ROLE_LABELS.items()
        if role == "ALL" or role not in completed_roles
    }

    tab1, tab2, tab3 = st.tabs(
        ["🎯 Live Asta", "📋 Rose & Analisi", "⭐️ Tutti i Giocatori (Rating)"]
    )

    with tab1:
        st.subheader("🎯 Assegnazione Guidata Giocatore")

        if auction_finished:
            st.success(
                "🎉 **ASTA CONCLUSA!** Tutte le squadre hanno completato "
                "le proprie rose."
            )
            current_role = "ALL"
        else:
            col_role, _ = st.columns(2)

            with col_role:
                selected_role_label = st.selectbox(
                    "1. Seleziona Ruolo",
                    list(available_role_labels),
                    key="main_role_select",
                )

            current_role = available_role_labels[
                selected_role_label
            ]

        render_top5(
            current_role,
            state.bought_player_ids,
            preferred_players,
        )

        render_team_analysis(
            teams_df,
            state,
            ratings,
        )

        render_admin_tools(
            teams_df,
            state,
        )

        render_manual_purchase(
            teams_df,
            state,
            current_role,
        )

        render_team_overview(
            teams_df,
            state,
            ratings,
        )

    with tab2:
        render_rosters_tab(
            teams,
            teams_df,
            rosters,
            state,
            ratings,
        )

    with tab3:
        render_all_players_tab()


if __name__ == "__main__":
    main()
