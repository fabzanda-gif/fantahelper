import random
import pandas as pd
import streamlit as st
from supabase import create_client

# CONNESSIONE AL DATABASE SUPABASE
supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

# CONFIGURAZIONE PAGINA
st.set_page_config(page_title="RCD Escanol Auction Center", layout="wide")
st.title("⚽ RCD Escanol - Live Auction Assistant")

# DEFINIZIONE LIMITI DI ROSA
ROLE_LIMITS = {"P": 3, "D": 8, "C": 8, "A": 6}
TOTAL_SLOTS_PER_TEAM = 25

# FUNZIONE PER IL CALCOLO DELLO SCORE GLOBALE (0-10)
def calculate_player_score(p):
    # BASE: 50% dal valore di listino (normalizzato su base 50)
    score = min(10, (p.get("list_price", 1) / 50) * 5)
    # MODIFICATORI QUALITATIVI
    if p.get("status_titolarita") == "Titolare": score += 2
    elif p.get("status_titolarita") == "Riserva": score -= 2
    if p.get("rigorista"): score += 1.5
    if p.get("propensione_cartellini") == "A rischio malus": score -= 1
    if p.get("primo_anno_serie_a"): score -= 0.5
    return round(max(0, min(10, score)), 1)

# RECUPERO DATI DAL DATABASE
teams_data = supabase.table("teams").select("id, name, remaining_budget, initial_budget").execute().data
teams_df = pd.DataFrame(teams_data)
rosters_data = supabase.table("rosters").select("purchase_price, teams(name), players(id, name, role, team_nfl, list_price, status_titolarita, rigorista, affidabilita_fisica, propensione_cartellini, slot_fantacalcio, primo_anno_serie_a)").execute().data

# ELABORAZIONE STATO ATTUALE DELLE ROSE
bought_player_ids = set()
team_role_totals = {t["name"]: {"P": 0, "D": 0, "C": 0, "A": 0} for t in teams_data}
team_total_bought = {t["name"]: 0 for t in teams_data}
team_players_map = {t["name"]: [] for t in teams_data}

if rosters_data:
    for r in rosters_data:
        if r.get("players"):
            bought_player_ids.add(r["players"]["id"])
            team_players_map[r["teams"]["name"]].append(r["players"])
            team_role_totals[r["teams"]["name"]][r["players"]["role"]] += 1
            team_total_bought[r["teams"]["name"]] += 1

auction_is_finished = all(bought >= TOTAL_SLOTS_PER_TEAM for bought in team_total_bought.values())

# LOGICA SELEZIONE RUOLO (ESCLUDE RUOLI COMPLETI)
role_mapping_full = {"Tutti i ruoli": "ALL", "Portieri (P)": "P", "Difensori (D)": "D", "Centrocampisti (C)": "C", "Attaccanti (A)": "A"}
completed_roles = [role for role, max_limit in ROLE_LIMITS.items() if all(team_role_totals[t][role] >= max_limit for t in team_role_totals)]
available_role_labels = {label: code for label, code in role_mapping_full.items() if code == "ALL" or code not in completed_roles}

# INTERFACCIA CENTRALE
st.subheader("🎯 Assegnazione Guidata Giocatore")
if auction_is_finished: st.success("🎉 **ASTA CONCLUSA!**")
else:
    col_r, col_t = st.columns(2)
    with col_r: current_role = available_role_labels[st.selectbox("1. Seleziona Ruolo", list(available_role_labels.keys()), key="main_role_select")]

# SIDEBAR ANALISI ASTA E VALUTAZIONE ROSA IN DECIMI
st.sidebar.subheader("🔮 Analisi Asta & Valutazione")
team_names = teams_df["name"].tolist()
selected_team = st.sidebar.selectbox("Analizza squadra", team_names, index=team_names.index("RCD Escanol") if "RCD Escanol" in team_names else 0, key="sidebar_team_analysis")

t_players = team_players_map[selected_team]
if t_players:
    avg_score = sum(calculate_player_score(p) for p in t_players) / len(t_players)
    st.sidebar.metric("Voto Rosa", f"{avg_score:.1f} / 10.0")
    # CONSIGLI STRATEGICI
    consigli = []
    if sum(1 for p in t_players if p["role"] == "P") < 3: consigli.append("• Completa i portieri.")
    for c in consigli: st.sidebar.write(c)

# STRUMENTI ADMIN (AUTOCOMPILA INTERMEDIO E RESET)
st.sidebar.divider()
st.sidebar.subheader("🛠️ Strumenti Mockup & Admin")
if st.sidebar.button("🎲 Autocompila rose (Intermedio)"):
    all_players = supabase.table("players").select("id, role, list_price").execute().data
    free = [p for p in all_players if p["id"] not in bought_player_ids]
    random.shuffle(free)
    # LA LOGICA AUTOCOMPILA RIPRENDE DAGLI SLOT RIMASTI
    for player in free:
        p_role = player["role"]
        valid = [t for t in team_total_bought if team_total_bought[t] < TOTAL_SLOTS_PER_TEAM and team_role_totals[t][p_role] < ROLE_LIMITS[p_role]]
        if valid:
            chosen = valid[0]
            supabase.table("rosters").insert({"team_id": teams_df[teams_df["name"]==chosen].iloc[0]["id"], "player_id": player["id"], "purchase_price": max(1, int(player.get("list_price", 1)))}).execute()
            team_total_bought[chosen] += 1
            team_role_totals[chosen][p_role] += 1
            bought_player_ids.add(player["id"])
    st.rerun()

if st.sidebar.button("🗑️ Reset Database", type="primary"):
    supabase.table("rosters").delete().gt("purchase_price", -1).execute()
    st.rerun()

# TABELLA DETTAGLIATA CON INSIGHTS
st.subheader("📋 Rose e Giocatori")
if rosters_data:
    st.dataframe(pd.DataFrame([{"Squadra": r["teams"]["name"], "Giocatore": r["players"]["name"], "Voto": calculate_player_score(r["players"]), "Ruolo": r["players"]["role"]} for r in rosters_data]), use_container_width=True)
