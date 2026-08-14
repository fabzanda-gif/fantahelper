import random
import unicodedata
import re
import os
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from supabase import create_client

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="RCD Escanyol Auction Center", layout="wide")
st.title("⚽ RCD Escanyol - Live Auction Assistant")

# --- CONNESSIONE DATABASE ---
supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

# --- COSTANTI ---
ROLE_LIMITS = {"P": 3, "D": 8, "C": 8, "A": 6}
TOTAL_SLOTS_PER_TEAM = 25

# --- STATO SESSIONE ---
if "show_celebration" not in st.session_state: st.session_state.show_celebration = None
if "audio_url" not in st.session_state: st.session_state.audio_url = None
if "preferred_players" not in st.session_state: st.session_state.preferred_players = set()

# --- FUNZIONI UTILI ---
def normalize_string(s):
    if not isinstance(s, str): return ""
    nfkd_form = unicodedata.normalize('NFKD', s)
    only_ascii = "".join([c for c in nfkd_form if not unicodedata.combining(c)])
    return re.sub(r'[^a-zA-Z0-9\s]', '', only_ascii).lower().strip()

@st.cache_data
def load_real_player_stats():
    if os.path.exists('player_aggregated_stats.csv'):
        return pd.read_csv('player_aggregated_stats.csv')
    return pd.DataFrame()

REAL_STATS_DF = load_real_player_stats()

@st.cache_data
def get_team_modifiers():
    team_map = {
        "Napoli": "NAP", "Juventus": "JUV", "Milan": "MIL", "Inter": "INT",
        "Roma": "ROM", "Lazio": "LAZ", "Atalanta": "ATA", "Fiorentina": "FIO",
        "Torino": "TOR", "Bologna": "BOL", "Genoa": "GEN", "Sassuolo": "SAS",
        "Udinese": "UDI", "Cagliari": "CAG", "Verona": "VER", "Lecce": "LEC",
        "Cremonese": "CRE", "Parma": "PAR", "Como": "COM", "Pisa": "PIS"
    }
    try:
        df_matches = pd.read_csv('season-2526.csv')
        home = df_matches.groupby('HomeTeam').agg(GF=('FTHG', 'sum'), GA=('FTAG', 'sum'), M=('FTHG', 'count')).reset_index().rename(columns={'HomeTeam': 'Team'})
        away = df_matches.groupby('AwayTeam').agg(GF=('FTAG', 'sum'), GA=('FTHG', 'sum'), M=('FTAG', 'count')).reset_index().rename(columns={'AwayTeam': 'Team'})
        ts = pd.merge(home, away, on='Team', how='outer').fillna(0)
        ts['Matches'] = ts['M_x'] + ts['M_y']
        ts['TotalGF'] = ts['GF_x'] + ts['GF_y']
        ts['TotalGA'] = ts['GA_x'] + ts['GA_y']
        
        avg_gf = ts['TotalGF'].sum() / ts['Matches'].sum() if ts['Matches'].sum() > 0 else 1.0
        avg_ga = ts['TotalGA'].sum() / ts['Matches'].sum() if ts['Matches'].sum() > 0 else 1.0
        
        modifiers = {}
        for _, row in ts.iterrows():
            code = team_map.get(row['Team'], row['Team'].upper()[:3])
            if row['Matches'] > 0:
                att_mod = ((row['TotalGF'] / row['Matches']) - avg_gf) * 0.8
                def_mod = (avg_ga - (row['TotalGA'] / row['Matches'])) * 0.9
                modifiers[code] = {"att": round(att_mod, 2), "def": round(def_mod, 2)}
            else:
                modifiers[code] = {"att": 0.0, "def": 0.0}
        return modifiers
    except: return {}

TEAM_MODIFIERS = get_team_modifiers()

def calculate_player_rating_detailed(p, preferred_players_set=None):
    role = p.get("role", "D")
    p_name_clean = normalize_string(p.get("name", ""))
    base_rating, has_real_stats = 5.0, False
    goals, assists, matches = 0, 0, 0
    
    if not REAL_STATS_DF.empty and p_name_clean:
        match = REAL_STATS_DF[REAL_STATS_DF['clean_name'].str.contains(p_name_clean, na=False)]
        if not match.empty:
            row = match.iloc[0]
            avg_vote = row.get('avg_vote', 6.0)
            goals, assists, matches = row.get('goals', 0), row.get('assists', 0), row.get('matches', 0)
            if matches > 3 and avg_vote > 0:
                base_rating = avg_vote + ((goals * 0.12) + (assists * 0.08) if role in ["A", "C"] else (goals * 0.15) + (assists * 0.10))
                has_real_stats = True

    if not has_real_stats:
        listino = p.get("list_price", 1) or 1
        base_rating = (5.0 if role in ["A", "P"] else 4.8 if role == "C" else 4.5) + (listino * 0.04)
    
    rating = base_rating
    titolarita = p.get("status_titolarita")
    titolarita_mod = 0.4 if titolarita == "Titolare" else (-0.3 if titolarita == "Ballottaggio" else (-1.5 if titolarita == "Riserva" else 0.0))
    rating += titolarita_mod

    team_mod = 0.0
    if p.get("team_nfl") in TEAM_MODIFIERS:
        team_mod = TEAM_MODIFIERS[p.get("team_nfl")]["att"] if role in ["A", "C"] else TEAM_MODIFIERS[p.get("team_nfl")]["def"]
        rating += team_mod

    has_malus = False
    rigorista_mod = 0.8 if p.get("rigorista") else 0.0
    cartellini_mod = -0.3 if p.get("propensione_cartellini") == "A rischio malus" else 0.0
    rookie_mod = -0.3 if p.get("primo_anno_serie_a") else 0.0
    pref_mod = 0.5 if (preferred_players_set and p.get("id") in preferred_players_set) else 0.0
    
    rating += rigorista_mod + cartellini_mod + rookie_mod + pref_mod
    if cartellini_mod < 0 or rookie_mod < 0 or titolarita in ["Ballottaggio", "Riserva"]: has_malus = True
    
    final_rating = round(max(1.0, min(10.0, rating)), 1)
    if (has_malus or p.get("primo_anno_serie_a")) and final_rating >= 10.0: final_rating = 9.0
        
    return {"base_or_fantamedia": round(base_rating, 2), "titolarita_mod": titolarita_mod, "team_mod": team_mod, 
            "bonus_rigorista": rigorista_mod, "malus_cartellini": cartellini_mod, "malus_rookie": rookie_mod, 
            "preferito_mod": pref_mod, "goals": int(goals), "assists": int(assists), "matches": int(matches), "final_rating": final_rating}

def calculate_player_rating(p, preferred_players_set=None):
    return calculate_player_rating_detailed(p, preferred_players_set)["final_rating"]

# --- RECUPERO DATI E INTERFACCIA ---
# (Il resto del codice resta invariato come nel precedente blocco di tab1, tab2, tab3)
# [Includi qui il codice delle tabelle e logica aste già consolidato]
