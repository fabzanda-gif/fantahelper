import pandas as pd
import streamlit as st
from supabase import create_client

# Connessione a Supabase
supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

st.set_page_config(
    page_title="RCD Escanol Auction Center", layout="wide"
)
st.title("⚽ RCD Escanol - Live Auction Assistant")

# 1. Recupero delle squadre dal DB
teams_data = (
    supabase.table("teams")
    .select("id, name, remaining_budget, initial_budget")
    .execute()
    .data
)
teams_df = pd.DataFrame(teams_data)

# Sidebar: Situazione Crediti
st.sidebar.header("📊 Situazione Crediti")
if not teams_df.empty:
  for _, row in teams_df.iterrows():
    st.sidebar.metric(
        label=f"{row['name']}",
        value=f"{row['remaining_budget']} / {row['initial_budget']}",
    )

# 2. Sezione Interattiva: Selezione Ruolo -> Giocatore -> Prezzo -> Squadra
st.subheader("🎯 Assegnazione Guidata Giocatore")

# Step A: Selezione Ruolo (Partendo dai portieri come richiesto)
role_mapping = {
    "Portieri (P)": "P",
    "Difensori (D)": "D",
    "Centrocampisti (C)": "C",
    "Attaccanti (A)": "A",
}
selected_role_label = st.selectbox("1. Seleziona Ruolo", list(role_mapping.keys()))
current_role = role_mapping[selected_role_label]

# Recupero i giocatori liberi o del listone per il ruolo selezionato
# (Per ora prendiamo tutti quelli del ruolo dal database)
players_data = (
    supabase.table("players")
    .select("id, name, team_nfl, list_price")
    .eq("role", current_role)
    .order("name")
    .execute()
    .data
)

if not players_data:
  st.warning(f"Nessun giocatore trovato per il ruolo {current_role}.")
else:
  # Creiamo un dizionario e una lista formattata per la selectbox con ricerca
  player_options = {
      f"{p['name']} ({p['team_nfl']} - Listino: {p['list_price']})": p
      for p in players_data
  }

  col1, col2, col3 = st.columns([3, 1, 2])

  with col1:
    # Step B & C: Campo di ricerca / Lookup del giocatore
    selected_player_label = st.selectbox(
        "2. Seleziona Giocatore", list(player_options.keys())
    )
    selected_player = player_options[selected_player_label]

  with col2:
    # Step D: Inserimento Costo (preimpostato sul prezzo di listino come comodo suggerimento)
    default_price = (
        selected_player["list_price"]
        if selected_player["list_price"]
        else 1
    )
    purchase_price = st.number_input(
        "3. Costo", min_value=1, max_value=500, value=int(default_price)
    )

  with col3:
    # Step E: Dropdown con il nome della squadra
    team_names = teams_df["name"].tolist() if not teams_df.empty else []
    target_team = st.selectbox("4. Squadra Acquirente", team_names)

  # Pulsante di conferma acquisto
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
        # Registra l'acquisto nella tabella rosters
        supabase.table("rosters").insert({
            "team_id": team_id,
            "player_id": selected_player["id"],
            "purchase_price": purchase_price,
        }).execute()

        # Aggiorna il budget della squadra
        new_budget = current_budget - purchase_price
        supabase.table("teams").update({"remaining_budget": new_budget}).eq(
            "id", team_id
        ).execute()

        st.success(
            f"✅ Acquistato **{selected_player['name']}** a"
            f" **{purchase_price}** crediti per **{target_team}**!"
        )
        st.rerun()

# 3. Tabella delle Rose Acquistate
st.divider()
st.subheader("📋 Rose e Giocatori Assegnati")

rosters_data = (
    supabase.table("rosters")
    .select(
        "purchase_price, teams(name), players(name, role, team_nfl,"
        " list_price)"
    )
    .execute()
    .data
)

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
