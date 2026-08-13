import random
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

# --- STATO SESSIONE PER FESTA ---
if "show_celebration" not in st.session_state: st.session_state.show_celebration = None
if "audio_url" not in st.session_state: st.session_state.audio_url = None
if "preferred_players" not in st.session_state: st.session_state.preferred_players = set()

# --- FUNZIONI ---
def play_sound(sound_url):
    sound_html = f"""<audio autoplay><source src="{sound_url}" type="audio/mp3"></audio>"""
    components.html(sound_html, height=0, width=0)

def calculate_player_rating(p, preferred_players_set=None):
    rating = 6.5 
    listino = p.get("list_price", 1)
    if listino >= 30: rating += 3.5
    elif listino >= 20: rating += 2.5
    elif listino >= 10: rating += 1.0
    elif listino >= 5: rating += 0.5
    if p.get("status_titolarita") == "Titolare": rating += 1.5
    elif p.get("status_titolarita") == "Riserva": rating -= 1.5
    if p.get("rigorista"): rating += 1.5
    if p.get("propensione_cartellini") == "A rischio malus": rating -= 0.3
    if p.get("primo_anno_serie_a"): rating -= 0.2
    if preferred_players_set and p.get("id") in preferred_players_set: rating += 0.8
    return round(max(0, min(10, rating)), 1)

# --- RECUPERO DATI ---
teams_data = supabase.table("teams").select("id, name, remaining_budget, initial_budget").execute().data
teams_df = pd.DataFrame(teams_data)
rosters_data = supabase.table("rosters").select("purchase_price, teams(name), players(id, name, role, team_nfl, list_price, status_titolarita, rigorista, affidabilita_fisica, propensione_cartellini, slot_fantacalcio, primo_anno_serie_a)").execute().data

bought_player_ids = set()
team_role_totals = {t["name"]: {"P": 0, "D": 0, "C": 0, "A": 0} for t in teams_data}
team_total_bought = {t["name"]: 0 for t in teams_data}
team_players_map = {t["name"]: [] for t in teams_data}
team_purchases_map = {t["name"]: [] for t in teams_data}

if rosters_data:
    for r in rosters_data:
        if r.get("players"):
            bought_player_ids.add(r["players"]["id"])
            t_name = r["teams"]["name"]
            team_players_map[t_name].append(r["players"])
            team_purchases_map[t_name].append(r)
            if r["players"]["role"] in team_role_totals[t_name]:
                team_role_totals[t_name][r["players"]["role"]] += 1
                team_total_bought[t_name] += 1

all_teams_ratings = {name: (sum(calculate_player_rating(p, st.session_state.preferred_players) for p in pl) / len(pl) if pl else 0.0) for name, pl in team_players_map.items()}
rating_rank_map = {name: idx + 1 for idx, (name, _) in enumerate(sorted(all_teams_ratings.items(), key=lambda x: x[1], reverse=True))}

# --- GESTIONE FESTA (PRIMA DI TUTTO) ---
if st.session_state.show_celebration:
    st.balloons(); st.snow()
    play_sound(st.session_state.audio_url)
    st.success(st.session_state.show_celebration)
    if st.button("Continua Asta"):
        st.session_state.show_celebration = None
        st.rerun()
    st.stop()

# --- INTERFACCIA ---
tab1, tab2 = st.tabs(["🎯 Live Asta", "📋 Rose & Analisi"])

with tab1:
    col_r, col_t = st.columns(2)
    # Selezione Ruolo
    selected_role_label_main = st.selectbox("1. Seleziona Ruolo", ["Tutti i ruoli", "Portieri (P)", "Difensori (D)", "Centrocampisti (C)", "Attaccanti (A)"], key="main_role_select")
    role_map = {"Tutti i ruoli": "ALL", "Portieri (P)": "P", "Difensori (D)": "D", "Centrocampisti (C)": "C", "Attaccanti (A)": "A"}
    current_role = role_map[selected_role_label_main]

    # Sidebar
    st.sidebar.subheader("🔥 Top 5 Liberi (Ranking)")
    top5_query = supabase.table("players").select("id, name, role, team_nfl, list_price, status_titolarita, rigorista, propensione_cartellini, primo_anno_serie_a")
    if current_role != "ALL": top5_query = top5_query.eq("role", current_role)
    top5_data = top5_query.execute().data
    free_players = [p for p in top5_data if p["id"] not in bought_player_ids]
    free_players.sort(key=lambda x: calculate_player_rating(x, st.session_state.preferred_players), reverse=True)
    
    with st.sidebar.container(border=True):
        for idx, p in enumerate(free_players[:5], 1):
            rtg = calculate_player_rating(p, st.session_state.preferred_players)
            st.markdown(f"**{idx}. {p['name']}** `[{p['role']}]` ⭐️ **{rtg}** | 💎 **{p['list_price']} cr**")

    # Analisi squadra
    selected_team = st.sidebar.selectbox("Analizza squadra", teams_df["name"].tolist(), index=teams_df["name"].tolist().index("Escanyol") if "Escanyol" in teams_df["name"].tolist() else 0)
    # (Inserisci qui il resto della logica sidebar alert e acquisto)
    
    # Conferma Acquisto (LOGICA FESTA)
    # ... nel tuo blocco if st.button("Conferma Acquisto"): ...
    # Se squadra == "Escanyol":
    #    st.session_state.show_celebration = "..."
    #    st.session_state.audio_url = "..."
    #    st.rerun()

with tab2:
    # Tabella rose e Pagelle Asta
    pass
