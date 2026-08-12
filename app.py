import pandas as pd
import streamlit as st

st.set_page_config(page_title="Fantacalcio Auction Helper", layout="wide")

st.title("⚽ Fantacalcio Live Assistant")

# Inizializziamo lo stato della sessione per i crediti e le rose
if "budget_iniziale" not in st.session_state:
    st.session_state.budget_iniziale = 500
    st.session_state.crediti_residui = 500

st.sidebar.header("Gestione Lega")
st.sidebar.metric(
    label="I Miei Crediti Residui", value=st.session_state.crediti_residui
)

# Area centrale per la Command Bar (inserimento rapido)
st.subheader("Inserimento Rapido")
command = st.text_input(
    "Digita comando (es: teo 18)",
    placeholder="es. barella 25",
    help="Premi invio per registrare l'acquisto",
)

if command:
    st.success(f"Comando ricevuto: {command}")
