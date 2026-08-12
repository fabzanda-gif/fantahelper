import pandas as pd
import streamlit as st
from supabase import create_client

# Connessione a Supabase usando i secrets
supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

st.set_page_config(page_title="RCD Escanol Auction Center", layout="wide")
st.title("⚽ RCD Escanol - Live Auction Helper")

# 1. Recupero delle squadre e dei crediti aggiornati dal DB
teams_data = (
    supabase.table("teams")
    .select("id, name, remaining_budget, initial_budget")
    .execute()
    .data
)
teams_df = pd.DataFrame(teams_data)

# Sidebar: Pannello di controllo delle squadre
st.sidebar.header("📊 Situazione Crediti")
if not teams_df.empty:
  for _, row in teams_df.iterrows():
    st.sidebar.metric(
        label=f"{row['name']}",
        value=f"{row['remaining_budget']} / {row['initial_budget']}",
    )

# 2. Sezione centrale: Command Bar per l'inserimento rapido
st.subheader("⚡ Inserimento Rapido Asta")
st.markdown(
    "Sintassi comando: `[nome_giocatore] [prezzo] [nome_squadra]` (es:"
    " `barella 40 RCD Escanol`)"
)

command = st.text_input(
    "Command Bar", placeholder="es. barella 40 RCD Escanol", label_visibility="collapsed"
)

if command:
  parts = command.strip().split()
  if len(parts) >= 3:
    # L'ultima parte è la squadra, la penultima è il prezzo, tutto il resto è il nome del giocatore
    try:
      price = int(parts[-1])
      target_team = " ".join(parts[-3:-1])  # Supporta nomi squadra a due parole
      player_query = " ".join(parts[:-2]).upper()

      # Se la squadra non viene trovata, proviamo a prenderne l'ultima come prezzo e l'ultima parola come squadra
      # Semplificazione: cerchiamo la squadra esatta nel database
      team_match = teams_df[
          teams_df["name"].str.lower() == " ".join(parts[-1:]).lower()
      ]
      if not team_match.empty:
        price = int(parts[-2])
        target_team = parts[-1]
        player_query = " ".join(parts[:-2]).upper()
      else:
        # Tentativo con squadra a due parole
        team_match = teams_df[
            teams_df["name"].str.lower()
            == " ".join(parts[-2:]).lower()
        ]
        if not team_match.empty:
          price = int(parts[-3])
          target_team = " ".join(parts[-2:])
          player_query = " ".join(parts[:-3]).upper()

      # Ridisattiva il match delle squadre
      team_row = teams_df[
          teams_df["name"].str.lower() == target_team.lower()
      ]

      if team_row.empty:
        st.error(
            f"❌ Squadra '{target_team}' non trovata! Controlla il nome esatto."
        )
      else:
        team_id = team_row.iloc[0]["id"]
        current_budget = team_row.iloc[0]["remaining_budget"]

        # Cerca il giocatore nel database
        player_res = (
            supabase.table("players")
            .select("id, name, role, list_price")
            .ilike("name", f"%{player_query}%")
            .execute()
            .data
        )

        if not player_res:
          st.warning(
              f"⚠️ Giocatore '{player_query}' non trovato nel listone di"
              " Supabase."
          )
        elif len(player_res) > 1:
          st.info(
              "Trovati più giocatori simili:"
              + ", ".join([p["name"] for p in player_res])
              + ". Sii più specifico."
          )
        else:
          player = player_res[0]
          # Registra l'acquisto nella tabella rosters e aggiorna il budget
          supabase.table("rosters").insert({
              "team_id": team_id,
              "player_id": player["id"],
              "purchase_price": price,
          }).execute()

          new_budget = current_budget - price
          supabase.table("teams").update({"remaining_budget": new_budget}).eq(
              "id", team_id
          ).execute()

          st.success(
              f"✅ Acquistato **{player['name']}** ({player['role']}) a"
              f" **{price}** crediti per **{target_team.upper()}**!"
          )
          st.rerun()

    except ValueError:
      st.error(
          "❌ Errore nel formato del prezzo. Assicurati che sia un numero."
      )
  else:
    st.error(
        "❌ Comando incompleto. Usa la sintassi: `giocatore prezzo squadra`"
    )

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
