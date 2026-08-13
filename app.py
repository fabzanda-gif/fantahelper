import random
import pandas as pd
import streamlit as st
from supabase import create_client

# CONNESSIONE E CONFIGURAZIONE
supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
st.set_page_config(page_title="RCD Escanol Auction Center", layout="wide")
st.title("⚽ RCD Escanol - Live Auction Assistant")

# FUNZIONE CALCOLO INDEX SCORE (0-10)
def calculate_player_score(p):
    # BASE: 50% dal valore di listino (assumendo 50 come tetto massimo realistico per la normalizzazione)
    score = min(10, (p.get("list_price", 1) / 50) * 5)
    # BONUS/MALUS
    if p.get("status_titolarita") == "Titolare": score += 2
    elif p.get("status_titolarita") == "Riserva": score -= 2
    if p.get("rigorista"): score += 1.5
    if p.get("propensione_cartellini") == "A rischio malus": score -= 1
    if p.get("primo_anno_serie_a"): score -= 0.5
    return round(max(0, min(10, score)), 1)

# RECUPERO DATI E CALCOLO ANALITICO
rosters_data = supabase.table("rosters").select("purchase_price, teams(name), players(id, name, role, list_price, status_titolarita, rigorista, affidabilita_fisica, propensione_cartellini, slot_fantacalcio, primo_anno_serie_a)").execute().data

# SIDEBAR: VALUTAZIONE ROSA IN DECIMI
st.sidebar.subheader("📈 Valutazione Rosa")
team_names = [t["name"] for t in supabase.table("teams").select("name").execute().data]
selected_team_analysis = st.sidebar.selectbox("Analizza squadra", team_names, index=team_names.index("RCD Escanol") if "RCD Escanol" in team_names else 0, key="sidebar_team_analysis")

# CALCOLO DEL VOTO MEDIA
team_players = [r["players"] for r in rosters_data if r.get("teams") and r["teams"]["name"] == selected_team_analysis]
if team_players:
    total_score = sum(calculate_player_score(p) for p in team_players)
    avg_score = total_score / len(team_players)
    st.sidebar.metric("Voto Rosa", f"{avg_score:.1f} / 10.0")
    
    # BARRA DI PROGRESSIONE COLORE
    if avg_score >= 7.5: st.sidebar.success("Rosa da Scudetto!")
    elif avg_score >= 6.0: st.sidebar.info("Rosa competitiva.")
    else: st.sidebar.warning("Rosa da rinforzare.")
else:
    st.sidebar.info("Assegna giocatori per vedere il voto.")

# LOGICA AUTOCOMPILA INTERMEDIA (GIÀ DISPONIBILE)
# Il pulsante "Autocompila" utilizza già le variabili 'bought_player_ids' e 'sim_roles' 
# che tengono conto di quanto è già stato acquistato manualmente.

# ... resto del codice invariato ...
