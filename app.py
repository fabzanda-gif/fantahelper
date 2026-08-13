import random
import pandas as pd
import streamlit as st
from supabase import create_client

# Connessione a Supabase
supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

st.set_page_config(page_title="RCD Escanol Auction Center", layout="wide")
st.title("⚽ RCD Escanol - Live Auction Assistant")

# Limiti massimi per ruolo e totale per squadra
ROLE_LIMITS = {
    "P": 3,
    "D": 8,
    "C": 8,
    "A": 6
}
TOTAL_SLOTS_PER_TEAM = 25

# 1. Recupero delle squadre e dei roster dal DB
teams_data = (
    supabase.table("teams")
    .select("id, name, remaining_budget, initial_budget")
    .execute()
    .data
)
teams_df = pd.DataFrame(teams_data)

rosters_data = (
    supabase.table("rosters")
    .select("purchase_price, teams(name), players(id, name, role, team_nfl, list_price)")
    .execute()
    .data
)

# Estraiamo gli ID di tutti i giocatori già acquistati per filtrarli
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

# Verifichiamo quali ruoli sono completi per TUTTE le squadre
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


# --- CORPO CENTRALE (Prima definizione per catturare il ruolo attivo) ---
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


# --- SIDEBAR: TOP 5 E STRUMENTI ADMIN (Sincronizzati con `current_role`) ---
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
st.sidebar.subheader("🛠️ Strumenti Mockup & Admin")

# Pulsante per riempire randomicamente le rose
if st.sidebar.button("🎲 Autocompila rose (Mockup)"):
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
    p_price = player["list_price"] if player["list_price"] else 1

    valid_teams = []
    for t_name in sim_bought:
      if sim_bought[t_name] < TOTAL_SLOTS_PER_TEAM and sim_roles[t_name][p_role] < ROLE_LIMITS[p_role] and sim_budgets[t_name] >= p_price:
        valid_teams.append(t_name)

    if valid_teams:
      chosen_team = random.choice(valid_teams)
      inserts.append({
          "team_id": team_id_map[chosen_team],
          "player_id": player["id"],
          "purchase_price": p_price
      })
      sim_bought[chosen_team] += 1
      sim_roles[chosen_team][p_role] += 1
      sim_budgets[chosen_team] -= p_price

  if inserts:
    supabase.table("rosters").insert(inserts).execute()
    for t_name, new_budget in sim_budgets.items():
      supabase.table("teams").update({"remaining_budget": int(new_budget)}).eq("id", team_id_map[t_name]).execute()
    
    st.sidebar.success("Rose autocompilate con successo!")
    st.rerun()
  else:
    st.sidebar.warning("Nessun inserimento possibile (limiti raggiunti o budget esauriti).")

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
      "id, name, role, team_nfl, list_price"
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
        f"{p['name']} [{p['role']}] ({p['team_nfl']} - Listino:"
        f" {p['list_price']})": p
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
              f"❌ La squadra {target_team} non ha abbastanza crediti! (Budget"
              f" residuo: {current_budget})"
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
              f"✅ Acquistato **{selected_player['name']}** [{p_role}] a"
              f" **{purchase_price}** crediti per **{target_team}**!"
          )
          st.rerun()

# 3. Tabella Orizzontale / Dashboard della Situazione Crediti delle Squadre
st.divider()
st.subheader("📊 Panoramica Squadre & Disponibilità")

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
    
    teams_summary.append({
        "data": t,
        "bought": bought,
        "slots_left": slots_left,
        "avg_price": avg_price,
        "avg_spent": avg_spent_per_player,
        "role_counts": team_role_totals.get(t_name, {"P": 0, "D": 0, "C": 0, "A": 0})
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
          st.markdown("---")

# 4. Tabella delle Rose Acquistate Dettagliata
st.subheader("📋 Rose e Giocatori Assegnati")

if rosters_data:
  formatted_rosters = []
  for r in rosters_data:
    if r["teams"] and r["players"]:
      formatted_rosters.append({
          "Squadra": r["teams"]["name"],
          "Giocatore": r["players"]["name"],
          "Ruolo": r["players"]["role"],
          "Club Serie A": r["players"]["team_nfl"],
          "Prezzo Listino": r["players"]["list_price"],
          "Pagato": r["purchase_price"],
          "Rilancio": r["purchase_price"] - r["players"]["list_price"],
      })
  df_rosters = pd.DataFrame(formatted_rosters)
  st.dataframe(df_rosters, use_container_width=True)
else:
  st.info("Nessun giocatore ancora acquistato in questa sessione d'asta.")
