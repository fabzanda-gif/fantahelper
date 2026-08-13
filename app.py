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

# --- FUNZIONI ---
def play_sound(sound_url):
    sound_html = f"""
        <audio autoplay>
            <source src="{sound_url}" type="audio/mp3">
        </audio>
    """
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
    if preferred_players_set and p.get("id") in preferred_players_set:
        rating += 0.8
    return round(max(0, min(10, rating)), 1)

# --- RECUPERO DATI ---
teams_data = supabase.table("teams").select("id, name, remaining_budget, initial_budget").execute().data
teams_df = pd.DataFrame(teams_data)
rosters_data = supabase.table("rosters").select("purchase_price, teams(name), players(id, name, role, team_nfl, list_price, status_titolarita, rigorista, affidabilita_fisica, propensione_cartellini, slot_fantacalcio, primo_anno_serie_a)").execute().data

if "preferred_players" not in st.session_state: st.session_state.preferred_players = set()

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

# --- INTERFACCIA ---
tab1, tab2 = st.tabs(["🎯 Live Asta", "📋 Rose & Analisi"])

with tab1:
    col_r, col_t = st.columns(2)
    # Selezione ruolo...
    # [Logica semplificata per brevità nel blocco, qui va il tuo codice di selezione]
    
    # Conferma Acquisto con Audio
    if st.button("Conferma Acquisto", type="primary"):
        # ... logica inserimento db ...
        p_rtg = calculate_player_rating(selected_player, st.session_state.preferred_players)
        
        if target_team == "Escanyol":
            if p_rtg >= 8.0:
                st.balloons(); st.snow()
                play_sound("https://www.myinstants.com/media/sounds/john-cena-sound-effect.mp3")
                st.success(f"🔥 MASSIVE COLPO! **{selected_player['name']}** (Rating {p_rtg})! AND HIS NAME IS JOHN CENA! 🎺")
                if st.button("Continua Asta"): st.rerun()
            elif p_rtg >= 7.0:
                st.balloons()
                play_sound("https://www.myinstants.com/media/sounds/ta-da.mp3")
                st.success(f"🎉 Gran colpo! **{selected_player['name']}** (Rating {p_rtg}) per l'Escanyol!")
                if st.button("Continua Asta"): st.rerun()
            else:
                st.rerun()
        else:
            st.rerun()

    # Panoramica squadre con Escanyol evidenziato
    # [Codice panoramica squadre]

with tab2:
    # [Tutto il codice della tab 2 con la classifica e il voto asta]
    pass
