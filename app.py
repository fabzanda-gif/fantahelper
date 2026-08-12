{\rtf1\ansi\ansicpg1252\cocoartf2870
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\fswiss\fcharset0 Helvetica;}
{\colortbl;\red255\green255\blue255;}
{\*\expandedcolortbl;;}
\paperw11900\paperh16840\margl1440\margr1440\vieww11520\viewh8400\viewkind0
\pard\tx720\tx1440\tx2160\tx2880\tx3600\tx4320\tx5040\tx5760\tx6480\tx7200\tx7920\tx8640\pardirnatural\partightenfactor0

\f0\fs24 \cf0 import pandas as pd\
import streamlit as st\
\
st.set_page_config(\
    page_title="Fantacalcio Auction Helper", layout="wide"\
)\
\
st.title("\uc0\u9917  Fantacalcio Live Assistant")\
\
# Inizializziamo lo stato della sessione per i crediti e le rose\
if "budget_iniziale" not in st.session_state:\
  st.session_state.budget_iniziale = 500\
  st.session_state.crediti_residui = 500\
\
st.sidebar.header("Gestione Lega")\
st.sidebar.metric(\
    label="I Miei Crediti Residui", value=st.session_state.crediti_residui\
)\
\
# Area centrale per la Command Bar (inserimento rapido)\
st.subheader("Inserimento Rapido")\
command = st.text_input(\
    "Digita comando (es: teo 18)",\
    placeholder="es. barella 25",\
    help="Premi invio per registrare l'acquisto",\
)\
\
if command:\
  st.success(f"Comando ricevuto: \{command\}")\
  # Qui metteremo la logica di parsing}