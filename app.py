import random
import pandas as pd
import streamlit as st
from supabase import create_client

# CONNESSIONE AL DATABASE SUPABASE
supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

st.set_page_config(page_title="RCD Escanyol Auction Center", layout="wide")
st.title("⚽ RCD Escanyol - Live Auction Assistant")

# LIMITI MASSIMI PER RUOLO E TOTALE PER SQUADRA
ROLE_LIMITS = {
    "P": 3,
    "D": 8,
    "C": 8,
    "A": 6
}
TOTAL_SLOTS_PER_TEAM = 25

# NUOVA FUNZIONE RATING PIÙ GENEROSA (RAGGIUNGIBILE IL 10 CON I TOP)
def calculate_player_rating(p):
    # Partiamo da una base di 6.5
    rating = 6.5 
    listino = p.get("list_price", 1)
    
    # Valore di listino molto premiante per i top player
    if listino >= 30: rating += 3.5
    elif listino >= 20: rating += 2.5
    elif listino >= 10: rating += 1.0
    elif listino >= 5: rating += 0.5
    
    # Titolarità e Ruoli chiave
    if p.get("status_titolarita") == "Titolare": rating += 1.5
    elif p.get("status_titolarita") == "Riserva": rating -= 1.5
    
    if p.get("rigorista"): rating += 1.5
    
    # Malus attenuati per non rovinare i top
    if p.get("propensione_cartellini") == "A rischio malus": rating -= 0.3
    if p.get("primo_anno_serie_a"): rating -= 0.2
    
    return round(max(0, min(10, rating)), 1)

# 1. RECUPERO DELLE SQUADRE E DEI ROSTER DAL DB (INCLUSI TUTTI GLI INSIGHTS)
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

# ESTRAZIONE DEGLI ID E CONTEGGIO STATO ATTUALE DELLE SQUADRE
bought_player_ids = set()
team_role_totals = {t["name"]: {"P": 0, "D": 0, "C": 0, "A": 0} for t in teams_data}
team_total_bought = {t["name"]: 0 for t in teams_data}
team_players_map = {t["name"]: [] for t in teams_data}

if rosters_data:
  for r in rosters_data:
    if r.get("players") and r["players"].get("id"):
      bought_player_ids.add(r["players"]["id"])
    if r.get("teams") and r.get("players"):
      t_name = r["teams"]["name"]
      p_role = r["players"]["role"]
      team_players_map[t_name].append(r["players"])
      if t_name in team_role_totals and p_role in team_role_totals[t_name]:
        team_role_totals[t_name][p_role] += 1
        team_total_bought[t_name] += 1

# VERIFICA RUOLI COMPLETI PER TUTTE LE SQUADRE
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

available_role_labels = {}
for label, code in role_mapping_full.items():
  if code == "ALL" or code not in completed_roles:
    available_role_labels[label] = code

# --- CORPO CENTRALE (Selezione Ruolo Attivo) ---
st.subheader("🎯 Assegnazione Guidata Giocatore")

if auction_is_finished:
  st.success("🎉 **ASTA CONCLUSA!** Tutte le squadre hanno completato le proprie rose.")
  current_role = "ALL"
else:
  col_r, col_t = st.columns(2)

  with col_r:
    selected_role_label_main = st.selectbox(
        "1. Seleziona Ruolo", list(available_role_labels.keys()), key="main_role_select"
    )
    current_role = available_role_labels[selected_role_label_main]

  if current_role in completed_roles:
    st.info(f"ℹ️ Il ruolo **{current_role}** è completo per tutte le squadre.")

# --- SIDEBAR: TOP 5 E STRUMENTI ADMIN ---
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

st.sidebar.divider()
st.sidebar.subheader("🔮 Analisi Asta & Valutazione")

# Seleziona la squadra da analizzare (Default: RCD Escanyol)
team_names = teams_df["name"].tolist()
default_team = "RCD Escanyol" if "RCD Escanyol" in team_names else (team_names[0] if team_names else None)
default_idx = team_names.index(default_team) if default_team else 0

selected_team_analysis = st.sidebar.selectbox(
    "Analizza squadra", 
    team_names, 
    index=default_idx, 
    key="sidebar_team_analysis"
)

if selected_team_analysis:
    t_players = team_players_map.get(selected_team_analysis, [])
    bought_count = len(t_players)
    
    team_budgets_sorted = teams_df.sort_values(by="remaining_budget", ascending=False).reset_index(drop=True)
    team_rank_row = team_budgets_sorted[team_budgets_sorted["name"] == selected_team_analysis]
    
    if not team_rank_row.empty:
        credit_rank = team_rank_row.index[0] + 1
        total_teams_count = len(teams_df)
        budget = team_rank_row.iloc[0]["remaining_budget"]
    else:
        credit_rank, total_teams_count, budget = 0, len(teams_df), 0

    slots_left = TOTAL_SLOTS_PER_TEAM - bought_count
    
    if t_players:
        avg_score = sum(calculate_player_rating(p) for p in t_players) / len(t_players)
        st.sidebar.metric("Rating Rosa", f"{avg_score:.1f} / 10.0")
        if avg_score >= 8.0: st.sidebar.success("Rosa da Scudetto!")
        elif avg_score >= 6.5: st.sidebar.info("Rosa competitiva.")
        else: st.sidebar.warning("Rosa da rinforzare.")
    else:
        st.sidebar.metric("Rating Rosa", "N/D")
        st.sidebar.info("Assegna giocatori per calcolare il rating.")
    
    st.sidebar.markdown(f"💰 **Posizione Crediti:** {credit_rank}° su {total_teams_count} ({budget} cr residui)")
    if slots_left > 0:
        avg_spendable = budget / slots_left
        st.sidebar.caption(f"Spesa media potenziale: **{avg_spendable:.1f} cr/slot** ({slots_left} slot liberi)")

    sidebar_alerts = []
    
    nfl_counts = {}
    for p in t_players:
      if p.get("role") != "P":
        club = p.get("team_nfl")
        if club: nfl_counts[club] = nfl_counts.get(club, 0) + 1
    for club, count in nfl_counts.items():
      if count >= 4: sidebar_alerts.append(f"🚨 **Rischio Blocco:** {count} giocatori su {club}")

    ballotaggio_count = sum(1 for p in t_players if p.get("status_titolarita") == "Ballottaggio")
    if bought_count >= 5 and ballotaggio_count >= (bought_count * 0.4):
      sidebar_alerts.append(f"⚠️ **Troppi Ballottaggi:** {ballotaggio_count} giocatori")

    cartellini_count = sum(1 for p in t_players if p.get("propensione_cartellini") == "A rischio malus")
    if cartellini_count >= 3:
      sidebar_alerts.append(f"🟨 **Rischio Malus:** {cartellini_count} a rischio cartellino")

    rookie_count = sum(1 for p in t_players if p.get("primo_anno_serie_a"))
    if rookie_count >= 3:
      sidebar_alerts.append(f"👶 **Rischio Rookie:** {rookie_count} al primo anno in A")

    if sidebar_alerts:
        st.sidebar.markdown("**Alert Squadra:**")
        for alert in sidebar_alerts:
            st.sidebar.markdown(alert)
    else:
        st.sidebar.caption("✅ Nessun alert di rilievo per questa rosa.")

st.sidebar.divider()
st.sidebar.subheader("🛠️ Strumenti Mockup & Admin")

ruolo_mockup = st.sidebar.selectbox("Completa ruolo (Mockup)", ["Tutti"] + list(ROLE_LIMITS.keys()))

if st.sidebar.button("🎲 Autocompila rose (Intermedio)"):
  all_players_res = supabase.table("players").select("id, role, list_price").execute().data
  free_players = [p for p in all_players_res if p["id"] not in bought_player_ids]
  if ruolo_mockup != "Tutti":
      free_players = [p for p in free_players if p["role"] == ruolo_mockup]
  random.shuffle(free_players)

  sim_bought = team_total_bought.copy()
  sim_roles = {t: team_role_totals[t].copy() for t in team_role_totals}
  sim_budgets = {t["name"]: t["remaining_budget"] for t in teams_data}
  team_id_map = {t["name"]: t["id"] for t in teams_data}

  inserts = []
  for player in free_players:
    p_role = player["role"]
    base_price = player["list_price"] if player["list_price"] and player["list_price"] > 0 else 1

    valid_teams = []
    for t_name in sim_bought:
      if sim_bought[t_name] < TOTAL_SLOTS_PER_TEAM and sim_roles[t_name][p_role] < ROLE_LIMITS[p_role]:
        valid_teams.append(t_name)

    if valid_teams:
      def score_team(t):
        slots_left = TOTAL_SLOTS_PER_TEAM - sim_bought[t]
        if slots_left <= 0: return -1
        return sim_budgets[t] / slots_left

      valid_teams.sort(key=score_team, reverse=True)
      chosen_team = valid_teams[0]

      slots_left = TOTAL_SLOTS_PER_TEAM - sim_bought[chosen_team]
      current_bud = sim_budgets[chosen_team]

      if slots_left == 1:
        purchase_price = max(1, int(current_bud))
      else:
        avg_allowed = current_bud / slots_left
        purchase_price = max(1, int((base_price + avg_allowed) / 2))
        if purchase_price > current_bud - (slots_left - 1):
          purchase_price = max(1, int(current_bud - (slots_left - 1)))

      inserts.append({
          "team_id": team_id_map[chosen_team],
          "player_id": player["id"],
          "purchase_price": purchase_price
      })
      sim_bought[chosen_team] += 1
      sim_roles[chosen_team][p_role] += 1
      sim_budgets[chosen_team] -= purchase_price

  if inserts:
    supabase.table("rosters").insert(inserts).execute()
    for t_name, new_budget in sim_budgets.items():
      supabase.table("teams").update({"remaining_budget": max(0, int(new_budget))}).eq("id", team_id_map[t_name]).execute()
    
    st.sidebar.success("Rose autocompilate con successo!")
    st.rerun()
  else:
    st.sidebar.warning("Nessun inserimento possibile o limiti già raggiunti.")

if st.sidebar.button("🗑️ Svuota tutte le rose (Reset)", type="primary"):
  supabase.table("rosters").delete().gt("purchase_price", -1).execute()
  for _, row in teams_df.iterrows():
    supabase.table("teams").update(
        {"remaining_budget": int(row["initial_budget"])}
    ).eq("id", row["id"]).execute()
  st.sidebar.success("Tutte le rose sono state svuotate e i budget resettati!")
  st.rerun()

# --- CONTINUAZIONE CORPO CENTRALE ---
if not auction_is_finished:
  query_base = supabase.table("players").select("team_nfl")
  if current_role != "ALL":
    query_base = query_base.eq("role", current_role)

  all_role_players = query_base.execute().data
  available_nfl_teams = (
      sorted(list(set([p["team_nfl"] for p in all_role_players if p["team_nfl"]])))
      if all_role_players
      else []
  )

  with col_t:
    nfl_filter = st.selectbox(
        "2. Filtra per Squadra Serie A (Opzionale)",
        ["Tutte le squadre"] + available_nfl_teams,
    )

  final_query = supabase.table("players").select(
      "id, name, role, team_nfl, list_price, status_titolarita, rigorista, affidabilita_fisica, propensione_cartellini, slot_fantacalcio, primo_anno_serie_a"
  )
  if current_role != "ALL":
    final_query = final_query.eq("role", current_role)
  if nfl_filter != "Tutte le squadre":
    final_query = final_query.eq("team_nfl", nfl_filter)

  players_data = final_query.order("name").execute().data
  available_players = [p for p in players_data if p["id"] not in bought_player_ids]

  if not available_players:
    st.warning("Nessun giocatore disponibile trovato con questi filtri.")
  else:
    player_options = {
        f"{p['name']} [{p['role']}] ({p['team_nfl']} - Listino: {p['list_price']})": p
        for p in available_players
    }

    col1, col2, col3 = st.columns([3, 1, 2])

    with col1:
      selected_player_label = st.selectbox(
          "3. Seleziona Giocatore", list(player_options.keys())
      )
      selected_player = player_options[selected_player_label]

    with col2:
      default_price = (
          selected_player["list_price"] if selected_player["list_price"] else 1
      )
      purchase_price = st.number_input(
          "4. Costo", min_value=1, max_value=500, value=int(default_price)
      )

    with col3:
      active_teams = []
      for _, t in teams_df.iterrows():
        t_name = t["name"]
        p_role = selected_player["role"]
        if team_total_bought[t_name] < TOTAL_SLOTS_PER_TEAM and team_role_totals[t_name][p_role] < ROLE_LIMITS[p_role]:
          active_teams.append(t_name)

      target_team = st.selectbox("5. Squadra Acquirente", active_teams if active_teams else teams_df["name"].tolist())

    if st.button("Conferma Acquisto", type="primary"):
      team_row = teams_df[teams_df["name"] == target_team]
      if team_row.empty:
        st.error("Seleziona una squadra valida.")
      else:
        team_id = team_row.iloc[0]["id"]
        current_budget = team_row.iloc[0]["remaining_budget"]
        p_role = selected_player["role"]

        team_role_count = team_role_totals[target_team][p_role]
        max_limit = ROLE_LIMITS.get(p_role, TOTAL_SLOTS_PER_TEAM)

        if team_role_count >= max_limit:
          st.error(f"❌ Limite raggiunto! La squadra **{target_team}** ha già completato i posti per il ruolo {p_role} ({team_role_count}/{max_limit}).")
        elif team_total_bought[target_team] >= TOTAL_SLOTS_PER_TEAM:
          st.error(f"❌ La squadra **{target_team}** ha completato la rosa (25/25).")
        elif purchase_price > current_budget:
          st.error(
              f"❌ La squadra {target_team} non ha abbastanza crediti! (Budget residuo: {current_budget})"
          )
        else:
          supabase.table("rosters").insert({
              "team_id": team_id,
              "player_id": selected_player["id"],
              "purchase_price": purchase_price,
          }).execute()

          new_budget = current_budget - purchase_price
          supabase.table("teams").update({"remaining_budget": int(new_budget)}).eq(
              "id", team_id
          ).execute()

          st.success(
              f"✅ Acquistato **{selected_player['name']}** [{p_role}] a **{purchase_price}** crediti per **{target_team}**!"
          )
          st.rerun()

# 3. PANORAMICA SQUADRE & ALERT STRATEGICI
st.divider()
st.subheader("📊 Panoramica Squadre & Alert Strategici")

if not teams_df.empty:
  teams_summary = []

  for _, t in teams_df.iterrows():
    t_name = t["name"]
    rem_budget = t["remaining_budget"]
    bought = team_total_bought[t_name]
    spent = sum([r.get("purchase_price", 0) for r in rosters_data if r.get("teams") and r["teams"]["name"] == t_name])
    avg_spent_per_player = round(spent / bought, 1) if bought > 0 else 0.0
    
    slots_left = max(0, TOTAL_SLOTS_PER_TEAM - bought)
    avg_price = round(rem_budget / slots_left, 1) if slots_left > 0 else 0
    
    t_players = team_players_map.get(t_name, [])
    
    team_avg_score = sum(calculate_player_rating(p) for p in t_players) / len(t_players) if t_players else 0.0
    top_players_count = sum(1 for p in t_players if p.get("slot_fantacalcio") == "1° Slot" or (p.get("list_price") or 0) >= 25)

    alerts = []
    
    nfl_counts = {}
    club_players_map = {}
    for p in t_players:
      if p.get("role") != "P":
        club = p.get("team_nfl")
        if club:
          nfl_counts[club] = nfl_counts.get(club, 0) + 1
          club_players_map.setdefault(club, []).append(f"{p.get('name')} [{p.get('role')}]")
    
    for club, count in nfl_counts.items():
      if count >= 4:
        alerts.append({
            "text": f"🚨 **Rischio Blocco:** {count} giocatori di movimento su {club}",
            "help": f"Giocatori di movimento del club {club}:\n- " + "\n- ".join(club_players_map[club])
        })

    ballotaggio_players = [f"{p.get('name')} [{p.get('role')}]" for p in t_players if p.get("status_titolarita") == "Ballottaggio"]
    if bought >= 5 and len(ballotaggio_players) >= (bought * 0.4):
      alerts.append({
          "text": f"⚠️ **Troppi Ballottaggi:** {len(ballotaggio_players)} giocatori",
          "help": "Giocatori in ballottaggio:\n- " + "\n- ".join(ballotaggio_players)
      })

    cartellini_players = [f"{p.get('name')} [{p.get('role')}]" for p in t_players if p.get("propensione_cartellini") == "A rischio malus"]
    if len(cartellini_players) >= 3:
      alerts.append({
          "text": f"🟨 **Rischio Malus:** {len(cartellini_players)} a rischio cartellino",
          "help": "Giocatori a rischio malus:\n- " + "\n- ".join(cartellini_players)
      })

    rookie_players = [f"{p.get('name')} [{p.get('role')}]" for p in t_players if p.get("primo_anno_serie_a")]
    if len(rookie_players) >= 3:
      alerts.append({
          "text": f"👶 **Rischio Rookie:** {len(rookie_players)} al primo anno in A",
          "help": "Giocatori al primo anno in Serie A:\n- " + "\n- ".join(rookie_players)
      })

    if bought == 0:
        status_msg = "📭 Rosa ancora vuota."
    else:
        risk_count = len(alerts)
        if risk_count == 0: risk_desc = "pochi rischi"
        elif risk_count == 1: risk_desc = "1 rischio potenziale"
        else: risk_desc = f"{risk_count} criticità da monitorare"
            
        status_msg = f"✨ Rating: **{team_avg_score:.1f}** ({top_players_count} Top) — {risk_desc}."

    teams_summary.append({
        "data": t,
        "bought": bought,
        "slots_left": slots_left,
        "avg_price": avg_price,
        "avg_spent": avg_spent_per_player,
        "role_counts": team_role_totals.get(t_name, {"P": 0, "D": 0, "C": 0, "A": 0}),
        "alerts": alerts,
        "status_msg": status_msg
    })

  teams_summary.sort(key=lambda x: (-x["avg_price"], -x["data"]["remaining_budget"], x["data"]["name"]))

  teams_per_row = 4
  for i in range(0, len(teams_summary), teams_per_row):
    cols = st.columns(teams_per_row)
    for j, col in enumerate(cols):
      if i + j < len(teams_summary):
        item = teams_summary[i + j]
        t = item["data"]
        t_name = t["name"]
        rem_budget = t["remaining_budget"]
        init_budget = t["initial_budget"]
        avg_price = item["avg_price"]
        avg_spent = item["avg_spent"]
        bought = item["bought"]
        rc = item["role_counts"]
        alerts = item["alerts"]
        status_msg = item["status_msg"]

        role_string = f"**P** {rc.get('P', 0)}/{ROLE_LIMITS['P']} | **D** {rc.get('D', 0)}/{ROLE_LIMITS['D']} | **C** {rc.get('C', 0)}/{ROLE_LIMITS['C']} | **A** {rc.get('A', 0)}/{ROLE_LIMITS['A']}"

        with col:
          st.markdown(f"**{t_name}**")
          delta_text = f"{avg_spent} cr/giocatore" if bought > 0 else "N/A"
          st.metric(
              label="Budget",
              value=f"{rem_budget} cr",
              delta=delta_text,
              delta_color="off"
          )
          st.markdown(role_string)
          st.text(f"Media max/giocatore: {avg_price} cr")
          st.progress(max(0.0, min(1.0, rem_budget / init_budget)))
          
          st.markdown(f"*{status_msg}*")

          if alerts:
            for alert in alerts:
              st.markdown(alert["text"], help=alert["help"])
            
          st.markdown("---")

# 4. TABELLA DELLE ROSE ACQUISTATE DETTAGLIATA (CON FILTRO SQUADRA E PRESELEZIONE RCD ESCANYOL)
st.subheader("📋 Rose e Giocatori Assegnati (con Insights & Rating)")

if rosters_data:
  formatted_rosters = []
  for r in rosters_data:
    if r["teams"] and r["players"]:
      p = r["players"]
      listino = p.get("list_price") or 1
      player_score = calculate_player_rating(p)
      
      formatted_rosters.append({
          "Squadra": r["teams"]["name"],
          "Giocatore": p["name"],
          "Ruolo": p["role"],
          "Rating": player_score,
          "Club Serie A": p["team_nfl"],
          "Listino": listino,
          "Pagato": r["purchase_price"],
          "Differenza": r["purchase_price"] - listino,  # Rinominato da 'rilancio' a 'differenza'
          "Slot": p.get("slot_fantacalcio", "Scommessa"),
          "Titolarità": p.get("status_titolarita", "Titolare"),
          "Rigorista": "Sì" if p.get("rigorista") else "No",
          "Fisico": p.get("affidabilita_fisica", "Integro"),
          "Cartellini": p.get("propensione_cartellini", "Normale"),
          "1° Anno A": "Sì" if p.get("primo_anno_serie_a") else "No"
      })
  
  df_rosters = pd.DataFrame(formatted_rosters)
  
  # Filtro per squadra nella tabella finale con preselezione su "RCD Escanyol"
  all_teams_filter = ["Tutte"] + team_names
  default_table_idx = all_teams_filter.index("RCD Escanyol") if "RCD Escanyol" in all_teams_filter else 0
  
  filtro_tabella = st.selectbox("Filtra per Squadra", all_teams_filter, index=default_table_idx, key="table_team_filter")
  if filtro_tabella != "Tutte":
      df_rosters = df_rosters[df_rosters["Squadra"] == filtro_tabella]
      
  st.dataframe(df_rosters, use_container_width=True)
else:
  st.info("Nessun giocatore ancora acquistato in questa sessione d'asta.")
