import pandas as pd
import streamlit as st
from supabase import create_client

# Connessione a Supabase
supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

st.set_page_config(page_title="RCD Escanol Auction Center", layout="wide")
st.title("⚽ RCD Escanol - Live Auction Assistant")

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
    .select("purchase_price, teams(name), players(name, role, team_nfl, list_price)")
    .execute()
    .data
)

# Sidebar: Strumenti Admin (Reset)
st.sidebar.subheader("🛠️ Strumenti Admin")
if st.sidebar.button("🗑️ Svuota tutte le rose (Reset)", type="primary"):
  supabase.table("rosters").delete().gt("purchase_price", -1).execute()
  for _, row in teams_df.iterrows():
    supabase.table("teams").update(
        {"remaining_budget": int(row["initial_budget"])}
    ).eq("id", row["id"]).execute()
  st.sidebar.success("Tutte le rose sono state svuotate e i budget resettati!")
  st.rerun()

# 2. Sezione Interattiva: Selezione Ruolo -> Squadra Serie A (Opzionale) -> Giocatore -> Prezzo -> Squadra
st.subheader("🎯 Assegnazione Guidata Giocatore")

col_r, col_t = st.columns(2)

with col_r:
  role_mapping = {
      "Tutti i ruoli": "ALL",
      "Portieri (P)": "P",
      "Difensori (D)": "D",
      "Centrocampisti (C)": "C",
      "Attaccanti (A)": "A",
  }
  selected_role_label = st.selectbox(
      "1. Seleziona Ruolo", list(role_mapping.keys())
  )
  current_role = role_mapping[selected_role_label]

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

if not players_data:
  st.warning("Nessun giocatore trovato con questi filtri.")
else:
  player_options = {
      f"{p['name']} [{p['role']}] ({p['team_nfl']} - Listino:"
      f" {p['list_price']})": p
      for p in players_data
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
    team_names = teams_df["name"].tolist() if not teams_df.empty else []
    target_team = st.selectbox("5. Squadra Acquirente", team_names)

  if st.button("Conferma Acquisto", type="primary"):
    team_row = teams_df[teams_df["name"] == target_team]
    if team_row.empty:
      st.error("Seleziona una squadra valida.")
    else:
      team_id = team_row.iloc[0]["id"]
      current_budget = team_row.iloc[0]["remaining_budget"]

      if purchase_price > current_budget:
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
            f"✅ Acquistato **{selected_player['name']}** a"
            f" **{purchase_price}** crediti per **{target_team}**!"
        )
        st.rerun()

# 3. Tabella Orizzontale / Dashboard della Situazione Crediti delle Squadre
st.divider()
st.subheader("📊 Panoramica Squadre & Disponibilità")

if not teams_df.empty:
  # Calcoliamo quanti giocatori ha comprato ciascuna squadra
  bought_counts = {}
  if rosters_data:
    for r in rosters_data:
      if r["teams"]:
        t_name = r["teams"]["name"]
        bought_counts[t_name] = bought_counts.get(t_name, 0) + 1

  # Dividiamo le 12 squadre in righe da 4 colonne per una visualizzazione pulita in orizzontale
  teams_per_row = 4
  teams_list = teams_df.to_dict(orient="records")

  for i in range(0, len(teams_list), teams_per_row):
    cols = st.columns(teams_per_row)
    for j, col in enumerate(cols):
      if i + j < len(teams_list):
        t = teams_list[i + j]
        t_name = t["name"]
        rem_budget = t["remaining_budget"]
        init_budget = t["initial_budget"]
        bought = bought_counts.get(t_name, 0)
        # Rosa standard ipotizzata a 25 elementi
        slots_left = max(0, 25 - bought)
        avg_price = (
            round(rem_budget / slots_left, 1) if slots_left > 0 else 0
        )

        with col:
          st.markdown(f"**{t_name}**")
          st.metric(
              label="Budget",
              value=f"{rem_budget} cr",
              delta=f"{rem_budget - init_budget} cr",
          )
          st.text(f"Comprati: {bought}/25 | Mancano: {slots_left}")
          st.text(f"Media max/giocatore: {avg_price} cr")
          # Semplice barra di progresso per visualizzare il budget residuo
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
