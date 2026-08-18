from __future__ import annotations

import os
import random
import re
import unicodedata
import uuid
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
   RCD ESCANYOL — PREMIUM HIGH-CONTRAST DASHBOARD
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

/* Tab: stesso font dell'app, solo con peso più marcato */
div[data-testid="stTabs"] button[role="tab"],
div[data-testid="stTabs"] button[role="tab"] p,
div[data-testid="stTabs"] button[role="tab"] span,
div[data-baseweb="tab-list"] button,
div[data-baseweb="tab-list"] button p,
div[data-baseweb="tab-list"] button span {
    font-family: inherit !important;
    font-weight: 700 !important;
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


# Tab 4: modifiche manuali persistenti ai giocatori.
# Richiede una tabella Supabase dedicata (SQL fornito sotto).
CUSTOM_MODIFIER_TABLE = "player_custom_modifiers"

# Nome della squadra dell'utente. Vengono tollerati anche i nomi usati
# nelle versioni precedenti, così il codice non dipende da una singola
# stringa hardcoded.
MY_TEAM_NAME = "RCD Escanyol"
MY_TEAM_ALIASES = (
    "RCD Escanyol",
    "Escanyol",
    "RCD Escalnyol",
)

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


def _auth_display_name(user: dict[str, Any]) -> str:
    metadata = user.get("metadata") or {}
    return str(
        metadata.get("full_name")
        or metadata.get("name")
        or metadata.get("user_name")
        or user.get("email")
        or "Utente"
    )


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


def sign_up_with_email_password(email: str, password: str) -> tuple[bool, str]:
    """Registrazione classica Supabase con email/password."""
    try:
        auth_client = get_auth_flow_client("password-signup")
        response = auth_client.auth.sign_up(
            {
                "email": email.strip(),
                "password": password,
            }
        )

        user = getattr(response, "user", None)
        session = getattr(response, "session", None)

        if user is None:
            return False, "Registrazione non completata."

        # Se la conferma email è disattivata, Supabase restituisce subito la sessione.
        if session is not None:
            access_token = getattr(session, "access_token", None)
            refresh_token = getattr(session, "refresh_token", None)
            if access_token and refresh_token:
                st.session_state["auth_access_token"] = access_token
                st.session_state["auth_refresh_token"] = refresh_token
                st.session_state["auth_user"] = _minimal_user_dict(user)
                st.session_state["auth_flow_id"] = "password-signup"
                return True, "signed_in"

        return True, "check_email"

    except Exception as exc:
        return False, str(exc)


def render_login_page() -> None:
    """Pagina login RCD Escanyol con pulsanti Google/Facebook e loghi."""
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
        '<div class="login-eyebrow">RCD ESCANYOL</div>'
        '<div class="login-title">⚽ Auction &amp; Season Center</div>'
        '<div class="login-subtitle">Asta, rosa, formazione e campionato in un unico posto.</div>'
        '</div>'
        '<div class="login-card">'
        '<div class="login-card-title">Accedi per continuare</div>'
        f'<a class="social-login google" href="{google_url}" target="_self">'
        '<svg class="social-logo" viewBox="0 0 24 24" aria-hidden="true">'
        '<path fill="#4285F4" d="M21.6 12.23c0-.71-.06-1.4-.18-2.07H12v3.92h5.38a4.6 4.6 0 0 1-2 3.02v2.54h3.24c1.9-1.75 2.98-4.33 2.98-7.41z"/>'
        '<path fill="#34A853" d="M12 22c2.7 0 4.97-.9 6.63-2.43l-3.24-2.54c-.9.6-2.05.96-3.39.96-2.61 0-4.82-1.76-5.61-4.13H3.04v2.62A10 10 0 0 0 12 22z"/>'
        '<path fill="#FBBC05" d="M6.39 13.86A6 6 0 0 1 6.08 12c0-.65.11-1.28.31-1.86V7.52H3.04A10 10 0 0 0 2 12c0 1.61.38 3.13 1.04 4.48l3.35-2.62z"/>'
        '<path fill="#EA4335" d="M12 6.01c1.47 0 2.79.51 3.83 1.5l2.87-2.87A9.63 9.63 0 0 0 12 2a10 10 0 0 0-8.96 5.52l3.35 2.62C7.18 7.77 9.39 6.01 12 6.01z"/>'
        '</svg>'
        '<span>Continua con Google</span>'
        '</a>'
        f'<a class="social-login facebook" href="{facebook_url}" target="_self">'
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
                ok, message = sign_up_with_email_password(email, password)
                if not ok:
                    st.error(f"Registrazione non riuscita: {message}")
                elif message == "signed_in":
                    st.success("Account creato. Accesso effettuato.")
                    st.rerun()
                else:
                    st.success(
                        "Account creato. Controlla la tua email per confermare "
                        "l'indirizzo, poi torna qui e accedi."
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



def render_authenticated_user_header(user: dict[str, Any]) -> None:
    """Profilo minimale in alto a destra: saluto + avatar."""
    first_name = escape(_first_name_from_user(user))
    greeting = escape(_dynamic_greeting())
    avatar = escape(_auth_avatar_url(user), quote=True)

    avatar_html = (
        f'<img class="rcd-profile-avatar" src="{avatar}" alt="Profilo">'
        if avatar
        else '<div class="rcd-profile-fallback">⚽</div>'
    )

    st.markdown(
        f"""
        <style>
        .rcd-user-topbar {{
            display:flex;
            align-items:center;
            justify-content:flex-end;
            gap:12px;
            margin:.35rem 0 .75rem 0;
            padding-right:.15rem;
            min-height:54px;
        }}
        .rcd-user-greeting {{
            display:flex;
            align-items:center;
            gap:8px;
            font-size:1.02rem;
            line-height:1;
            font-weight:900;
            color:#17325f !important;
            white-space:nowrap;
        }}
        .rcd-user-ball {{
            font-size:1.25rem;
        }}
        .rcd-profile-avatar,
        .rcd-profile-fallback {{
            width:46px;
            height:46px;
            border-radius:50%;
            object-fit:cover;
            border:3px solid #ffffff;
            box-shadow:0 5px 16px rgba(30,64,175,.20);
            background:#dbeafe;
        }}
        .rcd-profile-fallback {{
            display:flex;
            align-items:center;
            justify-content:center;
            font-size:1.25rem;
        }}
        @media (max-width: 720px) {{
            .rcd-user-topbar {{
                margin:.25rem 0 .65rem 0;
            }}
            .rcd-user-greeting {{
                font-size:.90rem;
            }}
            .rcd-profile-avatar,
            .rcd-profile-fallback {{
                width:40px;
                height:40px;
            }}
        }}
        </style>
        <div class="rcd-user-topbar">
            <div class="rcd-user-greeting">
                <span class="rcd-user-ball">⚽</span>
                <span>{greeting} {first_name}!</span>
            </div>
            {avatar_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_logout_sidebar() -> None:
    """Solo pulsante logout, senza Account/nome/email/avatar nella sidebar."""
    st.sidebar.markdown("---")
    if st.sidebar.button(
        "↪ Esci",
        key="auth_logout",
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
        st.rerun()



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
    """Trova RCD Escanyol anche con piccole differenze di formattazione."""
    normalized = {normalize_string(name): name for name in team_names if isinstance(name, str)}
    for candidate in (MY_TEAM_NAME, *MY_TEAM_ALIASES):
        hit = normalized.get(normalize_string(candidate))
        if hit:
            return hit
    return None


def is_my_team(team_name: str | None) -> bool:
    if not team_name:
        return False
    return normalize_string(team_name) == normalize_string(MY_TEAM_NAME) or normalize_string(team_name) in {
        normalize_string(alias) for alias in MY_TEAM_ALIASES
    }


def default_team_index(
    team_names: list[str],
    preferred: str = MY_TEAM_NAME,
) -> int:
    if not team_names:
        return 0

    # Prima prova il nome canonico, poi gli alias storici.
    for name in (preferred, *MY_TEAM_ALIASES):
        if name in team_names:
            return team_names.index(name)
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
        message = (
            f"**{player_name}** entra nella rosa RCD Escanyol · "
            f"Rating **{rating:.1f}** · Pagato **{purchase_price} cr**."
        )
    elif rating >= 8.0:
        level = "great"
        title = "✨ PRIMA FASCIA!"
        message = (
            f"Acquistato **{player_name}** · Rating **{rating:.1f}** · "
            f"Prezzo **{purchase_price} cr**. Innesto di livello."
        )
    else:
        level = "normal"
        title = "✅ ACQUISTO COMPLETATO"
        message = (
            f"**{player_name}** è un nuovo giocatore RCD Escanyol · "
            f"Rating **{rating:.1f}** · Pagato **{purchase_price} cr**."
        )

    st.session_state["pending_purchase_banner"] = {
        "level": level,
        "title": title,
        "message": message,
    }


def render_pending_purchase_banner() -> None:
    """Mostra il banner dell'ultimo acquisto dopo il rerun."""
    banner = st.session_state.get("pending_purchase_banner")
    if not banner:
        return

    # Evita che il banner venga riprodotto ad ogni rerun, ma lo mantiene
    # abbastanza a lungo da poter essere visualizzato anche se la pagina
    # ricostruisce più volte la UI.
    st.session_state.pop("pending_purchase_banner", None)
    level = banner["level"]
    text = f"**{banner['title']}** — {banner['message']}"

    # Banner visivo indipendente dai widget di Streamlit: rimane visibile
    # anche se il browser blocca l'autoplay dell'audio.
    banner_class = {
        "massive": "massive",
        "great": "great",
        "normal": "normal",
    }.get(level, "normal")
    st.markdown(
        f"""
        <div class=\"auction-banner {banner_class}\">
            <div class=\"auction-banner-title\">{banner['title']}</div>
            <div class=\"auction-banner-text\">{banner['message']}</div>
        </div>
        <style>
        .auction-banner {{
            padding: 22px 28px; margin: 12px 0 22px; border-radius: 18px;
            text-align: center; font-size: 1.15rem;
            border: 2px solid rgba(255,255,255,.55);
            box-shadow: 0 10px 30px rgba(0,0,0,.16);
            animation: auctionPulse 1.1s ease-in-out 2;
        }}
        .auction-banner.massive {{
            background: radial-gradient(circle at 90% 10%, rgba(250,204,21,.35), transparent 28%),
                        linear-gradient(135deg,#4c1d95,#1e3a8a);
            color:white;
        }}
        .auction-banner.great {{
            background: radial-gradient(circle at 90% 10%, rgba(74,222,128,.30), transparent 30%),
                        linear-gradient(135deg,#064e3b,#0f766e);
            color:white;
        }}
        .auction-banner.normal {{
            background: linear-gradient(135deg,#1e3a8a,#0f172a);
            color:white;
        }}
        .auction-banner,
        .auction-banner *,
        .auction-banner-title,
        .auction-banner-text {{
            color: #ffffff !important;
        }}
        .auction-banner-title {{
            font-size: 1.8rem;
            font-weight: 900;
            margin-bottom: 6px;
            letter-spacing:.02em;
        }}
        .auction-banner-text {{
            font-weight: 650;
            color: #ffffff !important;
        }}
        @keyframes auctionPulse {{
            0%,100% {{ transform: scale(1); }}
            50% {{ transform: scale(1.025); }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

    if level == "massive":
        st.balloons()
        play_sound(SOUND_URLS["massive"])
    elif level == "great":
        st.balloons()
        play_sound(SOUND_URLS["great"])
    else:
        play_sound(SOUND_URLS["normal"])


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
    """Restituisce il prossimo ruolo della rosa RCD Escanyol secondo PDCA."""
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

    rigorista_mod = 0.8 if player.get("rigorista") else 0.0
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

    final = amplified + star_bonus - weak_penalty

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

        if state.team_total_bought.get(selected_team, 0) >= TOTAL_SLOTS_PER_TEAM:
            if avg_score >= 6.5:
                st.sidebar.success("Rosa forte.")
            else:
                st.sidebar.warning("Rosa scarsa.")
        else:
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
) -> None:
    st.sidebar.divider()
    st.sidebar.subheader("🛠️ Strumenti Mockup & Admin")

    role_filter = st.sidebar.selectbox(
        "Completa ruolo (Mockup)",
        ["Tutti"] + list(ROLE_LIMITS),
    )

    st.sidebar.caption(
        "Nel mockup i TOP vengono assegnati prima delle fasce inferiori, "
        "così non restano irrealisticamente svincolati."
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
    rosters: list[dict[str, Any]],
) -> str:
    """Renderizza il pannello di acquisto manuale in una griglia allineata."""
    if is_auction_finished(state):
        return current_role

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
            index=default_team_index(team_names, MY_TEAM_NAME),
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

    selected_value_score = get_price_value_score(
        player_details["final_rating"], estimate["estimated_price"], int(selected_player.get("list_price") or 1)
    )
    selected_rating_per_10 = calculate_value_per_credit(
        player_details["final_rating"], estimate["estimated_price"]
    )
    st.markdown(
        f"💰 **Stima asta:** circa **{estimate['estimated_price']} cr** "
        f"(**x{estimate['multiplier']:.2f}** del listino) · "
        f"{estimate['source']} · campione {estimate['sample_size']} acquisti."
    )
    st.caption(
        f"📊 **Valore stimato:** {selected_rating_per_10:.2f} rating ogni 10 cr · "
        f"Value Score **{selected_value_score:.2f}** · "
        "la priorità premia rating alto + costo stimato contenuto."
    )

    if estimate["budget_note"]:
        st.caption(f"⚠️ {estimate['budget_note']}")
    elif estimate.get("max_bid") is not None:
        st.caption(f"Budget massimo sostenibile mantenendo 1 credito per ogni slot futuro: **{estimate['max_bid']} cr**.")

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
            MY_TEAM_NAME,
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
# TAB 1 — VALUTAZIONE E ROSA RCD ESCANYOL
# ============================================================

def render_my_team_evaluation(
    teams_df: pd.DataFrame,
    state: AuctionState,
    ratings: dict[str, float],
    rosters: list[dict[str, Any]],
) -> None:
    """Valuta RCD Escanyol in modo progressivo seguendo il draft PDCA."""
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

    # Classifica portieri solo quando almeno un portiere è stato acquistato.
    ranking = build_current_goalkeeper_ranking(state)
    if counts.get("P", 0) > 0 and ranking:
        goalkeeper_rows = []
        for code, position in sorted(ranking.items(), key=lambda item: item[1]):
            goalkeeper_rows.append({
                "Pos.": position,
                "Squadra": code,
                "Gol subiti": GOALS_CONCEDED.get(code, 0),
                "Mod. P": GOALKEEPER_GOALS_CONCEDED_MODIFIERS.get(position, 0.0),
            })
        with st.expander("🧤 Strategia portieri / difese scelte"):
            st.dataframe(
                pd.DataFrame(goalkeeper_rows),
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Mod. P": st.column_config.NumberColumn(format="%+.1f"),
                },
            )


def render_my_roster(
    state: AuctionState,
) -> None:
    """Mostra la rosa RCD Escanyol divisa P-D-C-A."""
    team_name = resolve_my_team_name(list(state.team_players_map))

    st.markdown('<div class="rcd-section">👕 Rosa RCD Escanyol</div>', unsafe_allow_html=True)
    if team_name is None:
        st.warning(
            "⚠️ La squadra **RCD Escanyol** non è presente tra le squadre configurate."
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
                "Crediti Spesi", "Bonus/Malus",
            ]
            st.dataframe(
                display[compact_cols],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Rating": st.column_config.NumberColumn(format="%.1f"),
                    "Crediti Spesi": st.column_config.NumberColumn(format="%d cr"),
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
        st.info("Non trovo una rosa RCD Escanyol da confrontare con i voti.")
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


# ============================================================
# MAIN
# ============================================================

def main() -> None:

    current_user = require_authentication()
    render_app_logo()
    render_authenticated_user_header(current_user)
    render_logout_sidebar()

    teams = load_teams()
    rosters = load_rosters()

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

    completed_roles = calculate_completed_roles(state)
    auction_finished = is_auction_finished(state)


    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(
        [
            "🎯 ASTA",
            "📊 LEGA",
            "⭐ GIOCATORI",
            "⚙️ BONUS / MALUS",
            "📥 GIORNATE",
            "🧠 FORMAZIONE",
            "🏆 CAMPIONATO",
        ]
    )

    with tab1:
        render_auction_dashboard_header(teams_df, state, ratings)

        # Mostrato dopo il rerun dell'acquisto.
        render_pending_purchase_banner()

        refresh_col, _ = st.columns([1, 6])
        with refresh_col:
            if st.button("↻ Aggiorna", key="refresh_live_data"):
                invalidate_data_cache()
                st.rerun()

        st.markdown('<div class="rcd-section">🎯 Acquista giocatore</div>', unsafe_allow_html=True)

        resolved_my_team = resolve_my_team_name(teams_df["name"].tolist())
        if resolved_my_team and resolved_my_team != "RCD Escanyol":
            st.caption(
                f"ℹ️ RCD Escanyol collegata alla squadra Supabase **{resolved_my_team}**."
            )

        if auction_finished:
            st.success(
                "🎉 **ASTA CONCLUSA!** Tutte le squadre hanno completato "
                "le proprie rose."
            )
            current_role = "ALL"
        else:
            current_role = "ALL"

        # Il pannello contiene tutti e 5 i dropdown/controlli sulla stessa riga.
        my_team_name = get_my_team_name_from_state(state)
        my_team_row = teams_df[teams_df["name"] == my_team_name] if my_team_name else pd.DataFrame()
        st.session_state["my_team_budget"] = int(my_team_row.iloc[0]["remaining_budget"]) if not my_team_row.empty else 0

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

        # La Top 5 serve solo durante l'asta.
        if not auction_finished:
            render_top5(
                current_role,
                state.bought_player_ids,
                preferred_players,
                state,
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

        with st.expander("🛠️ Strumenti asta e diagnostica", expanded=False):
            render_team_analysis(
                teams_df,
                state,
                ratings,
            )
            render_admin_tools(
                teams_df,
                state,
            )

    with tab2:
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

    with tab3:
        render_all_players_tab()

    with tab4:
        render_player_modifiers_tab()

    with tab5:
        render_matchday_import_tab()

    with tab6:
        render_formation_lab_tab(state)

    with tab7:
        render_championship_lab_tab()


if __name__ == "__main__":
    main()
