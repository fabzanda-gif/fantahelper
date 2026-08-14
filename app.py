import random, unicodedata, re, os, pandas as pd, streamlit as st
import streamlit.components.v1 as components
from supabase import create_client

# --- CONFIGURAZIONE E SETUP ---
st.set_page_config(page_title="RCD Escanyol Auction Center", layout="wide")
st.title("⚽ RCD Escanyol - Live Auction Assistant")
supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

ROLE_LIMITS = {"P": 3, "D": 8, "C": 8, "A": 6}
TOTAL_SLOTS_PER_TEAM = 25
TEAM_MAP = {"Napoli": "NAP", "Juventus": "JUV", "Milan": "MIL", "Inter": "INT", "Roma": "ROM", "Lazio": "LAZ", "Atalanta": "ATA", "Fiorentina": "FIO", "Torino": "TOR", "Bologna": "BOL", "Genoa": "GEN", "Sassuolo": "SAS", "Udinese": "UDI", "Cagliari": "CAG", "Verona": "VER", "Lecce": "LEC", "Cremonese": "CRE", "Parma": "PAR", "Como": "COM", "Pisa": "PIS"}

def normalize_string(s):
    return re.sub(r'[^a-zA-Z0-9\s]', '', "".join([c for c in unicodedata.normalize('NFKD', str(s)) if not unicodedata.combining(c)])).lower().strip()

@st.cache_data
def load_all_data():
    stats = pd.read_csv('player_aggregated_stats.csv') if os.path.exists('player_aggregated_stats.csv') else pd.DataFrame()
    mods = {}
    try:
        df = pd.read_csv('season-2526.csv')
        home = df.groupby('HomeTeam').agg(GF=('FTHG', 'sum'), GA=('FTAG', 'sum'), M=('FTHG', 'count')).reset_index().rename(columns={'HomeTeam': 'Team'})
        away = df.groupby('AwayTeam').agg(GF=('FTAG', 'sum'), GA=('FTHG', 'sum'), M=('FTAG', 'count')).reset_index().rename(columns={'AwayTeam': 'Team'})
        ts = pd.merge(home, away, on='Team', how='outer').fillna(0)
        ts['Matches'] = ts['M_x'] + ts['M_y']
        ts['TotalGF'] = ts['GF_x'] + ts['GF_y']
        ts['TotalGA'] = ts['GA_x'] + ts['GA_y']
        avg_gf, avg_ga = ts['TotalGF'].sum()/ts['Matches'].sum(), ts['TotalGA'].sum()/ts['Matches'].sum()
        for _, r in ts.iterrows():
            code = TEAM_MAP.get(r['Team'], r['Team'].upper()[:3])
            mods[code] = {"att": round(((r['TotalGF']/r['Matches'])-avg_gf)*0.8, 2), "def": round((avg_ga-(r['TotalGA']/r['Matches']))*0.9, 2)} if r['Matches'] > 0 else {"att": 0.0, "def": 0.0}
    except: pass
    return stats, mods

STATS, MODS = load_all_data()

def get_rating_data(p, pref_set=None):
    role = p.get("role", "D")
    p_name = normalize_string(p.get("name", ""))
    base, real, g, a, m = 5.0, False, 0, 0, 0
    if not STATS.empty and p_name:
        match = STATS[STATS['clean_name'].str.contains(p_name, na=False)]
        if not match.empty:
            r = match.iloc[0]
            g, a, m = r.get('goals', 0), r.get('assists', 0), r.get('matches', 0)
            if m > 3: base = r.get('avg_vote', 6.0) + ((g*0.12 + a*0.08) if role in ["A","C"] else (g*0.15 + a*0.10)); real = True
    if not real: base = (5.0 if role in ["A","P"] else 4.8 if role == "C" else 4.5) + ((p.get("list_price") or 1) * 0.04)
    tit = {"Titolare": 0.4, "Ballottaggio": -0.3, "Riserva": -1.5}.get(p.get("status_titolarita"), 0.0)
    tm = MODS.get(p.get("team_nfl"), {"att": 0.0, "def": 0.0})
    team_mod = tm["att"] if role in ["A", "C"] else tm["def"]
    rating = base + tit + team_mod + (0.8 if p.get("rigorista") else 0.0) + (-0.3 if p.get("propensione_cartellini") == "A rischio malus" else 0) + (-0.3 if p.get("primo_anno_serie_a") else 0) + (0.5 if (pref_set and p.get("id") in pref_set) else 0)
    final = round(max(1.0, min(10.0, rating)), 1)
    return {"final": final, "base": round(base, 2), "team_mod": team_mod, "g": int(g), "a": int(a)}

# --- UI ---
if "preferred_players" not in st.session_state: st.session_state.preferred_players = set()
rosters = supabase.table("rosters").select("*, teams(name), players(*)").execute().data
tab1, tab2, tab3 = st.tabs(["🎯 Live Asta", "📋 Rose & Analisi", "⭐️ Tutti i Giocatori"])

with tab1:
    st.subheader("🎯 Assegnazione Guidata Giocatore")
    # Logica asta qui...
    st.info("Logica asta attiva.")

with tab2:
    st.subheader("📋 Rose & Analisi")
    # Logica rose qui...
    st.info("Analisi rose attiva.")

with tab3:
    st.subheader("⭐️ Tutti i Giocatori (Rating)")
    all_p = supabase.table("players").select("*").execute().data
    data = []
    for p in all_p:
        d = get_rating_data(p, st.session_state.preferred_players)
        data.append({"Giocatore": p["name"], "Ruolo": p["role"], "Rating ⭐️": d["final"], "Base": d["base"], "Mod Squadra": d["team_mod"], "Gol": d["g"], "Ass": d["a"]})
    st.dataframe(pd.DataFrame(data).sort_values("Rating ⭐️", ascending=False), use_container_width=True)
