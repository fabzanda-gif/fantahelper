from __future__ import annotations

import os
import random
import re
import unicodedata
import uuid
import json
from difflib import SequenceMatcher

import requests
from bs4 import BeautifulSoup
from html import escape
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Any

import pandas as pd
import openpyxl
import streamlit as st
import streamlit.components.v1 as components
from supabase import Client, create_client


# ============================================================
# CONFIGURAZIONE
# ============================================================

st.set_page_config(page_title="fantahe1per", page_icon="https://raw.githubusercontent.com/fabzanda-gif/fantahelper/main/Gemini_Generated_Image_sf4v3ssf4v3ssf4v.jpeg", layout="wide")

st.markdown("""<style>
/* Tab navigation: forza realmente il grassetto sui label BaseWeb */
div[data-testid="stTabs"] [data-baseweb="tab-list"] button[role="tab"],
div[data-testid="stTabs"] [data-baseweb="tab-list"] button[role="tab"] *,
div[data-testid="stTabs"] button[data-baseweb="tab"],
div[data-testid="stTabs"] button[data-baseweb="tab"] * {
    font-weight: 800 !important;
    font-synthesis: weight !important;
}
</style>""", unsafe_allow_html=True)

st.markdown("""
<style>
/* ==========================================================
   FANTAHE1PER — PREMIUM HIGH-CONTRAST DASHBOARD
   Pensato per restare leggibile anche con tema Streamlit Light.
   ========================================================== */

:root {
    --rcd-bg: #eef4ff;
    --rcd-surface: #ffffff;
    --rcd-surface-soft: #edf4ff;
    --rcd-text: #172033;
    --rcd-muted: #64748b;
    --rcd-border: #dbe3ef;
    --rcd-blue: #2563eb;
    --rcd-blue-dark: #163c96;
    --rcd-green: #15803d;
    --rcd-red: #b91c1c;
    --rcd-amber: #b45309;
}

/* Layout generale */
.block-container {
    padding-top: 4.4rem;
    padding-bottom: 3rem;
    max-width: 1500px;
}

[data-testid="stAppViewContainer"] {
    background:
        radial-gradient(circle at 92% 2%, rgba(37,99,235,.20), transparent 27%),
        radial-gradient(circle at 5% 45%, rgba(59,130,246,.10), transparent 24%),
        linear-gradient(180deg, #f4f8ff 0%, #eaf2ff 52%, #f5f8ff 100%);
    color: var(--rcd-text);
}

/* Forza il contrasto del testo nel main */
[data-testid="stMain"] h1,
[data-testid="stMain"] h2,
[data-testid="stMain"] h3,
[data-testid="stMain"] h4,
[data-testid="stMain"] p,
[data-testid="stMain"] label,
[data-testid="stMain"] span,
[data-testid="stMain"] div {
    color: var(--rcd-text);
}

/* Sidebar volutamente chiara e separata */
[data-testid="stSidebar"] {
    background:
        linear-gradient(180deg, #f7faff 0%, #e7effc 100%);
    border-right: 1px solid #c9d8ef;
}
[data-testid="stSidebar"] * {
    color: #20283a;
}

/* Tabs: sticky, leggibili, mai sotto la toolbar */
[data-testid="stTabs"] > div:first-child {
    position: sticky;
    top: 3.15rem;
    z-index: 999;
    padding: .45rem .55rem;
    margin: 0 0 1rem 0;
    border: 1px solid var(--rcd-border);
    border-radius: 14px;
    background: rgba(239,246,255,.97);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    box-shadow: 0 8px 24px rgba(15,23,42,.08);
}

div[data-baseweb="tab-list"] {
    gap: .45rem;
}

button[data-baseweb="tab"] {
    min-height: 2.8rem;
    padding-left: 1.05rem;
    padding-right: 1.05rem;
    border-radius: 10px;
    font-weight: 800;
}

button[data-baseweb="tab"] p,
button[data-baseweb="tab"] span {
    color: #475569 !important;
}

button[data-baseweb="tab"][aria-selected="true"] {
    background: linear-gradient(135deg, var(--rcd-blue-dark), var(--rcd-blue));
    box-shadow: 0 6px 18px rgba(37,99,235,.22);
}

button[data-baseweb="tab"][aria-selected="true"] p,
button[data-baseweb="tab"][aria-selected="true"] span {
    color: #ffffff !important;
}

/* Hero */
.rcd-hero {
    border: 1px solid rgba(37,99,235,.22);
    border-radius: 20px;
    padding: 20px 24px;
    margin: 3px 0 18px 0;
    background:
        radial-gradient(circle at 94% 5%, rgba(147,197,253,.32), transparent 30%),
        linear-gradient(135deg, #102a62 0%, #1648a8 60%, #2563eb 100%);
    box-shadow: 0 16px 38px rgba(30,64,175,.16);
}

.rcd-hero,
.rcd-hero * {
    color: #ffffff !important;
}

.rcd-hero-title {
    font-size: 1.8rem;
    line-height: 1.05;
    font-weight: 900;
    letter-spacing: -.025em;
    margin-bottom: 3px;
}

.rcd-kicker {
    font-size: .74rem;
    font-weight: 850;
    letter-spacing: .12em;
    color: #bfdbfe !important;
}

.rcd-phase {
    display: inline-block;
    margin-top: 10px;
    padding: 6px 11px;
    border-radius: 999px;
    border: 1px solid rgba(255,255,255,.30);
    background: rgba(255,255,255,.13);
    color: #ffffff !important;
    font-size: .80rem;
    font-weight: 800;
}

/* Metric cards */
[data-testid="stMetric"] {
    border: 1px solid var(--rcd-border);
    border-radius: 15px;
    padding: .82rem .95rem;
    background: linear-gradient(145deg, #ffffff 0%, #f0f6ff 100%);
    box-shadow: 0 7px 20px rgba(30,64,175,.07);
}

[data-testid="stMetricLabel"] p,
[data-testid="stMetricLabel"] {
    color: var(--rcd-muted) !important;
    font-size: .80rem;
    font-weight: 700;
}

[data-testid="stMetricValue"] div,
[data-testid="stMetricValue"] {
    color: #172033 !important;
    font-weight: 850;
}

[data-testid="stMetricDelta"] div {
    color: #64748b !important;
}

/* Sezioni */
.rcd-section {
    color: #172033 !important;
    font-size: 1.14rem;
    font-weight: 900;
    letter-spacing: -.015em;
    margin: 1.25rem 0 .65rem 0;
}

.rcd-rolebar {
    color: #334155 !important;
    font-size: .88rem;
    font-weight: 750;
    padding: 9px 12px;
    border: 1px solid #cfe0f8;
    border-radius: 10px;
    background: #edf5ff;
    margin: 7px 0 12px 0;
}

/* Target */
.rcd-target {
    border: 1px solid #bbf7d0;
    border-left: 5px solid #22c55e;
    border-radius: 15px;
    padding: 15px 17px;
    background:
        radial-gradient(circle at 95% 10%, rgba(34,197,94,.12), transparent 28%),
        #f7fff9;
    box-shadow: 0 8px 24px rgba(21,128,61,.06);
    margin: 7px 0 11px 0;
}

.rcd-target *,
.rcd-target-name,
.rcd-target-meta {
    color: #173526 !important;
}

.rcd-target .rcd-kicker {
    color: #15803d !important;
}

.rcd-target-name {
    font-size: 1.25rem;
    font-weight: 900;
}

.rcd-target-meta {
    margin-top: 4px;
    color: #4b6354 !important;
}

/* Container, expander, form controls */
div[data-testid="stExpander"] {
    border-radius: 12px;
    border: 1px solid #cfddf2;
    background: rgba(245,249,255,.90);
}

div[data-testid="stVerticalBlockBorderWrapper"] {
    border-color: #cfddf2 !important;
    border-radius: 14px !important;
    background: linear-gradient(145deg, #ffffff, #f3f7ff);
}

div[data-baseweb="select"] > div,
[data-testid="stNumberInput"] input,
[data-testid="stTextInput"] input {
    background: #ffffff !important;
    color: #172033 !important;
    border-color: #cbd5e1 !important;
}

div[data-baseweb="select"] span,
div[data-baseweb="select"] div {
    color: #172033 !important;
}

.stButton > button {
    border-radius: 10px;
    min-height: 2.75rem;
    font-weight: 800;
}

.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #1d4ed8, #2563eb);
    border: none;
    color: #ffffff !important;
    box-shadow: 0 6px 16px rgba(37,99,235,.18);
}

.stButton > button[kind="primary"] * {
    color: #ffffff !important;
}

/* Alert Streamlit più leggibili */
[data-testid="stAlert"] {
    border-radius: 12px;
}
[data-testid="stAlert"] p,
[data-testid="stAlert"] div {
    color: #1e293b !important;
}

/* Dataframe: non alteriamo lo sfondo interno, ma titolo/contorno sì */
[data-testid="stDataFrame"] {
    border: 1px solid #dbe3ef;
    border-radius: 12px;
    overflow: hidden;
    background: #ffffff;
}

/* Caption */
[data-testid="stCaptionContainer"] p {
    color: #64748b !important;
}

/* Badge riutilizzabili */
.rcd-badge {
    display: inline-block;
    border-radius: 999px;
    padding: 3px 8px;
    font-size: .72rem;
    font-weight: 850;
    margin-right: 5px;
    border: 1px solid #dbe3ef;
    background: #f8fafc;
    color: #334155 !important;
}
.rcd-badge.good { color:#166534 !important; border-color:#bbf7d0; background:#f0fdf4; }
.rcd-badge.warn { color:#92400e !important; border-color:#fde68a; background:#fffbeb; }
.rcd-badge.bad  { color:#991b1b !important; border-color:#fecaca; background:#fef2f2; }

/* Evita testi "invisibili" nei markdown custom */
.rcd-league-card,
.rcd-league-card *,
.rcd-league-team {
    color: #172033 !important;
}

/* Scroll più pulito */
::-webkit-scrollbar { width: 10px; height: 10px; }
::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 999px; }
::-webkit-scrollbar-track { background: transparent; }




/* Solo le 4 card "Panoramica Squadre & Alert Strategici" */
div[data-testid="stVerticalBlock"]:has(> div > div > #league-overview-metrics)
div[data-testid="stHorizontalBlock"] div[data-testid="stMetricValue"] {
    font-size: clamp(1.55rem, 2.2vw, 2.25rem) !important;
    line-height: 1.05 !important;
}
div[data-testid="stVerticalBlock"]:has(> div > div > #league-overview-metrics)
div[data-testid="stHorizontalBlock"] div[data-testid="stMetricLabel"] {
    font-size: .92rem !important;
}
div[data-testid="stVerticalBlock"]:has(> div > div > #league-overview-metrics)
div[data-testid="stHorizontalBlock"] div[data-testid="stMetricDelta"] {
    font-size: .82rem !important;
}

</style>
""", unsafe_allow_html=True)

ROLE_LIMITS: dict[str, int] = {
    "P": 3,
    "D": 8,
    "C": 8,
    "A": 6,
}
TOTAL_SLOTS_PER_TEAM = sum(ROLE_LIMITS.values())

# Calibrazione finale per ruolo.
# Derivata dai target richiesti:
# P: 6.7 -> 9.0, D: 8.7 -> 9.2, C: 8.2 -> 8.5, A invariato.
ROLE_RATING_MULTIPLIERS = {
    "P": 9.0 / 6.7,
    "D": 9.2 / 8.7,
    "C": 8.5 / 8.2,
    "A": 1.0,
}


# Valutazione rosa più "netta".
# I giocatori TOP devono incidere più delle riserve/terze fasce.
TEAM_PLAYER_WEIGHTS = {
    "TOP": 2.40,          # >= 9.0
    "PRIMA": 1.70,        # 8.0 - 8.9
    "SECONDA": 1.20,      # 7.0 - 7.9
    "TERZA": 0.85,        # 6.5 - 6.9
    "SOTTO_SOGLIA": 0.55, # < 6.5
}

# Amplifica le differenze fra rose senza alterare i rating individuali.
TEAM_RATING_CENTER = 6.70
TEAM_RATING_SPREAD = 1.35
TOP_PLAYER_BONUS = 0.16
ELITE_PLAYER_BONUS = 0.08
WEAK_PLAYER_PENALTY = 0.10
TEAM_RATING_MIN = 4.0
TEAM_RATING_MAX = 9.5


# Calibrazione finale dei voti squadra.
# Obiettivo empirico richiesto:
# 4.5 -> ~5.5
# 6.7 -> ~8.0
TEAM_GRADE_CALIBRATION_X1 = 4.5
TEAM_GRADE_CALIBRATION_Y1 = 5.5
TEAM_GRADE_CALIBRATION_X2 = 6.7
TEAM_GRADE_CALIBRATION_Y2 = 8.0

# Stima iniziale usata solo quando non esistono ancora abbastanza
# precedenti di asta nel database. Appena ci sono acquisti reali,
# la stima viene sostituita dalla mediana dei moltiplicatori osservati.
DEFAULT_AUCTION_MULTIPLIER = 2.5
MIN_HISTORY_FOR_ROLE_ESTIMATE = 2

# Strategia di protezione budget durante l'asta.
# I portieri devono restare un reparto relativamente economico per lasciare
# margine sufficiente ai TOP di centrocampo e attacco.
THIRD_GOALKEEPER_CURRENT_BUDGET_SHARE = 0.025
SECOND_GOALKEEPER_CURRENT_BUDGET_SHARE = 0.08
PREMIUM_C_A_RESERVE_SHARE = 0.58

DRAFT_ORDER = ("P", "D", "C", "A")
ROLE_NAMES = {
    "P": "Portieri",
    "D": "Difensori",
    "C": "Centrocampisti",
    "A": "Attaccanti",
}

# Modificatore portieri:
# tra le tre squadre dei portieri presenti nella rosa, la squadra
# che ha subito meno gol prende +1.0, la seconda 0.0, la terza -1.0.
GOALKEEPER_GOALS_CONCEDED_MODIFIERS = {
    1: 1.0,
    2: 0.0,
    3: -1.0,
}

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
    "slot_fantacalcio, primo_anno_serie_a, "
    "ballottaggio_con, rigorista_ordine, piazzati, piazzati_ordine, "
    "quotazione_fc, fvm_fc, data_source, source_updated_at, source_aliases"
)

FANTACALCIO_FORMATIONS_URL = (
    "https://www.fantacalcio.it/news/calcio-italia/06_08_2026/"
    "asta-fantacalcio-le-probabili-formazioni-della-serie-a-enilive-2026-27-495558"
)
FANTACALCIO_QUOTES_URL = "https://www.fantacalcio.it/quotazioni-fantacalcio/2026-27"
PLAYER_DATA_SOURCE_LABEL = "Fantacalcio.it 2026/27"

TEAM_MAP = {
    "Napoli": "NAP", "Juventus": "JUV", "Milan": "MIL", "Inter": "INT",
    "Roma": "ROM", "Lazio": "LAZ", "Atalanta": "ATA", "Fiorentina": "FIO",
    "Torino": "TOR", "Bologna": "BOL", "Genoa": "GEN", "Sassuolo": "SAS",
    "Udinese": "UDI", "Cagliari": "CAG", "Verona": "VER", "Lecce": "LEC",
    "Cremonese": "CRE", "Parma": "PAR", "Como": "COM", "Pisa": "PIS",
    "Frosinone": "FRO", "Monza": "MON", "Venezia": "VEN",
}

DATA_DIR = Path(__file__).resolve().parent
STATS_FILE = DATA_DIR / "player_aggregated_stats.csv"
SEASON_FILE = DATA_DIR / "season-2526.csv"


# Tab 4: modifiche manuali persistenti ai giocatori.
# Richiede una tabella Supabase dedicata (SQL fornito sotto).
CUSTOM_MODIFIER_TABLE = "player_custom_modifiers"
USER_TEAM_TABLE = "user_team_assignments"
USER_STRATEGY_TABLE = "user_strategy_settings"

GOALKEEPER_STRATEGY_OPTIONS = (
    "Tre titolari",
    "Stessa Squadra",
)
CREDIT_STRATEGY_OPTIONS = (
    "Modificatore Difesa",
    "Bonus",
    "Bilanciato",
)

DEFAULT_GOALKEEPER_STRATEGY = "Stessa Squadra"
DEFAULT_CREDIT_STRATEGY = "Bilanciato"

# Con la strategia "Tre titolari" evitiamo i portieri dei club TOP:
# il vantaggio marginale non giustifica il costo e toglierebbe budget a C/A.
THREE_STARTERS_EXCLUDED_TOP_CLUBS = {
    "MIL",  # Milan
    "INT",  # Inter
    "JUV",  # Juventus
    "NAP",  # Napoli
    "ROM",  # Roma
    "COM",  # Como
}

# Budget consigliato su base 500 crediti.
# Il preset Bilanciato parte dai range definiti dall'utente:
# P 40–50, D 45–55, C 150–200; l'attacco riceve il residuo.
STRATEGY_BUDGET_ALLOCATIONS = {
    "Bilanciato": {
        "P": 45,
        "D": 50,
        "C": 175,
        "A": 230,
    },
    "Modificatore Difesa": {
        "P": 55,
        "D": 90,
        "C": 155,
        "A": 200,
    },
    "Bonus": {
        "P": 30,
        "D": 35,
        "C": 190,
        "A": 245,
    },
}


CUSTOM_MODIFIERS = {
    "Nessuna modifica": {"key": None, "value": 0.0},
    "⭐ Preferito (+0.5)": {"key": "preferito", "value": 0.5},
    "🟢 Bonus extra +1.0": {"key": "bonus_1", "value": 1.0},
    "🟢 Bonus extra +0.5": {"key": "bonus_05", "value": 0.5},
    "🟢 Bonus extra +0.3": {"key": "bonus_03", "value": 0.3},
    "🟡 Ballottaggio (-0.3)": {"key": "ballottaggio", "value": -0.3},
    "🟠 Malus -0.5": {"key": "malus_05", "value": -0.5},
    "🔴 Malus -1.0": {"key": "malus_1", "value": -1.0},
    "🔴 Riserva (-1.5)": {"key": "riserva", "value": -1.5},
}


SOUND_URLS = {
    "massive": "https://raw.githubusercontent.com/fabzanda-gif/fantahelper/main/johncenaprankcall_cutted.mp3",
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


# ============================================================
# AUTENTICAZIONE — GOOGLE / FACEBOOK VIA SUPABASE AUTH
# ============================================================

AUTH_SESSION_KEYS = (
    "auth_access_token",
    "auth_refresh_token",
    "auth_user",
    "auth_flow_id",
)


def get_public_app_url() -> str:
    """
    URL pubblico dell'app usato come redirect OAuth.

    In produzione è consigliato impostare in .streamlit/secrets.toml:
    APP_URL = "https://nome-app.streamlit.app"
    """
    configured = st.secrets.get("APP_URL")
    if configured:
        return str(configured).rstrip("/")

    try:
        headers = st.context.headers
        host = headers.get("Host") or headers.get("host")
        proto = (
            headers.get("X-Forwarded-Proto")
            or headers.get("x-forwarded-proto")
            or "https"
        )
        if host:
            return f"{proto}://{host}".rstrip("/")
    except Exception:
        pass

    return "http://localhost:8501"


@st.cache_resource
def get_auth_flow_client(flow_id: str) -> Client:
    """Client Supabase dedicato al flusso OAuth corrente."""
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_KEY"],
    )


def _oauth_response_url(response: Any) -> str:
    """Estrae l'URL OAuth sia da oggetti supabase-py sia da dict."""
    if response is None:
        return ""
    if isinstance(response, dict):
        return str(response.get("url") or "")
    return str(getattr(response, "url", "") or "")


def _minimal_user_dict(user: Any) -> dict[str, Any]:
    if user is None:
        return {}

    metadata = getattr(user, "user_metadata", None) or {}
    identities = getattr(user, "identities", None) or []

    return {
        "id": str(getattr(user, "id", "") or ""),
        "email": str(getattr(user, "email", "") or ""),
        "metadata": dict(metadata) if isinstance(metadata, dict) else {},
        "identities": identities,
    }


def _auth_avatar_url(user: dict[str, Any]) -> str:
    metadata = user.get("metadata") or {}
    return str(
        metadata.get("avatar_url")
        or metadata.get("picture")
        or ""
    )


def clear_auth_state() -> None:
    for key in AUTH_SESSION_KEYS:
        st.session_state.pop(key, None)


def save_authenticated_session(
    response: Any,
    fallback_user: Any | None = None,
) -> dict[str, Any]:
    """Salva in modo uniforme sessione e utente restituiti da Supabase."""
    session = getattr(response, "session", None)
    user = getattr(response, "user", None) or fallback_user

    # set_session() in alcune versioni può restituire direttamente una sessione.
    if session is None and getattr(response, "access_token", None):
        session = response

    if session is None:
        raise RuntimeError("Supabase non ha restituito una sessione valida.")

    access_token = getattr(session, "access_token", None)
    refresh_token = getattr(session, "refresh_token", None)

    if not access_token or not refresh_token:
        raise RuntimeError("Token OAuth non disponibili.")

    st.session_state["auth_access_token"] = access_token
    st.session_state["auth_refresh_token"] = refresh_token
    st.session_state["auth_user"] = _minimal_user_dict(user)

    return st.session_state["auth_user"]


def handle_oauth_callback() -> bool:
    """Scambia il code PKCE e trasferisce la sessione al client principale."""
    code_param = st.query_params.get("code")
    flow_id = st.query_params.get("auth_flow")

    if not code_param or not flow_id:
        return False

    try:
        # Fondamentale: recuperiamo lo stesso client usato per iniziare
        # questo specifico flusso OAuth/PKCE.
        auth_client = get_auth_flow_client(str(flow_id))

        response = auth_client.auth.exchange_code_for_session(
            {"auth_code": str(code_param)}
        )

        session = getattr(response, "session", None)
        user = getattr(response, "user", None)

        if session is None:
            session = auth_client.auth.get_session()

        access_token = getattr(session, "access_token", None)
        refresh_token = getattr(session, "refresh_token", None)

        if not access_token or not refresh_token:
            raise RuntimeError("Supabase non ha restituito una sessione OAuth valida.")

        if user is None:
            verified = auth_client.auth.get_user(access_token)
            user = getattr(verified, "user", None)

        # Trasferiamo esplicitamente i token anche al client Supabase principale.
        # Questo rende il ritorno OAuth più robusto, soprattutto su mobile,
        # dove Streamlit ricrea la pagina dopo il redirect completo.
        main_response = supabase.auth.set_session(
            access_token,
            refresh_token,
        )
        save_authenticated_session(
            main_response,
            fallback_user=user,
        )

        st.session_state["auth_flow_id"] = str(flow_id)

        st.query_params.clear()
        st.rerun()

    except Exception as exc:
        st.query_params.clear()
        st.session_state["auth_callback_error"] = str(exc)
        return False

    return True



def restore_and_verify_auth_session() -> dict[str, Any] | None:
    """Ripristina e verifica la sessione OAuth/email dopo i rerun Streamlit."""
    access_token = st.session_state.get("auth_access_token")
    refresh_token = st.session_state.get("auth_refresh_token")

    if not access_token or not refresh_token:
        return None

    try:
        # Manteniamo sincronizzato il client principale.
        main_response = supabase.auth.set_session(
            access_token,
            refresh_token,
        )

        main_session = getattr(main_response, "session", None)
        if main_session is not None:
            access_token = getattr(main_session, "access_token", access_token)
            refresh_token = getattr(main_session, "refresh_token", refresh_token)
            st.session_state["auth_access_token"] = access_token
            st.session_state["auth_refresh_token"] = refresh_token

        verified = supabase.auth.get_user(access_token)
        user_obj = getattr(verified, "user", None)

        if user_obj is None:
            clear_auth_state()
            return None

        user = _minimal_user_dict(user_obj)
        st.session_state["auth_user"] = user
        return user

    except Exception:
        clear_auth_state()
        return None



def build_provider_login_url(provider: str) -> str:
    """
    Genera URL OAuth separato per provider.
    Ogni provider usa un proprio verifier PKCE.
    """
    flow_id = uuid.uuid4().hex
    auth_client = get_auth_flow_client(flow_id)

    app_url = get_public_app_url().rstrip("/")
    redirect_to = (
        f"{app_url}/"
        f"?auth_callback=1&auth_flow={flow_id}"
    )

    response = auth_client.auth.sign_in_with_oauth(
        {
            "provider": provider,
            "options": {
                "redirect_to": redirect_to,
            },
        }
    )
    return _oauth_response_url(response)



def sign_in_with_email_password(email: str, password: str) -> tuple[bool, str]:
    """Login classico Supabase con email/password."""
    try:
        auth_client = get_auth_flow_client("password-login")
        response = auth_client.auth.sign_in_with_password(
            {
                "email": email.strip(),
                "password": password,
            }
        )

        session = getattr(response, "session", None)
        user = getattr(response, "user", None)

        if session is None:
            return False, "Supabase non ha restituito una sessione valida."

        access_token = getattr(session, "access_token", None)
        refresh_token = getattr(session, "refresh_token", None)

        if not access_token or not refresh_token:
            return False, "Token di sessione non disponibili."

        st.session_state["auth_access_token"] = access_token
        st.session_state["auth_refresh_token"] = refresh_token
        st.session_state["auth_user"] = _minimal_user_dict(user)
        st.session_state["auth_flow_id"] = "password-login"

        return True, ""

    except Exception as exc:
        return False, str(exc)


def load_registration_teams() -> list[dict[str, Any]]:
    """
    Legge id e nome delle fantasquadre per la registrazione.
    La tabella teams deve consentire SELECT con la chiave anon/publishable.
    """
    try:
        rows = (
            supabase.table("teams")
            .select("id, name")
            .order("name")
            .execute()
            .data
            or []
        )
        return [
            {"id": row.get("id"), "name": str(row.get("name") or "")}
            for row in rows
            if row.get("id") is not None and row.get("name")
        ]
    except Exception as exc:
        st.session_state["registration_teams_error"] = str(exc)
        return []


def sign_up_with_email_password(
    email: str,
    password: str,
    team_id: Any,
    team_name: str,
    goalkeeper_strategy: str,
    credit_strategy: str,
) -> tuple[bool, str]:
    """
    Registrazione Supabase email/password.

    La squadra scelta viene salvata subito nei user_metadata. Se l'email
    richiede conferma, al primo login autenticato verrà trasformata
    automaticamente nell'associazione persistente user_team_assignments.
    """
    try:
        auth_client = get_auth_flow_client("password-signup")
        response = auth_client.auth.sign_up(
            {
                "email": email.strip(),
                "password": password,
                "options": {
                    "data": {
                        "signup_team_id": str(team_id),
                        "signup_team_name": team_name,
                        "signup_goalkeeper_strategy": goalkeeper_strategy,
                        "signup_credit_strategy": credit_strategy,
                    },
                    "email_redirect_to": get_public_app_url().rstrip("/") + "/",
                },
            }
        )

        user = getattr(response, "user", None)
        session = getattr(response, "session", None)

        if user is None:
            return False, "Registrazione non completata."

        # Se Supabase crea subito una sessione, associamo immediatamente
        # anche la fantasquadra.
        if session is not None:
            access_token = getattr(session, "access_token", None)
            refresh_token = getattr(session, "refresh_token", None)

            if access_token and refresh_token:
                main_response = supabase.auth.set_session(
                    access_token,
                    refresh_token,
                )
                save_authenticated_session(
                    main_response,
                    fallback_user=user,
                )
                st.session_state["auth_flow_id"] = "password-signup"

                user_id = str(getattr(user, "id", "") or "")
                if user_id:
                    ok, error = save_user_team_assignment(
                        user_id,
                        team_id,
                        team_name,
                    )
                    if not ok:
                        return False, (
                            "Account creato, ma non riesco ad associare la squadra: "
                            + error
                        )

                    strategy_ok, strategy_error = save_user_strategy_settings(
                        user_id,
                        goalkeeper_strategy,
                        credit_strategy,
                    )
                    if not strategy_ok:
                        return False, (
                            "Account creato, ma non riesco a salvare la strategia: "
                            + strategy_error
                        )

                return True, "signed_in"

        return True, "check_email"

    except Exception as exc:
        return False, str(exc)



def render_login_page() -> None:
    """Pagina login fantahe1per con Google, Facebook ed email/password."""
    st.markdown(
        """
<style>
[data-testid="stSidebar"] { display: none; }
.login-shell { max-width: 470px; margin: 5vh auto 0 auto; }
.login-brand {
    border-radius: 24px; padding: 30px 30px 26px;
    background: radial-gradient(circle at 92% 4%, rgba(96,165,250,.42), transparent 31%),
                linear-gradient(145deg, #102a62 0%, #1648a8 64%, #2563eb 100%);
    box-shadow: 0 22px 55px rgba(30,64,175,.22);
    text-align: center; margin-bottom: 16px;
}
.login-brand * { color: #fff !important; }
.login-eyebrow { font-size:.74rem; font-weight:900; letter-spacing:.14em; color:#bfdbfe !important; }
.login-title { font-size:2rem; font-weight:950; letter-spacing:-.04em; margin:7px 0 4px; }
.login-subtitle { font-size:.95rem; color:#dbeafe !important; }
.login-card {
    border:1px solid #cbdcf5; border-radius:20px; padding:25px 24px;
    background:rgba(255,255,255,.97); box-shadow:0 13px 38px rgba(15,23,42,.08);
}
.login-card-title { text-align:center; font-weight:900; font-size:1.08rem; color:#172033 !important; margin-bottom:15px; }
.social-login {
    height:52px; display:flex; align-items:center; justify-content:center; gap:12px;
    width:100%; border-radius:12px; text-decoration:none !important;
    font-size:.96rem; font-weight:850; margin:11px 0; box-sizing:border-box;
}
.social-login:hover { transform:translateY(-1px); text-decoration:none !important; }
.social-login.google { color:#24324a !important; background:#fff; border:1px solid #cbd5e1; box-shadow:0 4px 12px rgba(15,23,42,.06); }
.social-login.facebook { color:#fff !important; background:#1877F2; border:1px solid #1468d4; box-shadow:0 5px 14px rgba(24,119,242,.18); }
.social-login.facebook span { color:#fff !important; }
.social-login.google span { color:#24324a !important; }
.social-logo { width:22px; height:22px; flex:0 0 22px; }
.login-note { text-align:center; color:#64748b !important; font-size:.78rem; line-height:1.45; margin-top:16px; }
        .login-shell + div { max-width: 470px; margin-left:auto; margin-right:auto; }
        div[data-testid="stForm"] {
            max-width: 470px;
            margin-left: auto;
            margin-right: auto;
            border: 1px solid #cbdcf5;
            border-radius: 18px;
            background: rgba(255,255,255,.97);
            padding: 18px 20px 20px;
            box-shadow: 0 10px 28px rgba(15,23,42,.06);
        }
        div[data-testid="stRadio"] {
            max-width: 470px;
            margin-left: auto;
            margin-right: auto;
        }
</style>
        """,
        unsafe_allow_html=True,
    )

    error = st.session_state.pop("auth_callback_error", None)

    try:
        google_url = build_provider_login_url("google")
        facebook_url = build_provider_login_url("facebook")
    except Exception as exc:
        st.error("Non riesco a generare i link di login. Controlla la configurazione Auth di Supabase.")
        st.caption(str(exc))
        st.stop()

    google_url = escape(google_url, quote=True)
    facebook_url = escape(facebook_url, quote=True)

    # IMPORTANTE: l'HTML viene costruito senza righe vuote/interruzioni tra i tag.
    # In questo modo il parser Markdown di Streamlit non spezza il blocco HTML
    # trasformandone alcune parti in testo/codice visibile.
    login_html = (
        '<div class="login-shell">'
        '<div class="login-brand">'
        '<div class="login-eyebrow">fantahe1per</div>'
        '<div class="login-title">⚽ Auction &amp; Season Center</div>'
        '<div class="login-subtitle">Asta, rosa, formazione e campionato in un unico posto.</div>'
        '</div>'
        '<div class="login-card">'
        '<div class="login-card-title">Accedi per continuare</div>'
        f'<a class="social-login google" href="{google_url}" target="_blank" rel="noopener">'
        '<svg class="social-logo" viewBox="0 0 24 24" aria-hidden="true">'
        '<path fill="#4285F4" d="M21.6 12.23c0-.71-.06-1.4-.18-2.07H12v3.92h5.38a4.6 4.6 0 0 1-2 3.02v2.54h3.24c1.9-1.75 2.98-4.33 2.98-7.41z"/>'
        '<path fill="#34A853" d="M12 22c2.7 0 4.97-.9 6.63-2.43l-3.24-2.54c-.9.6-2.05.96-3.39.96-2.61 0-4.82-1.76-5.61-4.13H3.04v2.62A10 10 0 0 0 12 22z"/>'
        '<path fill="#FBBC05" d="M6.39 13.86A6 6 0 0 1 6.08 12c0-.65.11-1.28.31-1.86V7.52H3.04A10 10 0 0 0 2 12c0 1.61.38 3.13 1.04 4.48l3.35-2.62z"/>'
        '<path fill="#EA4335" d="M12 6.01c1.47 0 2.79.51 3.83 1.5l2.87-2.87A9.63 9.63 0 0 0 12 2a10 10 0 0 0-8.96 5.52l3.35 2.62C7.18 7.77 9.39 6.01 12 6.01z"/>'
        '</svg>'
        '<span>Continua con Google</span>'
        '</a>'
        f'<a class="social-login facebook" href="{facebook_url}" target="_blank" rel="noopener">'
        '<svg class="social-logo" viewBox="0 0 24 24" aria-hidden="true">'
        '<circle cx="12" cy="12" r="12" fill="#ffffff"/>'
        '<path fill="#1877F2" d="M13.52 20v-7h2.35l.35-2.73h-2.7V8.53c0-.79.22-1.33 1.35-1.33h1.44V4.76c-.25-.03-1.1-.1-2.1-.1-2.08 0-3.5 1.27-3.5 3.6v2.01H8.36V13h2.35v7h2.81z"/>'
        '</svg>'
        '<span>Continua con Facebook</span>'
        '</a>'
        '<div class="login-note">L’autenticazione viene gestita da Supabase Auth. '
        'La password del tuo account Google o Facebook non viene gestita dall’app.</div>'
        '</div>'
        '</div>'
    )

    st.markdown(login_html, unsafe_allow_html=True)

    if error:
        st.error(f"Login non completato: {error}")

    st.markdown(
        """
        <div style="
            max-width:470px;
            margin:14px auto 0 auto;
            text-align:center;
            color:#64748b;
            font-size:.82rem;
            font-weight:700;
        ">
            oppure accedi con email e password
        </div>
        """,
        unsafe_allow_html=True,
    )

    login_mode = st.radio(
        "Modalità",
        ["Accedi", "Registrati"],
        horizontal=True,
        key="password_auth_mode",
        label_visibility="collapsed",
    )

    registration_teams = load_registration_teams() if login_mode == "Registrati" else []
    selected_registration_team = None
    selected_goalkeeper_strategy = DEFAULT_GOALKEEPER_STRATEGY
    selected_credit_strategy = DEFAULT_CREDIT_STRATEGY

    with st.form("password_auth_form", clear_on_submit=False):
        email = st.text_input(
            "Email",
            placeholder="nome@email.com",
            key="password_auth_email",
        )
        password = st.text_input(
            "Password",
            type="password",
            placeholder="••••••••",
            key="password_auth_password",
        )

        if login_mode == "Registrati":
            if registration_teams:
                registration_team_names = [
                    team["name"] for team in registration_teams
                ]
                selected_registration_team_name = st.selectbox(
                    "La tua squadra",
                    registration_team_names,
                    key="password_signup_team",
                    help="L'account verrà collegato a questa fantasquadra.",
                )
                selected_registration_team = next(
                    team
                    for team in registration_teams
                    if team["name"] == selected_registration_team_name
                )
            else:
                st.warning(
                    "Non riesco a caricare le squadre dal database. "
                    "La registrazione richiede la scelta della squadra."
                )

            st.markdown("##### 🎯 Strategia")
            selected_goalkeeper_strategy = st.radio(
                "Portieri",
                GOALKEEPER_STRATEGY_OPTIONS,
                index=GOALKEEPER_STRATEGY_OPTIONS.index(DEFAULT_GOALKEEPER_STRATEGY),
                horizontal=True,
                key="password_signup_goalkeeper_strategy",
                help=(
                    "Tre titolari: rotazione fra più squadre. "
                    "Stessa Squadra: dopo il primo portiere, priorità alla copertura dello stesso club."
                ),
            )
            selected_credit_strategy = st.radio(
                "Bilanciamento crediti",
                CREDIT_STRATEGY_OPTIONS,
                index=CREDIT_STRATEGY_OPTIONS.index(DEFAULT_CREDIT_STRATEGY),
                horizontal=True,
                key="password_signup_credit_strategy",
            )
            allocation = STRATEGY_BUDGET_ALLOCATIONS[selected_credit_strategy]
            st.caption(
                f"Budget consigliato → P {allocation['P']} · D {allocation['D']} · "
                f"C {allocation['C']} · A {allocation['A']} cr"
            )

        submit_label = "Accedi" if login_mode == "Accedi" else "Crea account"
        submitted = st.form_submit_button(
            submit_label,
            type="primary",
            use_container_width=True,
        )

        if submitted:
            if not email.strip() or not password:
                st.error("Inserisci email e password.")
            elif len(password) < 6:
                st.error("La password deve contenere almeno 6 caratteri.")
            elif login_mode == "Accedi":
                ok, message = sign_in_with_email_password(email, password)
                if ok:
                    st.rerun()
                else:
                    st.error(f"Login non riuscito: {message}")
            else:
                if selected_registration_team is None:
                    st.error(
                        "Seleziona una squadra prima di creare l'account."
                    )
                else:
                    ok, message = sign_up_with_email_password(
                        email,
                        password,
                        selected_registration_team["id"],
                        selected_registration_team["name"],
                        selected_goalkeeper_strategy,
                        selected_credit_strategy,
                    )
                    if not ok:
                        st.error(f"Registrazione non riuscita: {message}")
                    elif message == "signed_in":
                        st.success(
                            f"Account creato e associato a "
                            f"**{selected_registration_team['name']}**."
                        )
                        st.rerun()
                    else:
                        st.success(
                            f"Account creato per **{selected_registration_team['name']}**. "
                            "Controlla la tua email per confermare l'indirizzo, "
                            "poi torna qui e accedi."
                        )


def _first_name_from_user(user: dict[str, Any]) -> str:
    """Ricava solo il nome, senza cognome, dai metadata Google/Facebook."""
    metadata = user.get("metadata") or {}

    first_name = (
        metadata.get("given_name")
        or metadata.get("first_name")
        or ""
    )
    if first_name:
        return str(first_name).strip().split()[0]

    full_name = str(
        metadata.get("full_name")
        or metadata.get("name")
        or ""
    ).strip()
    if full_name:
        return full_name.split()[0]

    email = str(user.get("email") or "").strip()
    if email:
        candidate = email.split("@")[0]
        candidate = candidate.replace(".", " ").replace("_", " ").replace("-", " ")
        if candidate.strip():
            return candidate.strip().split()[0].capitalize()

    return "Mister"


def _dynamic_greeting() -> str:
    """Saluto in base all'ora italiana."""
    try:
        hour = datetime.now(ZoneInfo("Europe/Rome")).hour
    except Exception:
        hour = datetime.now().hour

    if 5 <= hour < 12:
        return "Buongiorno"
    if 12 <= hour < 18:
        return "Buon pomeriggio"
    return "Buonasera"


def render_app_logo() -> None:
    """Logo nella parte più alta della sidebar."""
    st.sidebar.markdown(
        """
        <style>
        [data-testid="stSidebar"] [data-testid="stSidebarContent"] {
            padding-top: .45rem;
        }
        .rcd-sidebar-logo-wrap {
            display:flex;
            align-items:center;
            justify-content:center;
            width:100%;
            padding:.10rem .20rem .70rem .20rem;
            margin:0;
        }
        .rcd-sidebar-logo {
            display:block;
            width:100%;
            max-width:245px;
            max-height:92px;
            height:auto;
            object-fit:contain;
            object-position:center;
        }
        @media (max-width: 720px) {
            .rcd-sidebar-logo {
                max-width:205px;
                max-height:76px;
            }
        }
        </style>
        <div class="rcd-sidebar-logo-wrap">
            <img
                class="rcd-sidebar-logo"
                src="https://raw.githubusercontent.com/fabzanda-gif/fantahelper/main/Screenshot%202026-08-18%20at%2020.11.38.png"
                alt="Fantahelper"
            >
        </div>
        """,
        unsafe_allow_html=True,
    )



def render_authenticated_user_header(user: dict[str, Any]) -> str:
    """Header con saluto, menu a tendina e avatar."""
    first_name = escape(_first_name_from_user(user))
    greeting = escape(_dynamic_greeting())
    avatar = escape(_auth_avatar_url(user), quote=True)

    pages = {
        "Asta": "🎯",
        "Lega": "📊",
        "Giocatori": "⭐",
        "Giornate": "📥",
        "Formazione": "🧠",
        "Campionato": "🏆",
        "Impostazioni": "⚙️",
    }
    if _is_player_data_admin(user):
        pages["Dati giocatori"] = "🔄"

    if st.session_state.get("active_page") not in pages:
        st.session_state["active_page"] = "Asta"

    st.markdown(
        """
        <style>
        .rcd-nav-greeting {
            text-align:right;
            font-size:1.02rem;
            line-height:1;
            font-weight:900;
            color:#17325f !important;
            white-space:nowrap;
            padding-top:4px;
        }
        .rcd-profile-avatar-wrap {
            width:70px;
            height:70px;
            aspect-ratio:1 / 1;
            flex:0 0 70px;
            border-radius:50%;
            overflow:hidden;
            border:4px solid #ffffff;
            box-shadow:0 5px 16px rgba(30,64,175,.20);
            background:#dbeafe;
            display:flex;
            align-items:center;
            justify-content:center;
        }
        .rcd-profile-avatar {
            display:block;
            width:100% !important;
            height:100% !important;
            min-width:100% !important;
            min-height:100% !important;
            max-width:none !important;
            max-height:none !important;
            aspect-ratio:1 / 1;
            object-fit:cover !important;
            object-position:center center;
            border:0 !important;
            border-radius:0 !important;
            clip-path:none !important;
        }
        .rcd-profile-fallback {
            width:100%;
            height:100%;
            display:flex;
            align-items:center;
            justify-content:center;
            font-size:1.5rem;
        }
        .st-key-profile_nav_popover button {
            width:38px !important;
            min-width:38px !important;
            height:38px !important;
            min-height:38px !important;
            padding:0 !important;
            border-radius:50% !important;
            border:1px solid #bfd2ee !important;
            background:#eef5ff !important;
            color:#17325f !important;
            font-size:1.1rem !important;
            box-shadow:0 4px 12px rgba(30,64,175,.10) !important;
        }
        .st-key-profile_nav_popover button:hover {
            background:#dbeafe !important;
            border-color:#93b6ea !important;
        }
        .st-key-profile_nav_menu button {
            justify-content:flex-start !important;
            text-align:left !important;
            border-radius:10px !important;
            font-weight:700 !important;
        }
        .st-key-profile_menu_logout button {
            background:linear-gradient(135deg,#1d4ed8,#2563eb) !important;
            border:1px solid #1d4ed8 !important;
            color:#ffffff !important;
            font-weight:850 !important;
            border-radius:10px !important;
            width:100% !important;
        }
        .st-key-profile_menu_logout button * {
            color:#ffffff !important;
        }
        .st-key-profile_menu_logout button:hover {
            background:linear-gradient(135deg,#1e40af,#1d4ed8) !important;
            border-color:#1e40af !important;
        }
        @media (max-width: 720px) {
            .rcd-nav-greeting { font-size:.90rem; }
            .rcd-profile-avatar-wrap {
                width:60px;
                height:60px;
                flex-basis:60px;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    _, greeting_col, menu_col, avatar_col = st.columns(
        [7.7, 2.45, 0.42, 0.78],
        gap="small",
        vertical_alignment="center",
    )

    with greeting_col:
        st.markdown(
            f'<div class="rcd-nav-greeting">⚽ {greeting} {first_name}!</div>',
            unsafe_allow_html=True,
        )

    with menu_col:
        with st.popover(" ", key="profile_nav_popover"):
            st.markdown("**Navigazione**")
            with st.container(key="profile_nav_menu"):
                for page, icon in pages.items():
                    active = page == st.session_state["active_page"]
                    label = f"{icon} {page}" + ("  ✓" if active else "")
                    if st.button(
                        label,
                        key=f"nav_page_{normalize_string(page)}",
                        use_container_width=True,
                        type="primary" if active else "secondary",
                    ):
                        st.session_state["active_page"] = page
                        st.rerun()

            st.divider()
            with st.container(key="profile_menu_logout"):
                if st.button(
                    "Logout",
                    key="auth_logout_menu",
                    type="primary",
                    use_container_width=True,
                ):
                    try:
                        flow_id = st.session_state.get("auth_flow_id") or "restored-session"
                        auth_client = get_auth_flow_client(str(flow_id))
                        access = st.session_state.get("auth_access_token")
                        refresh = st.session_state.get("auth_refresh_token")
                        if access and refresh:
                            auth_client.auth.set_session(access, refresh)
                        auth_client.auth.sign_out()
                    except Exception:
                        pass

                    clear_auth_state()
                    for key in (
                        "current_user_team_id",
                        "current_user_team_name",
                        "_ui_defaults_for_team",
                        "sidebar_team_analysis",
                        "manual_target_team",
                        "table_team_filter_tab2",
                        "my_team_budget",
                        "goalkeeper_strategy",
                        "credit_strategy",
                    ):
                        st.session_state.pop(key, None)
                    st.rerun()

    with avatar_col:
        if avatar:
            st.markdown(
                f'<div class="rcd-profile-avatar-wrap">'
                f'<img class="rcd-profile-avatar" src="{avatar}" alt="Profilo">'
                f'</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div class="rcd-profile-avatar-wrap">'
                '<div class="rcd-profile-fallback">⚽</div>'
                '</div>',
                unsafe_allow_html=True,
            )

    return st.session_state["active_page"]



def require_authentication() -> dict[str, Any]:
    """Gate dell'intera applicazione."""
    handle_oauth_callback()

    user = restore_and_verify_auth_session()
    if user:
        return user

    render_login_page()
    st.stop()
    return {}


@st.cache_data(ttl=5)
def load_teams() -> list[dict[str, Any]]:
    return (
        supabase.table("teams")
        .select("id, name, remaining_budget, initial_budget")
        .execute()
        .data
    )



def reconcile_team_budgets_from_rosters(
    teams: list[dict[str, Any]],
    rosters: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Ricostruisce il budget residuo dalla fonte più affidabile:
    budget iniziale - somma degli acquisti registrati.

    Questo evita che un remaining_budget azzerato/obsoleto in `teams`
    faccia apparire tutte le squadre a 0 crediti.
    """
    spent_by_team_id: dict[Any, int] = {}
    spent_by_team_name: dict[str, int] = {}

    for roster in rosters:
        price = int(roster.get("purchase_price") or 0)
        team_id = roster.get("team_id")
        team_data = roster.get("teams") or {}
        team_name = str(team_data.get("name") or "")

        if team_id is not None:
            spent_by_team_id[team_id] = spent_by_team_id.get(team_id, 0) + price
        if team_name:
            spent_by_team_name[team_name] = spent_by_team_name.get(team_name, 0) + price

    reconciled: list[dict[str, Any]] = []
    for team in teams:
        row = dict(team)
        initial = int(row.get("initial_budget") or 0)
        team_id = row.get("id")
        team_name = str(row.get("name") or "")

        spent = (
            spent_by_team_id.get(team_id)
            if team_id in spent_by_team_id
            else spent_by_team_name.get(team_name, 0)
        )
        spent = int(spent or 0)

        # Se conosciamo il budget iniziale, il residuo corretto è deterministico.
        if initial > 0:
            row["remaining_budget"] = max(0, initial - spent)
        else:
            row["remaining_budget"] = max(0, int(row.get("remaining_budget") or 0))

        reconciled.append(row)

    return reconciled


def get_current_user_team_name() -> str:
    """Restituisce esclusivamente la squadra associata al login corrente."""
    return str(st.session_state.get("current_user_team_name") or "")


def get_current_user_team_id() -> str | None:
    value = st.session_state.get("current_user_team_id")
    return str(value) if value is not None else None


def load_user_strategy_settings(user_id: str) -> dict[str, Any]:
    """Carica la strategia personale e indica se esiste già una riga persistente."""
    try:
        rows = (
            supabase.table(USER_STRATEGY_TABLE)
            .select("user_id, goalkeeper_strategy, credit_strategy")
            .eq("user_id", user_id)
            .limit(1)
            .execute()
            .data
            or []
        )
        if rows:
            row = rows[0]
            return {
                "exists": True,
                "goalkeeper_strategy": (
                    row.get("goalkeeper_strategy")
                    if row.get("goalkeeper_strategy") in GOALKEEPER_STRATEGY_OPTIONS
                    else DEFAULT_GOALKEEPER_STRATEGY
                ),
                "credit_strategy": (
                    row.get("credit_strategy")
                    if row.get("credit_strategy") in CREDIT_STRATEGY_OPTIONS
                    else DEFAULT_CREDIT_STRATEGY
                ),
            }
    except Exception as exc:
        st.session_state["user_strategy_table_error"] = str(exc)

    return {
        "exists": False,
        "goalkeeper_strategy": DEFAULT_GOALKEEPER_STRATEGY,
        "credit_strategy": DEFAULT_CREDIT_STRATEGY,
    }


def save_user_strategy_settings(
    user_id: str,
    goalkeeper_strategy: str,
    credit_strategy: str,
) -> tuple[bool, str]:
    """Salva la strategia personale su Supabase."""
    if goalkeeper_strategy not in GOALKEEPER_STRATEGY_OPTIONS:
        goalkeeper_strategy = DEFAULT_GOALKEEPER_STRATEGY
    if credit_strategy not in CREDIT_STRATEGY_OPTIONS:
        credit_strategy = DEFAULT_CREDIT_STRATEGY

    try:
        (
            supabase.table(USER_STRATEGY_TABLE)
            .upsert(
                {
                    "user_id": user_id,
                    "goalkeeper_strategy": goalkeeper_strategy,
                    "credit_strategy": credit_strategy,
                },
                on_conflict="user_id",
            )
            .execute()
        )
        st.session_state["goalkeeper_strategy"] = goalkeeper_strategy
        st.session_state["credit_strategy"] = credit_strategy
        return True, ""
    except Exception as exc:
        return False, str(exc)


def sync_user_strategy_session(user: dict[str, Any]) -> dict[str, str]:
    """
    Carica la strategia nel session_state.
    Per una nuova registrazione usa anche i metadata come bootstrap.
    """
    user_id = str(user.get("id") or "").strip()
    if not user_id:
        return {
            "goalkeeper_strategy": DEFAULT_GOALKEEPER_STRATEGY,
            "credit_strategy": DEFAULT_CREDIT_STRATEGY,
        }

    settings = load_user_strategy_settings(user_id)

    # I metadata di registrazione sono solo bootstrap iniziale.
    # Se esiste già una riga in user_strategy_settings, quella è la source of truth.
    if not settings.get("exists"):
        metadata = user.get("metadata") or {}
        metadata_gk = metadata.get("signup_goalkeeper_strategy")
        metadata_credit = metadata.get("signup_credit_strategy")

        if metadata_gk in GOALKEEPER_STRATEGY_OPTIONS:
            settings["goalkeeper_strategy"] = metadata_gk
        if metadata_credit in CREDIT_STRATEGY_OPTIONS:
            settings["credit_strategy"] = metadata_credit

        if metadata_gk or metadata_credit:
            save_user_strategy_settings(
                user_id,
                settings["goalkeeper_strategy"],
                settings["credit_strategy"],
            )

    st.session_state["goalkeeper_strategy"] = settings["goalkeeper_strategy"]
    st.session_state["credit_strategy"] = settings["credit_strategy"]
    return settings


def current_goalkeeper_strategy() -> str:
    return str(
        st.session_state.get("goalkeeper_strategy")
        or DEFAULT_GOALKEEPER_STRATEGY
    )


def current_credit_strategy() -> str:
    return str(
        st.session_state.get("credit_strategy")
        or DEFAULT_CREDIT_STRATEGY
    )


def load_user_team_assignment(user_id: str) -> dict[str, Any] | None:
    """Legge l'associazione persistente del solo utente autenticato."""
    try:
        rows = (
            supabase.table(USER_TEAM_TABLE)
            .select("user_id, team_id, team_name")
            .eq("user_id", user_id)
            .limit(1)
            .execute()
            .data
            or []
        )
        return rows[0] if rows else None
    except Exception as exc:
        st.session_state["user_team_table_error"] = str(exc)
        return None


def save_user_team_assignment(
    user_id: str,
    team_id: Any,
    team_name: str,
) -> tuple[bool, str]:
    """Crea/aggiorna l'associazione utente -> squadra."""
    try:
        (
            supabase.table(USER_TEAM_TABLE)
            .upsert(
                {
                    "user_id": user_id,
                    "team_id": str(team_id),
                    "team_name": team_name,
                },
                on_conflict="user_id",
            )
            .execute()
        )
        st.session_state["current_user_team_id"] = str(team_id)
        st.session_state["current_user_team_name"] = team_name
        st.session_state.pop("user_team_table_error", None)
        return True, ""
    except Exception as exc:
        return False, str(exc)


def require_user_team_assignment(
    user: dict[str, Any],
    teams: list[dict[str, Any]],
) -> str:
    """
    Ogni login deve essere associato a una fantasquadra.

    Se l'associazione esiste viene caricata automaticamente.
    Se manca, l'app mostra una schermata obbligatoria di scelta e si ferma
    finché l'utente non completa l'associazione.
    """
    user_id = str(user.get("id") or "").strip()
    if not user_id:
        st.error("Non riesco a identificare l'utente autenticato.")
        st.stop()

    team_by_id = {
        str(team.get("id")): team
        for team in teams
        if team.get("id") is not None
    }

    assignment = load_user_team_assignment(user_id)
    if assignment:
        assigned_id = str(assignment.get("team_id") or "")
        matched = team_by_id.get(assigned_id)

        if matched:
            team_name = str(matched.get("name") or assignment.get("team_name") or "")
            st.session_state["current_user_team_id"] = assigned_id
            st.session_state["current_user_team_name"] = team_name
            return team_name

    # Se l'utente si è registrato via email scegliendo già una squadra,
    # recuperiamo la scelta dai metadata e creiamo automaticamente
    # l'associazione persistente al primo accesso autenticato.
    metadata = user.get("metadata") or {}
    metadata_team_id = str(metadata.get("signup_team_id") or "")
    metadata_team_name = str(metadata.get("signup_team_name") or "")

    if metadata_team_id and metadata_team_name:
        matched = team_by_id.get(metadata_team_id)
        if matched:
            canonical_name = str(matched.get("name") or metadata_team_name)
            ok, error = save_user_team_assignment(
                user_id,
                metadata_team_id,
                canonical_name,
            )
            if ok:
                sync_user_team_ui_defaults(canonical_name)
                return canonical_name
            if "duplicate" in error.lower() or "unique" in error.lower():
                st.error(
                    f"La squadra **{canonical_name}** è già associata "
                    "a un altro account."
                )
                st.stop()

    # Se la tabella non esiste ancora, mostriamo un errore esplicito invece
    # di lasciare l'app in uno stato ambiguo.
    table_error = st.session_state.get("user_team_table_error")
    if table_error and (
        "does not exist" in table_error.lower()
        or "relation" in table_error.lower()
        or "schema cache" in table_error.lower()
    ):
        st.error(
            "Manca la tabella Supabase **user_team_assignments**. "
            "Esegui prima lo script SQL fornito con questa versione."
        )
        with st.expander("Dettaglio tecnico"):
            st.code(table_error)
        st.stop()

    st.markdown(
        """
        <div style="
            max-width:680px;
            margin:2.2rem auto .8rem auto;
            padding:24px 26px;
            border:1px solid #cfe0f8;
            border-radius:20px;
            background:linear-gradient(145deg,#ffffff,#eef5ff);
            box-shadow:0 12px 34px rgba(30,64,175,.09);
        ">
            <div style="font-size:.75rem;font-weight:900;letter-spacing:.12em;color:#315a9e;">
                CONFIGURAZIONE PROFILO
            </div>
            <div style="font-size:1.55rem;font-weight:950;color:#172033;margin-top:5px;">
                ⚽ Qual è la tua squadra?
            </div>
            <div style="color:#64748b;margin-top:6px;">
                Questa scelta collegherà il tuo login alla fantasquadra e verrà
                ricordata automaticamente ai prossimi accessi.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not teams:
        st.error("Non ci sono squadre configurate nel database.")
        st.stop()

    team_names = [str(team["name"]) for team in teams]
    selected_name = st.selectbox(
        "Seleziona la tua fantasquadra",
        team_names,
        key="first_login_team_assignment",
    )
    selected_team = next(
        team for team in teams
        if str(team["name"]) == selected_name
    )

    st.markdown("#### 🎯 Strategia")
    first_gk_strategy = st.radio(
        "Portieri",
        GOALKEEPER_STRATEGY_OPTIONS,
        index=GOALKEEPER_STRATEGY_OPTIONS.index(DEFAULT_GOALKEEPER_STRATEGY),
        horizontal=True,
        key="first_login_goalkeeper_strategy",
    )
    first_credit_strategy = st.radio(
        "Bilanciamento crediti",
        CREDIT_STRATEGY_OPTIONS,
        index=CREDIT_STRATEGY_OPTIONS.index(DEFAULT_CREDIT_STRATEGY),
        horizontal=True,
        key="first_login_credit_strategy",
    )
    first_allocation = STRATEGY_BUDGET_ALLOCATIONS[first_credit_strategy]
    st.caption(
        f"Budget consigliato → P {first_allocation['P']} · D {first_allocation['D']} · "
        f"C {first_allocation['C']} · A {first_allocation['A']} cr"
    )

    st.caption(
        "L'associazione e la strategia vengono ricordate ai prossimi accessi."
    )

    if st.button(
        "Conferma configurazione",
        type="primary",
        use_container_width=True,
        key="confirm_first_team_assignment",
    ):
        ok, error = save_user_team_assignment(
            user_id,
            selected_team["id"],
            selected_name,
        )
        if ok:
            strategy_ok, strategy_error = save_user_strategy_settings(
                user_id,
                first_gk_strategy,
                first_credit_strategy,
            )
            if not strategy_ok:
                st.error(
                    "Squadra associata, ma non riesco a salvare la strategia: "
                    f"{strategy_error}"
                )
                st.stop()

            st.success(
                f"Configurazione salvata per **{selected_name}**."
            )
            st.rerun()
        else:
            if "duplicate" in error.lower() or "unique" in error.lower():
                st.error(
                    "Questa squadra risulta già associata a un altro account. "
                    "Scegline un'altra oppure modifica l'associazione in Supabase."
                )
            else:
                st.error(f"Non riesco a salvare l'associazione: {error}")

    st.stop()
    return ""


@st.cache_data(ttl=5)
def load_rosters() -> list[dict[str, Any]]:
    """Carica le rose usando gli FK espliciti e ricostruisce le relazioni.

    Non dipendiamo da `teams(name)` / `players(...)` nella query di rosters:
    se Supabase non espone correttamente una relazione, la vecchia versione
    riceveva `teams=None` o `players=None` e la rosa risultava vuota nella UI
    pur avendo righe reali nella tabella `rosters`.
    """
    roster_rows = (
        supabase.table("rosters")
        .select("id, team_id, player_id, purchase_price")
        .execute()
        .data
    )

    if not roster_rows:
        return []

    team_ids = {row.get("team_id") for row in roster_rows if row.get("team_id") is not None}
    player_ids = {row.get("player_id") for row in roster_rows if row.get("player_id") is not None}

    teams_rows = (
        supabase.table("teams")
        .select("id, name, remaining_budget, initial_budget")
        .in_("id", list(team_ids))
        .execute()
        .data
    ) if team_ids else []

    players_rows = (
        supabase.table("players")
        .select(PLAYER_FIELDS)
        .in_("id", list(player_ids))
        .execute()
        .data
    ) if player_ids else []

    team_by_id = {row["id"]: row for row in teams_rows}
    player_by_id = {row["id"]: row for row in players_rows}

    hydrated = []
    for row in roster_rows:
        hydrated.append({
            "id": row.get("id"),
            "purchase_price": row.get("purchase_price", 0),
            "team_id": row.get("team_id"),
            "player_id": row.get("player_id"),
            "teams": team_by_id.get(row.get("team_id")),
            "players": player_by_id.get(row.get("player_id")),
        })

    return hydrated


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


@st.cache_data(ttl=5)
def load_custom_modifiers() -> dict[Any, dict[str, Any]]:
    """Carica le modifiche manuali persistenti dal database."""
    try:
        rows = (
            supabase.table(CUSTOM_MODIFIER_TABLE)
            .select("player_id, modifier_key, modifier_label, modifier_value")
            .execute()
            .data
        )
    except Exception:
        # Se la tabella non è stata ancora creata, l'app continua a funzionare
        # usando il rating standard.
        return {}

    return {
        row["player_id"]: row
        for row in rows
        if row.get("player_id") is not None
    }


def save_custom_modifier(
    player_id: Any,
    modifier_label: str,
) -> tuple[bool, str]:
    """Salva/sostituisce la modifica manuale di un giocatore."""
    config = CUSTOM_MODIFIERS[modifier_label]

    try:
        (
            supabase.table(CUSTOM_MODIFIER_TABLE)
            .delete()
            .eq("player_id", player_id)
            .execute()
        )

        if config["key"] is not None:
            (
                supabase.table(CUSTOM_MODIFIER_TABLE)
                .insert(
                    {
                        "player_id": player_id,
                        "modifier_key": config["key"],
                        "modifier_label": modifier_label,
                        "modifier_value": config["value"],
                    }
                )
                .execute()
            )

        load_custom_modifiers.clear()
        return True, ""
    except Exception as exc:
        return False, str(exc)


def reset_custom_modifier(player_id: Any) -> tuple[bool, str]:
    try:
        (
            supabase.table(CUSTOM_MODIFIER_TABLE)
            .delete()
            .eq("player_id", player_id)
            .execute()
        )
        load_custom_modifiers.clear()
        return True, ""
    except Exception as exc:
        return False, str(exc)


def invalidate_data_cache() -> None:
    load_teams.clear()
    load_rosters.clear()
    load_players.clear()
    load_external_data.clear()
    load_custom_modifiers.clear()


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


def resolve_my_team_name(team_names: list[str]) -> str | None:
    """Trova la squadra associata al login corrente fra le squadre disponibili."""
    assigned = get_current_user_team_name()
    if not assigned:
        return None

    normalized = {
        normalize_string(name): name
        for name in team_names
        if isinstance(name, str)
    }
    return normalized.get(normalize_string(assigned))



def is_my_team(team_name: str | None) -> bool:
    if not team_name:
        return False
    return (
        normalize_string(team_name)
        == normalize_string(get_current_user_team_name())
    )


def default_team_index(
    team_names: list[str],
    preferred: str | None = None,
) -> int:
    if not team_names:
        return 0

    preferred = preferred or get_current_user_team_name()

    for index, name in enumerate(team_names):
        if normalize_string(name) == normalize_string(preferred):
            return index

    return 0



def queue_purchase_banner(
    team_name: str,
    player_name: str,
    rating: float,
    purchase_price: int,
) -> None:
    """Memorizza il banner prima di st.rerun(), che interrompe subito il run."""
    if not is_my_team(team_name):
        st.session_state.pop("pending_purchase_banner", None)
        return

    if rating >= 9.0:
        level = "massive"
        title = "🏆 COLPO TOP!"
        lead = "entra nella rosa"
        closing = ""
    elif rating >= 8.0:
        level = "great"
        title = "✨ PRIMA FASCIA!"
        lead = "entra nella rosa"
        closing = "Innesto di livello."
    else:
        level = "normal"
        title = "✅ ACQUISTO COMPLETATO"
        lead = "è un nuovo giocatore di"
        closing = ""

    st.session_state["pending_purchase_banner"] = {
        "level": level,
        "title": title,
        "player_name": player_name,
        "team_name": team_name,
        "rating": float(rating),
        "purchase_price": int(purchase_price),
        "lead": lead,
        "closing": closing,
    }



def render_pending_purchase_banner() -> None:
    """Mostra il banner dell'ultimo acquisto dopo il rerun."""
    banner = st.session_state.get("pending_purchase_banner")
    if not banner:
        return

    st.session_state.pop("pending_purchase_banner", None)

    level = banner["level"]
    banner_class = {
        "massive": "massive",
        "great": "great",
        "normal": "normal",
    }.get(level, "normal")

    player_name = escape(str(banner.get("player_name") or "—"))
    team_name = escape(str(banner.get("team_name") or "—"))
    rating = float(banner.get("rating") or 0.0)
    purchase_price = int(banner.get("purchase_price") or 0)
    lead = escape(str(banner.get("lead") or "entra nella rosa"))
    closing = escape(str(banner.get("closing") or ""))

    closing_html = (
        f'<span class="auction-banner-closing">{closing}</span>'
        if closing
        else ""
    )

    banner_html = (
        "<style>"
        ".auction-banner{padding:22px 28px;margin:12px 0 22px;border-radius:18px;"
        "text-align:center;border:2px solid rgba(255,255,255,.55);"
        "box-shadow:0 10px 30px rgba(0,0,0,.16);animation:auctionPulse 1.1s ease-in-out 2;}"
        ".auction-banner.massive{background:radial-gradient(circle at 90% 10%,rgba(250,204,21,.35),transparent 28%),"
        "linear-gradient(135deg,#4c1d95,#1e3a8a);}"
        ".auction-banner.great{background:radial-gradient(circle at 90% 10%,rgba(74,222,128,.30),transparent 30%),"
        "linear-gradient(135deg,#064e3b,#0f766e);}"
        ".auction-banner.normal{background:linear-gradient(135deg,#1e3a8a,#0f172a);}"
        ".auction-banner,.auction-banner *{color:#fff!important;}"
        ".auction-banner-title{font-size:1.8rem;font-weight:900;margin-bottom:8px;letter-spacing:.02em;}"
        ".auction-banner-text{font-size:1.06rem;font-weight:600;line-height:1.45;}"
        ".auction-banner-text strong{font-weight:900;}"
        ".auction-banner-dot{opacity:.72;padding:0 5px;}"
        ".auction-banner-closing{display:block;margin-top:5px;font-size:.88rem;opacity:.9;}"
        "@keyframes auctionPulse{0%,100%{transform:scale(1)}50%{transform:scale(1.025)}}"
        "</style>"
        f'<div class="auction-banner {banner_class}">'
        f'<div class="auction-banner-title">{escape(str(banner["title"]))}</div>'
        '<div class="auction-banner-text">'
        f'<strong>{player_name}</strong> {lead} <strong>{team_name}</strong>'
        '<span class="auction-banner-dot">·</span>'
        f'Rating <strong>{rating:.1f}</strong>'
        '<span class="auction-banner-dot">·</span>'
        f'Pagato <strong>{purchase_price} cr</strong>'
        f'{closing_html}'
        '</div></div>'
    )

    st.markdown(banner_html, unsafe_allow_html=True)

    if level == "massive":
        st.balloons()
        play_sound(SOUND_URLS["massive"])
    elif level == "great":
        st.balloons()
        play_sound(SOUND_URLS["great"])
    else:
        play_sound(SOUND_URLS["normal"])


# ============================================================
# AGGIORNAMENTO DATI GIOCATORI — FONTI ESTERNE
# ============================================================

def _source_http_get(url: str, timeout: int = 20) -> str:
    """Scarica una pagina pubblica con user-agent browser e controlli minimi."""
    response = requests.get(
        url,
        timeout=timeout,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 Chrome/140 Safari/537.36"
            ),
            "Accept-Language": "it-IT,it;q=0.9,en;q=0.7",
        },
    )
    response.raise_for_status()
    return response.text


def _clean_source_player_name(value: str) -> str:
    value = re.sub(r"\([^)]*\)", "", str(value or ""))
    value = re.sub(r"\s+", " ", value)
    return value.strip(" ,.;:-–—")


def _split_source_names(value: str) -> list[str]:
    """Divide elenchi Fantacalcio separati da virgola/punto e virgola."""
    cleaned = re.sub(r"\([^)]*\)", "", str(value or ""))
    chunks = re.split(r"[;,]", cleaned)
    result: list[str] = []
    for chunk in chunks:
        name = _clean_source_player_name(chunk)
        if name:
            result.append(name)
    return result


def _team_code_from_heading(team_name: str) -> str:
    clean = str(team_name or "").strip().title()
    if clean in TEAM_MAP:
        return TEAM_MAP[clean]
    # Alcuni heading possono essere già codici.
    normalized = normalize_string(clean)
    for full_name, code_value in TEAM_MAP.items():
        if normalize_string(full_name) == normalized:
            return code_value
    return clean.upper()[:3]


def parse_fantacalcio_formations(html: str) -> dict[str, dict[str, Any]]:
    """
    Parser robusto dell'articolo Fantacalcio 2026/27.

    Strategia:
    1. converte l'articolo in testo lineare;
    2. individua le 20 sezioni squadra tramite heading;
    3. estrae da ogni sezione:
       - Probabile formazione
       - Ballottaggi
       - Rigoristi
       - Calci da fermo

    Questo evita di dipendere dalla struttura HTML/CSS del sito.
    """
    soup = BeautifulSoup(html, "html.parser")

    # Testo lineare: molto più stabile della navigazione per sibling/div.
    raw_text = soup.get_text("\n", strip=True)
    lines = [
        re.sub(r"\s+", " ", line).strip()
        for line in raw_text.splitlines()
        if re.sub(r"\s+", " ", line).strip()
    ]

    # Individua le righe che corrispondono a una squadra.
    valid_codes = set(TEAM_MAP.values())
    team_starts: list[tuple[int, str, str]] = []

    # IMPORTANTISSIMO: qui NON usiamo il fallback "prime 3 lettere"
    # di _team_code_from_heading(), perché parole come "Comparatore" -> COM
    # e "Mondo ..." -> MON verrebbero scambiate per COMO/MONZA e, con la
    # deduplica, nasconderebbero gli heading reali più avanti nell'articolo.
    normalized_team_names = {
        normalize_string(full_name): code_value
        for full_name, code_value in TEAM_MAP.items()
    }
    code_to_name = {
        code_value: full_name
        for full_name, code_value in TEAM_MAP.items()
    }

    for idx, line in enumerate(lines):
        normalized_line = normalize_string(line)
        code = normalized_team_names.get(normalized_line)

        # Accetta anche un heading che sia già il codice ufficiale.
        if code is None and line.strip().upper() in valid_codes:
            code = line.strip().upper()

        if code in valid_codes and len(line) <= 30:
            team_starts.append((idx, code, line))

    # Deduplica eventuali heading ripetuti mantenendo la prima occorrenza utile.
    deduped: list[tuple[int, str, str]] = []
    seen_codes: set[str] = set()
    for item in team_starts:
        if item[1] not in seen_codes:
            seen_codes.add(item[1])
            deduped.append(item)

    parsed: dict[str, dict[str, Any]] = {}

    for pos, (start_idx, team_code, team_heading) in enumerate(deduped):
        end_idx = (
            deduped[pos + 1][0]
            if pos + 1 < len(deduped)
            else len(lines)
        )
        section_lines = lines[start_idx + 1:end_idx]

        def _extract_single_field_line(label: str) -> str:
            """
            I quattro campi utili dell'articolo sono paragrafi singoli.
            Leggiamo SOLO la riga del campo (o al massimo la riga successiva
            se il renderer ha separato label e valore).

            Questo è fondamentale per l'ultima squadra: senza un heading
            successivo, una regex multi-linea su "Calci da fermo" finirebbe
            per inglobare articoli correlati, autore, pubblicità, ecc.
            """
            label_norm = normalize_string(label)

            for line_idx, line in enumerate(section_lines):
                line_norm = normalize_string(line)

                # Riconosce anche "Probabile formazione (da dx a sx): ..."
                if not line_norm.startswith(label_norm):
                    continue

                # Prima prova: valore sulla stessa riga dopo i due punti.
                if ":" in line:
                    value = line.split(":", 1)[1].strip()
                    if value:
                        return value

                # Fallback: il valore può essere nella riga immediatamente dopo.
                if line_idx + 1 < len(section_lines):
                    next_line = section_lines[line_idx + 1].strip()
                    next_norm = normalize_string(next_line)
                    known_labels = {
                        "allenatore",
                        "modulo",
                        "probabile formazione",
                        "ballottaggi",
                        "rigoristi",
                        "calci da fermo",
                    }
                    if (
                        next_line
                        and not any(
                            next_norm.startswith(known)
                            for known in known_labels
                        )
                    ):
                        return next_line

                return ""

            return ""

        formation_text = _extract_single_field_line("Probabile formazione")
        ballot_text = _extract_single_field_line("Ballottaggi")
        penalty_text = _extract_single_field_line("Rigoristi")
        set_piece_text = _extract_single_field_line("Calci da fermo")

        # XI probabile
        starters: list[str] = []
        for part in re.split(r"[;,]", formation_text):
            name = _clean_source_player_name(part)
            if name:
                starters.append(name)

        # Ballottaggi
        ballot_groups: list[list[str]] = []
        # Rimuove spiegazioni tattiche tra parentesi senza perdere la coppia.
        clean_ballot_text = re.sub(r"\([^)]*\)", "", ballot_text)
        for chunk in re.split(r"[;,]", clean_ballot_text):
            names = []
            for raw_name in chunk.split("/"):
                cleaned = _clean_source_player_name(raw_name)
                if cleaned:
                    names.append(cleaned)
            if len(names) >= 2:
                ballot_groups.append(names)

        penalties = _split_source_names(penalty_text)
        set_pieces = _split_source_names(set_piece_text)

        # Non includere sezioni chiaramente vuote/errate.
        if starters or ballot_groups or penalties or set_pieces:
            parsed[team_code] = {
                "team_name": team_heading.title(),
                "starters": starters,
                "ballot_groups": ballot_groups,
                "penalties": penalties,
                "set_pieces": set_pieces,
            }

    return parsed


def parse_fantacalcio_quotations(html: str) -> list[dict[str, Any]]:
    """
    Best-effort parser del Listone ufficiale.

    Serve soprattutto a verificare il club attuale e, quando disponibili
    come testo HTML, quotazione/FVM. Non inserisce automaticamente nuovi
    giocatori: quelli non presenti in Supabase vengono segnalati.
    """
    soup = BeautifulSoup(html, "html.parser")
    rows: list[dict[str, Any]] = []

    # Strategia 1: tabelle HTML reali.
    for table in soup.find_all("table"):
        headers = [
            th.get_text(" ", strip=True)
            for th in table.find_all("th")
        ]
        header_norm = [normalize_string(h) for h in headers]
        if not any("calciatore" in h for h in header_norm):
            continue

        for tr in table.find_all("tr"):
            cells = [td.get_text(" ", strip=True) for td in tr.find_all("td")]
            if len(cells) < 3:
                continue

            # Euristica: nome è il campo testuale più lungo tra i primi,
            # squadra è un codice di 3 lettere.
            team_code = next(
                (
                    c.strip().upper()
                    for c in cells
                    if re.fullmatch(r"[A-Z]{3}", c.strip().upper())
                ),
                "",
            )
            text_cells = [
                c.strip()
                for c in cells
                if c.strip()
                and not re.fullmatch(r"\d+(?:[.,]\d+)?", c.strip())
                and not re.fullmatch(r"[A-Z]{3}", c.strip().upper())
            ]
            if not team_code or not text_cells:
                continue

            player_name = max(text_cells, key=len)
            numbers = [
                int(float(c.replace(",", ".")))
                for c in cells
                if re.fullmatch(r"\d+(?:[.,]\d+)?", c.strip())
            ]

            rows.append(
                {
                    "name": player_name,
                    "team_nfl": team_code,
                    "quotazione_fc": numbers[0] if numbers else None,
                    "fvm_fc": numbers[2] if len(numbers) >= 3 else (
                        numbers[-1] if len(numbers) >= 2 else None
                    ),
                }
            )

    return rows


def _source_alias_token(source_name: str, team_code: str | None) -> str:
    """Alias stabile per ricordare associazioni manuali fonte -> giocatore."""
    return (
        f"{str(team_code or '').strip().upper()}|"
        f"{normalize_string(source_name)}"
    )


def _player_has_source_alias(
    player: dict[str, Any],
    source_name: str,
    team_code: str | None,
) -> bool:
    token = _source_alias_token(source_name, team_code)
    aliases = player.get("source_aliases") or []
    if isinstance(aliases, str):
        aliases = [aliases]
    return token in {str(alias) for alias in aliases}


def _name_similarity(left: str, right: str) -> float:
    return SequenceMatcher(
        None,
        normalize_string(left),
        normalize_string(right),
    ).ratio()


def _best_player_match(
    source_name: str,
    db_players: list[dict[str, Any]],
    team_code: str | None = None,
    min_score: float = 0.78,
) -> tuple[dict[str, Any] | None, float]:
    """Exact-first matching, poi fuzzy entro lo stesso club quando possibile."""
    source_norm = normalize_string(source_name)
    if not source_norm:
        return None, 0.0

    # Le associazioni confermate manualmente hanno precedenza assoluta.
    # Il controllo avviene prima del filtro squadra: se un giocatore cambia club,
    # l'alias continua a identificarlo e il nuovo team può essere aggiornato.
    for player in db_players:
        if _player_has_source_alias(player, source_name, team_code):
            return player, 1.0

    candidates = db_players
    if team_code:
        team_candidates = [
            player for player in db_players
            if str(player.get("team_nfl") or "") == team_code
        ]
        if team_candidates:
            candidates = team_candidates

    for player in candidates:
        if normalize_string(player.get("name", "")) == source_norm:
            return player, 1.0

    best = None
    best_score = 0.0
    for player in candidates:
        score = _name_similarity(source_name, str(player.get("name") or ""))
        if score > best_score:
            best = player
            best_score = score

    if best_score >= min_score:
        return best, best_score
    return None, best_score


def build_player_source_preview(
    db_players: list[dict[str, Any]],
    formations: dict[str, dict[str, Any]],
    quotations: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """
    Produce modifiche candidate senza scrivere nulla su Supabase.

    La preview è intenzionalmente conservativa:
    - aggiorna solo giocatori già presenti nel DB;
    - mostra i nuovi/non riconosciuti come unmatched;
    - ballottaggio prevale su titolare;
    - rigoristi e piazzati hanno ordine esplicito.
    """
    updates_by_id: dict[Any, dict[str, Any]] = {}
    unmatched: list[dict[str, Any]] = []
    now_iso = datetime.now(ZoneInfo("Europe/Rome")).isoformat()

    def ensure_update(player: dict[str, Any], confidence: float) -> dict[str, Any]:
        player_id = player.get("id")
        if player_id not in updates_by_id:
            updates_by_id[player_id] = {
                "player_id": player_id,
                "name": player.get("name"),
                "old_team": player.get("team_nfl"),
                "new_team": player.get("team_nfl"),
                "old_status": player.get("status_titolarita"),
                "new_status": player.get("status_titolarita"),
                "old_rigorista": bool(player.get("rigorista")),
                "new_rigorista": False,
                "old_ballottaggio_con": player.get("ballottaggio_con"),
                "new_ballottaggio_con": None,
                "old_quotazione_fc": player.get("quotazione_fc"),
                "new_quotazione_fc": player.get("quotazione_fc"),
                "old_fvm_fc": player.get("fvm_fc"),
                "new_fvm_fc": player.get("fvm_fc"),
                "rigorista_ordine": None,
                "piazzati": False,
                "piazzati_ordine": None,
                "confidence": confidence,
                "data_source": PLAYER_DATA_SOURCE_LABEL,
                "source_updated_at": now_iso,
            }
        else:
            updates_by_id[player_id]["confidence"] = max(
                float(updates_by_id[player_id]["confidence"]),
                confidence,
            )
        return updates_by_id[player_id]

    # 1. Quotazioni/listone: club corrente e quotazione/FVM.
    for source in quotations:
        match, confidence = _best_player_match(
            source.get("name", ""),
            db_players,
            source.get("team_nfl"),
            min_score=0.82,
        )
        if match is None:
            unmatched.append(
                {
                    "source": "Quotazioni",
                    "team": source.get("team_nfl"),
                    "name": source.get("name"),
                    "reason": f"Nessun match (score {confidence:.2f})",
                }
            )
            continue

        row = ensure_update(match, confidence)
        if source.get("team_nfl"):
            row["new_team"] = source["team_nfl"]
        if source.get("quotazione_fc") is not None:
            row["new_quotazione_fc"] = source["quotazione_fc"]
        if source.get("fvm_fc") is not None:
            row["new_fvm_fc"] = source["fvm_fc"]

    # 2. Gerarchie articolo.
    for team_code, data in formations.items():
        team_db_players = [
            player for player in db_players
            if str(player.get("team_nfl") or "") == team_code
        ]

        matched_ids: set[Any] = set()
        ballot_partner_map: dict[Any, list[str]] = {}

        # XI probabile.
        for source_name in data.get("starters", []):
            match, confidence = _best_player_match(
                source_name,
                db_players,
                team_code,
            )
            if match is None:
                unmatched.append(
                    {
                        "source": "Probabile XI",
                        "team": team_code,
                        "name": source_name,
                        "reason": f"Nessun match (score {confidence:.2f})",
                    }
                )
                continue
            matched_ids.add(match.get("id"))
            row = ensure_update(match, confidence)
            row["new_status"] = "Titolare"

        # Ballottaggi: tutti i membri diventano Ballottaggio.
        for group in data.get("ballot_groups", []):
            matched_group: list[tuple[dict[str, Any], str, float]] = []
            for source_name in group:
                match, confidence = _best_player_match(
                    source_name,
                    db_players,
                    team_code,
                )
                if match is None:
                    unmatched.append(
                        {
                            "source": "Ballottaggio",
                            "team": team_code,
                            "name": source_name,
                            "reason": f"Nessun match (score {confidence:.2f})",
                        }
                    )
                    continue
                matched_group.append((match, source_name, confidence))

            for match, source_name, confidence in matched_group:
                matched_ids.add(match.get("id"))
                row = ensure_update(match, confidence)
                row["new_status"] = "Ballottaggio"
                partners = [
                    other_name
                    for other_match, other_name, _ in matched_group
                    if other_match.get("id") != match.get("id")
                ]
                ballot_partner_map.setdefault(match.get("id"), []).extend(partners)

        for player_id, partners in ballot_partner_map.items():
            updates_by_id[player_id]["new_ballottaggio_con"] = ", ".join(
                dict.fromkeys(partners)
            )

        # Rigoristi.
        for order, source_name in enumerate(data.get("penalties", []), start=1):
            match, confidence = _best_player_match(
                source_name,
                db_players,
                team_code,
            )
            if match is None:
                unmatched.append(
                    {
                        "source": "Rigoristi",
                        "team": team_code,
                        "name": source_name,
                        "reason": f"Nessun match (score {confidence:.2f})",
                    }
                )
                continue
            row = ensure_update(match, confidence)
            row["new_rigorista"] = True
            row["rigorista_ordine"] = order

        # Piazzati.
        for order, source_name in enumerate(data.get("set_pieces", []), start=1):
            match, confidence = _best_player_match(
                source_name,
                db_players,
                team_code,
            )
            if match is None:
                unmatched.append(
                    {
                        "source": "Calci da fermo",
                        "team": team_code,
                        "name": source_name,
                        "reason": f"Nessun match (score {confidence:.2f})",
                    }
                )
                continue
            row = ensure_update(match, confidence)
            row["piazzati"] = True
            row["piazzati_ordine"] = order

        # Solo per club effettivamente presenti nell'articolo:
        # chi non è XI né ballottaggio viene trattato come riserva.
        for player in team_db_players:
            player_id = player.get("id")
            if player_id not in matched_ids:
                row = ensure_update(player, 1.0)
                row["new_status"] = "Riserva"
                row["new_ballottaggio_con"] = None

    preview = list(updates_by_id.values())

    # Mostriamo solo righe con almeno una variazione utile o nuovi metadata.
    filtered: list[dict[str, Any]] = []
    for row in preview:
        changed = any(
            (
                row.get("old_team") != row.get("new_team"),
                row.get("old_status") != row.get("new_status"),
                bool(row.get("old_rigorista")) != bool(row.get("new_rigorista")),
                (row.get("old_ballottaggio_con") or None)
                != (row.get("new_ballottaggio_con") or None),
                row.get("old_quotazione_fc") != row.get("new_quotazione_fc"),
                row.get("old_fvm_fc") != row.get("new_fvm_fc"),
                row.get("rigorista_ordine") is not None,
                bool(row.get("piazzati")),
            )
        )
        if changed:
            filtered.append(row)

    filtered.sort(key=lambda r: (str(r.get("new_team") or ""), str(r.get("name") or "")))
    unmatched.sort(key=lambda r: (str(r.get("team") or ""), str(r.get("name") or "")))
    return filtered, unmatched


def apply_player_source_preview(
    preview: list[dict[str, Any]],
) -> tuple[int, list[str]]:
    """Applica su Supabase solo la preview già approvata."""
    updated = 0
    errors: list[str] = []

    for row in preview:
        payload = {
            "team_nfl": row.get("new_team"),
            "status_titolarita": row.get("new_status"),
            "rigorista": bool(row.get("new_rigorista")),
            "rigorista_ordine": row.get("rigorista_ordine"),
            "ballottaggio_con": row.get("new_ballottaggio_con"),
            "piazzati": bool(row.get("piazzati")),
            "piazzati_ordine": row.get("piazzati_ordine"),
            "quotazione_fc": row.get("new_quotazione_fc"),
            "fvm_fc": row.get("new_fvm_fc"),
            "data_source": row.get("data_source"),
            "source_updated_at": row.get("source_updated_at"),
        }
        try:
            (
                supabase.table("players")
                .update(payload)
                .eq("id", row["player_id"])
                .execute()
            )
            updated += 1
        except Exception as exc:
            errors.append(f"{row.get('name')}: {exc}")

    if updated:
        invalidate_data_cache()
    return updated, errors



def _unmatched_source_payload(item: dict[str, Any]) -> dict[str, Any]:
    """Traduce il tipo di fonte in campi giocatore applicabili."""
    source = str(item.get("source") or "")
    payload: dict[str, Any] = {
        "team_nfl": item.get("team"),
        "data_source": PLAYER_DATA_SOURCE_LABEL,
        "source_updated_at": datetime.now(
            ZoneInfo("Europe/Rome")
        ).isoformat(),
    }
    if source == "Probabile XI":
        payload["status_titolarita"] = "Titolare"
    elif source == "Ballottaggio":
        payload["status_titolarita"] = "Ballottaggio"
    elif source == "Rigoristi":
        payload["rigorista"] = True
    elif source == "Calci da fermo":
        payload["piazzati"] = True
    return payload


def _compose_new_player_name(
    source_name: str,
    first_initial: str | None = None,
) -> str:
    """
    Builds the final database name for a new player.

    If the source only exposes a surname (e.g. "Tourè") and a homonym exists,
    we store "A. Tourè" using the admin-supplied initial.
    """
    base = _clean_source_player_name(source_name)
    initial = str(first_initial or "").strip().upper()[:1]

    # If source already looks like "A. Surname" or contains multiple words,
    # keep it as-is unless an explicit initial was supplied.
    if initial:
        surname = base.split()[-1] if base else ""
        return f"{initial}. {surname}".strip()

    return base


def _existing_name_conflicts(
    source_name: str,
    db_players: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Returns existing DB players with the same normalized surname/name.
    Useful when Fantacalcio exposes only a surname.
    """
    base = _clean_source_player_name(source_name)
    source_norm = normalize_string(base)
    source_surname = normalize_string(base.split()[-1] if base else "")

    conflicts: list[dict[str, Any]] = []
    for player in db_players:
        db_name = str(player.get("name") or "")
        db_norm = normalize_string(db_name)
        db_surname = normalize_string(db_name.split()[-1] if db_name else "")

        if db_norm == source_norm or (
            source_surname
            and db_surname == source_surname
        ):
            conflicts.append(player)

    return conflicts


def apply_unmatched_resolutions(
    unmatched: list[dict[str, Any]],
    resolutions: dict[int, dict[str, Any]],
) -> tuple[int, int, list[str]]:
    """
    Risolve manualmente i nomi non riconosciuti:
    - associa a un giocatore esistente, oppure
    - crea un nuovo giocatore e lo marca rookie Serie A.
    """
    associated = 0
    created = 0
    errors: list[str] = []

    for idx, item in enumerate(unmatched):
        resolution = resolutions.get(idx) or {}
        action = resolution.get("action", "Ignora")
        if action == "Ignora":
            continue

        payload = _unmatched_source_payload(item)

        try:
            if action == "Associa a esistente":
                player_id = resolution.get("player_id")
                if player_id is None:
                    errors.append(
                        f"{item.get('name')}: nessun giocatore selezionato."
                    )
                    continue

                source_team = str(item.get("team") or "").strip().upper()
                if not source_team:
                    errors.append(
                        f"{item.get('name')}: la fonte non contiene una squadra valida."
                    )
                    continue

                # L'associazione manuale certifica che il record esistente e il
                # nome trovato dalla fonte sono lo stesso calciatore.
                payload["team_nfl"] = source_team

                existing_player = (
                    supabase.table("players")
                    .select("id, source_aliases")
                    .eq("id", player_id)
                    .limit(1)
                    .execute()
                    .data
                    or []
                )
                existing_aliases = (
                    existing_player[0].get("source_aliases") or []
                    if existing_player
                    else []
                )
                if isinstance(existing_aliases, str):
                    existing_aliases = [existing_aliases]

                alias_token = _source_alias_token(
                    str(item.get("name") or ""),
                    source_team,
                )
                payload["source_aliases"] = list(
                    dict.fromkeys(
                        [str(alias) for alias in existing_aliases]
                        + [alias_token]
                    )
                )

                (
                    supabase.table("players")
                    .update(payload)
                    .eq("id", player_id)
                    .execute()
                )
                associated += 1

            elif action == "Nuovo giocatore":
                role = str(resolution.get("role") or "").strip()
                if role not in {"P", "D", "C", "A"}:
                    errors.append(
                        f"{item.get('name')}: ruolo P/D/C/A obbligatorio."
                    )
                    continue

                final_name = _compose_new_player_name(
                    str(item.get("name") or ""),
                    resolution.get("first_initial"),
                )
                if not final_name:
                    errors.append(
                        f"{item.get('name')}: nome giocatore non valido."
                    )
                    continue

                new_payload = {
                    "name": final_name,
                    "team_nfl": item.get("team"),
                    "role": role,
                    "list_price": int(resolution.get("list_price") or 1),
                    "status_titolarita": payload.get(
                        "status_titolarita", "Riserva"
                    ),
                    "rigorista": bool(payload.get("rigorista", False)),
                    "piazzati": bool(payload.get("piazzati", False)),
                    "primo_anno_serie_a": bool(
                        resolution.get("rookie", True)
                    ),
                    "data_source": PLAYER_DATA_SOURCE_LABEL,
                    "source_updated_at": payload["source_updated_at"],
                    "source_aliases": [
                        _source_alias_token(
                            str(item.get("name") or ""),
                            str(item.get("team") or ""),
                        )
                    ],
                }

                try:
                    (
                        supabase.table("players")
                        .insert(new_payload)
                        .execute()
                    )
                    created += 1
                except Exception as exc:
                    message = str(exc)
                    if (
                        "players_name_unique" in message
                        or "duplicate key value" in message.lower()
                    ):
                        errors.append(
                            f"{item.get('name')}: esiste già un giocatore con "
                            f"nome `{final_name}`. Usa l'iniziale del nome oppure "
                            "associalo al record esistente."
                        )
                    else:
                        raise

        except Exception as exc:
            errors.append(f"{item.get('name')}: {exc}")

    if associated or created:
        invalidate_data_cache()

    return associated, created, errors




def build_missing_from_source_candidates(
    db_players: list[dict[str, Any]],
    quotations: list[dict[str, Any]],
    rosters: list[dict[str, Any]] | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """
    Trova giocatori presenti in Supabase ma non nel Listone ufficiale letto.

    Sicurezza:
    - il controllo viene considerato affidabile solo se il Listone contiene
      abbastanza righe e una copertura ampia di squadre;
    - nessun giocatore viene eliminato automaticamente;
    - i giocatori già presenti in una rosa vengono marcati come protetti.
    """
    rosters = rosters or []

    source_names_by_team: dict[str, list[str]] = {}
    source_teams: set[str] = set()

    for row in quotations:
        team = str(row.get("team_nfl") or "").strip().upper()
        name = str(row.get("name") or "").strip()
        if not team or not name:
            continue
        source_teams.add(team)
        source_names_by_team.setdefault(team, []).append(name)

    # Un listone Serie A completo dovrebbe essere ampiamente sopra 300 righe
    # e coprire praticamente tutte le 20 squadre.
    source_is_complete_enough = (
        len(quotations) >= 300
        and len(source_teams) >= 18
    )

    rostered_player_ids = {
        roster.get("player_id")
        for roster in rosters
        if roster.get("player_id") is not None
    }

    candidates: list[dict[str, Any]] = []

    if not source_is_complete_enough:
        return candidates, {
            "safe": False,
            "rows": len(quotations),
            "teams": len(source_teams),
            "reason": (
                "Il Listone letto non sembra abbastanza completo per usare "
                "l'assenza come indicazione di possibile uscita dalla Serie A."
            ),
        }

    for player in db_players:
        player_id = player.get("id")
        team = str(player.get("team_nfl") or "").strip().upper()
        name = str(player.get("name") or "").strip()

        # Se il club stesso non compare nella fonte, non assumiamo nulla.
        if not team or team not in source_names_by_team or not name:
            continue

        source_team_names = source_names_by_team[team]

        exact = any(
            normalize_string(source_name) == normalize_string(name)
            for source_name in source_team_names
        )
        if exact:
            continue

        best_score = max(
            (
                _name_similarity(name, source_name)
                for source_name in source_team_names
            ),
            default=0.0,
        )

        # Soglia abbastanza permissiva per evitare falsi positivi dovuti
        # a abbreviazioni, apostrofi o traslitterazioni.
        if best_score >= 0.86:
            continue

        candidates.append(
            {
                "player_id": player_id,
                "name": name,
                "team_nfl": team,
                "role": player.get("role"),
                "status_titolarita": player.get("status_titolarita"),
                "in_roster": player_id in rostered_player_ids,
                "best_source_similarity": round(best_score, 2),
                "suggested_action": (
                    "Verifica manuale — presente in una rosa"
                    if player_id in rostered_player_ids
                    else "Possibile rimozione"
                ),
            }
        )

    candidates.sort(
        key=lambda row: (
            bool(row["in_roster"]),
            str(row["team_nfl"]),
            str(row["name"]),
        )
    )

    return candidates, {
        "safe": True,
        "rows": len(quotations),
        "teams": len(source_teams),
        "reason": "",
    }


def delete_verified_missing_players(
    candidates: list[dict[str, Any]],
    selected_ids: set[Any],
) -> tuple[int, list[str]]:
    """
    Elimina solo giocatori selezionati manualmente e non presenti in rose.

    Se esiste ancora una riga in rosters per il giocatore, l'eliminazione viene
    bloccata anche se la UI era obsoleta.
    """
    deleted = 0
    errors: list[str] = []

    for row in candidates:
        player_id = row.get("player_id")
        if player_id not in selected_ids:
            continue

        name = str(row.get("name") or player_id)

        try:
            linked = (
                supabase.table("rosters")
                .select("id")
                .eq("player_id", player_id)
                .limit(1)
                .execute()
                .data
                or []
            )
            if linked:
                errors.append(
                    f"{name}: non eliminato perché è ancora presente in una rosa."
                )
                continue

            (
                supabase.table("players")
                .delete()
                .eq("id", player_id)
                .execute()
            )
            deleted += 1

        except Exception as exc:
            errors.append(f"{name}: {exc}")

    if deleted:
        invalidate_data_cache()

    return deleted, errors



def _is_player_data_admin(user: dict[str, Any]) -> bool:
    """
    Pagina updater riservata agli admin configurati nei secrets.
    Esempio:
    ADMIN_EMAILS = "mail1@example.com,mail2@example.com"
    """
    configured = str(st.secrets.get("ADMIN_EMAILS", "") or "").strip()
    if not configured:
        return False
    allowed = {
        item.strip().lower()
        for item in configured.split(",")
        if item.strip()
    }
    email = str(user.get("email") or "").strip().lower()
    return bool(email and email in allowed)


def _guess_uploaded_column(
    columns: list[str],
    aliases: tuple[str, ...],
) -> str | None:
    normalized = {normalize_string(column): column for column in columns}
    for alias in aliases:
        alias_norm = normalize_string(alias)
        if alias_norm in normalized:
            return normalized[alias_norm]
    for column in columns:
        column_norm = normalize_string(column)
        for alias in aliases:
            alias_norm = normalize_string(alias)
            if alias_norm and (alias_norm in column_norm or column_norm in alias_norm):
                return column
    return None


def _read_uploaded_listone(uploaded_file: Any) -> pd.DataFrame:
    filename = str(getattr(uploaded_file, "name", "") or "").lower()
    if filename.endswith((".xlsx", ".xls")):
        return pd.read_excel(uploaded_file)
    if filename.endswith(".csv"):
        from io import BytesIO
        raw = uploaded_file.getvalue()
        for encoding in ("utf-8-sig", "utf-8", "latin-1"):
            try:
                return pd.read_csv(BytesIO(raw), encoding=encoding)
            except Exception:
                continue
    raise ValueError("Formato non supportato. Usa CSV, XLSX o XLS.")


def _uploaded_team_to_code(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    upper = text.upper()
    if upper in set(TEAM_MAP.values()):
        return upper
    normalized = normalize_string(text)
    for team_name, team_code in TEAM_MAP.items():
        if normalize_string(team_name) == normalized:
            return team_code
    return upper[:3]


def _uploaded_role_to_code(value: Any) -> str:
    text = str(value or "").strip().upper()
    if not text:
        return ""
    if text in {"P", "D", "C", "A"}:
        return text
    mapping = {
        "portiere": "P", "portieri": "P",
        "difensore": "D", "difensori": "D",
        "centrocampista": "C", "centrocampisti": "C",
        "attaccante": "A", "attaccanti": "A",
    }
    return mapping.get(normalize_string(text), text[:1])


def build_uploaded_listone_comparison(
    uploaded_df: pd.DataFrame,
    db_players: list[dict[str, Any]],
    name_col: str,
    team_col: str,
    role_col: str,
    quote_col: str | None = None,
    fvm_col: str | None = None,
) -> dict[str, Any]:
    source_rows: list[dict[str, Any]] = []
    for _, row in uploaded_df.iterrows():
        name = _clean_source_player_name(row.get(name_col, ""))
        if not name:
            continue
        team_code = _uploaded_team_to_code(row.get(team_col, ""))
        role_code = _uploaded_role_to_code(row.get(role_col, ""))

        quote_value = None
        fvm_value = None
        if quote_col:
            try:
                raw_quote = row.get(quote_col)
                if pd.notna(raw_quote):
                    quote_value = int(float(raw_quote))
            except Exception:
                pass
        if fvm_col:
            try:
                raw_fvm = row.get(fvm_col)
                if pd.notna(raw_fvm):
                    fvm_value = int(float(raw_fvm))
            except Exception:
                pass

        source_rows.append({
            "name": name,
            "team_nfl": team_code,
            "role": role_code,
            "quotazione_fc": quote_value,
            "fvm_fc": fvm_value,
        })

    matched_ids: set[Any] = set()
    matched: list[dict[str, Any]] = []
    new_players: list[dict[str, Any]] = []
    ambiguous: list[dict[str, Any]] = []
    changed_players: list[dict[str, Any]] = []

    for source in source_rows:
        match, confidence = _best_player_match(
            source["name"],
            db_players,
            source.get("team_nfl") or None,
            min_score=0.86,
        )

        if match is None:
            surname_matches = _existing_name_conflicts(source["name"], db_players)
            if surname_matches:
                ambiguous.append({
                    **source,
                    "possible_matches": " | ".join(
                        f"{p.get('name')} ({p.get('team_nfl')}, {p.get('role')})"
                        for p in surname_matches[:6]
                    ),
                    "confidence": round(confidence, 2),
                })
            else:
                new_players.append({**source, "confidence": round(confidence, 2)})
            continue

        matched_ids.add(match.get("id"))
        match_row = {
            "player_id": match.get("id"),
            "db_name": match.get("name"),
            "file_name": source["name"],
            "db_team": match.get("team_nfl"),
            "file_team": source.get("team_nfl"),
            "db_role": match.get("role"),
            "file_role": source.get("role"),
            "db_quote": match.get("quotazione_fc"),
            "file_quote": source.get("quotazione_fc"),
            "db_fvm": match.get("fvm_fc"),
            "file_fvm": source.get("fvm_fc"),
            "confidence": round(confidence, 2),
        }
        matched.append(match_row)

        team_changed = bool(source.get("team_nfl")) and str(match.get("team_nfl") or "") != source["team_nfl"]
        role_changed = bool(source.get("role")) and str(match.get("role") or "") != source["role"]
        quote_changed = source.get("quotazione_fc") is not None and match.get("quotazione_fc") != source.get("quotazione_fc")
        fvm_changed = source.get("fvm_fc") is not None and match.get("fvm_fc") != source.get("fvm_fc")

        if team_changed or role_changed or quote_changed or fvm_changed:
            changed_players.append({
                **match_row,
                "team_changed": team_changed,
                "role_changed": role_changed,
                "quote_changed": quote_changed,
                "fvm_changed": fvm_changed,
            })

    missing_players = [{
        "player_id": player.get("id"),
        "name": player.get("name"),
        "team_nfl": player.get("team_nfl"),
        "role": player.get("role"),
        "quotazione_fc": player.get("quotazione_fc"),
        "status_titolarita": player.get("status_titolarita"),
    } for player in db_players if player.get("id") not in matched_ids]

    return {
        "source_rows": source_rows,
        "matched": matched,
        "new_players": new_players,
        "missing_players": missing_players,
        "changed_players": changed_players,
        "ambiguous": ambiguous,
    }


def build_listone_review_sql(comparison: dict[str, Any]) -> str:
    def sql_text(value: Any) -> str:
        if value is None:
            return "NULL"
        return "'" + str(value).replace("'", "''") + "'"

    lines = [
        "-- fantahe1per - SQL generato dalla verifica Listone",
        "-- Controllare SEMPRE il file prima di eseguirlo.",
        "",
        "begin;",
        "",
        "-- AGGIORNAMENTI GIOCATORI ESISTENTI",
    ]

    for row in comparison.get("changed_players", []):
        assignments = []
        if row.get("file_team"):
            assignments.append(f"team_nfl = {sql_text(row['file_team'])}")
        if row.get("file_role"):
            assignments.append(f"role = {sql_text(row['file_role'])}")
        if row.get("file_quote") is not None:
            assignments.append(f"quotazione_fc = {int(row['file_quote'])}")
        if row.get("file_fvm") is not None:
            assignments.append(f"fvm_fc = {int(row['file_fvm'])}")
        if assignments:
            lines += [
                f"-- {row.get('db_name')}",
                "update public.players",
                "set " + ", ".join(assignments),
                f"where id = {sql_text(row.get('player_id'))};",
                "",
            ]

    lines += ["-- NUOVI GIOCATORI"]
    for row in comparison.get("new_players", []):
        vals = [
            sql_text(row.get("name")),
            sql_text(row.get("team_nfl")),
            sql_text(row.get("role")),
            str(int(row["quotazione_fc"])) if row.get("quotazione_fc") is not None else "NULL",
            str(int(row["fvm_fc"])) if row.get("fvm_fc") is not None else "NULL",
            "1", "false", "false", "false",
        ]
        lines += [
            f"-- Nuovo: {row.get('name')}",
            "insert into public.players "
            "(name, team_nfl, role, quotazione_fc, fvm_fc, list_price, rigorista, piazzati, primo_anno_serie_a)",
            "values (" + ", ".join(vals) + ");",
            "",
        ]

    lines += [
        "-- POSSIBILI RIMOZIONI (COMMENTATE DI DEFAULT)",
    ]
    for row in comparison.get("missing_players", []):
        lines.append(
            "-- delete from public.players "
            f"where id = {sql_text(row.get('player_id'))}; "
            f"-- {row.get('name')} · {row.get('team_nfl')} · {row.get('role')}"
        )

    lines += ["", "commit;"]
    return "\n".join(lines)


def render_uploaded_listone_checker() -> None:
    st.markdown("### 📤 Verifica Listone ufficiale")
    st.caption(
        "Carica CSV/XLSX. L'app confronta il file con Supabase e mostra "
        "giocatori nuovi, mancanti e dati cambiati prima di qualsiasi modifica."
    )

    uploaded = st.file_uploader(
        "Carica Listone",
        type=["csv", "xlsx", "xls"],
        key="official_listone_upload",
    )
    if uploaded is None:
        return

    try:
        source_df = _read_uploaded_listone(uploaded)
    except Exception as exc:
        st.error(f"Non riesco a leggere il file: {exc}")
        return

    if source_df.empty:
        st.warning("Il file non contiene righe.")
        return

    columns = [str(column) for column in source_df.columns]
    guessed_name = _guess_uploaded_column(columns, ("Nome", "Giocatore", "Calciatore", "Nome calciatore"))
    guessed_team = _guess_uploaded_column(columns, ("Squadra", "Club", "Team"))
    guessed_role = _guess_uploaded_column(columns, ("Ruolo", "R"))
    guessed_quote = _guess_uploaded_column(columns, ("Quotazione", "Qt.A", "QtA", "Quotazione attuale", "Qt"))
    guessed_fvm = _guess_uploaded_column(columns, ("FVM", "FVM M", "FVM Mantra"))

    st.markdown("#### Mappatura colonne")
    c1, c2, c3 = st.columns(3)
    with c1:
        name_col = st.selectbox("Nome giocatore", columns, index=columns.index(guessed_name) if guessed_name in columns else 0, key="listone_map_name")
    with c2:
        team_col = st.selectbox("Squadra", columns, index=columns.index(guessed_team) if guessed_team in columns else 0, key="listone_map_team")
    with c3:
        role_col = st.selectbox("Ruolo", columns, index=columns.index(guessed_role) if guessed_role in columns else 0, key="listone_map_role")

    optional_columns = ["— Non presente —"] + columns
    c4, c5 = st.columns(2)
    with c4:
        quote_col = st.selectbox("Quotazione", optional_columns, index=optional_columns.index(guessed_quote) if guessed_quote in optional_columns else 0, key="listone_map_quote")
    with c5:
        fvm_col = st.selectbox("FVM", optional_columns, index=optional_columns.index(guessed_fvm) if guessed_fvm in optional_columns else 0, key="listone_map_fvm")

    quote_col = None if quote_col == "— Non presente —" else quote_col
    fvm_col = None if fvm_col == "— Non presente —" else fvm_col

    if st.button("🔎 Confronta con Supabase", type="primary", use_container_width=True, key="compare_uploaded_listone"):
        st.session_state["uploaded_listone_comparison"] = build_uploaded_listone_comparison(
            source_df, load_players(), name_col, team_col, role_col, quote_col, fvm_col
        )

    comparison = st.session_state.get("uploaded_listone_comparison")
    if not comparison:
        st.dataframe(source_df.head(20), use_container_width=True, hide_index=True)
        return

    matched = comparison["matched"]
    new_players = comparison["new_players"]
    missing_players = comparison["missing_players"]
    changed_players = comparison["changed_players"]
    ambiguous = comparison["ambiguous"]

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Riconosciuti", len(matched))
    m2.metric("Da aggiungere", len(new_players))
    m3.metric("Da rimuovere?", len(missing_players))
    m4.metric("Dati cambiati", len(changed_players))
    m5.metric("Ambigui", len(ambiguous))

    if changed_players:
        with st.expander(f"🔄 Giocatori con dati cambiati ({len(changed_players)})", expanded=True):
            st.dataframe(pd.DataFrame(changed_players), use_container_width=True, hide_index=True)

    if new_players:
        with st.expander(f"➕ Possibili nuovi giocatori ({len(new_players)})", expanded=True):
            st.dataframe(pd.DataFrame(new_players), use_container_width=True, hide_index=True)

    if missing_players:
        with st.expander(f"➖ Presenti in Supabase ma assenti dal file ({len(missing_players)})", expanded=True):
            st.warning("Assenza dal file non significa automaticamente che il giocatore vada eliminato.")
            st.dataframe(pd.DataFrame(missing_players), use_container_width=True, hide_index=True)

    if ambiguous:
        with st.expander(f"❓ Abbinamenti ambigui ({len(ambiguous)})", expanded=True):
            st.dataframe(pd.DataFrame(ambiguous), use_container_width=True, hide_index=True)

    review_sql = build_listone_review_sql(comparison)
    st.download_button(
        "⬇️ Scarica SQL di riallineamento",
        data=review_sql.encode("utf-8"),
        file_name="fantahe1per_listone_alignment.sql",
        mime="text/plain",
        use_container_width=True,
    )
    st.caption(
        "Lo SQL aggiorna i giocatori riconosciuti e inserisce quelli chiaramente nuovi. "
        "Le DELETE sono commentate per sicurezza."
    )





def build_fantacalcio_hierarchy_preview(
    db_players: list[dict[str, Any]],
    formations: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """
    Preview dedicata SOLO a:
    - titolarità;
    - ballottaggi;
    - rigoristi;
    - calci da fermo.

    Non modifica squadra, quotazione o FVM.
    """
    preview, unmatched = build_player_source_preview(
        db_players,
        formations,
        [],
    )

    hierarchy_rows: list[dict[str, Any]] = []
    for row in preview:
        changed = any(
            (
                row.get("old_status") != row.get("new_status"),
                bool(row.get("old_rigorista")) != bool(row.get("new_rigorista")),
                (row.get("old_ballottaggio_con") or None)
                != (row.get("new_ballottaggio_con") or None),
                row.get("rigorista_ordine") is not None,
                bool(row.get("piazzati")),
                row.get("piazzati_ordine") is not None,
            )
        )
        if changed:
            hierarchy_rows.append(row)

    hierarchy_unmatched = [
        row
        for row in unmatched
        if row.get("source") in {
            "Probabile XI",
            "Ballottaggio",
            "Rigoristi",
            "Calci da fermo",
        }
    ]
    return hierarchy_rows, hierarchy_unmatched


def apply_fantacalcio_hierarchy_preview(
    preview: list[dict[str, Any]],
) -> tuple[int, list[str]]:
    """
    Scrive in public.players SOLO le gerarchie Fantacalcio.
    Non tocca team_nfl, quotazioni o FVM.
    """
    updated = 0
    errors: list[str] = []

    for row in preview:
        payload = {
            "status_titolarita": row.get("new_status"),
            "rigorista": bool(row.get("new_rigorista")),
            "rigorista_ordine": row.get("rigorista_ordine"),
            "ballottaggio_con": row.get("new_ballottaggio_con"),
            "piazzati": bool(row.get("piazzati")),
            "piazzati_ordine": row.get("piazzati_ordine"),
            "data_source": PLAYER_DATA_SOURCE_LABEL,
            "source_updated_at": row.get("source_updated_at")
            or datetime.now(ZoneInfo("Europe/Rome")).isoformat(),
        }
        try:
            (
                supabase.table("players")
                .update(payload)
                .eq("id", row["player_id"])
                .execute()
            )
            updated += 1
        except Exception as exc:
            errors.append(f"{row.get('name')}: {exc}")

    if updated:
        invalidate_data_cache()
    return updated, errors



def _group_hierarchy_unmatched(
    unmatched: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Raggruppa lo stesso nome+squadra anche se appare in più sezioni."""
    grouped: dict[tuple[str, str], dict[str, Any]] = {}

    for item in unmatched:
        name = str(item.get("name") or "").strip()
        team = str(item.get("team") or "").strip().upper()
        if not name or not team:
            continue

        key = (normalize_string(name), team)
        row = grouped.setdefault(
            key,
            {
                "name": name,
                "team": team,
                "sources": [],
                "reasons": [],
            },
        )

        source = str(item.get("source") or "").strip()
        reason = str(item.get("reason") or "").strip()
        if source and source not in row["sources"]:
            row["sources"].append(source)
        if reason and reason not in row["reasons"]:
            row["reasons"].append(reason)

    return sorted(
        grouped.values(),
        key=lambda row: (row["team"], normalize_string(row["name"])),
    )


def _merged_hierarchy_unmatched_payload(
    group: dict[str, Any],
) -> dict[str, Any]:
    """Fonde gli effetti delle fonti per un singolo nome+squadra."""
    payload: dict[str, Any] = {
        "team_nfl": group.get("team"),
        "data_source": PLAYER_DATA_SOURCE_LABEL,
        "source_updated_at": datetime.now(
            ZoneInfo("Europe/Rome")
        ).isoformat(),
    }

    sources = set(group.get("sources") or [])
    if "Probabile XI" in sources:
        payload["status_titolarita"] = "Titolare"
    if "Ballottaggio" in sources:
        payload["status_titolarita"] = "Ballottaggio"
    if "Rigoristi" in sources:
        payload["rigorista"] = True
    if "Calci da fermo" in sources:
        payload["piazzati"] = True

    return payload


def apply_hierarchy_unmatched_resolutions(
    groups: list[dict[str, Any]],
    resolutions: dict[int, dict[str, Any]],
) -> tuple[int, int, list[str]]:
    """
    Associa un nome fonte a un record esistente oppure crea un nuovo giocatore.
    Lo stesso nome viene gestito una sola volta anche se compare in più fonti.
    """
    associated = 0
    created = 0
    errors: list[str] = []

    for idx, group in enumerate(groups):
        resolution = resolutions.get(idx) or {}
        action = resolution.get("action", "Ignora")
        if action == "Ignora":
            continue

        source_name = str(group.get("name") or "").strip()
        source_team = str(group.get("team") or "").strip().upper()
        payload = _merged_hierarchy_unmatched_payload(group)

        try:
            if action == "Associa a esistente":
                player_id = resolution.get("player_id")
                if player_id is None:
                    errors.append(
                        f"{source_name}: nessun giocatore selezionato."
                    )
                    continue

                rows = (
                    supabase.table("players")
                    .select("id, name, team_nfl, source_aliases")
                    .eq("id", player_id)
                    .limit(1)
                    .execute()
                    .data
                    or []
                )
                if not rows:
                    errors.append(
                        f"{source_name}: record giocatore non trovato."
                    )
                    continue

                existing = rows[0]
                aliases = existing.get("source_aliases") or []
                if isinstance(aliases, str):
                    aliases = [aliases]

                alias_token = _source_alias_token(
                    source_name,
                    source_team,
                )
                payload["source_aliases"] = list(
                    dict.fromkeys(
                        [str(alias) for alias in aliases] + [alias_token]
                    )
                )
                payload["team_nfl"] = source_team

                (
                    supabase.table("players")
                    .update(payload)
                    .eq("id", player_id)
                    .execute()
                )
                associated += 1

            elif action == "Nuovo giocatore":
                role = str(resolution.get("role") or "").strip().upper()
                if role not in {"P", "D", "C", "A"}:
                    errors.append(
                        f"{source_name}: ruolo P/D/C/A obbligatorio."
                    )
                    continue

                final_name = str(
                    resolution.get("canonical_name") or source_name
                ).strip()
                if not final_name:
                    errors.append(
                        f"{source_name}: nome non valido."
                    )
                    continue

                new_payload = {
                    "name": final_name,
                    "team_nfl": source_team,
                    "role": role,
                    "list_price": max(
                        1,
                        int(resolution.get("list_price") or 1),
                    ),
                    "status_titolarita": payload.get(
                        "status_titolarita",
                        "Riserva",
                    ),
                    "rigorista": bool(payload.get("rigorista", False)),
                    "piazzati": bool(payload.get("piazzati", False)),
                    "primo_anno_serie_a": bool(
                        resolution.get("rookie", True)
                    ),
                    "data_source": PLAYER_DATA_SOURCE_LABEL,
                    "source_updated_at": payload["source_updated_at"],
                    "source_aliases": [
                        _source_alias_token(
                            source_name,
                            source_team,
                        )
                    ],
                }

                try:
                    (
                        supabase.table("players")
                        .insert(new_payload)
                        .execute()
                    )
                    created += 1
                except Exception as exc:
                    message = str(exc).lower()
                    if "duplicate" in message or "unique" in message:
                        errors.append(
                            f"{source_name}: esiste già un record compatibile. "
                            "Usa 'Associa a esistente'."
                        )
                    else:
                        raise

        except Exception as exc:
            errors.append(f"{source_name}: {exc}")

    if associated or created:
        invalidate_data_cache()

    return associated, created, errors


def render_hierarchy_unmatched_validator(
    unmatched: list[dict[str, Any]],
) -> bool:
    """
    UI di validazione per i nomi non riconosciuti.
    Ritorna True se restano casi non ancora esplicitamente gestiti.
    """
    groups = _group_hierarchy_unmatched(unmatched)
    if not groups:
        return False

    st.markdown("#### 🧩 Validazione nomi non riconosciuti")
    st.caption(
        "Lo stesso nome viene raggruppato una sola volta anche se compare, "
        "per esempio, sia nei Ballottaggi sia nei Rigoristi."
    )

    db_players = load_players()

    player_by_label: dict[str, dict[str, Any]] = {}
    for player in db_players:
        label = (
            f"{player.get('name')} · {player.get('team_nfl')} · "
            f"{player.get('role')}"
        )
        if label in player_by_label:
            label += f" · ID {player.get('id')}"
        player_by_label[label] = player
    labels = list(player_by_label.keys())

    accepted_ignored = st.session_state.setdefault(
        "hierarchy_unmatched_accepted_ignore",
        set(),
    )

    resolutions: dict[int, dict[str, Any]] = {}

    with st.expander(
        f"🧩 Gestisci {len(groups)} nomi unici",
        expanded=True,
    ):
        for idx, group in enumerate(groups):
            source_name = str(group.get("name") or "")
            source_team = str(group.get("team") or "")
            sources = ", ".join(group.get("sources") or [])
            group_key = f"{normalize_string(source_name)}|{source_team}"

            st.markdown(
                f"**{escape(source_name)}** · **{escape(source_team)}**"
            )
            st.caption(f"Compare in: {sources or '—'}")

            if group_key in accepted_ignored:
                st.info("Ignorato consapevolmente per questa sessione.")
                if st.button(
                    "↩️ Riapri caso",
                    key=f"hierarchy_unignore_{idx}_{group_key}",
                ):
                    accepted_ignored.discard(group_key)
                    st.session_state[
                        "hierarchy_unmatched_accepted_ignore"
                    ] = accepted_ignored
                    st.rerun()
                st.divider()
                resolutions[idx] = {"action": "Ignora"}
                continue

            ranked_labels = sorted(
                labels,
                key=lambda label: (
                    1
                    if str(
                        player_by_label[label].get("team_nfl") or ""
                    ).strip().upper() == source_team
                    else 0,
                    _name_similarity(
                        source_name,
                        str(player_by_label[label].get("name") or ""),
                    ),
                ),
                reverse=True,
            )

            if ranked_labels:
                best = player_by_label[ranked_labels[0]]
                best_score = _name_similarity(
                    source_name,
                    str(best.get("name") or ""),
                )
                st.caption(
                    f"Suggerimento: **{best.get('name')}** · "
                    f"{best.get('team_nfl')} · {best.get('role')} "
                    f"(somiglianza {best_score:.2f})"
                )

            action = st.radio(
                "Azione",
                [
                    "Da decidere",
                    "Associa a esistente",
                    "Nuovo giocatore",
                    "Ignora consapevolmente",
                ],
                horizontal=True,
                key=f"hierarchy_unmatched_action_{idx}_{group_key}",
            )

            resolution: dict[str, Any] = {"action": "Ignora"}

            if action == "Associa a esistente":
                selected_label = st.selectbox(
                    "Giocatore esistente",
                    ranked_labels,
                    index=0,
                    key=f"hierarchy_existing_{idx}_{group_key}",
                )
                selected = player_by_label[selected_label]
                resolution = {
                    "action": "Associa a esistente",
                    "player_id": selected.get("id"),
                }

                old_team = str(
                    selected.get("team_nfl") or ""
                ).strip().upper()
                if old_team != source_team:
                    st.warning(
                        f"Confermando, la squadra canonica verrà aggiornata "
                        f"da **{old_team}** a **{source_team}**."
                    )

            elif action == "Nuovo giocatore":
                st.info(
                    "Usa questa opzione se hai verificato che il giocatore "
                    "non esiste già in public.players."
                )

                canonical_name = st.text_input(
                    "Nome da salvare",
                    value=source_name,
                    key=f"hierarchy_new_name_{idx}_{group_key}",
                )

                c1, c2 = st.columns(2)
                with c1:
                    role = st.selectbox(
                        "Ruolo",
                        ["P", "D", "C", "A"],
                        key=f"hierarchy_new_role_{idx}_{group_key}",
                    )
                with c2:
                    list_price = st.number_input(
                        "Listino iniziale",
                        min_value=1,
                        max_value=500,
                        value=1,
                        step=1,
                        key=f"hierarchy_new_price_{idx}_{group_key}",
                    )

                rookie = st.checkbox(
                    "Primo anno in Serie A / rookie",
                    value=True,
                    key=f"hierarchy_new_rookie_{idx}_{group_key}",
                )

                resolution = {
                    "action": "Nuovo giocatore",
                    "canonical_name": canonical_name,
                    "role": role,
                    "list_price": int(list_price),
                    "rookie": bool(rookie),
                }

            elif action == "Ignora consapevolmente":
                if st.button(
                    "Conferma: ignora questo nome",
                    key=f"hierarchy_ignore_{idx}_{group_key}",
                    use_container_width=True,
                ):
                    accepted_ignored.add(group_key)
                    st.session_state[
                        "hierarchy_unmatched_accepted_ignore"
                    ] = accepted_ignored
                    st.rerun()

            resolutions[idx] = resolution
            st.divider()

        actionable = sum(
            1
            for resolution in resolutions.values()
            if resolution.get("action")
            in {"Associa a esistente", "Nuovo giocatore"}
        )

        if actionable:
            if st.button(
                "✅ Applica associazioni / crea nuovi giocatori",
                type="primary",
                use_container_width=True,
                key="hierarchy_apply_unmatched_resolutions",
            ):
                associated, created, errors = (
                    apply_hierarchy_unmatched_resolutions(
                        groups,
                        resolutions,
                    )
                )
                if errors:
                    st.error(
                        f"Associati {associated} · Creati {created} · "
                        f"Errori {len(errors)}"
                    )
                    st.write(errors)
                else:
                    st.success(
                        f"Associati {associated} · Creati {created}. "
                        "Rileggi ora Fantacalcio: il nuovo confronto completerà "
                        "partner di ballottaggio e ordine rigoristi."
                    )
                    for key in (
                        "hierarchy_sync_preview",
                        "hierarchy_sync_unmatched",
                        "hierarchy_sync_teams",
                        "hierarchy_sync_at",
                    ):
                        st.session_state.pop(key, None)
                    st.rerun()

    still_open = 0
    for group in groups:
        group_key = (
            f"{normalize_string(str(group.get('name') or ''))}|"
            f"{str(group.get('team') or '').strip().upper()}"
        )
        if group_key not in accepted_ignored:
            still_open += 1

    if still_open:
        st.warning(
            f"Restano **{still_open}** nomi da validare. "
            "Il salvataggio finale delle gerarchie resta bloccato."
        )

    return still_open > 0


def render_fantacalcio_hierarchy_diagnostic() -> None:
    """
    Pannello admin per verificare cosa c'è DAVVERO in Supabase
    e sincronizzare ballottaggi/rigoristi dalla fonte Fantacalcio.
    """
    st.markdown("### 🧪 Diagnostica ballottaggi e rigoristi")
    st.caption(
        "Fonte operativa dell'Asta: `public.players`. "
        "Qui puoi vedere i valori realmente salvati nel DB e confrontarli "
        "con l'articolo Fantacalcio prima di scrivere qualsiasi modifica."
    )

    db_players = load_players()

    diagnostic_rows = []
    for player in db_players:
        ballot = str(player.get("ballottaggio_con") or "").strip()
        try:
            rig_order = (
                int(player.get("rigorista_ordine"))
                if player.get("rigorista_ordine") is not None
                else None
            )
        except (TypeError, ValueError):
            rig_order = None

        try:
            set_order = (
                int(player.get("piazzati_ordine"))
                if player.get("piazzati_ordine") is not None
                else None
            )
        except (TypeError, ValueError):
            set_order = None

        if (
            str(player.get("status_titolarita") or "") == "Ballottaggio"
            or ballot
            or player.get("rigorista")
            or rig_order is not None
            or player.get("piazzati")
            or set_order is not None
        ):
            diagnostic_rows.append(
                {
                    "Giocatore": player.get("name"),
                    "Squadra": player.get("team_nfl"),
                    "Ruolo": player.get("role"),
                    "Titolarità": player.get("status_titolarita"),
                    "Ballottaggio con": ballot or None,
                    "Rigorista": bool(player.get("rigorista")),
                    "Ord. rigori": rig_order,
                    "Piazzati": bool(player.get("piazzati")),
                    "Ord. piazzati": set_order,
                }
            )

    c1, c2, c3 = st.columns(3)
    c1.metric(
        "In ballottaggio nel DB",
        sum(
            1
            for row in diagnostic_rows
            if row.get("Titolarità") == "Ballottaggio"
            or row.get("Ballottaggio con")
        ),
    )
    c2.metric(
        "Rigoristi nel DB",
        sum(1 for row in diagnostic_rows if row.get("Rigorista")),
    )
    c3.metric(
        "Piazzati nel DB",
        sum(1 for row in diagnostic_rows if row.get("Piazzati")),
    )

    # Ricerca rapida per casi tipo Kean/Douvikas.
    search_text = st.text_input(
        "Cerca giocatore nel DB",
        placeholder="Es. Kean, Douvikas, Scamacca…",
        key="hierarchy_db_search",
    ).strip()

    visible_rows = diagnostic_rows
    if search_text:
        needle = normalize_string(search_text)
        visible_rows = [
            row
            for row in diagnostic_rows
            if needle in normalize_string(str(row.get("Giocatore") or ""))
        ]

    if visible_rows:
        st.dataframe(
            pd.DataFrame(visible_rows),
            hide_index=True,
            use_container_width=True,
        )
    else:
        st.info(
            "Nessun record corrispondente trovato tra ballottaggi/rigoristi/piazzati."
        )

    st.markdown("#### 🌐 Confronta con Fantacalcio")

    if st.button(
        "Leggi Fantacalcio e prepara preview gerarchie",
        type="primary",
        use_container_width=True,
        key="hierarchy_fetch_preview",
    ):
        with st.spinner("Leggo ballottaggi, rigoristi e calci da fermo..."):
            try:
                formation_html = _source_http_get(
                    FANTACALCIO_FORMATIONS_URL
                )
                formations = parse_fantacalcio_formations(formation_html)

                preview, unmatched = build_fantacalcio_hierarchy_preview(
                    db_players,
                    formations,
                )

                st.session_state["hierarchy_sync_preview"] = preview
                st.session_state["hierarchy_sync_unmatched"] = unmatched
                st.session_state["hierarchy_sync_teams"] = sorted(
                    formations.keys()
                )
                st.session_state["hierarchy_sync_at"] = datetime.now(
                    ZoneInfo("Europe/Rome")
                ).strftime("%d/%m/%Y %H:%M")
            except Exception as exc:
                st.error(f"Errore lettura Fantacalcio: {exc}")

    preview = st.session_state.get("hierarchy_sync_preview") or []
    unmatched = st.session_state.get("hierarchy_sync_unmatched") or []
    teams_found = st.session_state.get("hierarchy_sync_teams") or []

    if teams_found:
        p1, p2, p3 = st.columns(3)
        p1.metric("Squadre lette", len(teams_found))
        p2.metric("Modifiche proposte", len(preview))
        p3.metric("Nomi da verificare", len(unmatched))

        expected_codes = {
            "ATA", "BOL", "CAG", "COM", "FIO", "FRO", "GEN", "INT", "JUV",
            "LAZ", "LEC", "MIL", "MON", "NAP", "PAR", "ROM", "SAS", "TOR",
            "UDI", "VEN",
        }
        missing_codes = sorted(expected_codes - set(teams_found))

        with st.expander("🔎 Codici squadra letti dal parser", expanded=False):
            st.write(", ".join(sorted(teams_found)))

        if missing_codes:
            st.error(
                "Sync BLOCCATO: non sono state lette tutte le squadre. "
                "Mancano: " + ", ".join(missing_codes)
            )
        else:
            st.success("Tutte le 20 squadre sono state lette dalla fonte.")

        if preview:
            preview_df = pd.DataFrame(
                [
                    {
                        "Giocatore": row.get("name"),
                        "Squadra": row.get("new_team"),
                        "Prima": row.get("old_status"),
                        "Dopo": row.get("new_status"),
                        "Ballottaggio prima": row.get("old_ballottaggio_con"),
                        "Ballottaggio dopo": row.get("new_ballottaggio_con"),
                        "Rigorista": bool(row.get("new_rigorista")),
                        "Ord. rigori": row.get("rigorista_ordine"),
                        "Piazzati": bool(row.get("piazzati")),
                        "Ord. piazzati": row.get("piazzati_ordine"),
                        "Match": round(float(row.get("confidence") or 0), 2),
                    }
                    for row in preview
                ]
            )
            st.dataframe(
                preview_df,
                hide_index=True,
                use_container_width=True,
            )

        has_open_unmatched = False

        if unmatched:
            suspicious_unmatched = [
                row
                for row in unmatched
                if row.get("source") == "Calci da fermo"
                and (
                    len(str(row.get("name") or "")) > 40
                    or '"' in str(row.get("name") or "")
                    or "pubblic" in normalize_string(str(row.get("name") or ""))
                    or "autore" in normalize_string(str(row.get("name") or ""))
                )
            ]
            if suspicious_unmatched:
                st.error(
                    "⚠️ Il parser ha ancora intercettato testo esterno alle "
                    "gerarchie giocatori. Non salvare questa preview."
                )

            with st.expander(
                f"⚠️ Nomi non riconosciuti ({len(unmatched)})",
                expanded=False,
            ):
                st.dataframe(
                    pd.DataFrame(unmatched),
                    hide_index=True,
                    use_container_width=True,
                )

            has_open_unmatched = render_hierarchy_unmatched_validator(
                unmatched
            )

        suspicious_unmatched_for_sync = [
            row
            for row in unmatched
            if row.get("source") == "Calci da fermo"
            and (
                len(str(row.get("name") or "")) > 40
                or '"' in str(row.get("name") or "")
                or "pubblic" in normalize_string(str(row.get("name") or ""))
                or "autore" in normalize_string(str(row.get("name") or ""))
            )
        ]

        safe_to_apply = (
            len(teams_found) == 20
            and len(preview) > 0
            and not suspicious_unmatched_for_sync
            and not has_open_unmatched
        )

        if has_open_unmatched:
            st.info(
                "🔒 Per sicurezza il sync finale è bloccato finché ogni nome "
                "non riconosciuto non viene associato, creato oppure ignorato "
                "esplicitamente."
            )

        if safe_to_apply:
            if st.button(
                "✅ Conferma e salva gerarchie in Supabase",
                type="primary",
                use_container_width=True,
                key="hierarchy_apply_preview",
            ):
                updated, errors = apply_fantacalcio_hierarchy_preview(preview)
                if errors:
                    st.error(
                        f"Aggiornati {updated} giocatori, con "
                        f"{len(errors)} errori."
                    )
                    st.write(errors)
                else:
                    st.success(
                        f"Aggiornati {updated} giocatori in public.players."
                    )
                    for key in (
                        "hierarchy_sync_preview",
                        "hierarchy_sync_unmatched",
                        "hierarchy_sync_teams",
                        "hierarchy_sync_at",
                    ):
                        st.session_state.pop(key, None)
                    st.rerun()


@st.cache_data(ttl=120)
def load_player_strategy_notes() -> list[dict[str, Any]]:
    """Carica le note strategiche personali da Supabase."""
    try:
        response = (
            supabase.table("player_strategy_notes")
            .select("*")
            .order("team_nfl")
            .order("player_name")
            .execute()
        )
        return response.data or []
    except Exception:
        return []


def _strategy_note_source_team(note: dict[str, Any]) -> str:
    """
    Squadra indicata originariamente nella nota.
    NON è la fonte canonica della squadra corrente del giocatore:
    quella è sempre players.team_nfl.
    """
    return str(
        note.get("source_team_nfl")
        or note.get("team_nfl")
        or ""
    ).strip().upper()


def _strategy_note_match(
    note: dict[str, Any],
    db_players: list[dict[str, Any]],
) -> tuple[dict[str, Any] | None, float, str]:
    """
    Matching volutamente conservativo:
    1. player_id già validato -> persisted;
    2. nome normalizzato + squadra esatti -> exact;
    3. altrimenti restituisce solo il miglior suggerimento, NON lo valida.
    """
    persisted_id = str(note.get("player_id") or "").strip()
    if persisted_id:
        for player in db_players:
            if str(player.get("id")) == persisted_id:
                return player, 1.0, "validated"

    source_name = str(note.get("player_name") or "")
    team_code = _strategy_note_source_team(note)
    source_norm = normalize_string(source_name)

    same_team = [
        player
        for player in db_players
        if str(player.get("team_nfl") or "").strip().upper() == team_code
    ]

    exact = [
        player
        for player in same_team
        if normalize_string(str(player.get("name") or "")) == source_norm
    ]
    if len(exact) == 1:
        return exact[0], 1.0, "exact"

    # Solo suggerimento fuzzy: mai scritto automaticamente.
    candidates = same_team or db_players
    best = None
    best_score = 0.0
    for player in candidates:
        score = _name_similarity(source_name, str(player.get("name") or ""))
        if score > best_score:
            best = player
            best_score = score

    return best, best_score, "suggested" if best is not None else "unmatched"


def build_strategy_notes_mapping_preview(
    notes: list[dict[str, Any]],
    db_players: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    preview: list[dict[str, Any]] = []
    for note in notes:
        match, confidence, method = _strategy_note_match(note, db_players)

        needs_validation = method not in {"validated", "exact"}
        preview.append(
            {
                "note_id": note.get("id"),
                "team_nfl": _strategy_note_source_team(note),
                "source_team_nfl": _strategy_note_source_team(note),
                "player_name": note.get("player_name"),
                "category": note.get("category"),
                "max_price": note.get("max_price"),
                "player_note": note.get("player_note"),
                "matched_player_id": match.get("id") if match else None,
                "matched_name": match.get("name") if match else None,
                "matched_team": match.get("team_nfl") if match else None,
                "matched_role": match.get("role") if match else None,
                "confidence": round(float(confidence), 3),
                "method": method,
                "needs_validation": needs_validation,
            }
        )
    return preview


def persist_exact_strategy_note_mappings(
    preview: list[dict[str, Any]],
) -> tuple[int, list[str]]:
    """
    Salva automaticamente SOLO i match nome+squadra esatti.
    I fuzzy devono essere confermati manualmente.
    """
    updated = 0
    errors: list[str] = []
    for row in preview:
        if row.get("method") != "exact" or row.get("matched_player_id") is None:
            continue
        try:
            (
                supabase.table("player_strategy_notes")
                .update(
                    {
                        "player_id": str(row["matched_player_id"]),
                        "canonical_player_name": row.get("matched_name"),
                        "mapping_status": "validated",
                        "mapping_confidence": 1.0,
                        "updated_at": datetime.now(
                            ZoneInfo("Europe/Rome")
                        ).isoformat(),
                    }
                )
                .eq("id", row["note_id"])
                .execute()
            )
            updated += 1
        except Exception as exc:
            errors.append(f"{row.get('player_name')}: {exc}")

    if updated:
        load_player_strategy_notes.clear()
        load_players.clear()
    return updated, errors


def persist_manual_strategy_note_mapping(
    note_id: Any,
    player: dict[str, Any],
    confidence: float,
    target_team: str | None = None,
) -> None:
    """
    Salva una associazione confermata dall'admin.

    Se target_team è valorizzato e diverso dal club attuale, aggiorna anche
    players.team_nfl. Questo consente di decidere esplicitamente se sia corretta
    la squadra della nota oppure quella già presente nel database.
    """
    player_id = player.get("id")
    if player_id is None:
        raise ValueError("ID giocatore mancante.")

    current_team = str(player.get("team_nfl") or "").strip().upper()
    final_team = str(target_team or current_team).strip().upper()

    if final_team and final_team != current_team:
        (
            supabase.table("players")
            .update(
                {
                    "team_nfl": final_team,
                    "source_updated_at": datetime.now(
                        ZoneInfo("Europe/Rome")
                    ).isoformat(),
                }
            )
            .eq("id", player_id)
            .execute()
        )

    (
        supabase.table("player_strategy_notes")
        .update(
            {
                "player_id": str(player_id),
                "canonical_player_name": player.get("name"),
                "mapping_status": "validated",
                "mapping_confidence": float(confidence),
                "updated_at": datetime.now(
                    ZoneInfo("Europe/Rome")
                ).isoformat(),
            }
        )
        .eq("id", note_id)
        .execute()
    )

    load_player_strategy_notes.clear()
    load_players.clear()


def create_player_from_strategy_note(
    note_id: Any,
    source_name: str,
    team_nfl: str,
    role: str,
    list_price: int = 1,
    rookie: bool = True,
    canonical_name: str | None = None,
) -> dict[str, Any]:
    """
    Crea un nuovo record in players partendo da una nota strategica e
    collega immediatamente la nota al nuovo giocatore.
    """
    final_name = str(canonical_name or source_name or "").strip()
    final_team = str(team_nfl or "").strip().upper()
    final_role = str(role or "").strip().upper()

    if not final_name:
        raise ValueError("Nome giocatore obbligatorio.")
    if not final_team:
        raise ValueError("Squadra obbligatoria.")
    if final_role not in {"P", "D", "C", "A"}:
        raise ValueError("Ruolo non valido: usa P, D, C o A.")

    payload = {
        "name": final_name,
        "team_nfl": final_team,
        "role": final_role,
        "list_price": max(1, int(list_price or 1)),
        "status_titolarita": "Riserva",
        "rigorista": False,
        "piazzati": False,
        "primo_anno_serie_a": bool(rookie),
        "data_source": "Note strategiche manuali",
        "source_updated_at": datetime.now(
            ZoneInfo("Europe/Rome")
        ).isoformat(),
        "source_aliases": [
            _source_alias_token(source_name, final_team)
        ],
    }

    try:
        response = (
            supabase.table("players")
            .insert(payload)
            .execute()
        )
    except Exception as exc:
        message = str(exc)
        if "duplicate" in message.lower() or "unique" in message.lower():
            raise ValueError(
                "Esiste già un giocatore con questa combinazione di nome, "
                "squadra e ruolo. Usa 'Associa a esistente' invece di crearne uno nuovo."
            ) from exc
        raise

    created_rows = response.data or []
    if not created_rows:
        # Recupero difensivo se il client non restituisce la riga inserita.
        created_rows = (
            supabase.table("players")
            .select("*")
            .eq("name", final_name)
            .eq("team_nfl", final_team)
            .eq("role", final_role)
            .limit(1)
            .execute()
            .data
            or []
        )

    if not created_rows:
        raise RuntimeError(
            "Il giocatore sembra essere stato inserito, ma non riesco a recuperare il nuovo record."
        )

    new_player = created_rows[0]

    (
        supabase.table("player_strategy_notes")
        .update(
            {
                "player_id": str(new_player.get("id")),
                "canonical_player_name": final_name,
                "mapping_status": "validated",
                "mapping_confidence": 1.0,
                "updated_at": datetime.now(
                    ZoneInfo("Europe/Rome")
                ).isoformat(),
            }
        )
        .eq("id", note_id)
        .execute()
    )

    load_player_strategy_notes.clear()
    load_players.clear()
    return new_player



def apply_strategy_note_team_to_player(
    note_id: Any,
    player_id: Any,
    source_team: str,
) -> None:
    """
    Corregge la squadra CANONICA del giocatore.
    Dopo questa scrittura Asta, Giocatori, Rose e Mapping leggono tutti
    players.team_nfl e vedono lo stesso valore.
    """
    final_team = str(source_team or "").strip().upper()
    if not final_team:
        raise ValueError("Squadra della nota mancante.")

    (
        supabase.table("players")
        .update(
            {
                "team_nfl": final_team,
                "source_updated_at": datetime.now(
                    ZoneInfo("Europe/Rome")
                ).isoformat(),
            }
        )
        .eq("id", player_id)
        .execute()
    )

    (
        supabase.table("player_strategy_notes")
        .update(
            {
                "mapping_status": "validated",
                "updated_at": datetime.now(
                    ZoneInfo("Europe/Rome")
                ).isoformat(),
            }
        )
        .eq("id", note_id)
        .execute()
    )

    # Fondamentale: l'Asta usa load_players(), quindi svuotiamo la stessa cache.
    invalidate_data_cache()
    load_player_strategy_notes.clear()



def reset_strategy_note_mapping(note_id: Any) -> None:
    (
        supabase.table("player_strategy_notes")
        .update(
            {
                "player_id": None,
                "canonical_player_name": None,
                "mapping_status": "pending",
                "mapping_confidence": None,
                "updated_at": datetime.now(
                    ZoneInfo("Europe/Rome")
                ).isoformat(),
            }
        )
        .eq("id", note_id)
        .execute()
    )
    load_player_strategy_notes.clear()


def render_strategy_notes_mapping_validator() -> None:
    st.markdown("### 🧭 Mappatura note strategiche")
    st.caption(
        "Associa le note che hai scritto ai record reali della tabella players. "
        "I match esatti nome+squadra vengono riconosciuti automaticamente; "
        "i match fuzzy restano sempre da confermare manualmente."
    )

    notes = load_player_strategy_notes()
    if not notes:
        st.info(
            "La tabella `player_strategy_notes` non contiene ancora note. "
            "Esegui prima il file SQL di importazione delle note."
        )
        return

    db_players = load_players()
    preview = build_strategy_notes_mapping_preview(notes, db_players)

    exact_pending = [
        row for row in preview
        if row.get("method") == "exact"
    ]
    unresolved = [
        row for row in preview
        if row.get("needs_validation")
    ]
    validated = [
        row for row in preview
        if row.get("method") == "validated"
    ]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Note totali", len(preview))
    c2.metric("Già validate", len(validated))
    c3.metric("Match esatti", len(exact_pending))
    c4.metric("Da validare", len(unresolved))

    if exact_pending:
        st.success(
            f"{len(exact_pending)} note hanno un match esatto per nome e squadra."
        )
        if st.button(
            "✅ Salva automaticamente i match esatti",
            use_container_width=True,
            key="strategy_save_exact_mappings",
        ):
            updated, errors = persist_exact_strategy_note_mappings(preview)
            if errors:
                st.error(
                    f"Salvati {updated} match esatti con {len(errors)} errori."
                )
                st.write(errors)
            else:
                st.success(f"Salvati {updated} match esatti.")
                st.rerun()

    if unresolved:
        st.warning(
            f"Restano {len(unresolved)} note da controllare manualmente."
        )
        st.caption(
            "Per ogni caso puoi: associare a un giocatore già esistente, "
            "creare un nuovo acquisto oppure ignorarlo per ora. "
            "Quando associ un esistente puoi anche scegliere quale squadra "
            "deve diventare quella definitiva."
        )

        team_codes = [
            "ATA", "BOL", "CAG", "COM", "FIO", "FRO", "GEN", "INT", "JUV",
            "LAZ", "LEC", "MIL", "MON", "NAP", "PAR", "ROM", "SAS", "TOR",
            "UDI", "VEN",
        ]

        # Opzioni leggibili, ma ID salvato separatamente.
        player_by_label: dict[str, dict[str, Any]] = {}
        for player in db_players:
            label = (
                f"{player.get('name')} · {player.get('team_nfl')} · "
                f"{player.get('role')}"
            )
            if label in player_by_label:
                label += f" · ID {player.get('id')}"
            player_by_label[label] = player
        labels = list(player_by_label.keys())

        with st.expander(
            f"⚠️ Associazioni da validare ({len(unresolved)})",
            expanded=True,
        ):
            for pos, row in enumerate(unresolved):
                source_name = str(row.get("player_name") or "")
                source_team = str(row.get("team_nfl") or "").strip().upper()
                suggested_name = str(row.get("matched_name") or "—")
                suggested_team = str(row.get("matched_team") or "—")

                st.markdown(
                    f"**{escape(source_name)}** · {escape(source_team)} "
                    f"· {escape(str(row.get('category') or '—'))}"
                )
                if row.get("max_price") is not None:
                    st.caption(
                        f"Prezzo massimo nota: {int(row['max_price'])} crediti"
                    )
                if row.get("player_note"):
                    st.caption(str(row.get("player_note")))

                st.caption(
                    f"Suggerimento automatico: **{escape(suggested_name)}** "
                    f"· {escape(suggested_team)} · "
                    f"somiglianza {float(row.get('confidence') or 0):.2f}"
                )

                action = st.radio(
                    "Cosa vuoi fare?",
                    [
                        "Associa a giocatore esistente",
                        "Nuovo giocatore",
                        "Ignora per ora",
                    ],
                    horizontal=True,
                    key=f"strategy_note_action_{row['note_id']}_{pos}",
                )

                if action == "Associa a giocatore esistente":
                    suggested_id = row.get("matched_player_id")
                    ranked_labels = sorted(
                        labels,
                        key=lambda label: (
                            1 if player_by_label[label].get("id") == suggested_id else 0,
                            1 if str(player_by_label[label].get("team_nfl") or "") == source_team else 0,
                            _name_similarity(
                                source_name,
                                str(player_by_label[label].get("name") or ""),
                            ),
                        ),
                        reverse=True,
                    )

                    selected_label = st.selectbox(
                        "Giocatore esistente",
                        ranked_labels,
                        index=0,
                        key=f"strategy_note_mapping_{row['note_id']}_{pos}",
                    )
                    selected_player = player_by_label[selected_label]
                    db_team = str(
                        selected_player.get("team_nfl") or ""
                    ).strip().upper()

                    if db_team != source_team:
                        st.warning(
                            f"⚠️ Squadra diversa: nella nota hai **{source_team}**, "
                            f"nel database il giocatore è **{db_team}**."
                        )

                        team_choice = st.radio(
                            "Quale squadra è quella corretta?",
                            [
                                f"Usa squadra della nota ({source_team})",
                                f"Mantieni squadra del database ({db_team})",
                                "Scegli un'altra squadra",
                            ],
                            key=f"strategy_team_choice_{row['note_id']}_{pos}",
                        )

                        if team_choice.startswith("Usa squadra"):
                            final_team = source_team
                        elif team_choice.startswith("Mantieni"):
                            final_team = db_team
                        else:
                            default_idx = (
                                team_codes.index(source_team)
                                if source_team in team_codes
                                else 0
                            )
                            final_team = st.selectbox(
                                "Squadra definitiva",
                                team_codes,
                                index=default_idx,
                                key=f"strategy_manual_team_{row['note_id']}_{pos}",
                            )
                    else:
                        final_team = db_team
                        st.success(
                            f"Squadra coerente: {db_team}"
                        )

                    if st.button(
                        "✅ Conferma associazione",
                        key=f"strategy_note_confirm_{row['note_id']}_{pos}",
                        use_container_width=True,
                    ):
                        confidence = _name_similarity(
                            source_name,
                            str(selected_player.get("name") or ""),
                        )
                        try:
                            persist_manual_strategy_note_mapping(
                                row["note_id"],
                                selected_player,
                                confidence,
                                target_team=final_team,
                            )
                            st.success(
                                f"{source_name} → {selected_player.get('name')} "
                                f"· squadra definitiva {final_team}."
                            )
                            st.rerun()
                        except Exception as exc:
                            st.error(
                                f"Impossibile salvare l'associazione: {exc}"
                            )

                elif action == "Nuovo giocatore":
                    st.info(
                        "Usa questa opzione quando il giocatore è un nuovo "
                        "acquisto e non esiste ancora nella tabella players."
                    )

                    new_name = st.text_input(
                        "Nome da salvare",
                        value=source_name,
                        key=f"strategy_new_name_{row['note_id']}_{pos}",
                    )

                    default_team_idx = (
                        team_codes.index(source_team)
                        if source_team in team_codes
                        else 0
                    )
                    new_team = st.selectbox(
                        "Squadra",
                        team_codes,
                        index=default_team_idx,
                        key=f"strategy_new_team_{row['note_id']}_{pos}",
                    )

                    c_role, c_price = st.columns(2)
                    with c_role:
                        new_role = st.selectbox(
                            "Ruolo",
                            ["P", "D", "C", "A"],
                            key=f"strategy_new_role_{row['note_id']}_{pos}",
                        )
                    with c_price:
                        default_price = int(row.get("max_price") or 1)
                        new_list_price = st.number_input(
                            "Quotazione/Listino iniziale",
                            min_value=1,
                            max_value=500,
                            value=max(1, default_price),
                            step=1,
                            key=f"strategy_new_price_{row['note_id']}_{pos}",
                        )

                    new_rookie = st.checkbox(
                        "Primo anno in Serie A / rookie",
                        value=True,
                        key=f"strategy_new_rookie_{row['note_id']}_{pos}",
                    )

                    st.caption(
                        "Il prezzo massimo della tua nota resta separato nella "
                        "tabella strategica; questo campo serve solo come listino "
                        "iniziale del nuovo record players."
                    )

                    if st.button(
                        "➕ Crea giocatore e valida",
                        key=f"strategy_note_create_{row['note_id']}_{pos}",
                        type="primary",
                        use_container_width=True,
                    ):
                        try:
                            created = create_player_from_strategy_note(
                                note_id=row["note_id"],
                                source_name=source_name,
                                canonical_name=new_name,
                                team_nfl=new_team,
                                role=new_role,
                                list_price=int(new_list_price),
                                rookie=bool(new_rookie),
                            )
                            st.success(
                                f"Creato {created.get('name')} · "
                                f"{created.get('team_nfl')} · {created.get('role')}."
                            )
                            st.rerun()
                        except Exception as exc:
                            st.error(
                                f"Impossibile creare il giocatore: {exc}"
                            )

                else:
                    st.caption(
                        "Nessuna modifica: il caso resterà tra quelli da validare."
                    )

                st.divider()
    else:
        st.success("Tutte le note strategiche risultano mappate.")

    if validated:
        with st.expander(
            f"✅ Mapping già validati ({len(validated)})",
            expanded=False,
        ):
            st.caption(
                "Fonte unica per nome, squadra e ruolo: **public.players**. "
                "La squadra della nota viene conservata solo come riferimento "
                "originale; Asta, Giocatori e Mapping usano la squadra del record players."
            )

            mismatches = [
                row
                for row in validated
                if str(row.get("source_team_nfl") or row.get("team_nfl") or "").strip().upper()
                != str(row.get("matched_team") or "").strip().upper()
            ]

            validated_df = pd.DataFrame(
                [
                    {
                        "Nota": row.get("player_name"),
                        "Squadra nota originale": (
                            row.get("source_team_nfl")
                            or row.get("team_nfl")
                        ),
                        "Giocatore canonico": row.get("matched_name"),
                        "Squadra canonica (players)": row.get("matched_team"),
                        "Ruolo": row.get("matched_role"),
                        "Coerente": (
                            "✅"
                            if str(
                                row.get("source_team_nfl")
                                or row.get("team_nfl")
                                or ""
                            ).strip().upper()
                            == str(row.get("matched_team") or "").strip().upper()
                            else "⚠️"
                        ),
                    }
                    for row in validated
                ]
            )
            st.dataframe(
                validated_df,
                hide_index=True,
                use_container_width=True,
            )

            if mismatches:
                st.warning(
                    f"Ci sono {len(mismatches)} mapping validati in cui la squadra "
                    "scritta nella nota è diversa dalla squadra canonica in players. "
                    "Finché non correggi players, l'Asta continuerà a mostrare il valore DB."
                )

                mismatch_by_label: dict[str, dict[str, Any]] = {}
                for row in mismatches:
                    source_team = str(
                        row.get("source_team_nfl")
                        or row.get("team_nfl")
                        or ""
                    ).strip().upper()
                    db_team = str(row.get("matched_team") or "").strip().upper()
                    label = (
                        f"{row.get('matched_name')} · "
                        f"{db_team} → {source_team}"
                    )
                    mismatch_by_label[label] = row

                mismatch_label = st.selectbox(
                    "Correggi squadra canonica",
                    ["—"] + list(mismatch_by_label.keys()),
                    key="strategy_canonical_team_fix_select",
                )

                if mismatch_label != "—":
                    fix_row = mismatch_by_label[mismatch_label]
                    source_team = str(
                        fix_row.get("source_team_nfl")
                        or fix_row.get("team_nfl")
                        or ""
                    ).strip().upper()
                    db_team = str(
                        fix_row.get("matched_team") or ""
                    ).strip().upper()

                    st.info(
                        f"Confermando, **public.players.team_nfl** verrà aggiornato "
                        f"da **{db_team}** a **{source_team}**. "
                        "Il nuovo valore sarà quindi lo stesso anche nell'Asta."
                    )

                    if st.button(
                        "✅ Usa la squadra della nota come squadra canonica",
                        key=f"strategy_apply_source_team_{fix_row['note_id']}",
                        type="primary",
                        use_container_width=True,
                    ):
                        try:
                            apply_strategy_note_team_to_player(
                                fix_row["note_id"],
                                fix_row["matched_player_id"],
                                source_team,
                            )
                            st.success(
                                f"{fix_row.get('matched_name')}: squadra canonica "
                                f"aggiornata a {source_team}."
                            )
                            st.rerun()
                        except Exception as exc:
                            st.error(
                                f"Impossibile aggiornare la squadra canonica: {exc}"
                            )
            else:
                st.success(
                    "Tutti i mapping validati coincidono con la squadra canonica "
                    "della tabella players."
                )

            st.divider()
            validated_by_label: dict[str, dict[str, Any]] = {}
            for row in validated:
                label = (
                    f"{row.get('player_name')} → "
                    f"{row.get('matched_name')} · {row.get('matched_team')}"
                )
                validated_by_label[label] = row

            reset_label = st.selectbox(
                "Riapri un mapping se il giocatore associato è sbagliato",
                ["—"] + list(validated_by_label.keys()),
                key="strategy_mapping_reset_select",
            )
            if (
                reset_label != "—"
                and st.button(
                    "↩️ Rimetti da validare",
                    key="strategy_mapping_reset_button",
                    use_container_width=True,
                )
            ):
                reset_strategy_note_mapping(
                    validated_by_label[reset_label]["note_id"]
                )
                st.rerun()


def render_player_data_updater_page(user: dict[str, Any]) -> None:
    st.markdown(
        '<div class="rcd-section">🔄 Aggiornamento dati giocatori</div>',
        unsafe_allow_html=True,
    )

    st.caption(
        "Fonte primaria: Fantacalcio.it 2026/27. "
        "Il sistema genera prima una preview: nessun dato viene scritto "
        "su Supabase finché non confermi esplicitamente."
    )

    render_uploaded_listone_checker()

    st.divider()
    render_strategy_notes_mapping_validator()

    st.divider()
    render_fantacalcio_hierarchy_diagnostic()

    st.divider()
    st.markdown("### 🌐 Controllo fonti online")

    c1, c2 = st.columns(2)
    with c1:
        st.link_button(
            "Apri probabili formazioni",
            FANTACALCIO_FORMATIONS_URL,
            use_container_width=True,
        )
    with c2:
        st.link_button(
            "Apri quotazioni ufficiali",
            FANTACALCIO_QUOTES_URL,
            use_container_width=True,
        )

    if not _is_player_data_admin(user):
        st.warning(
            "La preview è disponibile agli admin. Per abilitare questa pagina "
            "aggiungi la tua email in `.streamlit/secrets.toml` come "
            '`ADMIN_EMAILS = "tua@email"`.'
        )
        return

    if st.button(
        "🌐 Leggi fonti e prepara anteprima",
        type="primary",
        use_container_width=True,
        key="fetch_player_sources",
    ):
        with st.spinner("Leggo Fantacalcio.it e confronto con Supabase..."):
            try:
                formation_html = _source_http_get(FANTACALCIO_FORMATIONS_URL)
                quote_html = _source_http_get(FANTACALCIO_QUOTES_URL)

                formations = parse_fantacalcio_formations(formation_html)
                quotations = parse_fantacalcio_quotations(quote_html)
                db_players = load_players()

                preview, unmatched = build_player_source_preview(
                    db_players,
                    formations,
                    quotations,
                )

                current_rosters = load_rosters()
                missing_candidates, missing_check = (
                    build_missing_from_source_candidates(
                        db_players,
                        quotations,
                        current_rosters,
                    )
                )

                st.session_state["player_source_preview"] = preview
                st.session_state["player_source_unmatched"] = unmatched
                st.session_state["player_missing_candidates"] = missing_candidates
                st.session_state["player_missing_check"] = missing_check
                st.session_state["player_source_stats"] = {
                    "teams_found": len(formations),
                    "team_codes_found": sorted(formations.keys()),
                    "quotes_found": len(quotations),
                    "changes": len(preview),
                    "unmatched": len(unmatched),
                    "fetched_at": datetime.now(
                        ZoneInfo("Europe/Rome")
                    ).strftime("%d/%m/%Y %H:%M"),
                }
            except Exception as exc:
                st.error(f"Errore durante la lettura delle fonti: {exc}")

    stats = st.session_state.get("player_source_stats")
    preview = st.session_state.get("player_source_preview") or []
    unmatched = st.session_state.get("player_source_unmatched") or []
    missing_candidates = (
        st.session_state.get("player_missing_candidates") or []
    )
    missing_check = (
        st.session_state.get("player_missing_check") or {}
    )

    if not stats:
        st.info(
            "Premi il pulsante sopra. Vedrai prima tutte le modifiche proposte, "
            "incluse quelle di titolarità, ballottaggi, rigoristi e piazzati."
        )
        return

    st.markdown("### Anteprima")
    s1, s2, s3, s4 = st.columns(4)
    s1.metric("Squadre lette", stats["teams_found"])
    s2.metric("Righe listone", stats["quotes_found"])
    s3.metric("Modifiche", stats["changes"])
    s4.metric("Da verificare", stats["unmatched"])
    st.caption(f"Ultima lettura: {stats['fetched_at']}")

    expected_team_codes = {
        "ATA", "BOL", "CAG", "COM", "FIO", "FRO", "GEN", "INT", "JUV", "LAZ",
        "LEC", "MIL", "MON", "NAP", "PAR", "ROM", "SAS", "TOR", "UDI", "VEN",
    }
    found_team_codes = set(stats.get("team_codes_found") or [])
    missing_team_codes = sorted(expected_team_codes - found_team_codes)
    if missing_team_codes:
        st.warning(
            "Squadre non lette dalla fonte: "
            + ", ".join(missing_team_codes)
        )

    if preview:
        preview_df = pd.DataFrame(preview)
        visible_cols = [
            "name",
            "old_team",
            "new_team",
            "old_status",
            "new_status",
            "old_rigorista",
            "new_rigorista",
            "new_ballottaggio_con",
            "rigorista_ordine",
            "piazzati",
            "piazzati_ordine",
            "new_quotazione_fc",
            "new_fvm_fc",
            "confidence",
        ]
        visible_cols = [
            col for col in visible_cols
            if col in preview_df.columns
        ]
        st.dataframe(
            preview_df[visible_cols],
            use_container_width=True,
            hide_index=True,
            column_config={
                "name": "Giocatore",
                "old_team": "Club prima",
                "new_team": "Club nuovo",
                "old_status": "Status prima",
                "new_status": "Status nuovo",
                "old_rigorista": "Rig. prima",
                "new_rigorista": "Rigorista",
                "new_ballottaggio_con": "Ballottaggio con",
                "rigorista_ordine": "Ord. rigori",
                "piazzati": "Piazzati",
                "piazzati_ordine": "Ord. piazzati",
                "new_quotazione_fc": "Quotazione FC",
                "new_fvm_fc": "FVM FC",
                "confidence": st.column_config.NumberColumn(
                    "Confidenza",
                    format="%.2f",
                ),
            },
        )

        csv_data = preview_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Scarica anteprima CSV",
            data=csv_data,
            file_name="fantahe1per_player_update_preview.csv",
            mime="text/csv",
            use_container_width=True,
        )

    if unmatched:
        with st.expander(
            f"⚠️ Giocatori da verificare manualmente ({len(unmatched)})",
            expanded=True,
        ):
            st.caption(
                "Per ogni nome puoi associarlo a un giocatore già presente, "
                "segnalarlo come nuovo giocatore oppure ignorarlo. "
                "L'associazione a un giocatore esistente viene ricordata anche "
                "nei controlli successivi. I nuovi giocatori vengono marcati "
                "automaticamente come rookie al primo anno in Serie A."
            )

            db_players_for_resolution = load_players()
            player_options = {
                (
                    f"{player.get('name')} · {player.get('team_nfl')} · "
                    f"{player.get('role')}"
                ): player.get("id")
                for player in db_players_for_resolution
            }
            player_labels = list(player_options.keys())

            resolutions: dict[int, dict[str, Any]] = {}

            for idx, item in enumerate(unmatched):
                st.markdown(
                    f"**{escape(str(item.get('name') or '—'))}** "
                    f"· {escape(str(item.get('team') or '—'))} "
                    f"· {escape(str(item.get('source') or '—'))}"
                )

                action = st.radio(
                    "Come vuoi gestirlo?",
                    ("Ignora", "Associa a esistente", "Nuovo giocatore"),
                    horizontal=True,
                    key=f"unmatched_action_{idx}",
                    label_visibility="collapsed",
                )

                resolution: dict[str, Any] = {"action": action}

                if action == "Associa a esistente":
                    suggested = 0
                    source_name = str(item.get("name") or "")
                    source_team = str(item.get("team") or "")
                    if player_labels:
                        ranked = sorted(
                            enumerate(player_labels),
                            key=lambda pair: (
                                1 if f"· {source_team} ·" in pair[1] else 0,
                                _name_similarity(
                                    source_name,
                                    pair[1].split(" · ")[0],
                                ),
                            ),
                            reverse=True,
                        )
                        suggested = ranked[0][0]

                    selected_label = st.selectbox(
                        "Giocatore esistente",
                        player_labels,
                        index=suggested if player_labels else 0,
                        key=f"unmatched_existing_{idx}",
                    )
                    resolution["player_id"] = player_options.get(
                        selected_label
                    )

                    selected_existing = next(
                        (
                            player
                            for player in db_players_for_resolution
                            if player.get("id") == resolution["player_id"]
                        ),
                        None,
                    )
                    old_team = str(
                        (selected_existing or {}).get("team_nfl") or "—"
                    )
                    new_team = str(item.get("team") or "—")
                    if old_team != new_team:
                        st.info(
                            f"🔄 La squadra verrà aggiornata: "
                            f"**{old_team} → {new_team}**"
                        )
                    else:
                        st.caption(
                            f"Squadra già corretta: **{new_team}**."
                        )

                elif action == "Nuovo giocatore":
                    conflicts = _existing_name_conflicts(
                        str(item.get("name") or ""),
                        db_players_for_resolution,
                    )

                    if conflicts:
                        conflict_labels = ", ".join(
                            f"{player.get('name')} ({player.get('team_nfl')})"
                            for player in conflicts[:5]
                        )
                        st.warning(
                            "Ho trovato almeno un omonimo/cognome già presente: "
                            f"**{conflict_labels}**. "
                            "Inserisci l'iniziale del nome per distinguere il nuovo giocatore."
                        )
                        resolution["first_initial"] = st.text_input(
                            "Iniziale nome",
                            max_chars=1,
                            placeholder="Es. A",
                            key=f"unmatched_initial_{idx}",
                        ).strip().upper()
                    else:
                        resolution["first_initial"] = ""

                    c_role, c_price = st.columns(2)
                    with c_role:
                        resolution["role"] = st.selectbox(
                            "Ruolo",
                            ("P", "D", "C", "A"),
                            key=f"unmatched_role_{idx}",
                        )
                    with c_price:
                        resolution["list_price"] = st.number_input(
                            "Quotazione iniziale",
                            min_value=1,
                            max_value=100,
                            value=1,
                            step=1,
                            key=f"unmatched_price_{idx}",
                        )

                    resolution["rookie"] = st.checkbox(
                        "Primo anno in Serie A",
                        value=True,
                        key=f"unmatched_rookie_{idx}",
                    )

                    preview_name = _compose_new_player_name(
                        str(item.get("name") or ""),
                        resolution.get("first_initial"),
                    )
                    st.caption(
                        f"Nome che verrà salvato: **{preview_name or '—'}**"
                    )

                resolutions[idx] = resolution
                st.divider()

            st.session_state["player_unmatched_resolutions"] = resolutions

            actionable = 0
            for item_idx, resolution in resolutions.items():
                action = resolution.get("action")
                if action == "Ignora":
                    continue

                if action == "Nuovo giocatore":
                    conflicts = _existing_name_conflicts(
                        str(unmatched[item_idx].get("name") or ""),
                        db_players_for_resolution,
                    )
                    if conflicts and not str(
                        resolution.get("first_initial") or ""
                    ).strip():
                        continue

                actionable += 1
            st.caption(
                f"{actionable} giocatori selezionati per la risoluzione manuale."
            )

            if st.button(
                "🔗 Applica associazioni / crea nuovi giocatori",
                type="primary",
                use_container_width=True,
                disabled=actionable == 0,
                key="apply_unmatched_resolutions",
            ):
                associated, created, resolution_errors = (
                    apply_unmatched_resolutions(
                        unmatched,
                        resolutions,
                    )
                )

                if resolution_errors:
                    st.error(
                        f"Associati {associated} · Creati {created} · "
                        f"Errori {len(resolution_errors)}"
                    )
                    st.write(resolution_errors)
                else:
                    st.success(
                        f"Associati {associated} giocatori · "
                        f"Creati {created} nuovi rookie."
                    )

                # Rimuove dalla lista quelli gestiti con successo; al prossimo
                # fetch la fonte verrà nuovamente confrontata col DB aggiornato.
                if not resolution_errors:
                    resolved_keys = {
                        (
                            normalize_string(str(unmatched[item_idx].get("name") or "")),
                            str(unmatched[item_idx].get("team") or "").strip().upper(),
                        )
                        for item_idx, resolution in resolutions.items()
                        if resolution.get("action") != "Ignora"
                    }

                    # Lo stesso calciatore può comparire più volte nella fonte
                    # (XI, ballottaggi, rigoristi, piazzati). Una sola associazione
                    # manuale risolve tutte le occorrenze di quel nome/squadra.
                    st.session_state["player_source_unmatched"] = [
                        source_item
                        for source_item in unmatched
                        if (
                            normalize_string(
                                str(source_item.get("name") or "")
                            ),
                            str(source_item.get("team") or "").strip().upper(),
                        )
                        not in resolved_keys
                    ]
                    st.rerun()

    st.markdown("### 🧹 Secondo controllo — possibili giocatori da rimuovere")

    if not missing_check.get("safe"):
        st.warning(
            "Non uso ancora l'assenza dal Listone come criterio di rimozione: "
            f"ho letto {missing_check.get('rows', 0)} righe e "
            f"{missing_check.get('teams', 0)} squadre. "
            "Per sicurezza il controllo si attiva solo quando il Listone "
            "sembra sufficientemente completo."
        )
    elif not missing_candidates:
        st.success(
            "Tutti i giocatori presenti in Supabase risultano compatibili "
            "con il Listone ufficiale letto."
        )
    else:
        st.caption(
            "Questi giocatori sono presenti in Supabase ma non sono stati "
            "riconosciuti nel Listone ufficiale della loro squadra. "
            "Non vengono eliminati automaticamente."
        )

        protected_count = sum(
            bool(row.get("in_roster"))
            for row in missing_candidates
        )
        removable_count = len(missing_candidates) - protected_count

        m1, m2 = st.columns(2)
        m1.metric("Da verificare", len(missing_candidates))
        m2.metric("Eliminabili", removable_count)

        with st.expander(
            f"Mostra candidati ({len(missing_candidates)})",
            expanded=True,
        ):
            selected_delete_ids: set[Any] = set()

            for idx, row in enumerate(missing_candidates):
                c1, c2 = st.columns([4, 1])

                with c1:
                    st.markdown(
                        f"**{escape(str(row.get('name') or '—'))}** "
                        f"· {escape(str(row.get('team_nfl') or '—'))} "
                        f"· {escape(str(row.get('role') or '—'))}"
                    )
                    if row.get("in_roster"):
                        st.caption(
                            "🔒 Presente in una rosa: eliminazione bloccata."
                        )
                    else:
                        st.caption(
                            "Non trovato nel Listone letto. "
                            f"Somiglianza migliore: "
                            f"{float(row.get('best_source_similarity') or 0):.2f}"
                        )

                with c2:
                    remove = st.checkbox(
                        "Elimina",
                        value=False,
                        disabled=bool(row.get("in_roster")),
                        key=f"missing_delete_{idx}",
                    )
                    if remove:
                        selected_delete_ids.add(row.get("player_id"))

            if selected_delete_ids:
                st.warning(
                    f"Hai selezionato {len(selected_delete_ids)} giocatori. "
                    "Questa operazione li cancellerà dalla tabella players."
                )
                confirm_delete = st.checkbox(
                    "Confermo di aver verificato che questi giocatori "
                    "non appartengano più alla Serie A.",
                    key="confirm_missing_delete",
                )

                if st.button(
                    "🗑️ Elimina giocatori verificati",
                    type="primary",
                    use_container_width=True,
                    disabled=not confirm_delete,
                    key="delete_verified_missing_players",
                ):
                    deleted, delete_errors = delete_verified_missing_players(
                        missing_candidates,
                        selected_delete_ids,
                    )
                    if delete_errors:
                        st.error(
                            f"Eliminati {deleted} giocatori · "
                            f"{len(delete_errors)} errori."
                        )
                        st.write(delete_errors)
                    else:
                        st.success(
                            f"Eliminati {deleted} giocatori verificati."
                        )

                    # Rifare il fetch è il modo più sicuro per riallineare
                    # l'intera preview dopo una cancellazione.
                    st.session_state.pop("player_missing_candidates", None)
                    st.session_state.pop("player_missing_check", None)
                    st.rerun()

    if not preview:
        st.success("Nessuna modifica principale da applicare.")
        return

    st.divider()
    confirmed = st.checkbox(
        "Ho controllato l'anteprima e voglio applicare queste modifiche a Supabase.",
        key="confirm_player_source_apply",
    )
    if st.button(
        "✅ Applica aggiornamento a Supabase",
        type="primary",
        use_container_width=True,
        disabled=not confirmed,
        key="apply_player_source_update",
    ):
        with st.spinner("Aggiorno i giocatori..."):
            updated, errors = apply_player_source_preview(preview)

        if errors:
            st.error(
                f"Aggiornati {updated} giocatori, con {len(errors)} errori."
            )
            with st.expander("Errori"):
                st.write(errors)
        else:
            st.success(f"Aggiornati correttamente {updated} giocatori.")

        st.session_state.pop("player_source_preview", None)
        st.session_state.pop("player_source_unmatched", None)
        st.session_state.pop("player_source_stats", None)
        st.session_state.pop("player_missing_candidates", None)
        st.session_state.pop("player_missing_check", None)
        # Il checkbox con key="confirm_player_source_apply" è già stato creato
        # in questo run: assegnargli un valore qui genera StreamlitAPIException.
        # Rimuoviamo invece la chiave e lasciamo che il prossimo rerun
        # ricrei il widget nel suo stato di default.
        st.session_state.pop("confirm_player_source_apply", None)
        st.rerun()


# ============================================================
# DATI ESTERNI / NORMALIZZAZIONE
# ============================================================

def normalize_string(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    value = unicodedata.normalize("NFKD", value)
    value = "".join(c for c in value if not unicodedata.combining(c))
    value = re.sub(r"[^a-zA-Z0-9\s]", "", value)
    return re.sub(r"\s+", " ", value).strip().lower()


@st.cache_data(ttl=300)
def load_external_data() -> tuple[pd.DataFrame, dict[str, dict[str, float]], dict[str, float]]:
    stats = pd.DataFrame()
    mods: dict[str, dict[str, float]] = {}
    goals_conceded: dict[str, float] = {}

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
        return stats, mods, goals_conceded

    try:
        df = pd.read_csv(SEASON_FILE)
        required = {"HomeTeam", "AwayTeam", "FTHG", "FTAG"}
        if not required.issubset(df.columns):
            return stats, mods, goals_conceded

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

        # Memorizziamo i gol subiti per ogni club/codice Serie A.
        for _, row in ts.iterrows():
            if row["Matches"] > 0:
                code = TEAM_MAP.get(
                    str(row["Team"]),
                    str(row["Team"]).upper()[:3],
                )
                goals_conceded[code] = float(row["TotalGA"])

        total_matches = ts["Matches"].sum()
        if total_matches <= 0:
            return stats, mods, goals_conceded

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

    return stats, mods, goals_conceded


STATS, MODS, GOALS_CONCEDED = load_external_data()


def get_goalkeeper_ranking_for_teams(
    team_codes: set[str],
) -> dict[str, int]:
    """
    Classifica SOLO le squadre dei portieri presenti nella rosa.

    1 = meno gol subiti -> +1.0
    2 = seconda -> 0.0
    3 = più gol subiti -> -1.0

    Se sono presenti meno di tre squadre, vengono classificate solo
    quelle disponibili.
    """
    if not team_codes:
        return {}

    rows = [
        (code, GOALS_CONCEDED.get(code))
        for code in team_codes
        if GOALS_CONCEDED.get(code) is not None
    ]
    rows.sort(key=lambda item: (item[1], item[0]))

    return {
        code: position
        for position, (code, _) in enumerate(rows[:3], start=1)
    }


def get_goalkeeper_modifier(
    player: dict[str, Any],
    goalkeeper_ranking: dict[str, int] | None = None,
) -> tuple[float, int | None]:
    """Restituisce modificatore e posizione della squadra del portiere."""
    if player.get("role") != "P" or not goalkeeper_ranking:
        return 0.0, None

    position = goalkeeper_ranking.get(player.get("team_nfl"))
    if position is None:
        return 0.0, None

    return (
        GOALKEEPER_GOALS_CONCEDED_MODIFIERS.get(position, 0.0),
        position,
    )


ALL_GOALKEEPER_RANKING = get_goalkeeper_ranking_for_teams(set(GOALS_CONCEDED))


def get_my_team_name_from_state(state: "AuctionState") -> str | None:
    return resolve_my_team_name(list(state.team_players_map))


def get_my_team_players_and_purchases(
    state: "AuctionState",
) -> tuple[str | None, list[dict[str, Any]], list[dict[str, Any]]]:
    team_name = get_my_team_name_from_state(state)
    if team_name is None:
        return None, [], []
    return (
        team_name,
        state.team_players_map.get(team_name, []),
        state.team_purchases_map.get(team_name, []),
    )


def get_my_team_draft_role(state: "AuctionState") -> str | None:
    """Restituisce il prossimo ruolo della rosa squadra associata secondo PDCA."""
    team_name = get_my_team_name_from_state(state)
    if team_name is None:
        return "P"

    # Una rosa da 25 giocatori è definitivamente chiusa:
    # non generiamo più consigli anche se i conteggi ruolo risultano anomali.
    total_bought = state.team_total_bought.get(team_name, 0)
    actual_players = len(state.team_players_map.get(team_name, []))
    if max(total_bought, actual_players) >= TOTAL_SLOTS_PER_TEAM:
        return None

    counts = state.team_role_totals.get(team_name, {})
    for role in DRAFT_ORDER:
        if counts.get(role, 0) < ROLE_LIMITS[role]:
            return role
    return None


def role_label(role: str) -> str:
    return {
        "P": "Portieri (P)",
        "D": "Difensori (D)",
        "C": "Centrocampisti (C)",
        "A": "Attaccanti (A)",
    }.get(role, "Tutti i ruoli")


def auction_history_ratios(
    rosters: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Estrae i moltiplicatori prezzo pagato/listino dagli acquisti reali."""
    history = []
    for roster in rosters:
        player = roster.get("players") or {}
        list_price = float(player.get("list_price") or 0)
        paid = float(roster.get("purchase_price") or 0)
        if list_price <= 0 or paid <= 0:
            continue
        ratio = paid / list_price
        # Evitiamo che un errore/outlier renda inutile la mediana.
        ratio = max(0.5, min(8.0, ratio))
        history.append({
            "role": player.get("role"),
            "list_price": list_price,
            "paid": paid,
            "ratio": ratio,
            "name": player.get("name", ""),
        })
    return history


def estimate_auction_price(
    player: dict[str, Any],
    rosters: list[dict[str, Any]],
    budget: int | None = None,
    slots_left_after_purchase: int = 0,
) -> dict[str, Any]:
    """Stima il prezzo d'asta usando i moltiplicatori osservati nel draft."""
    history = auction_history_ratios(rosters)
    role = player.get("role")
    list_price = float(player.get("list_price") or 1)

    role_history = [h for h in history if h["role"] == role]
    similar_history = [
        h for h in role_history
        if 0.5 * list_price <= h["list_price"] <= 1.5 * list_price
    ]

    if len(similar_history) >= MIN_HISTORY_FOR_ROLE_ESTIMATE:
        sample = similar_history
        source = "precedenti dello stesso ruolo e fascia di listino"
    elif len(role_history) >= MIN_HISTORY_FOR_ROLE_ESTIMATE:
        sample = role_history
        source = "precedenti dello stesso ruolo"
    elif len(history) >= MIN_HISTORY_FOR_ROLE_ESTIMATE:
        sample = history
        source = "precedenti generali dell'asta"
    else:
        sample = []
        source = "baseline: non ci sono ancora abbastanza precedenti"

    if sample:
        ratios = sorted(h["ratio"] for h in sample)
        multiplier = float(pd.Series(ratios).median())
    else:
        multiplier = DEFAULT_AUCTION_MULTIPLIER

    estimated = max(1, int(round(list_price * multiplier)))
    feasible = True
    budget_note = ""
    max_bid = None

    if budget is not None:
        reserve = max(0, int(slots_left_after_purchase))
        max_bid = max(1, int(budget) - reserve)
        if estimated > max_bid:
            feasible = False
            budget_note = (
                f"Budget massimo sostenibile: {max_bid} cr; "
                f"la stima di mercato è {estimated} cr."
            )

    return {
        "multiplier": round(multiplier, 2),
        "estimated_price": estimated,
        "source": source,
        "sample_size": len(sample),
        "feasible": feasible,
        "budget_note": budget_note,
        "max_bid": max_bid,
    }


def get_player_strategy_note_for_player(player: dict[str, Any]) -> dict[str, Any] | None:
    """Recupera l'eventuale nota strategica collegata al giocatore."""
    try:
        notes = load_player_strategy_notes()
    except Exception:
        return None

    player_id = str(player.get("id") or "").strip()
    player_name = normalize_string(str(player.get("name") or ""))
    player_team = str(player.get("team_nfl") or "").strip().upper()
    player_role = str(player.get("role") or "").strip().upper()

    for note in notes:
        if player_id and str(note.get("player_id") or "").strip() == player_id:
            return note

    exact_matches: list[dict[str, Any]] = []
    loose_matches: list[dict[str, Any]] = []
    for note in notes:
        note_name = normalize_string(str(note.get("player_name") or ""))
        note_team = _strategy_note_source_team(note)
        note_role = str(note.get("role") or "").strip().upper()
        if note_name != player_name:
            continue
        if note_team == player_team and (not note_role or note_role == player_role):
            exact_matches.append(note)
        else:
            loose_matches.append(note)

    if exact_matches:
        return exact_matches[0]
    if loose_matches:
        return loose_matches[0]
    return None


def get_player_budget_spend_focus(
    player: dict[str, Any],
    estimate: dict[str, Any],
    total_budget: int = 500,
) -> dict[str, Any]:
    """Restituisce un singolo tetto di spesa chiaro e visibile per il giocatore."""
    note = get_player_strategy_note_for_player(player)
    note_max = note.get("max_price") if note else None
    try:
        note_max = int(note_max) if note_max not in (None, "") else None
    except Exception:
        note_max = None

    estimated_price = max(1, int(estimate.get("estimated_price") or 1))
    sustainable_cap = estimate.get("max_bid")
    try:
        sustainable_cap = int(sustainable_cap) if sustainable_cap is not None else None
    except Exception:
        sustainable_cap = None

    if note_max is not None and sustainable_cap is not None:
        recommended_cap = max(1, min(note_max, sustainable_cap))
        source = "Nota strategica + budget disponibile"
    elif note_max is not None:
        recommended_cap = max(1, note_max)
        source = "Nota strategica"
    elif sustainable_cap is not None:
        recommended_cap = max(1, min(estimated_price, sustainable_cap))
        source = "Stima d'asta"
    else:
        recommended_cap = estimated_price
        source = "Stima d'asta"

    pct = (recommended_cap / max(1, total_budget)) * 100.0
    return {
        "recommended_cap": recommended_cap,
        "pct_total_budget": pct,
        "source": source,
        "note": note,
    }


def render_player_spend_focus_card(spend_focus: dict[str, Any]) -> None:
    """Card compatta e leggibile: mostra solo tetto di spesa e % budget."""
    cap = int(spend_focus.get("recommended_cap") or 1)
    pct = float(spend_focus.get("pct_total_budget") or 0.0)
    source = str(spend_focus.get("source") or "")

    st.markdown(
        f"""
        <div style="
            margin: 0.45rem 0 1rem 0;
            padding: 1rem 1.2rem;
            border-radius: 20px;
            background: linear-gradient(135deg, rgba(37,99,235,0.16), rgba(29,78,216,0.26));
            border: 1px solid rgba(37,99,235,0.22);
            box-shadow: 0 10px 24px rgba(37,99,235,0.08);
        ">
            <div style="font-size:0.92rem;font-weight:800;color:#1d4ed8;letter-spacing:0.02em;display:flex;align-items:center;gap:0.45rem;">
                💰 Tetto di spesa consigliato
            </div>
            <div style="display:flex;flex-wrap:wrap;align-items:flex-end;justify-content:space-between;gap:0.85rem;margin-top:0.55rem;">
                <div>
                    <div style="font-size:2.2rem;line-height:1;font-weight:900;color:#0f172a;">{cap} cr</div>
                    <div style="font-size:0.95rem;color:#334155;font-weight:700;margin-top:0.35rem;">{pct:.1f}% del budget totale</div>
                </div>
                <div style="padding:0.55rem 0.85rem;border-radius:999px;background:rgba(255,255,255,0.72);color:#1e293b;font-weight:800;font-size:0.88rem;white-space:nowrap;">
                    {escape(source)}
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


RECOMMENDATION_TIERS = {
    "TOP": {"min_rating": 9.0, "max_rating": 10.0},
    "Prima Fascia": {"min_rating": 8.0, "max_rating": 8.9},
    "Seconda Fascia": {"min_rating": 7.0, "max_rating": 7.9},
    "Terza Fascia": {"min_rating": 6.5, "max_rating": 6.9},
}
RECOMMENDATION_TIER_OPTIONS = list(RECOMMENDATION_TIERS.keys())

def get_recommendation_tier(rating: float) -> str | None:
    r = float(rating)
    if r >= 9.0: return "TOP"
    if r >= 8.0: return "Prima Fascia"
    if r >= 7.0: return "Seconda Fascia"
    if r >= 6.5: return "Terza Fascia"
    return None

def get_roster_tier(rating: float) -> str:
    tier = get_recommendation_tier(rating)
    return tier if tier is not None else "Scommessa"


def get_price_value_score(rating: float, estimated_price: int, list_price: int) -> float:
    """Punteggio qualità/prezzo: privilegia rating alto a costo d'asta contenuto."""
    price=max(1.0,float(estimated_price)); lp=max(1.0,float(list_price)); r=float(rating)
    rating_per_100=(r/price)*100.0
    list_efficiency=lp/price
    quality_bonus=max(0.0,r-7.0)
    return round(rating_per_100*0.68 + list_efficiency*4.0 + quality_bonus*0.90,3)

def calculate_value_per_credit(rating: float, estimated_price: int) -> float:
    """Rating ottenibile ogni 10 crediti stimati."""
    return round((float(rating)/max(1,estimated_price))*10.0,3)


def build_next_player_recommendations(
    state: "AuctionState",
    rosters: list[dict[str, Any]],
    preferred_players: set[Any],
    custom_modifiers: dict[Any, dict[str, Any]],
    role: str | None,
    limit: int = 5,
) -> list[dict[str, Any]]:
    """Restituisce i migliori obiettivi acquistabili nel ruolo corrente."""
    if not role:
        return []

    team_name = get_my_team_name_from_state(state)
    if team_name is None:
        return []

    # Il consiglio è costruito sul budget RCD e sugli slot ancora disponibili.
    # Cerchiamo il budget nello stato tramite le rose/teams in main e lo passiamo
    # indirettamente in una variabile di sessione, se presente.
    budget = st.session_state.get("my_team_budget")
    role_count = state.team_role_totals.get(team_name, {}).get(role, 0)
    total_count = state.team_total_bought.get(team_name, 0)
    # Dopo questo acquisto bisogna comunque conservare almeno 1 credito
    # per ogni slot della rosa che resterà da completare, indipendentemente dal ruolo.
    slots_after = max(0, TOTAL_SLOTS_PER_TEAM - total_count - 1)

    goalkeeper_ranking = build_current_goalkeeper_ranking(state)
    candidates = [
        player for player in load_players(role=role)
        if player.get("id") not in state.bought_player_ids
    ]

    selected_tier = st.session_state.get("recommendation_tier", "TOP")
    rows = []
    for player in candidates:
        details = calculate_player_rating_detailed(
            player, preferred_players, custom_modifiers, goalkeeper_ranking
        )
        rating = float(details["final_rating"])
        tier = get_recommendation_tier(rating)
        if tier is None or tier != selected_tier:
            continue
        estimate = estimate_auction_price(
            player, rosters, budget=budget,
            slots_left_after_purchase=slots_after,
        )
        list_price = int(player.get("list_price") or 1)
        score = get_price_value_score(
            rating, estimate["estimated_price"], list_price
        )
        rows.append({
            "player": player,
            "details": details,
            "estimate": estimate,
            "score": score,
            "tier": tier,
            "rating_per_10_cr": calculate_value_per_credit(
                rating, estimate["estimated_price"]
            ),
        })

    feasible_rows = [row for row in rows if row["estimate"]["feasible"]]
    if feasible_rows:
        rows = feasible_rows

    # Il rating determina la fascia; il prezzo determina il miglior affare
    # SOLO all'interno della fascia selezionata.
    rows.sort(
        key=lambda row: (
            row["score"],
            row["details"]["final_rating"],
            -row["estimate"]["estimated_price"],
        ),
        reverse=True,
    )
    return rows[:limit]



def describe_goalkeeper_strategy(players: list[dict[str, Any]]) -> str:
    """Valuta la strategia P senza chiedere di correggere un reparto già chiuso."""
    keepers=[p for p in players if p.get("role")=="P"]
    if not keepers: return ""
    clubs=[p.get("team_nfl") for p in keepers if p.get("team_nfl")]
    unique_clubs=list(dict.fromkeys(clubs))
    club_goal_data=[(c,GOALS_CONCEDED.get(c)) for c in unique_clubs if GOALS_CONCEDED.get(c) is not None]
    ranking=build_current_goalkeeper_ranking_from_players(keepers)
    details=[calculate_player_rating_detailed(p,st.session_state.preferred_players,load_custom_modifiers(),ranking) for p in keepers]
    avg_rating=sum(d["final_rating"] for d in details)/len(details)
    if len(unique_clubs)==1:
        diversification=f"Hai scelto {len(keepers)}/{len(keepers)} portieri della stessa squadra ({unique_clubs[0]}): strategia molto concentrata, ma non è un difetto in sé se la difesa è affidabile."
    elif len(unique_clubs)==len(keepers):
        diversification=f"Hai scelto {len(keepers)} portieri di {len(unique_clubs)} squadre diverse: ottima diversificazione e minore dipendenza da una singola difesa."
    else:
        diversification=f"Hai {len(keepers)} portieri distribuiti su {len(unique_clubs)} squadre: diversificazione parziale."
    if club_goal_data:
        avg_ga=sum(v for _,v in club_goal_data)/len(club_goal_data)
        vals=list(GOALS_CONCEDED.values()); median=float(pd.Series(vals).median()) if vals else avg_ga
        if avg_ga <= median-4: defense="Le squadre scelte prendono pochi gol: la scelta è particolarmente solida."
        elif avg_ga >= median+4: defense="Le squadre scelte prendono molti gol: hai accettato un rischio che va compensato soprattutto nei difensori."
        else: defense="Le squadre scelte sono nella fascia media per gol subiti."
    else: defense="Non ho abbastanza dati sui gol subiti per giudicare le difese."
    quality=(f"Rating medio portieri {avg_rating:.1f}: reparto di alto livello." if avg_rating>=8 else f"Rating medio portieri {avg_rating:.1f}: reparto competitivo." if avg_rating>=7 else f"Rating medio portieri {avg_rating:.1f}: reparto sotto il livello ideale.")
    if len(keepers)>=ROLE_LIMITS["P"]:
        return f"{diversification} {defense} {quality} Portieri completati: non c'è nulla da correggere qui. Ora sposterei attenzione e budget sui difensori."
    return f"{diversification} {defense} {quality} Finché il reparto non è completo, privilegia il valore per credito e non il solo rating."


def build_current_goalkeeper_ranking_from_players(
    players: list[dict[str, Any]],
) -> dict[str, int]:
    clubs = {p.get("team_nfl") for p in players if p.get("team_nfl")}
    return get_goalkeeper_ranking_for_teams(clubs)


def build_draft_strategy_text(
    state: "AuctionState",
    rosters: list[dict[str, Any]],
    teams_df: pd.DataFrame,
    ratings: dict[str, float],
) -> tuple[str, str, str]:
    """Valutazione progressiva; a draft chiuso solo resoconto finale."""
    team_name, players, _ = get_my_team_players_and_purchases(state)
    if team_name is None or not players:
        return "", "", ""

    counts = state.team_role_totals.get(team_name, {})
    current_role = get_my_team_draft_role(state)
    # Consideriamo conclusa l'asta della squadra appena la rosa ha 25 elementi.
    # Questo evita consigli impossibili nel caso in cui i conteggi ruolo del DB
    # non coincidano perfettamente con 3/8/8/6.
    draft_complete = (
        len(players) >= TOTAL_SLOTS_PER_TEAM
        or state.team_total_bought.get(team_name, 0) >= TOTAL_SLOTS_PER_TEAM
    )

    custom_modifiers = load_custom_modifiers()
    goalkeeper_ranking = build_current_goalkeeper_ranking(state)

    def role_avg(role: str) -> float:
        role_players = [p for p in players if p.get("role") == role]
        if not role_players:
            return 0.0
        values = [
            calculate_player_rating_detailed(
                p,
                st.session_state.preferred_players,
                custom_modifiers,
                goalkeeper_ranking,
            )["final_rating"]
            for p in role_players
        ]
        return sum(values) / len(values)

    sections = []

    if draft_complete:
        keepers = [p for p in players if p.get("role") == "P"]
        if keepers:
            p_avg = role_avg("P")
            clubs = [p.get("team_nfl") for p in keepers if p.get("team_nfl")]
            unique_clubs = len(set(clubs))
            structure = (
                "tre portieri della stessa squadra"
                if unique_clubs == 1
                else "portieri distribuiti su due squadre"
                if unique_clubs == 2
                else "tre portieri di tre squadre diverse"
            )
            selected_ga = [
                GOALS_CONCEDED.get(code)
                for code in set(clubs)
                if GOALS_CONCEDED.get(code) is not None
            ]
            if selected_ga:
                league_values = list(GOALS_CONCEDED.values())
                league_median = float(pd.Series(league_values).median()) if league_values else 0
                avg_ga = sum(selected_ga) / len(selected_ga)
                defensive_quality = (
                    "difese che concedono pochi gol"
                    if avg_ga <= league_median
                    else "difese che concedono molti gol"
                )
            else:
                defensive_quality = "difese senza dati sufficienti sui gol subiti"
            p_level = "alto livello" if p_avg >= 8.0 else "solido" if p_avg >= 6.5 else "debole"
            sections.append(
                f"**Portieri:** {structure}, su {defensive_quality}. "
                f"Rating medio {p_avg:.1f}: reparto {p_level}."
            )

        d_avg = role_avg("D")
        c_avg = role_avg("C")
        a_avg = role_avg("A")
        d_level = "alto livello" if d_avg >= 8 else "buona" if d_avg >= 7 else "discreta" if d_avg >= 6 else "debole"
        c_level = "alto livello" if c_avg >= 8 else "buono" if c_avg >= 7 else "discreto" if c_avg >= 6 else "debole"
        a_level = "alto livello" if a_avg >= 8 else "buono" if a_avg >= 7 else "discreto" if a_avg >= 6 else "debole"

        sections.append(f"**Difesa:** rating medio {d_avg:.1f}: difesa {d_level}.")
        sections.append(f"**Centrocampo:** rating medio {c_avg:.1f}: centrocampo {c_level}.")
        sections.append(f"**Attacco:** rating medio {a_avg:.1f}: attacco {a_level}.")

        team_rating = ratings.get(team_name, 0.0)
        overall = "rosa forte" if team_rating >= 6.5 else "rosa scarsa"
        return (
            "🏁 **Asta conclusa — valutazione finale**",
            " ".join(sections) + f" **Giudizio complessivo:** {overall}.",
            "",
        )

    if counts.get("P", 0) > 0:
        sections.append("**Portieri:** " + describe_goalkeeper_strategy(players))

    if counts.get("D", 0) > 0:
        d_avg = role_avg("D")
        if d_avg >= 8.0:
            d_text = "Difesa molto forte: hai già una base di alto livello."
        elif d_avg >= 7.0:
            d_text = "Difesa competitiva, ma puoi ancora alzare il livello con 1-2 profili forti."
        else:
            d_text = "Difesa sotto il livello desiderabile: spingerei di più sui prossimi difensori."
        sections.append(f"**Difesa:** rating medio {d_avg:.1f}. {d_text}")

    if counts.get("C", 0) > 0:
        midfielders = [p for p in players if p.get("role") == "C"]
        c_avg = role_avg("C")
        bonus_flags = sum(
            bool(p.get("rigorista")) or bool((p.get("list_price") or 0) >= 25)
            for p in midfielders
        )
        if bonus_flags < max(1, len(midfielders) // 3):
            c_text = "Hai pochi profili ad alto potenziale bonus: qui conviene spingere."
        elif c_avg >= 8.0:
            c_text = "Centrocampo molto forte e con buon potenziale bonus."
        else:
            c_text = "Centrocampo discreto: cerca ancora qualità e giocatori con bonus."
        sections.append(f"**Centrocampo:** rating medio {c_avg:.1f}. {c_text}")

    if counts.get("A", 0) > 0:
        a_avg = role_avg("A")
        if a_avg >= 8.0:
            a_text = "Attacco di livello alto: la fase offensiva è una forza della rosa."
        elif a_avg >= 7.0:
            a_text = "Attacco competitivo: manca ancora un profilo che faccia davvero la differenza."
        else:
            a_text = "Attacco debole: qui va concentrata una parte importante del budget."
        sections.append(f"**Attacco:** rating medio {a_avg:.1f}. {a_text}")

    next_name = ROLE_NAMES[current_role]
    if current_role == "P":
        advice = "Stai costruendo i portieri: privilegia il rapporto rating/costo e, a parità di valore, preferisci squadre che concedono pochi gol."
    elif current_role == "D":
        advice = "I portieri sono chiusi: ora cerca difensori con rating alto ma soprattutto con buon rapporto rating/costo."
    elif current_role == "C":
        advice = "Portieri e difensori sono acquisiti: cerca centrocampisti ad alto valore per credito, con titolarità, rigoristi e potenziale bonus."
    else:
        advice = "Sugli attaccanti puoi concentrare più budget sui profili forti, ma continua a confrontare rating, stima d'asta e crediti residui."

    phase = f"Fase draft: **{next_name}** ({counts.get(current_role, 0)}/{ROLE_LIMITS[current_role]})."
    return phase, " ".join(sections), advice


# ============================================================
# RATING
# ============================================================

def calculate_player_rating_detailed(
    player: dict[str, Any],
    preferred_players: set[Any] | None = None,
    custom_modifiers: dict[Any, dict[str, Any]] | None = None,
    goalkeeper_ranking: dict[str, int] | None = None,
) -> dict[str, Any]:
    preferred_players = preferred_players or set()
    if custom_modifiers is None:
        custom_modifiers = load_custom_modifiers()
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

    # Portieri: il modificatore difensivo standard viene sostituito
    # dal criterio richiesto basato sui gol subiti delle tre squadre.
    goalkeeper_mod, goalkeeper_rank = get_goalkeeper_modifier(
        player,
        goalkeeper_ranking,
    )
    team_mod = (
        goalkeeper_mod
        if role == "P"
        else team_mods["att"]
        if role in {"A", "C"}
        else team_mods["def"]
    )

    # Rigoristi: utilizziamo anche la gerarchia della fonte Fantacalcio.
    # Il primo rigorista vale sensibilmente più di una seconda/terza scelta.
    try:
        rigorista_order = int(player.get("rigorista_ordine")) if player.get("rigorista_ordine") is not None else None
    except (TypeError, ValueError):
        rigorista_order = None

    if rigorista_order == 1:
        rigorista_mod = 0.8
    elif rigorista_order == 2:
        rigorista_mod = 0.45
    elif rigorista_order == 3:
        rigorista_mod = 0.20
    elif player.get("rigorista"):
        rigorista_mod = 0.30
    else:
        rigorista_mod = 0.0
    cartellini_mod = -0.3 if player.get("propensione_cartellini") == "A rischio malus" else 0.0
    rookie_mod = -0.3 if player.get("primo_anno_serie_a") else 0.0
    # Il preferito proveniente dalla sessione resta compatibile.
    # Se il preferito è salvato nella nuova tabella, viene letto da lì.
    db_modifier = custom_modifiers.get(player.get("id"), {})
    custom_mod = float(db_modifier.get("modifier_value") or 0.0)
    db_modifier_key = db_modifier.get("modifier_key")

    preferred_mod = (
        0.5
        if (
            player.get("id") in preferred_players
            and db_modifier_key != "preferito"
        )
        else 0.0
    )

    # Rating grezzo prima della calibrazione per ruolo.
    raw_rating = (
        base
        + titolarita_mod
        + team_mod
        + rigorista_mod
        + cartellini_mod
        + rookie_mod
        + preferred_mod
        + custom_mod
    )

    # Calibrazione richiesta per rendere confrontabili i ruoli senza
    # penalizzare portieri, difensori e centrocampisti rispetto agli attaccanti.
    role_multiplier = ROLE_RATING_MULTIPLIERS.get(role, 1.0)
    calibrated_rating = raw_rating * role_multiplier

    final = round(
        max(1.0, min(10.0, calibrated_rating)),
        1,
    )

    if (
        (cartellini_mod < 0 or rookie_mod < 0 or player.get("status_titolarita") in {"Ballottaggio", "Riserva"})
        and final >= 10.0
    ):
        final = 9.0

    return {
        "final_rating": final,
        "raw_rating": round(raw_rating, 2),
        "role_multiplier": round(role_multiplier, 3),
        "calibrated_rating": round(calibrated_rating, 2),
        "base": round(base, 2),
        "team_mod": team_mod,
        "goalkeeper_mod": goalkeeper_mod,
        "goalkeeper_rank": goalkeeper_rank,
        "tit": titolarita_mod,
        "rig": rigorista_mod,
        "cart": cartellini_mod,
        "rook": rookie_mod,
        "pref": preferred_mod,
        "custom_mod": custom_mod,
        "custom_label": db_modifier.get("modifier_label", "Nessuna modifica"),
        "g": goals,
        "a": assists,
        "m": matches,
    }


def calculate_player_rating(
    player: dict[str, Any],
    preferred_players: set[Any] | None = None,
    custom_modifiers: dict[Any, dict[str, Any]] | None = None,
    goalkeeper_ranking: dict[str, int] | None = None,
) -> float:
    return calculate_player_rating_detailed(
        player,
        preferred_players,
        custom_modifiers,
        goalkeeper_ranking,
    )["final_rating"]



def build_current_goalkeeper_ranking(
    state: "AuctionState",
) -> dict[str, int]:
    """Classifica le squadre dei portieri attualmente presenti nelle rose."""
    goalkeeper_teams: set[str] = set()

    for players in state.team_players_map.values():
        for player in players:
            if player.get("role") == "P" and player.get("team_nfl"):
                goalkeeper_teams.add(player["team_nfl"])

    return get_goalkeeper_ranking_for_teams(goalkeeper_teams)


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


def _role_club_key(player: dict[str, Any]) -> tuple[str, str]:
    return (
        str(player.get("team_nfl") or ""),
        str(player.get("role") or ""),
    )


def count_role_coverage_synergies(players: list[dict[str, Any]]) -> dict[str, int]:
    """
    Counts useful same-club/same-role cover combinations.

    - starter + reserve: useful direct cover
    - two ballot players: the pair covers the same starting slot uncertainty
    """
    groups: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for player in players:
        key = _role_club_key(player)
        if not all(key):
            continue
        groups.setdefault(key, []).append(player)

    starter_reserve_pairs = 0
    ballot_pairs = 0

    for group in groups.values():
        starters = sum(
            p.get("status_titolarita") == "Titolare"
            for p in group
        )
        reserves = sum(
            p.get("status_titolarita") == "Riserva"
            for p in group
        )
        ballots = sum(
            p.get("status_titolarita") == "Ballottaggio"
            for p in group
        )

        starter_reserve_pairs += min(starters, reserves)
        ballot_pairs += ballots // 2

    return {
        "starter_reserve_pairs": starter_reserve_pairs,
        "ballot_pairs": ballot_pairs,
    }


def get_uncovered_ballot_players(
    players: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Returns only ballot players that are not protected by another ballot
    from the same Serie A club and role.

    A pair of ballot players in the same club/role is treated as coverage,
    therefore neither contributes to the ballot alert.
    """
    groups: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for player in players:
        if player.get("status_titolarita") != "Ballottaggio":
            continue
        key = _role_club_key(player)
        groups.setdefault(key, []).append(player)

    uncovered: list[dict[str, Any]] = []
    for group in groups.values():
        # Every complete pair is considered covered.
        if len(group) % 2:
            uncovered.append(group[-1])

    return uncovered


def player_team_weight(rating: float) -> float:
    """Peso del giocatore nella valutazione della rosa."""
    if rating >= 9.0:
        return TEAM_PLAYER_WEIGHTS["TOP"]
    if rating >= 8.0:
        return TEAM_PLAYER_WEIGHTS["PRIMA"]
    if rating >= 7.0:
        return TEAM_PLAYER_WEIGHTS["SECONDA"]
    if rating >= 6.5:
        return TEAM_PLAYER_WEIGHTS["TERZA"]
    return TEAM_PLAYER_WEIGHTS["SOTTO_SOGLIA"]


def calculate_single_team_rating(
    players: list[dict[str, Any]],
    preferred_players: set[Any],
    custom_modifiers: dict[Any, dict[str, Any]] | None = None,
    goalkeeper_ranking: dict[str, int] | None = None,
) -> float:
    """
    Rating rosa non lineare.

    - I TOP pesano molto più degli altri.
    - I giocatori sotto 6.5 incidono negativamente.
    - Le differenze attorno alla fascia media vengono amplificate.
    """
    if not players:
        return 0.0

    player_ratings = [
        calculate_player_rating(
            player,
            preferred_players,
            custom_modifiers,
            goalkeeper_ranking,
        )
        for player in players
    ]

    weights = [player_team_weight(rating) for rating in player_ratings]
    weighted_avg = sum(
        rating * weight
        for rating, weight in zip(player_ratings, weights)
    ) / max(0.001, sum(weights))

    top_count = sum(rating >= 9.0 for rating in player_ratings)
    elite_count = sum(8.5 <= rating < 9.0 for rating in player_ratings)
    weak_count = sum(rating < 6.5 for rating in player_ratings)

    # Amplificazione attorno al centro: due rose simili non finiscono
    # automaticamente tutte nello stesso intervallo 5.5-5.9.
    amplified = (
        TEAM_RATING_CENTER
        + (weighted_avg - TEAM_RATING_CENTER) * TEAM_RATING_SPREAD
    )

    # La presenza di veri TOP cambia il potenziale di una rosa.
    star_bonus = min(
        1.10,
        top_count * TOP_PLAYER_BONUS
        + elite_count * ELITE_PLAYER_BONUS,
    )

    # Profili deboli continuano a pesare, ma meno dei TOP in positivo.
    weak_penalty = min(1.20, weak_count * WEAK_PLAYER_PENALTY)

    coverage = count_role_coverage_synergies(players)

    # A reserve behind our own starter, or a paired ballot from the same
    # club/role, has more practical value than two unrelated uncertain slots.
    # Keep the bonus deliberately modest so player quality remains dominant.
    coverage_bonus = min(
        0.45,
        coverage["starter_reserve_pairs"] * 0.08
        + coverage["ballot_pairs"] * 0.12,
    )

    final = amplified + star_bonus + coverage_bonus - weak_penalty

    return round(
        max(TEAM_RATING_MIN, min(TEAM_RATING_MAX, final)),
        1,
    )


def calculate_team_ratings(
    state: AuctionState,
    preferred_players: set[Any],
    custom_modifiers: dict[Any, dict[str, Any]] | None = None,
    goalkeeper_ranking: dict[str, int] | None = None,
) -> dict[str, float]:
    return {
        team_name: calculate_single_team_rating(
            players,
            preferred_players,
            custom_modifiers,
            goalkeeper_ranking,
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
        "ballottaggio": len(get_uncovered_ballot_players(players)),
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

        if state.team_total_bought.get(selected_team, 0) >= TOTAL_SLOTS_PER_TEAM:
            # A rosa completa il giudizio è relativo al ranking della lega.
            league_size = max(1, len(ratings))

            if rating_position == 1:
                outlook_icon = "🏆"
                outlook_title = "Favorita per la vittoria"
                outlook_text = "La rosa parte davanti a tutte per qualità complessiva."
                outlook_tone = "elite"
            elif rating_position <= max(2, round(league_size * 0.25)):
                outlook_icon = "🔥"
                outlook_title = "Rosa da titolo"
                outlook_text = "Sei nel gruppo delle squadre con reali possibilità di vittoria."
                outlook_tone = "strong"
            elif rating_position <= max(4, round(league_size * 0.42)):
                outlook_icon = "⚔️"
                outlook_title = "Rosa da alta classifica"
                outlook_text = "Rosa competitiva per stare stabilmente nelle prime posizioni."
                outlook_tone = "good"
            elif rating_position <= max(6, round(league_size * 0.58)):
                outlook_icon = "📊"
                outlook_title = "Rosa da metà classifica"
                outlook_text = "Valore complessivo in linea con la zona centrale della lega."
                outlook_tone = "mid"
            elif rating_position <= max(9, round(league_size * 0.75)):
                outlook_icon = "📉"
                outlook_title = "Rosa da medio-bassa classifica"
                outlook_text = "Parte dietro alle rose più forti della lega."
                outlook_tone = "warn"
            else:
                outlook_icon = "⚠️"
                outlook_title = "Rosa da bassa classifica"
                outlook_text = "Il rating complessivo la colloca tra le rose meno competitive."
                outlook_tone = "bad"

            outlook_html = (
                "<style>"
                ".roster-outlook{padding:15px 16px;border-radius:16px;margin:12px 0 8px;"
                "border:1px solid #cbdcf5;box-shadow:0 7px 20px rgba(30,64,175,.07);}"
                ".roster-outlook.elite{background:linear-gradient(135deg,#fff7d6,#eef5ff);border-color:#f4c95d;}"
                ".roster-outlook.strong{background:linear-gradient(135deg,#e9fff3,#edf6ff);border-color:#9bd8b4;}"
                ".roster-outlook.good{background:linear-gradient(135deg,#edf7ff,#f7fbff);border-color:#b9d5f5;}"
                ".roster-outlook.mid{background:linear-gradient(135deg,#f3f6fb,#eef4ff);border-color:#cad6e8;}"
                ".roster-outlook.warn{background:linear-gradient(135deg,#fff7df,#fffaf0);border-color:#e9cc83;}"
                ".roster-outlook.bad{background:linear-gradient(135deg,#fff0f0,#fff7f7);border-color:#e7abab;}"
                ".roster-outlook-top{display:flex;align-items:center;gap:10px;margin-bottom:6px;}"
                ".roster-outlook-icon{font-size:1.45rem;line-height:1;}"
                ".roster-outlook-title{font-size:1.02rem;font-weight:950;color:#172033!important;}"
                ".roster-outlook-text{font-size:.78rem;line-height:1.35;color:#64748b!important;margin-bottom:8px;}"
                ".roster-outlook-rank{display:inline-block;padding:4px 8px;border-radius:999px;"
                "background:rgba(255,255,255,.72);font-size:.72rem;font-weight:850;color:#315a9e!important;}"
                "</style>"
                f"<div class=\"roster-outlook {outlook_tone}\">"
                f"<div class=\"roster-outlook-top\"><span class=\"roster-outlook-icon\">{outlook_icon}</span>"
                f"<span class=\"roster-outlook-title\">{outlook_title}</span></div>"
                f"<div class=\"roster-outlook-text\">{outlook_text}</div>"
                f"<span class=\"roster-outlook-rank\">Ranking rosa: {rating_position}° / {league_size}</span>"
                "</div>"
            )
            st.sidebar.markdown(outlook_html, unsafe_allow_html=True)
        else:
            # Durante l'asta mostriamo una card compatta invece dei box
            # success/info/warning standard di Streamlit.
            if avg_score >= 8:
                draft_icon = "🔥"
                draft_title = "Rosa da Scudetto"
                draft_text = "La qualità raccolta fin qui è da vertice."
                draft_tone = "excellent"
            elif avg_score >= 6.5:
                draft_icon = "⚔️"
                draft_title = "Rosa competitiva"
                draft_text = "La base è buona: ora conta come investi i crediti rimasti."
                draft_tone = "competitive"
            else:
                draft_icon = "🛠️"
                draft_title = "Rosa da rinforzare"
                draft_text = "Hai ancora margine per alzare il livello nei prossimi acquisti."
                draft_tone = "building"

            avg_spendable = budget / max(1, slots_left)

            draft_html = (
                "<style>"
                ".draft-status-card{padding:14px 15px;border-radius:16px;margin:11px 0 10px;"
                "border:1px solid #cbdcf5;box-shadow:0 6px 18px rgba(30,64,175,.07);}"
                ".draft-status-card.excellent{background:linear-gradient(135deg,#eafff2,#edf6ff);border-color:#9edab7;}"
                ".draft-status-card.competitive{background:linear-gradient(135deg,#eef6ff,#f8fbff);border-color:#b9d5f5;}"
                ".draft-status-card.building{background:linear-gradient(135deg,#fff8e8,#f4f8ff);border-color:#ead39a;}"
                ".draft-status-head{display:flex;align-items:center;gap:9px;margin-bottom:5px;}"
                ".draft-status-icon{font-size:1.35rem;line-height:1;}"
                ".draft-status-title{font-size:1rem;font-weight:950;color:#172033!important;}"
                ".draft-status-text{font-size:.75rem;line-height:1.35;color:#64748b!important;margin-bottom:11px;}"
                ".draft-economy-grid{display:grid;grid-template-columns:1fr 1fr;gap:7px;}"
                ".draft-economy-box{padding:9px 9px 8px;border-radius:11px;background:rgba(255,255,255,.72);"
                "border:1px solid rgba(203,220,245,.85);}"
                ".draft-economy-label{font-size:.62rem;font-weight:900;letter-spacing:.04em;"
                "text-transform:uppercase;color:#7c8da8!important;margin-bottom:3px;}"
                ".draft-economy-value{font-size:.95rem;font-weight:950;color:#172033!important;line-height:1.1;}"
                ".draft-economy-sub{font-size:.65rem;font-weight:700;color:#64748b!important;margin-top:3px;}"
                "</style>"
                f'<div class="draft-status-card {draft_tone}">'
                '<div class="draft-status-head">'
                f'<span class="draft-status-icon">{draft_icon}</span>'
                f'<span class="draft-status-title">{draft_title}</span>'
                '</div>'
                f'<div class="draft-status-text">{draft_text}</div>'
                '<div class="draft-economy-grid">'
                '<div class="draft-economy-box">'
                '<div class="draft-economy-label">💰 Crediti</div>'
                f'<div class="draft-economy-value">{budget} cr</div>'
                f'<div class="draft-economy-sub">{credit_rank}° / {len(team_names)} per residuo</div>'
                '</div>'
                '<div class="draft-economy-box">'
                '<div class="draft-economy-label">🎯 Margine slot</div>'
                f'<div class="draft-economy-value">{avg_spendable:.1f} cr</div>'
                f'<div class="draft-economy-sub">media · {slots_left} slot liberi</div>'
                '</div>'
                '</div></div>'
            )
            st.sidebar.markdown(draft_html, unsafe_allow_html=True)
    else:
        st.sidebar.metric("Rating Rosa", "N/D")
        st.sidebar.info("Assegna giocatori per calcolare il rating.")

    st.sidebar.markdown("---")

    risks = get_team_risk_counts(players)

    block_status = (
        "Ottimale" if risks["max_block"] < 4
        else "Rischio blocco"
    )
    block_tone = "good" if risks["max_block"] < 4 else "bad"

    ballot_status = risk_label(
        risks["ballottaggio"], 3, 6,
        "Ottimale", "Moderato", "Troppi",
    )
    ballot_tone = (
        "good" if risks["ballottaggio"] < 3
        else "warn" if risks["ballottaggio"] < 6
        else "bad"
    )

    card_status = risk_label(
        risks["cartellini"], 2, 4,
        "Pulita", "Attenzione", "Troppi malus",
    )
    card_tone = (
        "good" if risks["cartellini"] < 2
        else "warn" if risks["cartellini"] < 4
        else "bad"
    )

    rookie_status = risk_label(
        risks["rookie"], 2, 4,
        "Esperti", "Equilibrato", "Troppi rookie",
    )
    rookie_tone = (
        "good" if risks["rookie"] < 2
        else "warn" if risks["rookie"] < 4
        else "bad"
    )

    risk_html = (
        "<style>"
        ".risk-dashboard-title{display:flex;align-items:center;gap:8px;margin:.1rem 0 .65rem;"
        "font-size:1rem;font-weight:900;color:#172033!important;}"
        ".risk-grid{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:.6rem;}"
        ".risk-card{min-width:0;padding:10px 10px 9px;border:1px solid #cfddf1;border-radius:13px;"
        "background:linear-gradient(145deg,#ffffff,#eef5ff);box-shadow:0 4px 12px rgba(30,64,175,.05);}"
        ".risk-card-head{display:flex;align-items:center;justify-content:space-between;gap:5px;margin-bottom:5px;}"
        ".risk-card-label{min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;"
        "font-size:.73rem;font-weight:850;color:#64748b!important;}"
        ".risk-card-value{font-size:1.25rem;line-height:1;font-weight:950;color:#172033!important;}"
        ".risk-chip{display:inline-block;max-width:100%;padding:3px 6px;border-radius:999px;"
        "font-size:.64rem;line-height:1.15;font-weight:850;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}"
        ".risk-chip.good{background:#dcfce7;color:#166534!important;}"
        ".risk-chip.warn{background:#fef3c7;color:#92400e!important;}"
        ".risk-chip.bad{background:#fee2e2;color:#991b1b!important;}"
        "</style>"
        "<div class=\"risk-dashboard-title\">📊 <span>Rischi rosa</span></div>"
        "<div class=\"risk-grid\">"
        f"<div class=\"risk-card\"><div class=\"risk-card-head\">"
        f"<div class=\"risk-card-label\">🚨 Blocco club</div>"
        f"<div class=\"risk-card-value\">{risks['max_block']}</div></div>"
        f"<span class=\"risk-chip {block_tone}\">{block_status}</span></div>"
        f"<div class=\"risk-card\"><div class=\"risk-card-head\">"
        f"<div class=\"risk-card-label\">⚠️ Ballottaggi</div>"
        f"<div class=\"risk-card-value\">{risks['ballottaggio']}</div></div>"
        f"<span class=\"risk-chip {ballot_tone}\">{ballot_status}</span></div>"
        f"<div class=\"risk-card\"><div class=\"risk-card-head\">"
        f"<div class=\"risk-card-label\">🟨 Cartellini</div>"
        f"<div class=\"risk-card-value\">{risks['cartellini']}</div></div>"
        f"<span class=\"risk-chip {card_tone}\">{card_status}</span></div>"
        f"<div class=\"risk-card\"><div class=\"risk-card-head\">"
        f"<div class=\"risk-card-label\">👶 Rookie</div>"
        f"<div class=\"risk-card-value\">{risks['rookie']}</div></div>"
        f"<span class=\"risk-chip {rookie_tone}\">{rookie_status}</span></div>"
        "</div>"
    )
    st.sidebar.markdown(risk_html, unsafe_allow_html=True)


def build_smart_next_purchase_recommendation(
    state: AuctionState,
    rosters: list[dict[str, Any]],
    preferred_players: set[Any],
    role: str | None,
) -> dict[str, Any] | None:
    """
    Chooses ONE next purchase using roster structure before pure value.

    Priority:
    1. Complete a same-club/same-role ballot pair.
    2. Goalkeepers: after a keeper from a strong defence, prefer his reserve;
       otherwise prefer another strong starting keeper.
    3. In D/C/A, keep chasing strong options first.
    4. If budget is tight and starters already cover the role, allow a cheap
       same-club reserve to preserve credits for later premium slots.
    """
    if not role:
        return None

    team_name = get_my_team_name_from_state(state)
    if not team_name:
        return None

    owned = state.team_players_map.get(team_name, [])
    owned_role = [p for p in owned if p.get("role") == role]
    budget = int(st.session_state.get("my_team_budget") or 0)
    total_count = state.team_total_bought.get(team_name, 0)
    slots_after = max(0, TOTAL_SLOTS_PER_TEAM - total_count - 1)

    available = [
        p for p in load_players(role=role)
        if p.get("id") not in state.bought_player_ids
    ]
    if not available:
        return None

    custom_modifiers = load_custom_modifiers()
    goalkeeper_ranking = build_current_goalkeeper_ranking(state)

    def enrich(player: dict[str, Any], reason: str, priority: int) -> dict[str, Any]:
        details = calculate_player_rating_detailed(
            player,
            preferred_players,
            custom_modifiers,
            goalkeeper_ranking,
        )
        estimate = estimate_auction_price(
            player,
            rosters,
            budget=budget,
            slots_left_after_purchase=slots_after,
        )
        return {
            "player": player,
            "details": details,
            "estimate": estimate,
            "reason": reason,
            "priority": priority,
            "value": get_price_value_score(
                float(details["final_rating"]),
                int(estimate["estimated_price"]),
                int(player.get("list_price") or 1),
            ),
        }

    # 1) Complete a ballot pair before generic recommendations.
    ballot_keys = {
        _role_club_key(p)
        for p in owned_role
        if p.get("status_titolarita") == "Ballottaggio"
    }
    paired_candidates = [
        p for p in available
        if p.get("status_titolarita") == "Ballottaggio"
        and _role_club_key(p) in ballot_keys
    ]
    if paired_candidates:
        rows = [
            enrich(
                p,
                "Completa un ballottaggio che hai già in rosa: stessa squadra e stesso ruolo, quindi riduci il rischio di perdere il titolare.",
                100,
            )
            for p in paired_candidates
        ]
        rows.sort(
            key=lambda r: (
                r["details"]["final_rating"],
                r["value"],
                -r["estimate"]["estimated_price"],
            ),
            reverse=True,
        )
        return rows[0]

    # 2) Goalkeeper-specific strategy.
    if role == "P":
        goalkeeper_strategy = current_goalkeeper_strategy()
        credit_strategy = current_credit_strategy()

        # Quanto abbiamo già speso sui portieri.
        team_purchases = state.team_purchases_map.get(team_name, [])
        goalkeeper_spent = sum(
            int(purchase.get("purchase_price") or 0)
            for purchase in team_purchases
            if (purchase.get("players") or {}).get("role") == "P"
        )

        # Stima del budget iniziale della squadra: residuo corrente + speso totale.
        total_spent = sum(
            int(purchase.get("purchase_price") or 0)
            for purchase in team_purchases
        )
        estimated_initial_budget = max(budget + total_spent, budget)

        # Il tetto portieri segue direttamente il piano crediti selezionato.
        goalkeeper_total_cap = STRATEGY_BUDGET_ALLOCATIONS.get(
            credit_strategy,
            STRATEGY_BUDGET_ALLOCATIONS["Bilanciato"],
        )["P"]

        # Manteniamo intenzionalmente una quota ampia del capitale per C/A:
        # il consiglio portieri non deve "mangiare" la possibilità di competere
        # per i profili premium più avanti nell'asta.
        premium_future_reserve = int(
            round(budget * PREMIUM_C_A_RESERVE_SHARE)
        )

        if not owned_role:
            starters = [
                p for p in available
                if p.get("status_titolarita") in {"Titolare", "Ballottaggio"}
                and (
                    goalkeeper_strategy != "Tre titolari"
                    or p.get("team_nfl") not in THREE_STARTERS_EXCLUDED_TOP_CLUBS
                )
            ]

            # Fallback tecnico solo se i dati non contengono alcun titolare
            # compatibile: manteniamo comunque l'esclusione dei club TOP.
            if not starters and goalkeeper_strategy == "Tre titolari":
                starters = [
                    p for p in available
                    if p.get("team_nfl") not in THREE_STARTERS_EXCLUDED_TOP_CLUBS
                ]
            if not starters:
                starters = available

            rows = [
                enrich(
                    p,
                    (
                        "Primo portiere: nella strategia Tre titolari escludo i club TOP "
                        "e cerco il miglior titolare fra le squadre più economiche. "
                        if goalkeeper_strategy == "Tre titolari"
                        else "Primo portiere: cerca qualità, ma senza sovrainvestire. "
                        "Il reparto portieri deve lasciare la maggior parte del budget "
                        "disponibile per centrocampisti e attaccanti TOP."
                    ),
                    90,
                )
                for p in starters
            ]

            # Primo portiere: qualità prima, ma il value rompe i pareggi.
            rows.sort(
                key=lambda r: (
                    r["details"]["final_rating"],
                    r["value"],
                    -r["estimate"]["estimated_price"],
                ),
                reverse=True,
            )
            return rows[0]

        # ========================================================
        # TERZO PORTIERE: deve essere un acquisto di copertura.
        # Mai inseguire un altro TOP dopo aver già preso due P.
        # ========================================================
        if len(owned_role) >= 2:
            owned_clubs = {
                p.get("team_nfl")
                for p in owned_role
                if p.get("team_nfl")
            }

            if goalkeeper_strategy == "Tre titolari":
                # Strategia esplicita: anche il terzo deve giocare, ma mai da
                # un club TOP perché il costo vanificherebbe il senso della strategia.
                candidate_pool = [
                    p for p in available
                    if p.get("status_titolarita") in {"Titolare", "Ballottaggio"}
                    and p.get("team_nfl") not in owned_clubs
                    and p.get("team_nfl") not in THREE_STARTERS_EXCLUDED_TOP_CLUBS
                ] or [
                    p for p in available
                    if p.get("status_titolarita") in {"Titolare", "Ballottaggio"}
                    and p.get("team_nfl") not in THREE_STARTERS_EXCLUDED_TOP_CLUBS
                ] or [
                    p for p in available
                    if p.get("team_nfl") not in THREE_STARTERS_EXCLUDED_TOP_CLUBS
                ]
            else:
                # Strategia blocco: prima scelta una riserva dello stesso club.
                same_club_reserves = [
                    p for p in available
                    if p.get("status_titolarita") == "Riserva"
                    and p.get("team_nfl") in owned_clubs
                ]
                reserve_pool = same_club_reserves or [
                    p for p in available
                    if p.get("status_titolarita") == "Riserva"
                ]
                candidate_pool = reserve_pool or available

            rows = [
                enrich(
                    p,
                    (
                        "Terzo portiere: ora la priorità è la copertura a basso costo, "
                        "non aggiungere un altro TOP. Conserviamo crediti per poter "
                        "competere sui migliori centrocampisti e attaccanti."
                    ),
                    110,
                )
                for p in candidate_pool
            ]

            third_keeper_cap = max(
                2,
                min(
                    8,
                    int(round(budget * THIRD_GOALKEEPER_CURRENT_BUDGET_SHARE)),
                    max(2, goalkeeper_total_cap - goalkeeper_spent),
                ),
            )

            affordable = [
                r for r in rows
                if int(r["estimate"]["estimated_price"]) <= third_keeper_cap
            ]
            if affordable:
                rows = affordable

            # Riserva dello stesso club > costo basso > rating.
            rows.sort(
                key=lambda r: (
                    1 if r["player"].get("team_nfl") in owned_clubs else 0,
                    1 if r["player"].get("status_titolarita") == "Riserva" else 0,
                    -int(r["estimate"]["estimated_price"]),
                    r["details"]["final_rating"],
                ),
                reverse=True,
            )

            best = rows[0]
            best["reason"] = (
                f"Terzo portiere: spenderei poco (target circa ≤ {third_keeper_cap} cr). "
                f"Hai già due portieri: questo slot serve soprattutto come copertura. "
                f"Obiettivo strategico: lasciare almeno ~{premium_future_reserve} cr "
                "del budget attuale disponibili per costruire centrocampo e attacco."
            )
            return best

        # ========================================================
        # SECONDO PORTIERE
        # ========================================================
        first_keeper = max(
            owned_role,
            key=lambda p: calculate_player_rating(
                p,
                preferred_players,
                custom_modifiers,
                goalkeeper_ranking,
            ),
        )
        first_club = first_keeper.get("team_nfl")
        ga_values = list(GOALS_CONCEDED.values())
        ga_median = float(pd.Series(ga_values).median()) if ga_values else None
        first_ga = GOALS_CONCEDED.get(first_club)
        strong_defence = (
            first_ga is not None
            and ga_median is not None
            and first_ga <= ga_median
        )

        if strong_defence or goalkeeper_strategy == "Stessa Squadra":
            same_club_reserves = [
                p for p in available
                if p.get("team_nfl") == first_club
                and p.get("status_titolarita") == "Riserva"
            ]
            if same_club_reserves:
                rows = [
                    enrich(
                        p,
                        f"Hai già il portiere di {first_club}, una difesa sopra la media: "
                        "la sua riserva completa il blocco spendendo poco e protegge "
                        "il budget per i TOP di centrocampo e attacco.",
                        105,
                    )
                    for p in same_club_reserves
                ]
                rows.sort(
                    key=lambda r: (
                        -int(r["estimate"]["estimated_price"]),
                        r["details"]["final_rating"],
                    ),
                    reverse=True,
                )
                return rows[0]

        # Se il primo portiere non appartiene a una difesa di prima fascia,
        # cerchiamo un secondo TITOLARE, ma non un altro acquisto premium.
        other_starters = [
            p for p in available
            if p.get("status_titolarita") in {"Titolare", "Ballottaggio"}
            and p.get("team_nfl") not in {
                owned_player.get("team_nfl") for owned_player in owned_role
            }
            and (
                goalkeeper_strategy != "Tre titolari"
                or p.get("team_nfl") not in THREE_STARTERS_EXCLUDED_TOP_CLUBS
            )
        ]
        if other_starters:
            rows = [
                enrich(
                    p,
                    "Secondo portiere: aggiungi un altro titolare di una squadra diversa, "
                    "ma privilegiando rapporto qualità/prezzo. Due portieri TOP "
                    "assorbirebbero troppo budget rispetto al vantaggio ottenuto.",
                    90,
                )
                for p in other_starters
            ]

            second_keeper_cap = max(
                5,
                min(
                    20,
                    int(round(budget * SECOND_GOALKEEPER_CURRENT_BUDGET_SHARE)),
                    max(5, goalkeeper_total_cap - goalkeeper_spent),
                ),
            )

            non_premium = [
                r for r in rows
                if float(r["details"]["final_rating"]) < 9.0
                and int(r["estimate"]["estimated_price"]) <= second_keeper_cap
            ]
            affordable = [
                r for r in rows
                if int(r["estimate"]["estimated_price"]) <= second_keeper_cap
            ]

            if non_premium:
                rows = non_premium
            elif affordable:
                rows = affordable

            rows.sort(
                key=lambda r: (
                    r["value"],
                    r["details"]["final_rating"],
                    -int(r["estimate"]["estimated_price"]),
                ),
                reverse=True,
            )
            return rows[0]

    # 3/4) Movement roles.
    starters_owned = sum(
        p.get("status_titolarita") == "Titolare"
        for p in owned_role
    )
    role_limit = ROLE_LIMITS.get(role, 1)
    role_coverage_ratio = starters_owned / max(1, role_limit)
    credit_strategy = current_credit_strategy()

    slots_left = max(1, TOTAL_SLOTS_PER_TEAM - total_count)
    avg_budget_per_slot = budget / slots_left if budget else 0
    low_budget = budget > 0 and avg_budget_per_slot <= 4.0

    if low_budget and role_coverage_ratio >= 0.5:
        starter_keys = {
            _role_club_key(p)
            for p in owned_role
            if p.get("status_titolarita") == "Titolare"
        }
        cheap_covers = [
            p for p in available
            if p.get("status_titolarita") == "Riserva"
            and _role_club_key(p) in starter_keys
        ]
        if cheap_covers:
            rows = [
                enrich(
                    p,
                    "Budget stretto e ruolo già abbastanza coperto: questa riserva copre un tuo titolare a basso costo e conserva crediti per colpi più forti.",
                    80,
                )
                for p in cheap_covers
            ]
            rows.sort(
                key=lambda r: (
                    r["estimate"]["estimated_price"],
                    -r["details"]["final_rating"],
                )
            )
            return rows[0]

    # Default: quality first, then price/value. Never recommend below 6.5.
    rows = []
    for p in available:
        row = enrich(
            p,
            "Priorità alla qualità nel ruolo: tra i profili forti privilegio quello con il miglior equilibrio fra rating e costo stimato.",
            50,
        )
        if float(row["details"]["final_rating"]) >= 6.5:
            rows.append(row)

    if not rows:
        return None

    if credit_strategy == "Bonus" and role in {"C", "A"}:
        rows.sort(
            key=lambda r: (
                (
                    4 - int(r["player"].get("rigorista_ordine"))
                    if str(r["player"].get("rigorista_ordine") or "").isdigit()
                    and int(r["player"].get("rigorista_ordine")) in {1, 2, 3}
                    else 1 if r["player"].get("rigorista") else 0
                ),
                r["details"]["final_rating"],
                r["value"],
                -r["estimate"]["estimated_price"],
            ),
            reverse=True,
        )
    elif credit_strategy == "Modificatore Difesa" and role == "D":
        rows.sort(
            key=lambda r: (
                r["details"]["final_rating"],
                1 if r["player"].get("status_titolarita") == "Titolare" else 0,
                r["value"],
                -r["estimate"]["estimated_price"],
            ),
            reverse=True,
        )
    else:
        rows.sort(
            key=lambda r: (
                r["details"]["final_rating"],
                r["value"],
                -r["estimate"]["estimated_price"],
            ),
            reverse=True,
        )
    return rows[0]


def render_smart_next_purchase_card(
    state: AuctionState,
    rosters: list[dict[str, Any]],
    preferred_players: set[Any],
    role: str | None,
) -> None:
    recommendation = build_smart_next_purchase_recommendation(
        state,
        rosters,
        preferred_players,
        role,
    )
    if not recommendation:
        return

    player = recommendation["player"]
    details = recommendation["details"]
    estimate = recommendation["estimate"]
    reason = escape(str(recommendation["reason"]))
    name = escape(str(player.get("name") or "—"))
    club = escape(str(player.get("team_nfl") or "—"))
    status = escape(str(player.get("status_titolarita") or "—"))
    rating = float(details["final_rating"])

    html = (
        "<style>"
        ".next-buy-card{padding:13px 14px;border:1px solid #9fc2f4;border-radius:15px;"
        "background:radial-gradient(circle at 95% 5%,rgba(59,130,246,.14),transparent 32%),"
        "linear-gradient(145deg,#ffffff,#edf5ff);box-shadow:0 7px 20px rgba(30,64,175,.07);"
        "margin:.2rem 0 .85rem;}"
        ".next-buy-kicker{font-size:.68rem;font-weight:950;letter-spacing:.08em;color:#2563eb!important;}"
        ".next-buy-name{font-size:1.02rem;font-weight:950;color:#172033!important;margin:3px 0;}"
        ".next-buy-meta{font-size:.72rem;font-weight:750;color:#64748b!important;margin-bottom:7px;}"
        ".next-buy-reason{font-size:.74rem;line-height:1.35;color:#334155!important;}"
        "</style>"
        "<div class=\"next-buy-card\">"
        "<div class=\"next-buy-kicker\">🎯 PROSSIMO ACQUISTO CONSIGLIATO</div>"
        f"<div class=\"next-buy-name\">{name} · ⭐ {rating:.1f}</div>"
        f"<div class=\"next-buy-meta\">{club} · {status} · "
        f"Listino {int(player.get('list_price') or 0)} cr · "
        f"Stima {int(estimate['estimated_price'])} cr</div>"
        f"<div class=\"next-buy-reason\">{reason}</div>"
        "</div>"
    )
    st.sidebar.markdown(html, unsafe_allow_html=True)


# ============================================================
# TOP 5
# ============================================================

def render_top5(
    role: str,
    bought_player_ids: set[Any],
    preferred_players: set[Any],
    state: AuctionState | None = None,
) -> None:
    """Top 5 liberi in formato card compatte e leggibili nella sidebar."""
    st.sidebar.markdown(
        """
        <style>
        .top5-title {
            display:flex;
            align-items:center;
            gap:8px;
            margin:.15rem 0 .65rem 0;
            font-size:1.02rem;
            font-weight:900;
            color:#172033 !important;
        }
        .top5-stack {
            display:flex;
            flex-direction:column;
            gap:8px;
            margin-bottom:.65rem;
        }
        .top5-card {
            display:grid;
            grid-template-columns:38px minmax(0,1fr) auto;
            grid-template-areas:
                "rank name rating"
                "rank meta price";
            gap:2px 9px;
            align-items:center;
            padding:10px 11px;
            border:1px solid #cfe0f8;
            border-radius:13px;
            background:linear-gradient(145deg,#ffffff 0%,#f1f6ff 100%);
            box-shadow:0 4px 12px rgba(30,64,175,.055);
        }
        .top5-card:first-child {
            border-color:#93c5fd;
            background:
                radial-gradient(circle at 92% 5%,rgba(59,130,246,.13),transparent 30%),
                linear-gradient(145deg,#ffffff 0%,#edf5ff 100%);
        }
        .top5-rank {
            grid-area:rank;
            width:30px;
            height:30px;
            display:flex;
            align-items:center;
            justify-content:center;
            border-radius:9px;
            background:#1d4ed8;
            color:#ffffff !important;
            font-weight:900;
            font-size:.82rem;
        }
        .top5-name {
            grid-area:name;
            min-width:0;
            overflow:hidden;
            text-overflow:ellipsis;
            white-space:nowrap;
            font-weight:900;
            font-size:.90rem;
            color:#172033 !important;
        }
        .top5-meta {
            grid-area:meta;
            display:flex;
            align-items:center;
            gap:5px;
            min-width:0;
            font-size:.72rem;
            font-weight:750;
            color:#64748b !important;
        }
        .top5-role {
            display:inline-flex;
            align-items:center;
            justify-content:center;
            padding:1px 6px;
            border-radius:6px;
            background:#e8f0ff;
            color:#315a9e !important;
            font-weight:850;
        }
        .top5-tier {
            overflow:hidden;
            text-overflow:ellipsis;
            white-space:nowrap;
        }
        .top5-rating {
            grid-area:rating;
            white-space:nowrap;
            font-size:.92rem;
            font-weight:950;
            color:#b45309 !important;
        }
        .top5-price {
            grid-area:price;
            white-space:nowrap;
            font-size:.78rem;
            font-weight:850;
            color:#1d4ed8 !important;
        }
        .top5-pref {
            color:#f59e0b !important;
        }
        </style>
        <div class="top5-title">🔥 <span>Top 5 liberi</span></div>
        """,
        unsafe_allow_html=True,
    )

    players = load_players(role=role)
    available = [
        player for player in players
        if player["id"] not in bought_player_ids
    ]

    goalkeeper_ranking = (
        build_current_goalkeeper_ranking(state)
        if state
        else ALL_GOALKEEPER_RANKING
    )
    custom_modifiers = load_custom_modifiers()

    available.sort(
        key=lambda player: calculate_player_rating(
            player,
            preferred_players,
            custom_modifiers,
            goalkeeper_ranking,
        ),
        reverse=True,
    )

    if not available:
        st.sidebar.info("Nessun giocatore disponibile.")
        return

    cards = ['<div class="top5-stack">']

    for index, player in enumerate(available[:5], start=1):
        rating = calculate_player_rating(
            player,
            preferred_players,
            custom_modifiers,
            goalkeeper_ranking,
        )
        tier = get_roster_tier(rating)
        preferred = player["id"] in preferred_players

        player_name = escape(str(player.get("name") or "—"))
        player_role = escape(str(player.get("role") or "—"))
        player_team = escape(str(player.get("team_nfl") or "—"))
        list_price = int(player.get("list_price") or 0)
        pref_html = '<span class="top5-pref">★</span>' if preferred else ""

        card_html = (
            '<div class="top5-card">'
            f'<div class="top5-rank">{index}</div>'
            f'<div class="top5-name">{player_name} {pref_html}</div>'
            f'<div class="top5-rating">⭐ {rating:.1f}</div>'
            '<div class="top5-meta">'
            f'<span class="top5-role">{player_role}</span>'
            f'<span>{player_team}</span>'
            '<span>·</span>'
            f'<span class="top5-tier">{escape(tier)}</span>'
            '</div>'
            f'<div class="top5-price">💎 {list_price} cr</div>'
            '</div>'
        )
        cards.append(card_html)

    cards.append("</div>")
    st.sidebar.markdown("".join(cards), unsafe_allow_html=True)


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

    # Mockup più realistico:
    # i giocatori TOP non possono rimanere liberi mentre gli slot vengono
    # riempiti da profili peggiori. Ordiniamo quindi la simulazione per fascia:
    # TOP -> Prima -> Seconda -> Terza -> Scommesse.
    #
    # All'interno della stessa fascia manteniamo una componente casuale,
    # così simulazioni successive non producono sempre la stessa asta.
    custom_modifiers = load_custom_modifiers()

    def mockup_player_rating(player: dict[str, Any]) -> float:
        # Per i portieri usiamo il ranking generale delle difese:
        # durante il mockup non conosciamo ancora le tre squadre finali.
        return calculate_player_rating(
            player,
            st.session_state.preferred_players,
            custom_modifiers,
            ALL_GOALKEEPER_RANKING,
        )

    tier_priority = {
        "TOP": 0,
        "Prima Fascia": 1,
        "Seconda Fascia": 2,
        "Terza Fascia": 3,
        "Scommessa": 4,
    }

    # Generiamo prima un valore casuale così l'ordinamento è random
    # solo tra giocatori appartenenti alla stessa fascia.
    randomized_players = [
        (
            tier_priority[get_roster_tier(mockup_player_rating(player))],
            random.random(),
            -mockup_player_rating(player),
            player,
        )
        for player in free_players
    ]
    randomized_players.sort(
        key=lambda item: (item[0], item[1], item[2])
    )
    free_players = [item[3] for item in randomized_players]

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

        player_rating = mockup_player_rating(player)
        player_tier = get_roster_tier(player_rating)

        def team_score(team_name: str) -> float:
            slots_left = TOTAL_SLOTS_PER_TEAM - sim_bought[team_name]
            if slots_left <= 0:
                return -1

            budget_per_slot = sim_budgets[team_name] / slots_left

            # Per i TOP aggiungiamo un piccolo fattore casuale:
            # continuano a favorire chi ha più capacità di spesa, ma non
            # finiscono sistematicamente tutti alla stessa squadra.
            if player_tier == "TOP":
                return budget_per_slot * random.uniform(0.88, 1.12)

            return budget_per_slot * random.uniform(0.94, 1.06)

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
    user: dict[str, Any],
) -> None:
    """Strumenti distruttivi/mockup: disponibili esclusivamente agli admin."""
    if not _is_player_data_admin(user):
        st.warning("Strumenti amministrativi non disponibili per questo account.")
        return

    st.subheader("🛠️ Strumenti Mockup & Admin")

    role_filter = st.selectbox(
        "Completa ruolo (Mockup)",
        ["Tutti"] + list(ROLE_LIMITS),
        key="admin_autofill_role",
    )

    st.caption(
        "Nel mockup i TOP vengono assegnati prima delle fasce inferiori, "
        "così non restano irrealisticamente svincolati."
    )

    if st.button(
        "🎲 Autocompila rose (Intermedio)",
        key="admin_autofill_rosters",
    ):
        if perform_autofill(
            teams_df.to_dict("records"),
            state,
            role_filter,
        ):
            st.success("Rose autocompilate con successo!")
            invalidate_data_cache()
            st.rerun()
        else:
            st.warning("Nessun inserimento possibile o limiti già raggiunti.")

    if st.button(
        "🗑️ Svuota tutte le rose (Reset)",
        type="primary",
        key="admin_reset_rosters",
    ):
        st.session_state["confirm_reset"] = True

    if st.session_state.get("confirm_reset"):
        st.warning(
            "Questa operazione cancellerà tutti gli acquisti e "
            "ripristinerà i budget iniziali."
        )

        confirm_col, cancel_col = st.columns(2)

        with confirm_col:
            if st.button("Conferma reset", key="confirm_reset_button"):
                reset_auction(teams_df)
                st.session_state.pop("confirm_reset", None)
                invalidate_data_cache()
                st.rerun()

        with cancel_col:
            if st.button("Annulla", key="cancel_reset_button"):
                st.session_state.pop("confirm_reset", None)
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




def get_goalkeeper_purchase_alerts(
    selected_player: dict[str, Any],
    target_team: str,
    state: AuctionState,
) -> list[dict[str, str]]:
    """
    Alert strategici per i portieri.

    Regole:
    - Se il portiere selezionato è il secondo per listino nella sua squadra e
      il fantasy team non possiede il primo, segnala rischio panchina.
    - Se i primi due portieri della stessa squadra hanno entrambi listino > 10,
      trattiamo il caso come possibile ballottaggio e consigliamo di averli insieme.
    - Se la coppia è già completa, mostriamo conferma positiva.
    """
    if str(selected_player.get("role") or "").upper() != "P":
        return []

    club = str(selected_player.get("team_nfl") or "").strip().upper()
    if not club:
        return []

    club_goalkeepers = [
        p for p in load_players(role="P", team_nfl=club)
        if str(p.get("team_nfl") or "").strip().upper() == club
    ]
    club_goalkeepers.sort(
        key=lambda p: (
            int(p.get("list_price") or 0),
            float(calculate_player_rating_detailed(
                p,
                st.session_state.preferred_players,
                load_custom_modifiers(),
                build_current_goalkeeper_ranking(state),
            )["final_rating"]),
        ),
        reverse=True,
    )

    if not club_goalkeepers:
        return []

    owned_ids = {
        str((purchase.get("players") or {}).get("id"))
        for purchase in state.team_purchases_map.get(target_team, [])
        if (purchase.get("players") or {}).get("role") == "P"
    }

    selected_id = str(selected_player.get("id"))
    top = club_goalkeepers[0]
    second = club_goalkeepers[1] if len(club_goalkeepers) > 1 else None
    top_id = str(top.get("id"))
    second_id = str(second.get("id")) if second else None
    top_price = int(top.get("list_price") or 0)
    second_price = int(second.get("list_price") or 0) if second else 0

    alerts: list[dict[str, str]] = []

    # Caso classico: stai prendendo il secondo portiere senza il primo.
    if second and selected_id == second_id and top_id not in owned_ids:
        alerts.append({
            "level": "error",
            "title": "🚨 Secondo portiere senza il primo",
            "message": (
                f"{selected_player.get('name')} risulta il secondo portiere di {club} "
                f"per valore di listino ({second_price} cr contro {top_price} cr di "
                f"{top.get('name')}). Non comprarlo da solo se non hai già "
                f"{top.get('name')}: rischi di occupare uno slot con un panchinaro."
            ),
        })

    # Due portieri costosi della stessa squadra = possibile ballottaggio.
    if second and top_price > 10 and second_price > 10:
        pair_names = f"{top.get('name')} + {second.get('name')}"
        owns_top = top_id in owned_ids or selected_id == top_id
        owns_second = second_id in owned_ids or selected_id == second_id

        # Se selezionandolo completeresti la coppia, messaggio positivo.
        if owns_top and owns_second:
            alerts.append({
                "level": "success",
                "title": "✅ Coppia portieri completa",
                "message": (
                    f"{pair_names}: entrambi hanno listino superiore a 10 cr. "
                    "È un profilo da possibile ballottaggio, ma con entrambi in rosa "
                    "copri il rischio titolarità."
                ),
            })
        else:
            missing = second if owns_top else top
            alerts.append({
                "level": "warning",
                "title": "⚠️ Possibile ballottaggio in porta",
                "message": (
                    f"{pair_names} costano rispettivamente {top_price} e {second_price} cr: "
                    "quando due portieri della stessa squadra superano entrambi 10 cr, "
                    "li tratto come possibile ballottaggio. Se scegli questo portiere, "
                    f"pianifica di prendere anche {missing.get('name')}."
                ),
            })

    return alerts


def render_goalkeeper_purchase_alerts(
    selected_player: dict[str, Any],
    target_team: str,
    state: AuctionState,
) -> None:
    for alert in get_goalkeeper_purchase_alerts(selected_player, target_team, state):
        content = f"**{alert['title']}**  \n{alert['message']}"
        if alert["level"] == "error":
            st.error(content)
        elif alert["level"] == "warning":
            st.warning(content)
        elif alert["level"] == "success":
            st.success(content)
        else:
            st.info(content)



def _fantasy_team_owned_players(
    target_team: str,
    state: AuctionState,
) -> list[dict[str, Any]]:
    return [
        purchase.get("players") or {}
        for purchase in state.team_purchases_map.get(target_team, [])
        if purchase.get("players")
    ]


def _find_ballot_partner_players(
    player: dict[str, Any],
    all_players: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Risoluzione conservativa dei nomi in ballottaggio_con nella stessa squadra."""
    raw = str(player.get("ballottaggio_con") or "").strip()
    if not raw:
        return []

    team = str(player.get("team_nfl") or "").strip().upper()
    partner_tokens = [
        token.strip()
        for token in re.split(r"[,;/|]+", raw)
        if token.strip()
    ]

    result: list[dict[str, Any]] = []
    seen: set[str] = set()

    for token in partner_tokens:
        token_norm = normalize_string(token)
        candidates = [
            candidate
            for candidate in all_players
            if str(candidate.get("team_nfl") or "").strip().upper() == team
            and str(candidate.get("id")) != str(player.get("id"))
        ]

        exact = [
            candidate
            for candidate in candidates
            if normalize_string(str(candidate.get("name") or "")) == token_norm
        ]
        if exact:
            match = exact[0]
        else:
            ranked = sorted(
                candidates,
                key=lambda candidate: _name_similarity(
                    token,
                    str(candidate.get("name") or ""),
                ),
                reverse=True,
            )
            match = ranked[0] if ranked and _name_similarity(
                token,
                str(ranked[0].get("name") or ""),
            ) >= 0.78 else None

        if match is not None:
            key = str(match.get("id") or match.get("name"))
            if key not in seen:
                seen.add(key)
                result.append(match)

    return result


def render_ballot_and_penalty_alerts(
    selected_player: dict[str, Any],
    target_team: str,
    state: AuctionState,
) -> None:
    """
    Alert immediati nell'Asta.
    - Un giocatore in ballottaggio è sconsigliato da solo.
    - Se possiedi già il compagno di ballottaggio, la coppia è coperta.
    - Se il compagno è già stato preso da un'altra fantasquadra, alert critico.
    - Mostra anche la gerarchia rigoristi aggiornata.
    """
    # ---------- RIGORISTI ----------
    try:
        rig_order = (
            int(selected_player.get("rigorista_ordine"))
            if selected_player.get("rigorista_ordine") is not None
            else None
        )
    except (TypeError, ValueError):
        rig_order = None

    if rig_order == 1:
        st.success(
            "🎯 **Primo rigorista** — bonus importante: questa informazione "
            "entra anche nel rating e nella priorità della strategia Bonus."
        )
    elif rig_order == 2:
        st.info(
            "🎯 **Secondo rigorista** — valore aggiunto, ma con meno certezza "
            "rispetto alla prima scelta."
        )
    elif rig_order == 3:
        st.info(
            "🎯 **Terzo rigorista** — bonus potenziale marginale; non va valutato "
            "come un rigorista principale."
        )
    elif selected_player.get("rigorista"):
        st.info(
            "🎯 **Rigorista segnalato**, ma senza ordine affidabile nella gerarchia."
        )

    # ---------- BALLOTTAGGI ----------
    raw_ballot = str(selected_player.get("ballottaggio_con") or "").strip()
    is_ballot = (
        str(selected_player.get("status_titolarita") or "").strip() == "Ballottaggio"
        or bool(raw_ballot)
    )
    if not is_ballot:
        return

    all_players = load_players()
    partners = _find_ballot_partner_players(selected_player, all_players)
    owned = _fantasy_team_owned_players(target_team, state)
    owned_ids = {str(player.get("id")) for player in owned if player.get("id") is not None}

    if partners:
        partner_names = ", ".join(
            str(partner.get("name") or "")
            for partner in partners
        )
        owned_partners = [
            partner for partner in partners
            if str(partner.get("id")) in owned_ids
        ]

        if owned_partners:
            covered_names = ", ".join(
                str(partner.get("name") or "")
                for partner in owned_partners
            )
            st.success(
                f"✅ **Ballottaggio coperto** — {selected_player.get('name')} è in "
                f"ballottaggio con **{partner_names}** e {target_team} possiede già "
                f"**{covered_names}**. La coppia riduce il rischio di restare senza titolare."
            )
            return

        # Capire se il/i compagno/i sono ancora liberi oppure già di un'altra fantasquadra.
        roster_owner_by_id: dict[str, str] = {}
        for fantasy_team, purchases in state.team_purchases_map.items():
            for purchase in purchases:
                p = purchase.get("players") or {}
                if p.get("id") is not None:
                    roster_owner_by_id[str(p.get("id"))] = fantasy_team

        unavailable = [
            partner
            for partner in partners
            if str(partner.get("id")) in roster_owner_by_id
            and roster_owner_by_id[str(partner.get("id"))] != target_team
        ]

        if len(unavailable) == len(partners):
            owners = ", ".join(
                f"{partner.get('name')} → {roster_owner_by_id.get(str(partner.get('id')))}"
                for partner in unavailable
            )
            st.error(
                f"🚨 **Ballottaggio non copribile: sconsigliato.** "
                f"{selected_player.get('name')} è in ballottaggio con **{partner_names}**, "
                f"ma il/i compagno/i risultano già acquistati ({owners}). "
                "Rischi di spendere uno slot per un possibile panchinaro senza poter completare la coppia."
            )
        else:
            st.warning(
                f"⚠️ **Ballottaggio: sconsigliato singolarmente.** "
                f"{selected_player.get('name')} è in ballottaggio con **{partner_names}**. "
                f"Compralo solo se {target_team} ha già il compagno oppure se prevedi "
                "di acquistare anche l'altro giocatore della coppia."
            )
    else:
        partner_text = f" con **{raw_ballot}**" if raw_ballot else ""
        st.warning(
            f"⚠️ **Giocatore in ballottaggio: sconsigliato singolarmente.** "
            f"{selected_player.get('name')} risulta in ballottaggio{partner_text}. "
            "Prima di acquistarlo assicurati di poter coprire lo stesso slot."
        )


def render_manual_purchase(
    teams_df: pd.DataFrame,
    state: AuctionState,
    current_role: str,
    rosters: list[dict[str, Any]],
) -> str:
    """Renderizza il pannello di acquisto manuale in una griglia allineata."""
    if is_auction_finished(state):
        return current_role

    # Fonte unica dell'Asta: public.players.
    # Le note strategiche non possono sovrascrivere nome/squadra/ruolo qui.
    players_for_filter = load_players()

    available_nfl_teams = sorted(
        {
            player["team_nfl"]
            for player in players_for_filter
            if player.get("team_nfl")
        }
    )

    # Tutti i controlli restano sulla stessa riga: evita lo sfalsamento
    # causato da colonne vuote usate come spaziatori.
    col1, col2, col3, col4, col5 = st.columns(
        [1.25, 1.45, 2.8, 1.0, 1.55],
        gap="small",
    )

    with col1:
        my_team_name = get_my_team_name_from_state(state)
        my_counts = state.team_role_totals.get(my_team_name or "", {})
        role_options = {
            label: role
            for label, role in ROLE_LABELS.items()
            if role == "ALL"
            or my_counts.get(role, 0) < ROLE_LIMITS[role]
        }
        role_labels = list(role_options)
        current_label = next(
            (label for label, role in role_options.items() if role == current_role),
            role_labels[0],
        )
        selected_role_label = st.selectbox(
            "1. Seleziona Ruolo",
            role_labels,
            index=role_labels.index(current_label),
            key="main_role_select",
        )
        current_role = role_options[selected_role_label]

    with col2:
        nfl_filter_label = st.selectbox(
            "2. Filtra per Squadra Serie A",
            ["Tutte le squadre"] + available_nfl_teams,
            key="manual_nfl_filter",
        )
        team_filter = (
            "ALL"
            if nfl_filter_label == "Tutte le squadre"
            else nfl_filter_label
        )

    players = load_players(role=current_role, team_nfl=team_filter)
    available_players = [
        player
        for player in players
        if player["id"] not in state.bought_player_ids
    ]

    if not available_players:
        st.warning("Nessun giocatore disponibile trovato con questi filtri.")
        return current_role

    player_options = {
        (
            f"{player['name']} [{player['role']}] "
            f"({player['team_nfl']} - {int(player.get('list_price') or 0)} cr. - "
            f"{calculate_player_rating_detailed(player, st.session_state.preferred_players, load_custom_modifiers(), build_current_goalkeeper_ranking(state))['final_rating']:.1f})"
        ): player
        for player in available_players
    }

    with col3:
        selected_label = st.selectbox(
            "3. Seleziona Giocatore",
            list(player_options),
            key="manual_player_select",
        )
        selected_player = player_options[selected_label]

    with col4:
        default_price = max(1, int(selected_player.get("list_price") or 1))
        purchase_price = st.number_input(
            "4. Costo",
            min_value=1,
            max_value=500,
            value=default_price,
            step=1,
            key="manual_purchase_price",
        )

    with col5:
        role = selected_player["role"]
        active_teams = [
            team_name
            for team_name in teams_df["name"].tolist()
            if (
                state.team_total_bought[team_name] < TOTAL_SLOTS_PER_TEAM
                and state.team_role_totals[team_name][role] < ROLE_LIMITS[role]
            )
        ]
        team_names = active_teams or teams_df["name"].tolist()

        target_team = st.selectbox(
            "5. Squadra Acquirente",
            team_names,
            index=default_team_index(team_names, get_current_user_team_name()),
            key="manual_target_team",
        )

    # Valutazione immediata del giocatore selezionato.
    current_custom = load_custom_modifiers()
    goalkeeper_ranking = build_current_goalkeeper_ranking(state)
    player_details = calculate_player_rating_detailed(
        selected_player,
        st.session_state.preferred_players,
        current_custom,
        goalkeeper_ranking,
    )
    estimate = estimate_auction_price(
        selected_player,
        rosters,
        budget=st.session_state.get("my_team_budget"),
        slots_left_after_purchase=max(
            0,
            TOTAL_SLOTS_PER_TEAM
            - state.team_total_bought.get(get_my_team_name_from_state(state) or "", 0)
            - 1,
        ),
    )

    # Alert immediati sui portieri, riferiti alla squadra acquirente selezionata.
    render_goalkeeper_purchase_alerts(selected_player, target_team, state)

    # Ballottaggi e rigoristi provengono dal dataset Fantacalcio aggiornato:
    # sono alert visibili prima di confermare qualsiasi acquisto.
    render_ballot_and_penalty_alerts(selected_player, target_team, state)

    spend_focus = get_player_budget_spend_focus(selected_player, estimate)
    render_player_spend_focus_card(spend_focus)

    if not st.button(
        "Conferma Acquisto",
        type="primary",
        key="confirm_manual_purchase",
    ):
        return current_role

    success, error = execute_purchase(
        teams_df,
        state,
        selected_player,
        int(purchase_price),
        target_team,
    )

    if not success:
        st.error(error)
        return current_role

    rating = player_details["final_rating"]

    # IMPORTANTE: st.rerun() interrompe immediatamente l'esecuzione del run.
    # Per questo il banner deve essere salvato in session_state PRIMA del rerun.
    if is_my_team(target_team):
        queue_purchase_banner(
            target_team,
            selected_player["name"],
            rating,
            int(purchase_price),
        )
    else:
        st.session_state.pop("pending_purchase_banner", None)

    invalidate_data_cache()
    st.rerun()
    return current_role


# ============================================================ SQUADRE
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
        for player in get_uncovered_ballot_players(players)
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
    """Panoramica lega compatta: snapshot, classifica e dettagli solo su richiesta."""
    st.markdown('<div class="rcd-section">📊 Panoramica Squadre & Alert Strategici</div>', unsafe_allow_html=True)

    if teams_df.empty:
        st.info("Nessuna squadra configurata.")
        return

    grades_df = calculate_auction_grades(
        teams_df.to_dict("records"),
        state,
        ratings,
    )
    auction_grade_map = {
        row["Squadra"]: float(row["Voto Asta"])
        for _, row in grades_df.iterrows()
    }

    rows = []
    alerts_by_team: dict[str, list[dict[str, str]]] = {}

    for _, team in teams_df.iterrows():
        name = team["name"]
        players = state.team_players_map.get(name, [])
        purchases = state.team_purchases_map.get(name, [])
        bought = state.team_total_bought.get(name, 0)
        budget = int(team["remaining_budget"])
        spent = sum(int(p.get("purchase_price") or 0) for p in purchases)
        total_listino = sum(int(p.get("list_price") or 0) for p in players)
        multiplier = round(spent / total_listino, 2) if total_listino else 0.0
        alerts = build_team_alerts(players, bought)
        alerts_by_team[name] = alerts

        # TOP basati sul rating effettivo, non sul solo listino.
        player_ratings = [
            calculate_player_rating(
                p,
                st.session_state.preferred_players,
                load_custom_modifiers(),
                build_current_goalkeeper_ranking(state),
            )
            for p in players
        ]
        top_count = sum(r >= 9.0 for r in player_ratings)

        roles = state.team_role_totals.get(name, {})
        rows.append({
            "Squadra": name,
            "Rating": round(ratings.get(name, 0.0), 1),
            "Voto Asta": round(auction_grade_map.get(name, 0.0), 1),
            "Budget": budget,
            "Rosa": f"{bought}/{TOTAL_SLOTS_PER_TEAM}",
            "P": f"{roles.get('P',0)}/{ROLE_LIMITS['P']}",
            "D": f"{roles.get('D',0)}/{ROLE_LIMITS['D']}",
            "C": f"{roles.get('C',0)}/{ROLE_LIMITS['C']}",
            "A": f"{roles.get('A',0)}/{ROLE_LIMITS['A']}",
            "TOP": top_count,
            "x Listino": multiplier,
            "Alert": len(alerts),
        })

    league_df = pd.DataFrame(rows).sort_values(
        ["Voto Asta", "Rating"],
        ascending=False,
    ).reset_index(drop=True)
    league_df.index += 1

    # Snapshot: solo quattro informazioni veramente utili.
    best_rating = max(rows, key=lambda r: r["Rating"]) if rows else None
    best_auction = max(rows, key=lambda r: r["Voto Asta"]) if rows else None
    richest = max(rows, key=lambda r: r["Budget"]) if rows else None
    completed = sum(
        state.team_total_bought.get(name, 0) >= TOTAL_SLOTS_PER_TEAM
        for name in teams_df["name"].tolist()
    )

    st.markdown('<div id="league-overview-metrics"></div>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(
        "⭐ Miglior rosa",
        best_rating["Squadra"] if best_rating else "—",
        f"{best_rating['Rating']:.1f}" if best_rating else None,
        delta_color="off",
    )
    c2.metric(
        "🏆 Miglior asta",
        best_auction["Squadra"] if best_auction else "—",
        f"{best_auction['Voto Asta']:.1f}" if best_auction else None,
        delta_color="off",
    )
    c3.metric(
        "💰 Più crediti",
        richest["Squadra"] if richest else "—",
        f"{richest['Budget']} cr" if richest else None,
        delta_color="off",
    )
    c4.metric("✅ Rose complete", f"{completed}/{len(rows)}")

    st.markdown('<div class="rcd-section">🏁 Classifica live</div>', unsafe_allow_html=True)
    st.dataframe(
        league_df,
        use_container_width=True,
        column_config={
            "Rating": st.column_config.NumberColumn(format="%.1f"),
            "Voto Asta": st.column_config.NumberColumn(format="%.1f"),
            "Budget": st.column_config.NumberColumn(format="%d cr"),
            "x Listino": st.column_config.NumberColumn(format="x%.2f"),
            "TOP": st.column_config.NumberColumn(format="%d"),
            "Alert": st.column_config.NumberColumn(format="%d"),
        },
    )

    # I dettagli/alert non occupano più tutta la pagina.
    st.markdown('<div class="rcd-section">🚨 Dettagli e alert</div>', unsafe_allow_html=True)
    st.caption("Apri solo la squadra che vuoi analizzare.")

    ordered_names = league_df["Squadra"].tolist()
    for name in ordered_names:
        row = next(r for r in rows if r["Squadra"] == name)
        alert_count = row["Alert"]
        label = (
            f"{name} · ⭐ {row['Rating']:.1f} · 🏆 {row['Voto Asta']:.1f} · "
            f"💰 {row['Budget']} cr · 🚨 {alert_count}"
        )
        with st.expander(label, expanded=False):
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Rating", f"{row['Rating']:.1f}")
            m2.metric("Voto Asta", f"{row['Voto Asta']:.1f}")
            m3.metric("TOP", row["TOP"])
            m4.metric("Moltiplicatore", f"x{row['x Listino']:.2f}")

            st.markdown(
                f"**Composizione:** P {row['P']} · D {row['D']} · "
                f"C {row['C']} · A {row['A']} · Rosa {row['Rosa']}"
            )

            alerts = alerts_by_team.get(name, [])
            if not alerts:
                st.success("Nessuna criticità strategica rilevante.")
            else:
                for alert in alerts:
                    st.warning(alert["text"], icon="⚠️")
                    if alert.get("help"):
                        st.caption(alert["help"])


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
                "Moltiplicatore Asta": round(
                    float(roster.get("purchase_price", 0)) / float(list_price)
                    if float(list_price) > 0 else 0.0,
                    2,
                ),
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


def calculate_market_efficiency(
    purchases: list[dict[str, Any]],
    all_rosters: list[dict[str, Any]],
) -> tuple[float, float]:
    """
    Confronta quanto una squadra ha pagato rispetto al mercato reale dell'asta.

    Ritorna:
    - bonus/malus economico [-1.0, +1.0]
    - moltiplicatore medio pagato dalla squadra

    Il confronto usa il moltiplicatore mediano osservato nell'asta, non
    'listino - prezzo pagato', che in un fanta a 12 penalizzerebbe quasi tutti.
    """
    market_ratios = []
    for roster in all_rosters:
        player = roster.get("players") or {}
        list_price = float(player.get("list_price") or 0)
        paid = float(roster.get("purchase_price") or 0)
        if list_price > 0 and paid > 0:
            market_ratios.append(paid / list_price)

    market_multiplier = (
        float(pd.Series(market_ratios).median())
        if market_ratios
        else DEFAULT_AUCTION_MULTIPLIER
    )

    team_ratios = []
    for purchase in purchases:
        player = purchase.get("players") or {}
        list_price = float(player.get("list_price") or 0)
        paid = float(purchase.get("purchase_price") or 0)
        if list_price > 0 and paid > 0:
            team_ratios.append(paid / list_price)

    if not team_ratios:
        return 0.0, 0.0

    team_multiplier = sum(team_ratios) / len(team_ratios)

    # Se paghi meno del mercato hai bonus; se paghi più del mercato hai malus.
    relative = market_multiplier / max(team_multiplier, 0.01)
    economic_bonus = (relative - 1.0) * 2.5
    economic_bonus = max(-1.0, min(1.0, economic_bonus))

    return round(economic_bonus, 2), round(team_multiplier, 2)


def calibrate_team_grade(raw_grade: float) -> float:
    """
    Rimappa linearmente il voto finale per allargare la scala utile.

    4.5 -> 5.5
    6.7 -> 8.0

    La stessa pendenza viene mantenuta anche fuori dall'intervallo,
    con clamp finale 4.0-9.8.
    """
    x1 = TEAM_GRADE_CALIBRATION_X1
    y1 = TEAM_GRADE_CALIBRATION_Y1
    x2 = TEAM_GRADE_CALIBRATION_X2
    y2 = TEAM_GRADE_CALIBRATION_Y2

    slope = (y2 - y1) / (x2 - x1)
    calibrated = y1 + (raw_grade - x1) * slope

    return round(max(4.0, min(9.8, calibrated)), 1)


def calculate_auction_grades(
    teams: list[dict[str, Any]],
    state: AuctionState,
    ratings: dict[str, float],
) -> pd.DataFrame:
    grades = []

    all_rosters = [
        purchase
        for purchases in state.team_purchases_map.values()
        for purchase in purchases
    ]

    for team in teams:
        name = team["name"]
        players = state.team_players_map[name]
        purchases = state.team_purchases_map[name]

        if not players:
            grades.append(
                {
                    "Squadra": name,
                    "Voto Asta": 0.0,
                    "Rating Rosa": 0.0,
                    "TOP (>=9)": 0,
                    "Moltiplicatore Pagato": 0.0,
                    "Efficienza Mercato": 0.0,
                    "Criticità Rilevate": 0,
                }
            )
            continue

        player_scores = [
            calculate_player_rating(
                player,
                st.session_state.preferred_players,
                load_custom_modifiers(),
                build_current_goalkeeper_ranking(state),
            )
            for player in players
        ]

        top_count = sum(score >= 9.0 for score in player_scores)

        alerts = build_team_alerts(players, len(players))
        criticality = len(alerts)

        economic_bonus, team_multiplier = calculate_market_efficiency(
            purchases,
            all_rosters,
        )

        # Il cuore del voto è la qualità della rosa.
        # L'economia può spostare il voto, ma non schiacciare tutte le squadre.
        quality = ratings[name]

        # Un numero elevato di TOP ha un ulteriore piccolo premio nel voto asta.
        top_bonus = min(0.50, top_count * 0.07)

        # Criticità strategiche restano rilevanti, ma non dominanti.
        risk_penalty = min(0.80, criticality * 0.18)

        grade = (
            quality * 0.88
            + economic_bonus * 0.65
            + top_bonus
            - risk_penalty
        )

        # Calibrazione finale più leggibile:
        # circa 4.5 -> 5.5 e 6.7 -> 8.0.
        grade = calibrate_team_grade(grade)

        grades.append(
            {
                "Squadra": name,
                "Voto Asta": grade,
                "Rating Rosa": round(quality, 1),
                "TOP (>=9)": top_count,
                "Moltiplicatore Pagato": team_multiplier,
                "Efficienza Mercato": economic_bonus,
                "Criticità Rilevate": criticality,
            }
        )

    result = (
        pd.DataFrame(grades)
        .sort_values("Voto Asta", ascending=False)
        .reset_index(drop=True)
    )
    result.index = range(1, len(result) + 1)
    result.index.name = "Posizione"
    return result


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
            "Moltiplicatore Asta": st.column_config.NumberColumn(
                "Moltiplicatore Asta",
                format="x%.2f",
            ),
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
        "Il voto dell'asta privilegia la **qualità reale della rosa**: "
        "i giocatori TOP pesano più degli altri. La gestione economica viene "
        "valutata rispetto ai prezzi realmente osservati nell'asta, mentre "
        "le criticità strategiche applicano penalità moderate. La scala finale "
        "è calibrata per rendere più leggibili le differenze tra rose forti e deboli."
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
        "modificatore squadra, rigoristi, rischio cartellini, rookie e preferiti. "
        "Per i portieri, il modificatore difensivo è sostituito dal criterio "
        "gol subiti: 1ª squadra +1.0, 2ª 0.0, 3ª -1.0."
    )

    all_players = load_players()
    custom_modifiers = load_custom_modifiers()
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
            custom_modifiers,
            ALL_GOALKEEPER_RANKING,
        )
        rows.append(
            {
                "⭐ Preferito": player["id"] in st.session_state.preferred_players,
                "Giocatore": player.get("name", ""),
                "Ruolo": player.get("role", ""),
                "Rating ⭐️": details["final_rating"],
                "Moltiplicatore ruolo": details.get("role_multiplier", 1.0),
                "Rating pre-calibrazione": details.get("raw_rating", details["final_rating"]),
                "Base/Fantamedia": details["base"],
                "Mod Squadra": details["team_mod"],
                "Mod. Portiere": details.get("goalkeeper_mod", 0.0),
                "Pos. Difesa": details.get("goalkeeper_rank"),
                "Titolarità": details["tit"],
                "Rigorista": details["rig"],
                "Cartellini": details["cart"],
                "Rookie": details["rook"],
                "Bonus/Malus manuale": details["custom_label"],
                "Mod. manuale": details["custom_mod"],
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
            "Moltiplicatore ruolo": st.column_config.NumberColumn(
                "Moltiplicatore ruolo",
                format="x%.3f",
            ),
            "Rating pre-calibrazione": st.column_config.NumberColumn(
                "Rating pre-calibrazione",
                format="%.1f",
            ),
            "Mod. manuale": st.column_config.NumberColumn(
                "Mod. manuale",
                format="%+.1f",
            ),
        },
    )


# ============================================================
# TAB 4 — GESTIONE BONUS / MALUS
# ============================================================

def render_player_modifiers_tab() -> None:
    st.subheader("🛠️ Gestione Bonus / Malus Giocatori")
    st.caption(
        "Le modifiche inserite qui vengono salvate in Supabase e "
        "si sommano al rating calcolato automaticamente. "
        "Il reset elimina solo la modifica manuale, senza toccare i dati originali del giocatore."
    )

    all_players = load_players()
    if not all_players:
        st.info("Nessun giocatore trovato nel database.")
        return

    modifiers = load_custom_modifiers()

    rows = []
    for player in all_players:
        current = modifiers.get(player["id"], {})
        rows.append(
            {
                "_player_id": player["id"],
                "Giocatore": player.get("name", ""),
                "Ruolo": player.get("role", ""),
                "Club": player.get("team_nfl", ""),
                "Modifica attuale": current.get(
                    "modifier_label",
                    "Nessuna modifica",
                ),
                "Valore": float(current.get("modifier_value") or 0.0),
            }
        )

    df = pd.DataFrame(rows)

    c1, c2, c3 = st.columns(3)
    with c1:
        role_filter = st.selectbox(
            "Ruolo",
            ["Tutti", "P", "D", "C", "A"],
            key="tab4_role_filter",
        )
    with c2:
        modifier_filter = st.selectbox(
            "Stato modifica",
            ["Tutti", "Con bonus/malus", "Senza modifica"],
            key="tab4_modifier_filter",
        )
    with c3:
        search = st.text_input(
            "Cerca giocatore",
            key="tab4_search",
        )

    filtered = df.copy()

    if role_filter != "Tutti":
        filtered = filtered[filtered["Ruolo"] == role_filter]

    if modifier_filter == "Con bonus/malus":
        filtered = filtered[filtered["Valore"] != 0]
    elif modifier_filter == "Senza modifica":
        filtered = filtered[filtered["Valore"] == 0]

    if search:
        filtered = filtered[
            filtered["Giocatore"].astype(str).str.contains(
                re.escape(search),
                case=False,
                na=False,
                regex=True,
            )
        ]

    st.markdown("### Modifica singolo giocatore")

    if filtered.empty:
        st.info("Nessun giocatore corrisponde ai filtri.")
        return

    player_labels = {
        f"{row['Giocatore']} [{row['Ruolo']}] — {row['Club']}": row["_player_id"]
        for _, row in filtered.iterrows()
    }

    selected_label = st.selectbox(
        "Giocatore",
        list(player_labels),
        key="tab4_selected_player",
    )
    selected_id = player_labels[selected_label]

    current = modifiers.get(selected_id, {})
    current_label = current.get(
        "modifier_label",
        "Nessuna modifica",
    )

    modifier_options = list(CUSTOM_MODIFIERS)
    current_index = (
        modifier_options.index(current_label)
        if current_label in modifier_options
        else 0
    )

    selected_modifier = st.selectbox(
        "Bonus / Malus",
        modifier_options,
        index=current_index,
        key=f"tab4_modifier_{selected_id}",
        help=(
            "La modifica viene aggiunta al rating. "
            "Esempio: se Audero è indicato come Titolare ma tu ritieni "
            "che sia in ballottaggio, seleziona 'Ballottaggio (-0.3)'."
        ),
    )

    player = next(
        player for player in all_players
        if player["id"] == selected_id
    )

    base_details = calculate_player_rating_detailed(
        player,
        st.session_state.preferred_players,
        modifiers,
    )
    new_value = CUSTOM_MODIFIERS[selected_modifier]["value"]
    current_rating = base_details["final_rating"]
    # Il rating attuale include già la modifica esistente.
    rating_without_current_custom = current_rating - float(
        current.get("modifier_value") or 0.0
    )
    preview_rating = round(
        max(
            1.0,
            min(10.0, rating_without_current_custom + new_value),
        ),
        1,
    )

    p1, p2, p3 = st.columns(3)
    with p1:
        st.metric("Rating senza modifica manuale", f"{rating_without_current_custom:.1f}")
    with p2:
        st.metric("Modifica scelta", f"{new_value:+.1f}")
    with p3:
        st.metric("Rating finale previsto", f"{preview_rating:.1f}")

    b1, b2 = st.columns(2)

    with b1:
        if st.button(
            "💾 Salva bonus/malus",
            type="primary",
            use_container_width=True,
        ):
            ok, error = save_custom_modifier(
                selected_id,
                selected_modifier,
            )
            if ok:
                st.success(
                    f"Modifica salvata per **{player['name']}**."
                )
                invalidate_data_cache()
                st.rerun()
            else:
                st.error(
                    "Impossibile salvare la modifica. "
                    "Controlla che la tabella Supabase "
                    f"`{CUSTOM_MODIFIER_TABLE}` esista.\n\n{error}"
                )

    with b2:
        if st.button(
            "♻️ Reset modifica giocatore",
            use_container_width=True,
        ):
            ok, error = reset_custom_modifier(selected_id)
            if ok:
                st.success(
                    f"Modifica rimossa da **{player['name']}**."
                )
                invalidate_data_cache()
                st.rerun()
            else:
                st.error(f"Impossibile effettuare il reset: {error}")

    st.divider()
    st.markdown("### 📋 Modifiche attualmente salvate")

    active = df[df["Valore"] != 0].copy()
    if active.empty:
        st.info("Nessun bonus/malus personalizzato salvato.")
    else:
        st.dataframe(
            active.drop(columns=["_player_id"]),
            use_container_width=True,
            hide_index=True,
            column_config={
                "Valore": st.column_config.NumberColumn(
                    "Valore",
                    format="%+.1f",
                ),
            },
        )

    with st.expander("⚠️ Reset di tutte le modifiche manuali"):
        st.warning(
            "Cancella tutti i bonus/malus personalizzati della tabella. "
            "Non modifica i dati originali dei giocatori."
        )
        if st.button(
            "🗑️ Cancella TUTTI i bonus/malus",
            type="secondary",
            key="tab4_reset_all",
        ):
            try:
                saved = (
                    supabase.table(CUSTOM_MODIFIER_TABLE)
                    .select("player_id")
                    .execute()
                    .data
                )
                for row in saved:
                    (
                        supabase.table(CUSTOM_MODIFIER_TABLE)
                        .delete()
                        .eq("player_id", row["player_id"])
                        .execute()
                    )
                invalidate_data_cache()
                st.success("Tutte le modifiche manuali sono state cancellate.")
                st.rerun()
            except Exception as exc:
                st.error(
                    f"Reset globale non riuscito: {exc}"
                )


def render_auction_dashboard_header(
    teams_df: pd.DataFrame,
    state: AuctionState,
    ratings: dict[str, float],
) -> None:
    """Hero compatto: identità, fase, budget, slot e rating."""
    team_name = get_my_team_name_from_state(state)
    if team_name is None:
        return

    team_row = teams_df[teams_df["name"] == team_name]
    remaining = int(team_row.iloc[0]["remaining_budget"]) if not team_row.empty else 0
    bought = state.team_total_bought.get(team_name, 0)
    rating = ratings.get(team_name, 0.0)
    draft_role = get_my_team_draft_role(state)
    complete = bought >= TOTAL_SLOTS_PER_TEAM

    phase = (
        "ASTA COMPLETATA"
        if complete
        else f"FASE: {ROLE_NAMES.get(draft_role, 'Asta').upper()}"
    )

    st.markdown(
        f"""
        <div class="rcd-hero">
          <div class="rcd-kicker">fantahe1per</div>
          <div class="rcd-hero-title">⚽ Live Auction Dashboard</div>
          <div class="rcd-phase">{phase}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("💰 Budget", f"{remaining} cr")
    c2.metric("👥 Rosa", f"{bought}/{TOTAL_SLOTS_PER_TEAM}")
    c3.metric("⭐ Rating Rosa", f"{rating:.1f}")
    c4.metric("🎯 Prossimo ruolo", "—" if complete else ROLE_NAMES.get(draft_role, "—"))


# ============================================================
# TAB 1 — VALUTAZIONE E ROSA DELLA SQUADRA ASSOCIATA
# ============================================================

def render_my_team_evaluation(
    teams_df: pd.DataFrame,
    state: AuctionState,
    ratings: dict[str, float],
    rosters: list[dict[str, Any]],
) -> None:
    """Valuta squadra associata in modo progressivo seguendo il draft PDCA."""
    team_name, players, purchases = get_my_team_players_and_purchases(state)
    if team_name is None or not players:
        # A rosa vuota non mostriamo valutazioni generiche: l'utente ha chiesto
        # che la strategia inizi dal primo acquisto dei portieri.
        return

    team_row = teams_df[teams_df["name"] == team_name]
    bought = len(players)
    remaining = int(team_row.iloc[0]["remaining_budget"]) if not team_row.empty else 0
    initial = int(team_row.iloc[0]["initial_budget"]) if not team_row.empty else 0
    spent = sum(int(p.get("purchase_price") or 0) for p in purchases)
    listino = sum(int((p.get("players") or {}).get("list_price") or 1) for p in purchases)
    slots_left = max(0, TOTAL_SLOTS_PER_TEAM - bought)
    rating = ratings.get(team_name, 0.0)
    counts = state.team_role_totals.get(team_name, {})
    roster_complete = (
        bought >= TOTAL_SLOTS_PER_TEAM
        or state.team_total_bought.get(team_name, 0) >= TOTAL_SLOTS_PER_TEAM
    )
    current_role = None if roster_complete else get_my_team_draft_role(state)

    grades = calculate_auction_grades(
        teams_df.to_dict("records"),
        state,
        ratings,
    )
    grade_row = grades[grades["Squadra"] == team_name]
    auction_grade = float(grade_row.iloc[0]["Voto Asta"]) if not grade_row.empty else 0.0

    phase, assessment, advice = build_draft_strategy_text(
        state,
        rosters,
        teams_df,
        ratings,
    )

    st.markdown(
        '<div class="rcd-section">🏁 Valutazione finale</div>'
        if roster_complete
        else '<div class="rcd-section">🧠 Assistente asta</div>',
        unsafe_allow_html=True,
    )
    if phase:
        st.markdown(f"**{phase}**")

    c1, c2, c3 = st.columns(3)
    c1.metric("🏆 Valutazione Asta", f"{auction_grade:.1f}/10")
    c2.metric("💸 Crediti spesi", f"{spent} cr")
    c3.metric("📋 Valore listino", f"{listino} cr")

    role_parts = []
    for role in DRAFT_ORDER:
        value = counts.get(role, 0)
        limit = ROLE_LIMITS[role]
        check = " ✓" if value >= limit else ""
        role_parts.append(f"{role} {value}/{limit}{check}")
    st.markdown(
        '<div class="rcd-rolebar">' + " &nbsp; · &nbsp; ".join(role_parts) + "</div>",
        unsafe_allow_html=True,
    )

    if assessment:
        st.info(assessment)
    if advice:
        st.success(f"💡 **Consiglio:** {advice}")

    if roster_complete:
        custom_modifiers = load_custom_modifiers()
        goalkeeper_ranking = build_current_goalkeeper_ranking(state)
        tier_counts = {
            "TOP": 0,
            "Prima Fascia": 0,
            "Seconda Fascia": 0,
            "Terza Fascia": 0,
            "Scommessa": 0,
        }

        for player in state.team_players_map.get(team_name, []):
            details = calculate_player_rating_detailed(
                player,
                st.session_state.preferred_players,
                custom_modifiers,
                goalkeeper_ranking,
            )
            tier_counts[get_roster_tier(details["final_rating"])] += 1

        st.markdown("### 📊 Composizione qualitativa della rosa")
        q1, q2, q3, q4, q5 = st.columns(5)
        q1.metric("🏆 TOP", tier_counts["TOP"])
        q2.metric("🥇 Prima Fascia", tier_counts["Prima Fascia"])
        q3.metric("🥈 Seconda Fascia", tier_counts["Seconda Fascia"])
        q4.metric("🥉 Terza Fascia", tier_counts["Terza Fascia"])
        q5.metric("🎲 Scommesse", tier_counts["Scommessa"])

    # Suggerimenti disponibili solo durante l'asta.
    if (not roster_complete) and current_role:
        st.markdown(f"### 🎯 Prossimi obiettivi — {ROLE_NAMES[current_role]}")
        history = auction_history_ratios(rosters)
        if history:
            median_multiplier = float(pd.Series([h["ratio"] for h in history]).median())
            st.caption(
                f"📈 Mercato osservato finora: moltiplicatore mediano **x{median_multiplier:.2f}** "
                f"su {len(history)} acquisti con listino disponibile."
            )
        # Budget corrente salvato per la funzione di raccomandazione.
        st.session_state["my_team_budget"] = remaining

        recommendation_tier = st.selectbox(
            "🎯 Fascia dei giocatori consigliati",
            RECOMMENDATION_TIER_OPTIONS,
            index=RECOMMENDATION_TIER_OPTIONS.index(
                st.session_state.get("recommendation_tier", "TOP")
            ),
            key="recommendation_tier",
            help=(
                "TOP ≥ 9.0 · Prima Fascia 8.0–8.9 · "
                "Seconda Fascia 7.0–7.9 · Terza Fascia 6.5–6.9. "
                "Sotto 6.5 non vengono mai consigliati."
            ),
        )
        tier_min = RECOMMENDATION_TIERS[recommendation_tier]["min_rating"]
        tier_max = RECOMMENDATION_TIERS[recommendation_tier]["max_rating"]
        st.caption(
            f"Filtro: **{recommendation_tier}** · Rating "
            f"{tier_min:.1f}" + (f"–{tier_max:.1f}" if tier_max < 10 else "+") +
            ". Il costo viene usato per trovare il miglior affare dentro la fascia."
        )

        recommendations = build_next_player_recommendations(
            state,
            rosters,
            st.session_state.preferred_players,
            load_custom_modifiers(),
            current_role,
            limit=5,
        )
        if recommendations:
            best = recommendations[0]
            best_player = best["player"]
            best_details = best["details"]
            best_estimate = best["estimate"]
            st.markdown(
                f"""
                <div class="rcd-target">
                  <div class="rcd-kicker">🎯 TARGET #1 · {recommendation_tier.upper()}</div>
                  <div class="rcd-target-name">{best_player.get('name', '')} · ⭐ {best_details['final_rating']:.1f}</div>
                  <div class="rcd-target-meta">
                    {best_player.get('team_nfl', '—')} · Listino {int(best_player.get('list_price') or 0)} cr ·
                    Stima {best_estimate['estimated_price']} cr (x{best_estimate['multiplier']:.2f}) ·
                    Value {best.get('rating_per_10_cr', 0.0):.2f}/10 cr
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            rec_rows = []
            for index, row in enumerate(recommendations, start=1):
                player = row["player"]
                details = row["details"]
                estimate = row["estimate"]
                rec_rows.append({
                    "#": index,
                    "Giocatore": player.get("name", ""),
                    "Fascia": row.get("tier", recommendation_tier),
                    "Rating": details["final_rating"],
                    "Listino": int(player.get("list_price") or 0),
                    "Moltiplicatore": f"x{estimate['multiplier']:.2f}",
                    "Stima asta": estimate["estimated_price"],
                    "Rating / 10 cr": row.get("rating_per_10_cr", 0.0),
                    "Valore Score": row.get("score", 0.0),
                    "Club": player.get("team_nfl", "—"),
                })
            with st.expander("Mostra altri giocatori consigliati", expanded=False):
                st.dataframe(
                    pd.DataFrame(rec_rows),
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Rating": st.column_config.NumberColumn(format="%.1f"),
                        "Listino": st.column_config.NumberColumn(format="%d cr"),
                        "Stima asta": st.column_config.NumberColumn(format="%d cr"),
                        "Rating / 10 cr": st.column_config.NumberColumn(format="%.2f"),
                        "Valore Score": st.column_config.NumberColumn(format="%.2f"),
                    },
                )
        else:
            st.caption("Non ci sono obiettivi compatibili disponibili per questo ruolo.")



def render_my_roster(
    state: AuctionState,
) -> None:
    """Mostra la rosa squadra associata divisa P-D-C-A."""
    team_name = resolve_my_team_name(list(state.team_players_map))

    st.markdown(
        f'<div class="rcd-section">👕 Rosa {escape(team_name or get_current_user_team_name())}</div>',
        unsafe_allow_html=True,
    )
    if team_name is None:
        st.warning(
            f"⚠️ La squadra **{get_current_user_team_name()}** non è presente tra le squadre configurate."
        )
        return

    players = state.team_players_map.get(team_name, [])
    if not players:
        st.info("La rosa è ancora vuota.")
        return

    custom_modifiers = load_custom_modifiers()
    goalkeeper_ranking = build_current_goalkeeper_ranking(state)
    purchases = state.team_purchases_map.get(team_name, [])
    purchase_by_player = {
        purchase.get("players", {}).get("id"): purchase
        for purchase in purchases
        if purchase.get("players")
    }

    # In build_auction_state players e purchases provengono dalla stessa query,
    # quindi usiamo anche la posizione per sicurezza nel caso l'id non sia presente.
    rows_by_role = {role: [] for role in ["P", "D", "C", "A"]}
    for player in players:
        details = calculate_player_rating_detailed(
            player,
            st.session_state.preferred_players,
            custom_modifiers,
            goalkeeper_ranking,
        )
        purchase = purchase_by_player.get(player.get("id"), {})
        manual_value = details.get("custom_mod", 0.0)
        manual_label = details.get("custom_label", "Nessuna modifica")
        bonus_malus = (
            f"{manual_label} ({manual_value:+.1f})"
            if manual_value
            else "—"
        )
        rows_by_role.setdefault(player.get("role", "D"), []).append(
            {
                "Nome": player.get("name", ""),
                "Rating": details["final_rating"],
                "Fascia": get_roster_tier(details["final_rating"]),
                "Squadra": player.get("team_nfl", "—"),
                "Titolarità": player.get("status_titolarita") or "—",
                "Rigorista": "✅ Sì" if player.get("rigorista") else "—",
                "Rookie": "🆕 Sì" if player.get("primo_anno_serie_a") else "—",
                "Cartellini": player.get("propensione_cartellini") or "—",
                "Crediti Spesi": int(purchase.get("purchase_price") or 0),
                "Crediti Dichiarati": int(player.get("list_price") or 0),
                "Moltiplicatore Asta": round(
                    int(purchase.get("purchase_price") or 0) / max(1, int(player.get("list_price") or 0)),
                    2,
                ),
                "Bonus/Malus": bonus_malus,
                "_sort_rating": details["final_rating"],
            }
        )

    role_titles = {
        "P": "🧤 Portieri",
        "D": "🛡️ Difensori",
        "C": "🎯 Centrocampisti",
        "A": "⚡ Attaccanti",
    }

    for role in ["P", "D", "C", "A"]:
        role_rows = sorted(
            rows_by_role.get(role, []),
            key=lambda row: (-row["_sort_rating"], row["Nome"]),
        )
        complete_mark = " ✓" if len(role_rows) >= ROLE_LIMITS[role] else ""
        with st.container(border=True):
            st.markdown(
                f"**{role_titles[role]}** &nbsp; "
                f"`{len(role_rows)}/{ROLE_LIMITS[role]}{complete_mark}`"
            )
            if not role_rows:
                st.caption("Nessun giocatore acquistato in questo ruolo.")
                continue

            display = pd.DataFrame(role_rows).drop(columns=["_sort_rating"])
            compact_cols = [
                "Nome", "Rating", "Fascia", "Squadra",
                "Titolarità", "Rigorista", "Rookie",
                "Cartellini", "Bonus/Malus",
            ]
            st.dataframe(
                display[compact_cols],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Nome": st.column_config.TextColumn(width="medium"),
                    "Rating": st.column_config.NumberColumn(format="%.1f", width="small"),
                    "Fascia": st.column_config.TextColumn(width="medium"),
                    "Squadra": st.column_config.TextColumn(width="small"),
                    "Titolarità": st.column_config.TextColumn(width="medium"),
                    "Rigorista": st.column_config.TextColumn(width="small"),
                    "Rookie": st.column_config.TextColumn(width="small"),
                    "Cartellini": st.column_config.TextColumn(width="medium"),
                    "Bonus/Malus": st.column_config.TextColumn(width="medium"),
                },
            )
            with st.expander("Dettagli economici", expanded=False):
                st.dataframe(
                    display[[
                        "Nome", "Crediti Dichiarati",
                        "Crediti Spesi", "Moltiplicatore Asta",
                    ]],
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Crediti Dichiarati": st.column_config.NumberColumn(format="%d cr"),
                        "Crediti Spesi": st.column_config.NumberColumn(format="%d cr"),
                        "Moltiplicatore Asta": st.column_config.NumberColumn(format="x%.2f"),
                    },
                )



# ============================================================
# MODULO STAGIONE — IMPORT VOTI / FORMAZIONE / CAMPIONATO
# ============================================================

FANTASY_RULES_DEFAULT = {
    "assist": 1.0,
    "clean_sheet": 1.0,
    "goal_conceded": -1.0,
    "missed_penalty": -3.0,
    "own_goal": -1.0,
    "red_card": -1.0,
    "penalty_saved": 3.0,
    "goal": 3.0,
    "yellow_card": -0.5,
}

GOAL_THRESHOLDS_DEFAULT = {
    1: 66,
    2: 70,
    3: 74,
    4: 78,
    5: 82,
    6: 86,
    7: 90,
    8: 94,
    9: 98,
    10: 102,
    11: 106,
    12: 110,
}


def _parse_vote(value: Any) -> float | None:
    """Converte 6*, 6.5, ecc.; valori non numerici diventano None."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().replace(",", ".").replace("*", "")
    match = re.search(r"-?\d+(?:\.\d+)?", text)
    return float(match.group()) if match else None


def parse_fantacalcio_votes_xlsx(uploaded_file: Any, sheet_name: str = "Fantacalcio") -> pd.DataFrame:
    """
    Legge il formato XLSX Fantacalcio mostrato nel file di test.
    Le righe con un solo testo prima dell'header sono interpretate come club.
    """
    raw = pd.read_excel(uploaded_file, sheet_name=sheet_name, header=None)
    rows: list[dict[str, Any]] = []
    current_team = ""

    for _, row in raw.iterrows():
        values = row.tolist()
        first = values[0] if len(values) else None

        if str(first).strip() == "Cod.":
            continue

        # Riga squadra: prima cella testuale, resto vuoto.
        rest = values[1:13]
        if (
            isinstance(first, str)
            and first.strip()
            and all(pd.isna(v) for v in rest)
            and not first.startswith(("Voti Fantacalcio", "Solo su ", "QUESTO FILE", "E' DA "))
        ):
            current_team = first.strip()
            continue

        if not isinstance(first, (int, float)) or pd.isna(first):
            continue
        if len(values) < 13:
            continue

        role = str(values[1]).strip() if not pd.isna(values[1]) else ""
        name = str(values[2]).strip() if not pd.isna(values[2]) else ""
        if role not in {"P", "D", "C", "A"} or not name:
            continue

        rows.append({
            "Codice": int(first),
            "Ruolo": role,
            "Giocatore": name,
            "Squadra": current_team,
            "Voto": _parse_vote(values[3]),
            "Gf": int(values[4] or 0) if not pd.isna(values[4]) else 0,
            "Gs": int(values[5] or 0) if not pd.isna(values[5]) else 0,
            "Rp": int(values[6] or 0) if not pd.isna(values[6]) else 0,
            "Rs": int(values[7] or 0) if not pd.isna(values[7]) else 0,
            "Rf": int(values[8] or 0) if not pd.isna(values[8]) else 0,
            "Au": int(values[9] or 0) if not pd.isna(values[9]) else 0,
            "Amm": int(values[10] or 0) if not pd.isna(values[10]) else 0,
            "Esp": int(values[11] or 0) if not pd.isna(values[11]) else 0,
            "Ass": int(values[12] or 0) if not pd.isna(values[12]) else 0,
        })

    return pd.DataFrame(rows)


def calculate_weekly_fantasy_score(row: pd.Series, rules: dict[str, float]) -> float | None:
    """Fantavoto di test basato sui bonus/malus forniti dall'utente."""
    vote = row.get("Voto")
    if vote is None or pd.isna(vote):
        return None

    score = float(vote)
    score += float(row.get("Gf", 0)) * rules["goal"]
    score += float(row.get("Gs", 0)) * rules["goal_conceded"]
    score += float(row.get("Rp", 0)) * rules["penalty_saved"]
    score += float(row.get("Rs", 0)) * rules["missed_penalty"]
    score += float(row.get("Au", 0)) * rules["own_goal"]
    score += float(row.get("Amm", 0)) * rules["yellow_card"]
    score += float(row.get("Esp", 0)) * rules["red_card"]
    score += float(row.get("Ass", 0)) * rules["assist"]

    # Dalla schermata: Porta inviolata +1.
    # Nel file è inferibile con sufficiente sicurezza solo per il portiere con voto.
    if row.get("Ruolo") == "P" and int(row.get("Gs", 0)) == 0:
        score += rules["clean_sheet"]

    return round(score, 2)


def points_to_goals(points: float, thresholds: dict[int, int] | None = None) -> int:
    thresholds = thresholds or GOAL_THRESHOLDS_DEFAULT
    goals = 0
    for goal, threshold in sorted(thresholds.items()):
        if points >= threshold:
            goals = goal
    return goals


def get_season_rules_ui() -> dict[str, float]:
    if "season_rules" not in st.session_state:
        st.session_state.season_rules = FANTASY_RULES_DEFAULT.copy()
    return st.session_state.season_rules


def render_matchday_import_tab() -> None:
    st.markdown('<div class="rcd-section">📥 Importa voti giornata</div>', unsafe_allow_html=True)
    st.caption(
        "Area di test per i file XLSX Fantacalcio. Per ora i dati restano nella sessione "
        "e non vengono scritti su Supabase."
    )

    left, right = st.columns([1.25, 1])
    with left:
        uploaded = st.file_uploader(
            "File voti Fantacalcio (.xlsx)",
            type=["xlsx"],
            key="season_votes_upload",
        )
    with right:
        sheet = st.selectbox(
            "Redazione",
            ["Fantacalcio", "Statistico", "Italia"],
            key="season_votes_sheet",
        )

    with st.expander("⚙️ Regolamento bonus/malus usato nel test", expanded=False):
        rules = get_season_rules_ui()
        cols = st.columns(4)
        labels = [
            ("assist", "Assist"),
            ("clean_sheet", "Porta inviolata"),
            ("goal_conceded", "Gol subito"),
            ("goal", "Gol segnato"),
            ("missed_penalty", "Rigore sbagliato"),
            ("penalty_saved", "Rigore parato"),
            ("own_goal", "Autogol"),
            ("red_card", "Espulsione"),
            ("yellow_card", "Ammonizione"),
        ]
        for i, (key, label) in enumerate(labels):
            rules[key] = cols[i % 4].number_input(
                label,
                value=float(rules[key]),
                step=0.5,
                key=f"rule_{key}",
            )
        st.caption(
            "Gol vittoria/pareggio, assist gold/soft e Player of the Match sono 0/1 "
            "nel regolamento mostrato, ma il file XLSX di test non contiene colonne separate "
            "per identificarli. Non vengono quindi inventati."
        )

    with st.expander("🥅 Soglie gol", expanded=False):
        st.write(
            "**66 = 1 gol · 70 = 2 · 74 = 3 · 78 = 4 · 82 = 5 · "
            "86 = 6 · 90 = 7 · 94 = 8 · 98 = 9 · 102 = 10 · 106 = 11 · 110 = 12**"
        )

    if uploaded is not None:
        try:
            votes = parse_fantacalcio_votes_xlsx(uploaded, sheet)
            if votes.empty:
                st.error("Non sono riuscito a trovare righe giocatore nel file.")
                return

            votes["Fantavoto"] = votes.apply(
                lambda r: calculate_weekly_fantasy_score(r, rules),
                axis=1,
            )
            st.session_state["season_votes_df"] = votes
            st.session_state["season_votes_source"] = uploaded.name
            st.session_state["season_votes_loaded_sheet"] = sheet

            played = int(votes["Voto"].notna().sum())
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Giocatori nel file", len(votes))
            c2.metric("Con voto", played)
            c3.metric("Gol", int(votes["Gf"].sum()))
            c4.metric("Assist", int(votes["Ass"].sum()))

            st.success(f"File letto correttamente: **{uploaded.name}** · redazione **{sheet}**.")
        except Exception as exc:
            st.error(f"Errore durante la lettura del file: {exc}")
            return

    votes = st.session_state.get("season_votes_df")
    if isinstance(votes, pd.DataFrame) and not votes.empty:
        st.markdown('<div class="rcd-section">🔎 Anteprima giornata</div>', unsafe_allow_html=True)
        c1, c2 = st.columns([1, 2])
        with c1:
            role = st.selectbox("Ruolo", ["Tutti", "P", "D", "C", "A"], key="votes_role")
        with c2:
            search = st.text_input("Cerca giocatore", key="votes_search")

        view = votes.copy()
        if role != "Tutti":
            view = view[view["Ruolo"] == role]
        if search.strip():
            q = normalize_string(search)
            view = view[view["Giocatore"].map(normalize_string).str.contains(q, na=False)]

        st.dataframe(
            view[["Codice", "Ruolo", "Giocatore", "Squadra", "Voto", "Fantavoto", "Gf", "Gs", "Ass", "Amm", "Esp"]],
            use_container_width=True,
            hide_index=True,
            column_config={
                "Voto": st.column_config.NumberColumn(format="%.1f"),
                "Fantavoto": st.column_config.NumberColumn(format="%.1f"),
            },
        )


def _match_vote_for_player(player: dict[str, Any], votes: pd.DataFrame) -> pd.Series | None:
    target = normalize_string(player.get("name", ""))
    if not target:
        return None

    exact = votes[votes["Giocatore"].map(normalize_string) == target]
    if not exact.empty:
        return exact.iloc[0]

    # Fallback prudente per abbreviazioni tipo "Paz N.".
    candidates = votes[
        votes["Giocatore"].map(normalize_string).apply(
            lambda x: bool(x) and (x in target or target in x)
        )
    ]
    return candidates.iloc[0] if len(candidates) == 1 else None


def render_formation_lab_tab(state: AuctionState) -> None:
    st.markdown('<div class="rcd-section">🧠 Formation Lab</div>', unsafe_allow_html=True)
    st.caption(
        "Prototype retrospettivo: usa i voti caricati per verificare abbinamenti e logica "
        "della futura formazione consigliata."
    )

    votes = st.session_state.get("season_votes_df")
    if not isinstance(votes, pd.DataFrame) or votes.empty:
        st.info("Carica prima un XLSX nella tab **📥 GIORNATE**.")
        return

    team_name, players, _ = get_my_team_players_and_purchases(state)
    if team_name is None or not players:
        st.info(
            f"Non trovo la rosa **{get_current_user_team_name()}** da confrontare con i voti."
        )
        return

    matched = []
    missing = []
    for player in players:
        row = _match_vote_for_player(player, votes)
        if row is None:
            missing.append(player.get("name", ""))
            continue
        matched.append({
            "Nome": player.get("name", ""),
            "Ruolo": player.get("role", ""),
            "Squadra": row.get("Squadra", ""),
            "Voto": row.get("Voto"),
            "Fantavoto": row.get("Fantavoto"),
            "Gol": row.get("Gf", 0),
            "Assist": row.get("Ass", 0),
        })

    if not matched:
        st.warning(
            "Nessun giocatore della rosa attuale coincide con il file storico. "
            "È normale se stai usando rose/stagioni diverse."
        )
        return

    df = pd.DataFrame(matched)
    c1, c2, c3 = st.columns(3)
    c1.metric("Abbinati", f"{len(df)}/{len(players)}")
    c2.metric("Con voto", int(df["Voto"].notna().sum()))
    c3.metric(
        "Fantavoto medio",
        f"{df['Fantavoto'].dropna().mean():.2f}" if df["Fantavoto"].notna().any() else "—",
    )

    # XI di test 3-4-3: non pretende ancora di essere il motore finale.
    chosen = []
    for role, n in [("P", 1), ("D", 3), ("C", 4), ("A", 3)]:
        part = df[(df["Ruolo"] == role) & df["Fantavoto"].notna()].nlargest(n, "Fantavoto")
        chosen.append(part)
    xi = pd.concat(chosen, ignore_index=True) if chosen else pd.DataFrame()

    st.markdown('<div class="rcd-section">🧪 Miglior XI retrospettivo · 3-4-3</div>', unsafe_allow_html=True)
    st.caption(
        "Serve solo per validare l'import: usa i fantavoti già avvenuti, quindi non è ancora "
        "un consiglio predittivo per la giornata successiva."
    )
    if len(xi) == 11:
        total = float(xi["Fantavoto"].sum())
        c1, c2 = st.columns(2)
        c1.metric("Punteggio XI", f"{total:.1f}")
        c2.metric("Gol da soglia", points_to_goals(total))
    else:
        st.warning(f"XI incompleto: trovati {len(xi)}/11 giocatori con voto nei ruoli richiesti.")

    st.dataframe(
        xi[["Ruolo", "Nome", "Squadra", "Voto", "Fantavoto", "Gol", "Assist"]],
        use_container_width=True,
        hide_index=True,
    )

    if missing:
        with st.expander(f"Giocatori non abbinati ({len(missing)})", expanded=False):
            st.write(", ".join(missing))


def render_championship_lab_tab() -> None:
    st.markdown('<div class="rcd-section">🏆 Campionato & Classifica</div>', unsafe_allow_html=True)
    st.caption("Struttura già pronta per la fase post-asta.")

    c1, c2, c3 = st.columns(3)
    c1.metric("Soglia 1° gol", "66 pt")
    c2.metric("Scatto successivo", "+4 pt")
    c3.metric("Squadre", "12")

    st.info(
        "Per produrre la **classifica ufficiale** servono anche le formazioni schierate "
        "da ciascuna fantasquadra e il calendario degli scontri diretti. Il solo file voti "
        "Fantacalcio contiene i voti dei calciatori reali, non dice quali 11 siano stati "
        "schierati da ogni squadra della lega."
    )

    st.markdown('<div class="rcd-section">📐 Motore punteggio già impostato</div>', unsafe_allow_html=True)
    demo = pd.DataFrame({
        "Punti": [65.5, 66, 69.5, 70, 74, 78, 82, 90, 102, 110],
    })
    demo["Gol"] = demo["Punti"].map(points_to_goals)
    st.dataframe(demo, use_container_width=True, hide_index=True)

    st.markdown('<div class="rcd-section">🚧 Prossimi dati da importare</div>', unsafe_allow_html=True)
    st.write(
        "Quando avremo un export Fantaleghe con **formazioni/risultati/calendario**, "
        "questa tab potrà generare automaticamente: classifica, GF/GS, differenza reti, "
        "fantapunti, forma ultime 5, miglior attacco/difesa e analisi fortuna/sfortuna."
    )


def render_settings_page(
    user: dict[str, Any],
    teams: list[dict[str, Any]],
) -> None:
    """Impostazioni account, squadra e strategia d'asta."""
    st.markdown(
        '<div class="rcd-section">⚙️ Impostazioni</div>',
        unsafe_allow_html=True,
    )

    user_id = str(user.get("id") or "").strip()
    if not user_id:
        st.error("Utente non identificato.")
        return

    current_team_id = get_current_user_team_id()
    current_team_name = get_current_user_team_name()

    team_names = [str(team.get("name") or "") for team in teams]
    current_index = 0
    for i, team in enumerate(teams):
        if (
            str(team.get("id")) == str(current_team_id)
            or str(team.get("name")) == current_team_name
        ):
            current_index = i
            break

    settings = {
        "goalkeeper_strategy": current_goalkeeper_strategy(),
        "credit_strategy": current_credit_strategy(),
    }

    st.markdown("### 👕 Squadra")
    selected_team_name = st.selectbox(
        "Fantasquadra associata",
        team_names,
        index=current_index if team_names else 0,
        key="settings_team",
        help="Una fantasquadra può essere associata a un solo account.",
    )
    selected_team = next(
        (team for team in teams if str(team.get("name")) == selected_team_name),
        None,
    )

    st.markdown("### 🎯 Strategia portieri")
    selected_gk = st.radio(
        "Come vuoi costruire il reparto?",
        GOALKEEPER_STRATEGY_OPTIONS,
        index=GOALKEEPER_STRATEGY_OPTIONS.index(
            settings["goalkeeper_strategy"]
        ),
        horizontal=True,
        key="settings_goalkeeper_strategy",
    )

    if selected_gk == "Tre titolari":
        st.info(
            "🧤 **Tre titolari:** il motore cercherà tre portieri titolari "
            "di squadre diverse, escludendo Milan, Inter, Juventus, Napoli, Roma "
            "e Como. L'obiettivo è spendere meno nel reparto e conservare crediti "
            "per centrocampisti e attaccanti TOP."
        )
    else:
        st.info(
            "🧤 **Stessa Squadra:** dopo il primo portiere, il motore darà "
            "priorità alle sue riserve per completare il blocco a costi contenuti."
        )

    st.markdown("### 💰 Bilanciamento crediti")
    selected_credit = st.radio(
        "Priorità di spesa",
        CREDIT_STRATEGY_OPTIONS,
        index=CREDIT_STRATEGY_OPTIONS.index(
            settings["credit_strategy"]
        ),
        horizontal=True,
        key="settings_credit_strategy",
    )

    allocation = STRATEGY_BUDGET_ALLOCATIONS[selected_credit]
    allocation_total = sum(allocation.values())
    role_meta = {
        "P": ("🧤", "Portieri"),
        "D": ("🛡️", "Difensori"),
        "C": ("🎯", "Centrocampisti"),
        "A": ("⚡", "Attaccanti"),
    }

    budget_chart_parts = [
        "<style>"
        ".budget-strategy-card{margin:14px 0 6px;padding:16px;border:1px solid #cbdcf5;"
        "border-radius:18px;background:linear-gradient(145deg,#ffffff,#eef5ff);"
        "box-shadow:0 7px 20px rgba(30,64,175,.07);}"
        ".budget-chart-title{font-size:.76rem;font-weight:950;letter-spacing:.08em;"
        "text-transform:uppercase;color:#315a9e!important;margin-bottom:12px;}"
        ".budget-role-row{display:grid;grid-template-columns:165px 1fr 72px;gap:12px;"
        "align-items:center;margin:10px 0;}"
        ".budget-role-label{font-size:.86rem;font-weight:850;color:#172033!important;white-space:nowrap;}"
        ".budget-role-track{height:13px;border-radius:999px;background:#e4ebf5;overflow:hidden;}"
        ".budget-role-fill{height:100%;border-radius:999px;background:linear-gradient(90deg,#2563eb,#60a5fa);}"
        ".budget-role-value{text-align:right;font-size:.88rem;font-weight:950;color:#172033!important;}"
        ".budget-role-percent{font-size:.66rem;font-weight:750;color:#64748b!important;}"
        ".budget-total{margin-top:13px;padding-top:10px;border-top:1px solid #d8e3f2;"
        "display:flex;justify-content:space-between;font-size:.76rem;font-weight:850;color:#64748b!important;}"
        "@media(max-width:720px){.budget-role-row{grid-template-columns:120px 1fr 62px;gap:8px;}"
        ".budget-role-label{font-size:.76rem;}}"
        "</style>"
        f'<div class="budget-strategy-card">'
        f'<div class="budget-chart-title">💰 Piano crediti · {escape(selected_credit)}</div>'
    ]

    for role in ("P", "D", "C", "A"):
        icon, label = role_meta[role]
        credits = int(allocation[role])
        percent = (credits / allocation_total * 100) if allocation_total else 0
        budget_chart_parts.append(
            '<div class="budget-role-row">'
            f'<div class="budget-role-label">{icon} {label}</div>'
            '<div class="budget-role-track">'
            f'<div class="budget-role-fill" style="width:{percent:.1f}%"></div>'
            '</div>'
            f'<div class="budget-role-value">{credits} cr'
            f'<div class="budget-role-percent">{percent:.0f}%</div></div>'
            '</div>'
        )

    budget_chart_parts.append(
        '<div class="budget-total">'
        '<span>Budget pianificato</span>'
        f'<span>{allocation_total} crediti</span>'
        '</div></div>'
    )
    st.markdown("".join(budget_chart_parts), unsafe_allow_html=True)

    st.divider()

    if st.button(
        "Salva impostazioni",
        type="primary",
        use_container_width=True,
        key="save_settings",
    ):
        if selected_team is None:
            st.error("Seleziona una squadra valida.")
            return

        team_ok, team_error = save_user_team_assignment(
            user_id,
            selected_team["id"],
            selected_team_name,
        )
        if not team_ok:
            if "duplicate" in team_error.lower() or "unique" in team_error.lower():
                st.error(
                    "Questa squadra è già associata a un altro account."
                )
            else:
                st.error(f"Non riesco a salvare la squadra: {team_error}")
            return

        strategy_ok, strategy_error = save_user_strategy_settings(
            user_id,
            selected_gk,
            selected_credit,
        )
        if not strategy_ok:
            st.error(f"Non riesco a salvare la strategia: {strategy_error}")
            return

        # Nuovi default UI coerenti con la nuova squadra.
        for key in (
            "_ui_defaults_for_team",
            "sidebar_team_analysis",
            "manual_target_team",
            "table_team_filter_tab2",
        ):
            st.session_state.pop(key, None)

        st.success("Impostazioni salvate.")
        st.rerun()


# ============================================================
# MAIN
# ============================================================

def main() -> None:

    current_user = require_authentication()
    render_app_logo()
    active_page = render_authenticated_user_header(current_user)

    teams = load_teams()
    require_user_team_assignment(current_user, teams)
    sync_user_strategy_session(current_user)
    rosters = load_rosters()

    # Il budget visualizzato/usato dall'asta viene ricostruito dagli acquisti:
    # initial_budget - purchase_price. In questo modo un remaining_budget
    # accidentalmente azzerato nel DB non porta tutte le squadre a 0 crediti.
    teams = reconcile_team_budgets_from_rosters(teams, rosters)
    teams_df = pd.DataFrame(teams)
    state = build_auction_state(teams, rosters)

    if "preferred_players" not in st.session_state:
        st.session_state.preferred_players = set()

    preferred_players = st.session_state.preferred_players
    custom_modifiers = load_custom_modifiers()
    goalkeeper_ranking = build_current_goalkeeper_ranking(state)
    ratings = calculate_team_ratings(
        state,
        preferred_players,
        custom_modifiers,
        goalkeeper_ranking,
    )

    auction_finished = is_auction_finished(state)

    # Sidebar persistente: resta disponibile in tutte le sezioni dell'app.
    my_team_name = get_my_team_name_from_state(state)
    my_team_row = (
        teams_df[teams_df["name"] == my_team_name]
        if my_team_name
        else pd.DataFrame()
    )
    st.session_state["my_team_budget"] = (
        int(my_team_row.iloc[0]["remaining_budget"])
        if not my_team_row.empty
        else 0
    )

    sidebar_role = get_my_team_draft_role(state)
    if not auction_finished and sidebar_role:
        render_smart_next_purchase_card(
            state,
            rosters,
            preferred_players,
            sidebar_role,
        )
        render_top5(
            sidebar_role,
            state.bought_player_ids,
            preferred_players,
            state,
        )

    render_team_analysis(
        teams_df,
        state,
        ratings,
    )

    if active_page == "Asta":
        render_auction_dashboard_header(teams_df, state, ratings)

        # Mostrato dopo il rerun dell'acquisto.
        render_pending_purchase_banner()

        refresh_col, _ = st.columns([1, 6])
        with refresh_col:
            if st.button("↻ Aggiorna", key="refresh_live_data"):
                invalidate_data_cache()
                st.rerun()

        st.markdown('<div class="rcd-section">🎯 Acquista giocatore</div>', unsafe_allow_html=True)

        if auction_finished:
            st.success(
                "🎉 **ASTA CONCLUSA!** Tutte le squadre hanno completato "
                "le proprie rose."
            )
            current_role = "ALL"
        else:
            current_role = "ALL"

        # Il pannello contiene tutti e 5 i dropdown/controlli sulla stessa riga.
        draft_role = get_my_team_draft_role(state)
        if draft_role:
            draft_label = role_label(draft_role)
            valid_role_labels = [
                label for label, role in ROLE_LABELS.items()
                if role == "ALL" or role == draft_role or (
                    role in DRAFT_ORDER and state.team_role_totals.get(my_team_name or "", {}).get(role, 0) < ROLE_LIMITS[role]
                )
            ]
            if st.session_state.get("main_role_select") not in valid_role_labels:
                st.session_state["main_role_select"] = draft_label
            current_role = draft_role
        else:
            current_role = "ALL"

        current_role = render_manual_purchase(
            teams_df,
            state,
            current_role,
            rosters,
        )

        resolved_my_team = resolve_my_team_name(teams_df["name"].tolist())
        if resolved_my_team:
            db_team_count = sum(
                1 for roster in rosters
                if roster.get("teams", {}).get("name") == resolved_my_team
                and roster.get("players")
            )
            if db_team_count != state.team_total_bought.get(resolved_my_team, 0):
                st.warning(
                    "⚠️ Incoerenza nei dati caricati: "
                    f"Supabase contiene {db_team_count} giocatori per **{resolved_my_team}**, "
                    f"ma lo stato dell'asta ne ha caricati {state.team_total_bought.get(resolved_my_team, 0)}. "
                    "La query delle rose è stata resa esplicita tramite team_id/player_id per evitare questo problema."
                )

        render_my_team_evaluation(
            teams_df,
            state,
            ratings,
            rosters,
        )

        render_my_roster(state)

        if _is_player_data_admin(current_user):
            with st.expander("🛠️ Strumenti asta e diagnostica", expanded=False):
                render_admin_tools(
                    teams_df,
                    state,
                    current_user,
                )

    elif active_page == "Lega":
        render_team_overview(
            teams_df,
            state,
            ratings,
        )
        st.divider()
        render_rosters_tab(
            teams,
            teams_df,
            rosters,
            state,
            ratings,
        )

    elif active_page == "Giocatori":
        render_all_players_tab()

    elif active_page == "Giornate":
        render_matchday_import_tab()

    elif active_page == "Formazione":
        render_formation_lab_tab(state)

    elif active_page == "Campionato":
        render_championship_lab_tab()

    elif active_page == "Impostazioni":
        render_settings_page(
            current_user,
            teams,
        )

    elif active_page == "Dati giocatori":
        if _is_player_data_admin(current_user):
            render_player_data_updater_page(current_user)
            with st.expander(
                "🛠️ Correzioni manuali rating (legacy / emergenza)",
                expanded=False,
            ):
                render_player_modifiers_tab()


if __name__ == "__main__":
    main()
