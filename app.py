import random
import pandas as pd
import streamlit as st
from supabase import create_client

# CONNESSIONE AL DATABASE SUPABASE
supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

# CONFIGURAZIONE PAGINA E TITOLO
st.set_page_config(page_title="RCD Escanol Auction Center", layout="wide")
st.title("⚽ RCD Escanol - Live Auction Assistant")

# DEFINIZIONE COSTANTI E LIMITI DI ROSA
ROLE_LIMITS = {
    "P": 3,
    "D": 8,
    "C": 8,
    "A": 6
}
TOTAL_SLOTS_PER_TEAM = 25

# RECUPERO DATI SQUADRE E ROSTER DAL DATABASE
teams_data = (
    supabase.table("teams")
    .select("id, name, remaining_budget, initial_budget")
    .execute()
    .data
)
teams_df = pd.DataFrame(teams_data)

rosters_data = (
    supabase.table("rosters")
    .select("purchase_price, teams(name), players(id, name, role, team_nfl, list_price, status_titolarita, rigorista, affidabilita_fisica, propensione_cartellini, slot_fantacalcio, primo_anno_serie_a)")
    .execute()
    .data
)

# ELABORAZIONE STATO ATTUALE DELLE ROSE E GIOCATORI ACQUISTATI
bought_player_ids = set()
team_role_totals = {t["name"]: {"P": 0, "D": 0, "C": 0, "A": 0} for t in teams_data}
team_total_bought = {t["name"]: 0 for t in teams_data}

if rosters_data:
  for r in rosters_data:
    if r.get("players") and r["players"].get("id"):
      bought_player_ids.add(r["players"]["id"])
    if r.get("teams") and r.get("players"):
      t_name = r["teams"]["name"]
      p_role = r["players"]["role"]
      if t_name in team_role_totals and p_role in team_role_totals[t_name]:
        team_role_totals[t_name][p_role] += 1
        team_total_bought[t_name] += 1

# CALCOLO RUOLI COMPLETATI PER TUTTE LE SQUADRE
completed_roles = []
for role, max_limit in ROLE_LIMITS.items():
  all_teams_completed_role = True
  for t_name, counts in team_role_totals.items():
    if counts[role] < max_limit:
      all_teams_completed_role = False
      break
  if all_teams_completed_role:
    completed_roles.append(role)

auction_is_finished = all(bought >= TOTAL_SLOTS_PER_TEAM for bought in team_total_bought.values())

role_mapping_full = {
    "Tutti i ruoli": "ALL",
    "Portieri (P)": "P",
    "Difensori (D)": "D",
    "Centrocampisti (C)": "C",
    "Attaccanti (A)": "A",
}

available_role_labels = {label: code for label, code in role_mapping_full.items() if code == "ALL" or code not in completed_roles}

# INTERFACCIA CENTRALE PER ASSEGNAZIONE GIOCATORI
st.subheader("🎯 Assegnazione Guidata Giocatore")

if auction_is_finished:
  st.success("🎉 **ASTA CONCLUSA!** Tutte le squadre hanno completato le proprie rose.")
  current_role = "ALL"
else:
  col_r, col_t = st.columns(2)
  with col_r:
    selected_role_label_main = st.selectbox("1. Seleziona Ruolo", list(available_role_labels.keys()), key="main_role_select")
    current_role = available_role_labels[selected_role_label_main]
  if current_role in completed_roles:
    st.info(f"ℹ️ Il ruolo **{current_role}** è completo per tutte le squadre.")

# SIDEBAR CON TOP 5 GIOCATORI LIBERI
st.sidebar.subheader("🔥 Top 5 Liberi")
top5_query = supabase.table("players").select("id, name, role, team_nfl, list_price")
if current_role != "ALL":
  top5_query = top5_query.eq("role", current_role)
top5_data = top5_query.order("list_price", desc=True).execute().data
top5_available = [p for p in top5_data if p["id"] not in bought_player_ids][:5]

with st.sidebar.container(border=True):
  if top5_available:
    for idx, p in enumerate(top5_available, 1):
      st.markdown(f"**{idx}. {p['name']}** `[{p['role']}]` ({p['team_nfl']}) — 💎 **{p['list_price']} cr**")
  else:
    st.info("Nessun giocatore disponibile.")

# SIDEBAR ANALISI ASTA E CONSIGLI STRATEGICI
st.sidebar.divider()
st.sidebar.subheader("🔮 Analisi Asta & Consigli")
selected_team_analysis = st.sidebar.selectbox("Analizza squadra", teams_df["name"].tolist())

# LOGICA DI GENERAZIONE CONSIGLI
if selected_team_analysis:
    t_players = [r["players"] for r in rosters_data if r.get("teams") and r["teams"]["name"] == selected_team_analysis]
    bought_count = len(t_players)
    budget = teams_df[teams_df["name"] == selected_team_analysis]["remaining_budget"].values[0]
    slots_left = TOTAL_SLOTS_PER_TEAM - bought_count
    
    p_count = sum(1 for p in t_players if p["role"] == "P")
    d_count = sum(1 for p in t_players if p["role"] == "D")
    c_count = sum(1 for p in t_players if p["role"] == "C")
    a_count = sum(1 for p in t_players if p["role"] == "A")
    
    consigli = []
    if p_count < 3: consigli.append(f"• Ti mancano {3-p_count} portieri.")
    if d_count < 8: consigli.append(f"• Cerca {8-d_count} difensori titolari.")
    if c_count < 8: consigli.append(f"• Ti servono {8-c_count} centrocampisti.")
    if a_count < 6: consigli.append(f"• Completa l'attacco con {6-a_count} giocatori.")
    
    if slots_left > 0:
        avg_spendable = budget / slots_left
        consigli.append(f"• Hai {avg_spendable:.1f} cr/slot disponibili.")
            
    if consigli:
        st.sidebar.markdown("**Consigli strategici:**")
        for consiglio in consigli: st.sidebar.write(consiglio)
    else: st.sidebar.success("Rosa completa!")

# SIDEBAR STRUMENTI AMMINISTRATIVI (AUTOCOMPILA E RESET)
st.sidebar.divider()
st.sidebar.subheader("🛠️ Strumenti Mockup & Admin")
if st.sidebar.button("🎲 Autocompila rose (Mockup Intelligente)"):
    # LOGICA DI AUTO-COMPILAZIONE INTELLIGENTE
    all_players_res = supabase.table("players").select("id, role, list_price").execute().data
    free_players = [p for p in all_players_res if p["id"] not in bought_player_ids]
    random.shuffle(free_players)
    sim_bought = team_total_bought.copy()
    sim_roles = {t: team_role_totals[t].copy() for t in team_role_totals}
    sim_budgets = {t["name"]: t["remaining_budget"] for t in teams_data}
    team_id_map = {t["name"]: t["id"] for t in teams_data}
    inserts = []
    for player in free_players:
        p_role = player["role"]
        base_price = player["list_price"] if player["list_price"] else 1
        valid_teams = [t_name for t_name in sim_bought if sim_bought[t_name] < TOTAL_SLOTS_PER_TEAM and sim_roles[t_name][p_role] < ROLE_LIMITS[p_role]]
        if valid_teams:
            valid_teams.sort(key=lambda t: sim_budgets[t] / (TOTAL_SLOTS_PER_TEAM - sim_bought[t]), reverse=True)
            chosen_team = valid_teams[0]
            slots_left = TOTAL_SLOTS_PER_TEAM - sim_bought[chosen_team]
            purchase_price = max(1, int(sim_budgets[chosen_team])) if slots_left == 1 else max(1, int((base_price + (sim_budgets[chosen_team]/slots_left))/2))
            inserts.append({"team_id": team_id_map[chosen_team], "player_id": player["id"], "purchase_price": purchase_price})
            sim_bought[chosen_team] += 1
            sim_roles[chosen_team][p_role] += 1
            sim_budgets[chosen_team] -= purchase_price
    if inserts:
        supabase.table("rosters").insert(inserts).execute()
        for t_name, new_budget in sim_budgets.items(): supabase.table("teams").update({"remaining_budget": max(0, int(new_budget))}).eq("id", team_id_map[t_name]).execute()
        st.rerun()

if st.sidebar.button("🗑️ Svuota tutte le rose (Reset)", type="primary"):
    supabase.table("rosters").delete().gt("purchase_price", -1).execute()
    for _, row in teams_df.iterrows(): supabase.table("teams").update({"remaining_budget": int(row["initial_budget"])}).eq("id", row["id"]).execute()
    st.rerun()

# --- CONTINUAZIONE CORPO CENTRALE ---
if not auction_is_finished:
    # FILTRAGGIO GIOCATORI E CONFERMA ACQUISTO
    query_base = supabase.table("players").select("team_nfl").eq("role", current_role) if current_role != "ALL" else supabase.table("players").select("team_nfl")
    available_nfl_teams = sorted(list(set([p["team_nfl"] for p in query_base.execute().data if p["team_nfl"]])))
    with col_t: nfl_filter = st.selectbox("2. Filtra per Squadra Serie A (Opzionale)", ["Tutte le squadre"] + available_nfl_teams)
    
    final_query = supabase.table("players").select("id, name, role, team_nfl, list_price, status_titolarita, rigorista, affidabilita_fisica, propensione_cartellini, slot_fantacalcio, primo_anno_serie_a")
    if current_role != "ALL": final_query = final_query.eq("role", current_role)
    if nfl_filter != "Tutte le squadre": final_query = final_query.eq("team_nfl", nfl_filter)
    
    players_data = final_query.order("name").execute().data
    available_players = [p for p in players_data if p["id"] not in bought_player_ids]
    
    if available_players:
        player_options = {f"{p['name']} [{p['role']}] ({p['team_nfl']} - Listino: {p['list_price']})": p for p in available_players}
        col1, col2, col3 = st.columns([3, 1, 2])
        with col1: selected_player = player_options[st.selectbox("3. Seleziona Giocatore", list(player_options.keys()))]
        with col2: purchase_price = st.number_input("4. Costo", min_value=1, value=int(selected_player["list_price"] or 1))
        with col3: 
            active_teams = [t["name"] for _, t in teams_df.iterrows() if team_total_bought[t["name"]] < TOTAL_SLOTS_PER_TEAM and team_role_totals[t["name"]][selected_player["role"]] < ROLE_LIMITS[selected_player["role"]]]
            target_team = st.selectbox("5. Squadra Acquirente", active_teams if active_teams else teams_df["name"].tolist())
        
        if st.button("Conferma Acquisto", type="primary"):
            team_row = teams_df[teams_df["name"] == target_team]
            supabase.table("rosters").insert({"team_id": team_row.iloc[0]["id"], "player_id": selected_player["id"], "purchase_price": purchase_price}).execute()
            supabase.table("teams").update({"remaining_budget": int(team_row.iloc[0]["remaining_budget"] - purchase_price)}).eq("id", team_row.iloc[0]["id"]).execute()
            st.rerun()

# PANORAMICA SQUADRE E ALERT STRATEGICI
st.divider()
st.subheader("📊 Panoramica Squadre & Alert Strategici")
if not teams_df.empty:
    teams_summary = []
    for _, t in teams_df.iterrows():
        t_players = [r["players"] for r in rosters_data if r.get("teams") and r["teams"]["name"] == t["name"]]
        alerts = []
        # LOGICA ALERT CON DETTAGLIO TOOLTIP
        nfl_counts, club_map = {}, {}
        for p in t_players:
            if p.get("role") != "P":
                club = p.get("team_nfl")
                if club:
                    nfl_counts[club] = nfl_counts.get(club, 0) + 1
                    club_map.setdefault(club, []).append(f"{p.get('name')} [{p.get('role')}]")
        for club, count in nfl_counts.items():
            if count >= 4: alerts.append({"text": f"🚨 **Rischio Blocco:** {count} su {club}", "help": f"Giocatori:\n- " + "\n- ".join(club_map[club])})
        
        # AGGIUNTA ALTRI ALERT (BALLOTTAGGI, CARTELLINI, ROOKIE)
        if len([p for p in t_players if p.get("status_titolarita") == "Ballottaggio"]) >= (len(t_players) * 0.4): alerts.append({"text": "⚠️ **Troppi Ballottaggi**", "help": "Troppi giocatori a rischio voto"})
        if len([p for p in t_players if p.get("propensione_cartellini") == "A rischio malus"]) >= 3: alerts.append({"text": "🟨 **Rischio Malus**", "help": "Troppi giocatori cattivi"})
        if len([p for p in t_players if p.get("primo_anno_serie_a")]) >= 3: alerts.append({"text": "👶 **Rischio Rookie**", "help": "Troppi giocatori al primo anno"})
        
        teams_summary.append({"data": t, "bought": team_total_bought[t["name"]], "rc": team_role_totals[t["name"]], "alerts": alerts})
    
    for i in range(0, len(teams_summary), 4):
        cols = st.columns(4)
        for j, col in enumerate(cols):
            if i + j < len(teams_summary):
                item = teams_summary[i + j]
                with col:
                    st.markdown(f"**{item['data']['name']}**")
                    st.metric("Budget", f"{item['data']['remaining_budget']} cr")
                    st.markdown(f"**P** {item['rc']['P']} | **D** {item['rc']['D']} | **C** {item['rc']['C']} | **A** {item['rc']['A']}")
                    for alert in item['alerts']: st.markdown(alert["text"], help=alert["help"])
                    st.markdown("---")

# TABELLA DETTAGLIATA ROSE
st.subheader("📋 Rose e Giocatori Assegnati (con Insights)")
if rosters_data:
    st.dataframe(pd.DataFrame([{"Squadra": r["teams"]["name"], "Giocatore": r["players"]["name"], "Ruolo": r["players"]["role"], "Pagato": r["purchase_price"], "Slot": r["players"].get("slot_fantacalcio"), "Titolarità": r["players"].get("status_titolarita"), "1° Anno A": "Sì" if r["players"].get("primo_anno_serie_a") else "No"} for r in rosters_data]), use_container_width=True)
