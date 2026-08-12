import streamlit as st
from supabase import create_client

# Connessione
supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

st.set_page_config(page_title="RCD Escanol Auction", layout="wide")
st.title("⚽ RCD Escanol Auction Center")

# Recupero squadre dal DB
teams = supabase.table("teams").select("*").execute().data

# Sidebar: Visualizzazione Budget
st.sidebar.subheader("Budget Squadre")
for team in teams:
    st.sidebar.write(f"{team['name']}: {team['remaining_budget']} crediti")

# Command Bar
command = st.text_input("Comando (es: gollini 5 zaga)", placeholder="giocatore prezzo squadra")

if command:
    parts = command.split()
    if len(parts) >= 3:
        player, price, team_name = parts[0], parts[1], parts[2]
        st.write(f"Acquisto: {player} a {price} per {team_name}")
        # Qui aggiungeremo la logica di inserimento in tabella 'rosters'
