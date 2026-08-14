import random
import unicodedata
import re
import os
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from supabase import create_client

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="RCD Escanyol Auction Center", layout="wide")
st.title("⚽ RCD Escanyol - Live Auction Assistant")

# --- CONNESSIONE DATABASE ---
supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

# --- COSTANTI ---
ROLE_LIMITS = {"P": 3, "D": 8, "C": 8, "A": 6}
TOTAL_SLOTS_PER_TEAM = 25

# --- STATO SESSIONE PER FESTA ---
if "show_celebration" not in st.session_state: st.session_state.show_celebration = None
if "audio_url" not in st.session_state: st.session_state.audio_url = None
if "preferred_players" not in st.session_state: st.session_state.preferred_players = set()

# --- FUNZIONI DI NORMALIZZAZIONE E DATI ESTERNI ---
def normalize_string(s):
    if not isinstance(s, str):
        return ""
    nfkd_form = unicodedata.normalize('NFKD', s)
    only_ascii = "".join([c for c in nfkd_form if not unicodedata.combining(c)])
    return re.sub(r'[^a-zA-Z0-9\s]', '', only_ascii).lower().strip()

@st.cache_data
def load_real_player_stats():
    try:
        if os.path.exists('player_aggregated_stats.csv'):
            return pd.read_csv('player_aggregated_stats.csv')
    except Exception as e:
        pass
    return pd.DataFrame()

REAL_STATS_DF = load_real_player_stats()

@st.cache_data
def get_team_modifiers():
    try:
        df_matches = pd.read_csv('season-2526.csv')
        home = df_matches.groupby('HomeTeam').agg(
            GF=('FTHG', 'sum'), GA=('FTAG', 'sum'), M=('FTHG', 'count')
        ).reset_index().rename(columns={'HomeTeam': 'Team'})
        
        away = df_matches.groupby('AwayTeam').agg(
            GF=('FTAG', 'sum'), GA=('FTHG', 'sum'), M=('FTAG', 'count')
        ).reset_index().rename(columns={'AwayTeam': 'Team'})
        
        ts = pd.merge(home, away, on='Team', how='outer').fillna(0)
        ts['Matches'] = ts['M_x'] + ts['M_y']
        ts['TotalGF'] = ts['GF_x'] + ts['GF_y']
        ts['TotalGA'] = ts['GA_x'] + ts['GA_y']
        
        avg_gf_league = ts['TotalGF'].sum() / ts['Matches'].sum() if ts['Matches'].sum() > 0 else 1.0
        avg_ga_league = ts['TotalGA'].sum() / ts['Matches'].sum() if ts['Matches'].sum() > 0 else 1.0
        
        modifiers = {}
        for _, row in ts.iterrows():
            team = row['Team']
            matches = row['Matches']
            if matches > 0:
                team_gf_per_match = row['TotalGF'] / matches
                team_ga_per_match = row['TotalGA'] / matches
                att_mod = (team_gf_per_match - avg_gf_league) * 0.8
                def_mod = (avg_ga_league - team_ga_per_match) * 0.9
                modifiers[team] = {"att": round(att_mod, 2), "def": round(def_mod, 2)}
            else:
                modifiers[team] = {"att": 0.0, "def": 0.0}
        return modifiers
    except Exception as e:
        return {}

TEAM_MODIFIERS = get_team_modifiers()

def play_sound(sound_url):
    sound_html = f"""<audio autoplay><source src="{sound_url}" type="audio/mp3"></audio>"""
    components.html(sound_html, height=0, width=0)

def calculate_player_rating_detailed(p, preferred_players_set=None):
    """Calcola il rating restituendo anche i dettagli dei contributi per la Tab 3"""
    role = p.get("role", "D")
    p_name_clean = normalize_string(p.get("name", ""))
    
    base_rating = 5.0
    has_real_stats = False
    goals, assists, matches, avg_vote = 0, 0, 0, 0.0
    
    if not REAL_STATS_DF.empty and p_name_clean:
        match = REAL_STATS_DF[REAL_STATS_DF['clean_name'].str.contains(p_name_clean, na=False)]
        if not match.empty:
            row = match.iloc[0]
            avg_vote = row.get('avg_vote', 6.0)
            goals = row.get('goals', 0)
            assists = row.get('assists', 0)
            matches = row.get('matches', 0)
            
            if matches > 3:
                base_rating = avg_vote
                if role in ["A", "C"]:
                    base_rating += (goals * 0.12) + (assists * 0.08)
                else:
                    base_rating += (goals * 0.15) + (assists * 0.10)
                has_real_stats = True

    if not has_real_stats:
        listino = p.get("list_price", 1)
        if listino is None: listino = 1
        if role == "A": base_rating = 5.5 + (listino * 0.08)
        elif role == "C": base_rating = 5.0 + (listino * 0.06)
        elif role == "P": base_rating = 5.0 + (listino * 0.05)
        else: base_rating = 4.5 + (listino * 0.05)
    
    rating = base_rating
    
    titolarita = p.get("status_titolarita")
    titolarita_mod = 0.0
    if titolarita == "Titolare": titolarita_mod = 0.4
    elif titolarita == "Ballottaggio": titolarita_mod = -0.3
    elif titolarita == "Riserva": titolarita_mod = -1.5
    rating += titolarita_mod

    team_mod = 0.0
    team_serie_a = p.get("team_nfl")
    if team_serie_a in TEAM_MODIFIERS:
        mods = TEAM_MODIFIERS[team_serie_a]
        if role in ["A", "C"]: team_mod = mods["att"]
        elif role in ["D", "P"]: team_mod = mods["def"]
        rating += team_mod

    has_malus = False
    rigorista_mod = 1.2 if p.get("rigorista") else 0.0
    if p.get("rigorista"): rating += 0.8
    
    cartellini_mod = -0.3 if p.get("propensione_cartellini") == "A rischio malus" else 0.0
    if cartellini_mod < 0: has_malus = True; rating += cartellini_mod
        
    rookie_mod = -0.3 if p.get("primo_anno_serie_a") else 0.0
    if rookie_mod < 0: has_malus = True; rating += rookie_mod

    if titolarita in ["Ballottaggio", "Riserva"]:
        has_malus = True
    
    pref_mod = 0.5 if (preferred_players_set and p.get("id") in preferred_players_set) else 0.0
    rating += pref_mod
        
    final_rating = round(max(1.0, min(10.0, rating)), 1)
    if has_malus and final_rating >= 10.0:
        final_rating = 9.0
        
    details = {
        "base_or_fantamedia": round(base_rating, 2),
        "titolarita_mod": titolarita_mod,
        "team_mod": team_mod,
        "bonus_rigorista": 0.8 if p.get("rigorista") else 0.0,
        "malus_cartellini": cartellini_mod,
        "malus_rookie": rookie_mod,
        "preferito_mod": pref_mod,
        "goals": int(goals),
        "assists": int(assists),
        "matches": int(matches),
        "final_rating": final_rating
    }
    return details

def calculate_player_rating(p, preferred_players_set=None):
    return calculate_player_rating_detailed(p, preferred_players_set)["final_rating"]

# --- RECUPERO DATI ---
teams_data = supabase.table("teams").select("id, name, remaining_budget, initial_budget").execute().data
teams_df = pd.DataFrame(teams_data)
rosters_data = supabase.table("rosters").select("id, purchase_price, teams(name), players(id, name, role, team_nfl, list_price, status_titolarita, rigorista, affidabilita_fisica, propensione_cartellini, slot_fantacalcio, primo_anno_serie_a)").execute().data

bought_player_ids = set()
team_role_totals = {t["name"]: {"P": 0, "D": 0, "C": 0, "A": 0} for t in teams_data}
team_total_bought = {t["name"]: 0 for t in teams_data}
team_players_map = {t["name"]: [] for t in teams_data}
team_purchases_map = {t["name"]: [] for t in teams_data}

if rosters_data:
    for r in rosters_data:
        if r.get("players"):
            bought_player_ids.add(r["players"]["id"])
            t_name = r["teams"]["name"]
            team_players_map[t_name].append(r["players"])
            team_purchases_map[t_name].append(r)
            if r["players"]["role"] in team_role_totals[t_name]:
                team_role_totals[t_name][r["players"]["role"]] += 1
                team_total_bought[t_name] += 1

all_teams_ratings = {name: (sum(calculate_player_rating(p, st.session_state.preferred_players) for p in pl) / len(pl) if pl else 0.0) for name, pl in team_players_map.items()}
rating_rank_map = {name: idx + 1 for idx, (name, _) in enumerate(sorted(all_teams_ratings.items(), key=lambda x: x[1], reverse=True))}
total_teams_count = len(teams_df)

completed_roles = []
for role, max_limit in ROLE_LIMITS.items():
    all_teams_completed_role = True
    for t_name, counts in team_role_totals.items():
        if counts[role] < max_limit:
            all_teams_completed_role = False
            break
    if all_teams_completed_role: completed_roles.append(role)

auction_is_finished = all(bought >= TOTAL_SLOTS_PER_TEAM for bought in team_total_bought.values())

role_mapping_full = {
    "Tutti i ruoli": "ALL",
    "Portieri (P)": "P",
    "Difensori (D)": "D",
    "Centrocampisti (C)": "C",
    "Attaccanti (A)": "A",
}

available_role_labels = {label: code for label, code in role_mapping_full.items() if code == "ALL" or code not in completed_roles}

# --- GESTIONE FESTA ---
if st.session_state.show_celebration:
    st.balloons(); st.snow()
    play_sound(st.session_state.audio_url)
    st.success(st.session_state.show_celebration)
    if st.button("Continua Asta"):
        st.session_state.show_celebration = None
        st.rerun()
    st.stop()

# --- INTERFACCIA (3 TAB) ---
tab1, tab2, tab3 = st.tabs(["🎯 Live Asta", "📋 Rose & Analisi", "⭐️ Tutti i Giocatori (Rating)"])

with tab1:
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

    # --- SIDEBAR: TOP 5 LIBERI (RANKING) ---
    st.sidebar.subheader("🔥 Top 5 Liberi (Ranking)")
    top5_query = supabase.table("players").select("id, name, role, team_nfl, list_price, status_titolarita, rigorista, propensione_cartellini, primo_anno_serie_a")
    if current_role != "ALL":
        top5_query = top5_query.eq("role", current_role)
    top5_data = top5_query.execute().data
    
    free_players = [p for p in top5_data if p["id"] not in bought_player_ids]
    free_players.sort(key=lambda x: calculate_player_rating(x, st.session_state.preferred_players), reverse=True)
    top5_available = free_players[:5]

    with st.sidebar.container(border=True):
        if top5_available:
            for idx, p in enumerate(top5_available, 1):
                p_rtg = calculate_player_rating(p, st.session_state.preferred_players)
                star_indicator = " ⭐" if p["id"] in st.session_state.preferred_players else ""
                st.markdown(f"**{idx}. {p['name']}**{star_indicator} `[{p['role']}]` ({p['team_nfl']}) — ⭐️ **{p_rtg}** | 💎 **{p['list_price']} cr**")
        else:
            st.info("Nessun giocatore disponibile.")

    st.sidebar.divider()
    st.sidebar.subheader("🔮 Analisi Asta & Valutazione")

    team_names = teams_df["name"].tolist()
    default_team = "Escanyol" if "Escanyol" in team_names else (team_names[0] if team_names else None)
    default_idx = team_names.index(default_team) if default_team else 0

    selected_team_analysis = st.sidebar.selectbox("Analizza squadra", team_names, index=default_idx, key="sidebar_team_analysis")

    if selected_team_analysis:
        t_players = team_players_map.get(selected_team_analysis, [])
        bought_count = len(t_players)
        team_budgets_sorted = teams_df.sort_values(by="remaining_budget", ascending=False).reset_index(drop=True)
        team_rank_row = team_budgets_sorted[team_budgets_sorted["name"] == selected_team_analysis]
        
        if not team_rank_row.empty:
            credit_rank = team_rank_row.index[0] + 1
            budget = team_rank_row.iloc[0]["remaining_budget"]
        else:
            credit_rank, budget = 0, 0

        slots_left = TOTAL_SLOTS_PER_TEAM - bought_count
        
        if t_players:
            avg_score = sum(calculate_player_rating(p, st.session_state.preferred_players) for p in t_players) / len(t_players)
            rating_position = rating_rank_map.get(selected_team_analysis, "-")
            st.sidebar.metric("Rating Rosa", f"{avg_score:.1f} / 10.0", delta=f"Posizione: {rating_position}/{total_teams_count}", delta_color="off")
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

        st.sidebar.markdown("---")
        st.sidebar.markdown("**📊 Cruscotto Rischi Rosa:**")

        nfl_counts = {}
        for p in t_players:
            if p.get("role") != "P":
                club = p.get("team_nfl")
                if club: nfl_counts[club] = nfl_counts.get(club, 0) + 1
        max_block_count = max(nfl_counts.values()) if nfl_counts else 0
        block_status = "👍 Ottimale" if max_block_count < 4 else "👎 Rischio Blocco"
        st.sidebar.write(f"🚨 **Blocco Squadra:** {max_block_count} max | {block_status}")

        ballotaggio_count = sum(1 for p in t_players if p.get("status_titolarita") == "Ballottaggio")
        ballot_status = "👍 Ottimale" if ballotaggio_count < 3 else ("🟡 Moderato" if ballotaggio_count < 6 else "👎 Troppi")
        st.sidebar.write(f"⚠️ **Ballottaggi:** {ballotaggio_count} giocatori | {ballot_status}")

        cartellini_count = sum(1 for p in t_players if p.get("propensione_cartellini") == "A rischio malus")
        cart_status = "👍 Pulita" if cartellini_count < 2 else ("🟡 Attenzione" if cartellini_count < 4 else "👎 Troppi Malus")
        st.sidebar.write(f"🟨 **A rischio malus:** {cartellini_count} | {cart_status}")

        rookie_count = sum(1 for p in t_players if p.get("primo_anno_serie_a"))
        rookie_status = "👍 Esperti" if rookie_count < 2 else ("🟡 Equilibrato" if rookie_count < 4 else "👎 Troppi Rookie")
        st.sidebar.write(f"👶 **Primo anno in A:** {rookie_count} | {rookie_status}")

    st.sidebar.divider()
    st.sidebar.subheader("🛠️ Strumenti Mockup & Admin")
    ruolo_mockup = st.sidebar.selectbox("Completa ruolo (Mockup)", ["Tutti"] + list(ROLE_LIMITS.keys()))

    if st.sidebar.button("🎲 Autocompila rose (Intermedio)"):
        all_players_res = supabase.table("players").select("id, role, list_price").execute().data
        free_players_sim = [p for p in all_players_res if p["id"] not in bought_player_ids]
        if ruolo_mockup != "Tutti":
            free_players_sim = [p for p in free_players_sim if p["role"] == ruolo_mockup]
        random.shuffle(free_players_sim)

        sim_bought = team_total_bought.copy()
        sim_roles = {t: team_role_totals[t].copy() for t in team_role_totals}
        sim_budgets = {t["name"]: t["remaining_budget"] for t in teams_data}
        team_id_map = {t["name"]: t["id"] for t in teams_data}

        inserts = []
        for player in free_players_sim:
            p_role = player["role"]
            base_price = player["list_price"] if player["list_price"] and player["list_price"] > 0 else 1
            valid_teams = [t_name for t_name in sim_bought if sim_bought[t_name] < TOTAL_SLOTS_PER_TEAM and sim_roles[t_name][p_role] < ROLE_LIMITS[p_role]]

            if valid_teams:
                valid_teams.sort(key=lambda t: sim_budgets[t] / max(1, (TOTAL_SLOTS_PER_TEAM - sim_bought[t])), reverse=True)
                chosen_team = valid_teams[0]
                slots_left = TOTAL_SLOTS_PER_TEAM - sim_bought[chosen_team]
                current_bud = sim_budgets[chosen_team]
                purchase_price = max(1, int(current_bud)) if slots_left == 1 else max(1, int((base_price + (current_bud / slots_left)) / 2))

                inserts.append({"team_id": team_id_map[chosen_team], "player_id": player["id"], "purchase_price": purchase_price})
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
            st.sidebar.warning("Nessun inserimento possibile.")

    if st.sidebar.button("🗑️ Svuota tutte le rose (Reset)", type="primary"):
        supabase.table("rosters").delete().gt("purchase_price", -1).execute()
        for _, row in teams_df.iterrows():
            supabase.table("teams").update({"remaining_budget": int(row["initial_budget"])}).eq("id", row["id"]).execute()
        st.sidebar.success("Reset completato!")
        st.rerun()

    # --- ACQUISTO MANUALE CORPO CENTRALE ---
    if not auction_is_finished:
        query_base = supabase.table("players").select("team_nfl")
        if current_role != "ALL": query_base = query_base.eq("role", current_role)
        all_role_players = query_base.execute().data
        available_nfl_teams = sorted(list(set([p["team_nfl"] for p in all_role_players if p["team_nfl"]]))) if all_role_players else []

        with col_t:
            nfl_filter = st.selectbox("2. Filtra per Squadra Serie A (Opzionale)", ["Tutte le squadre"] + available_nfl_teams)

        final_query = supabase.table("players").select("id, name, role, team_nfl, list_price, status_titolarita, rigorista, affidabilita_fisica, propensione_cartellini, slot_fantacalcio, primo_anno_serie_a")
        if current_role != "ALL": final_query = final_query.eq("role", current_role)
        if nfl_filter != "Tutte le squadre": final_query = final_query.eq("team_nfl", nfl_filter)

        players_data = final_query.order("name").execute().data
        available_players = [p for p in players_data if p["id"] not in bought_player_ids]

        if not available_players:
            st.warning("Nessun giocatore disponibile trovato con questi filtri.")
        else:
            player_options = {f"{p['name']} [{p['role']}] ({p['team_nfl']} - Listino: {p['list_price']})": p for p in available_players}
            col1, col2, col3 = st.columns([3, 1, 2])

            with col1:
                selected_player_label = st.selectbox("3. Seleziona Giocatore", list(player_options.keys()))
                selected_player = player_options[selected_player_label]
            with col2:
                purchase_price = st.number_input("4. Costo", min_value=1, max_value=500, value=int(selected_player["list_price"] or 1))
            with col3:
                active_teams = [t["name"] for t in teams_data if team_total_bought[t["name"]] < TOTAL_SLOTS_PER_TEAM and team_role_totals[t["name"]][selected_player["role"]] < ROLE_LIMITS[selected_player["role"]]]
                default_target_idx = active_teams.index("Escanyol") if "Escanyol" in active_teams else 0
                target_team = st.selectbox("5. Squadra Acquirente", active_teams if active_teams else team_names, index=default_target_idx)

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
                        st.error(f"❌ Limite raggiunto per il ruolo {p_role} ({team_role_count}/{max_limit}).")
                    elif team_total_bought[target_team] >= TOTAL_SLOTS_PER_TEAM:
                        st.error(f"❌ La squadra ha completato la rosa (25/25).")
                    elif purchase_price > current_budget:
                        st.error(f"❌ Crediti insufficienti! (Budget residuo: {current_budget})")
                    else:
                        supabase.table("rosters").insert({"team_id": team_id, "player_id": selected_player["id"], "purchase_price": purchase_price}).execute()
                        supabase.table("teams").update({"remaining_budget": int(current_budget - purchase_price)}).eq("id", team_id).execute()

                        p_rtg = calculate_player_rating(selected_player, st.session_state.preferred_players)
                        
                        if target_team == "Escanyol" and p_rtg >= 8.0:
                            st.balloons(); st.snow()
                            play_sound("https://www.myinstants.com/media/sounds/john-cena-sound-effect.mp3")
                            st.success(f"🔥 MASSIVE COLPO! **{selected_player['name']}** (Rating {p_rtg})! AND HIS NAME IS JOHN CENA! 🎺")
                            if st.button("🎉 Clicca qui per continuare l'asta"): st.rerun()
                        elif target_team == "Escanyol" and p_rtg >= 7.0:
                            st.balloons()
                            play_sound("https://www.myinstants.com/media/sounds/ta-da.mp3")
                            st.success(f"🎉 Gran colpo! **{selected_player['name']}** (Rating {p_rtg}) per l'Escanyol!")
                            if st.button("🎉 Clicca qui per continuare l'asta"): st.rerun()
                        else:
                            st.success(f"✅ Acquistato **{selected_player['name']}** per **{target_team}** a {purchase_price} crediti!")
                            if st.button("Continua"): st.rerun()

    # --- PANORAMICA SQUADRE ---
    st.divider()
    st.subheader("📊 Panoramica Squadre & Alert Strategici")

    if not teams_df.empty:
        teams_summary = []
        for _, t in teams_df.iterrows():
            t_name = t["name"]
            rem_budget = t["remaining_budget"]
            bought = team_total_bought[t_name]
            spent = sum([r.get("purchase_price", 0) for r in rosters_data if r.get("teams") and r["teams"]["name"] == t_name]) if rosters_data else 0
            avg_spent_per_player = round(spent / bought, 1) if bought > 0 else 0.0
            slots_left = max(0, TOTAL_SLOTS_PER_TEAM - bought)
            avg_price = round(rem_budget / slots_left, 1) if slots_left > 0 else 0
            t_players = team_players_map.get(t_name, [])
            team_avg_score = all_teams_ratings.get(t_name, 0.0)
            top_players_count = sum(1 for p in t_players if p.get("slot_fantacalcio") == "1° Slot" or (p.get("list_price") or 0) >= 25)

            alerts = []
            nfl_counts = {}
            for p in t_players:
                if p.get("role") != "P":
                    club = p.get("team_nfl")
                    if club: nfl_counts[club] = nfl_counts.get(club, 0) + 1
            for club, count in nfl_counts.items():
                if count >= 4: alerts.append({"text": f"🚨 **Rischio Blocco:** {count} su {club}", "help": "Club bloccato"})

            ballotaggio_players = [f"{p.get('name')}" for p in t_players if p.get("status_titolarita") == "Ballottaggio"]
            if bought >= 5 and len(ballotaggio_players) >= (bought * 0.4): alerts.append({"text": f"⚠️ **Troppi Ballottaggi:** {len(ballotaggio_players)}", "help": "Ballottaggi"})
            cartellini_players = [f"{p.get('name')}" for p in t_players if p.get("propensione_cartellini") == "A rischio malus"]
            if len(cartellini_players) >= 3: alerts.append({"text": f"🟨 **Rischio Malus:** {len(cartellini_players)}", "help": "Cartellini"})

            status_msg = "📭 Rosa vuota." if bought == 0 else f"✨ Rating: **{team_avg_score:.1f}** ({top_players_count} Top)."
            teams_summary.append({"data": t, "bought": bought, "avg_price": avg_price, "avg_spent": avg_spent_per_player, "role_counts": team_role_totals.get(t_name, {"P": 0, "D": 0, "C": 0, "A": 0}), "alerts": alerts, "status_msg": status_msg})

        teams_summary.sort(key=lambda x: (-x["avg_price"], -x["data"]["remaining_budget"], x["data"]["name"]))

        for i in range(0, len(teams_summary), 4):
            cols = st.columns(4)
            for j, col in enumerate(cols):
                if i + j < len(teams_summary):
                    item = teams_summary[i + j]
                    t = item["data"]
                    t_name = t["name"]
                    rem_budget = t["remaining_budget"]
                    bought = item["bought"]
                    rc = item["role_counts"]
                    with col:
                        st.markdown(f"**{t_name}** — ⭐️ {all_teams_ratings.get(t_name, 0.0):.1f}")
                        if bought < TOTAL_SLOTS_PER_TEAM:
                            st.metric(label="Budget", value=f"{rem_budget} cr", delta=f"{item['avg_spent']} cr/giocatore" if bought > 0 else "N/A", delta_color="off")
                            st.markdown(f"**P** {rc.get('P', 0)}/{ROLE_LIMITS['P']} | **D** {rc.get('D', 0)}/{ROLE_LIMITS['D']} | **C** {rc.get('C', 0)}/{ROLE_LIMITS['C']} | **A** {rc.get('A', 0)}/{ROLE_LIMITS['A']}")
                            st.progress(max(0.0, min(1.0, rem_budget / t["initial_budget"])))
                        else:
                            st.success(f"✅ Rosa Completata ({TOTAL_SLOTS_PER_TEAM}/{TOTAL_SLOTS_PER_TEAM})")
                        st.markdown(f"*{item['status_msg']}*")
                        for alert in item["alerts"]: st.markdown(alert["text"])
                        st.markdown("---")

with tab2:
    st.subheader("📋 Tutte le Rose & Pagelle Post-Asta")
    st.info("🛠️ [MOCKUP] Qui sotto puoi anche eliminare i giocatori dalle rose per fare prove.")

    if rosters_data:
        formatted_rosters = []
        for r in rosters_data:
            if r["teams"] and r["players"]:
                p = r["players"]
                listino = p.get("list_price") or 1
                player_score = calculate_player_rating(p, st.session_state.preferred_players)
                formatted_rosters.append({
                    "🗑️ Elimina": False, 
                    "⭐ Preferito": p["id"] in st.session_state.preferred_players,
                    "Squadra": r["teams"]["name"],
                    "Giocatore": p["name"],
                    "Ruolo": p["role"],
                    "Rating": player_score,
                    "Club Serie A": p["team_nfl"],
                    "Listino": listino,
                    "Pagato": r["purchase_price"],
                    "Differenza": r["purchase_price"] - listino,
                    "_roster_id": r["id"],
                    "_player_id": p["id"]
                })
        
        df_rosters_raw = pd.DataFrame(formatted_rosters)
        all_teams_filter = ["Tutte"] + team_names
        default_table_idx = all_teams_filter.index("Escanyol") if "Escanyol" in all_teams_filter else 0
        filtro_tabella = st.selectbox("Filtra per Squadra", all_teams_filter, index=default_table_idx, key="table_team_filter_tab2")
        
        df_display = df_rosters_raw.copy()
        if filtro_tabella != "Tutte": df_display = df_display[df_display["Squadra"] == filtro_tabella]
        
        edited_df = st.data_editor(
            df_display, 
            column_config={
                "_roster_id": None,
                "_player_id": None,
                "🗑️ Elimina": st.column_config.CheckboxColumn("🗑️ Elimina (Mockup)", default=False),
                "⭐ Preferito": st.column_config.CheckboxColumn("⭐ Preferito", default=False)
            }, 
            use_container_width=True, 
            hide_index=True
        )
        
        rosters_to_delete = []
        for _, row in edited_df.iterrows():
            if row["⭐ Preferito"]: st.session_state.preferred_players.add(row["_player_id"])
            else: st.session_state.preferred_players.discard(row["_player_id"])
            
            if row["🗑️ Elimina"]: rosters_to_delete.append(row["_roster_id"])

        if rosters_to_delete:
            if st.button("Conferma eliminazione selezionati (Mockup)", type="primary"):
                for r_id in rosters_to_delete:
                    del_item = next((item for item in rosters_data if item["id"] == r_id), None)
                    if del_item and del_item.get("teams"):
                        t_name = del_item["teams"]["name"]
                        price = del_item["purchase_price"]
                        t_row = teams_df[teams_df["name"] == t_name]
                        if not t_row.empty:
                            t_id = t_row.iloc[0]["id"]
                            curr_b = t_row.iloc[0]["remaining_budget"]
                            supabase.table("teams").update({"remaining_budget": int(curr_b + price)}).eq("id", t_id).execute()
                    
                    supabase.table("rosters").delete().eq("id", r_id).execute()
                st.success("Giocatori eliminati e budget ripristinati con successo!")
                st.rerun()

        st.divider()
        st.subheader("🏆 Classifica e Voto Asta per Squadra")
        auction_grades = []
        for t_name in team_names:
            t_players = team_players_map.get(t_name, [])
            t_purchases = team_purchases_map.get(t_name, [])
            if not t_players: continue
            avg_rtg = all_teams_ratings.get(t_name, 0.0)
            risparmio_crediti = sum((p.get("list_price") or 1) for p in t_players) - sum(r.get("purchase_price", 0) for r in t_purchases)
            voto_asta = round(max(0.0, min(10, (avg_rtg * 0.7) + 1.5 + max(-2.0, min(2.0, risparmio_crediti / 15.0)))), 1)
            auction_grades.append({"Squadra": t_name, "Voto Asta": voto_asta, "Rating Medio": round(avg_rtg, 1), "Bilancio Affari": risparmio_crediti})

        if auction_grades:
            df_grades = pd.DataFrame(auction_grades).sort_values(by="Voto Asta", ascending=False).reset_index(drop=True)
            df_grades.index += 1
            st.dataframe(df_grades, use_container_width=True)
    else:
        st.info("Nessun giocatore acquistato.")

with tab3:
    st.subheader("⭐️ Tutti i Giocatori ordinati per Rating")
    st.info("In questa tabella trovi l'elenco completo di tutti i calciatori presenti nel database, ordinati per rating complessivo, con il dettaglio dei singoli fattori che compongono il voto.")

    # Recuperiamo tutti i giocatori da Supabase
    all_players_db = supabase.table("players").select("id, name, role, team_nfl, list_price, status_titolarita, rigorista, propensione_cartellini, primo_anno_serie_a").execute().data

    if all_players_db:
        detailed_players_list = []
        for p in all_players_db:
            det = calculate_player_rating_detailed(p, st.session_state.preferred_players)
            is_bought = p["id"] in bought_player_ids
            
            detailed_players_list.append({
                "Giocatore": p["name"],
                "Ruolo": p["role"],
                "Squadra A": p["team_nfl"],
                "Rating ⭐️": det["final_rating"],
                "Base / Fantamedia": det["base_or_fantamedia"],
                "Gol": det["goals"],
                "Assist": det["assists"],
                "Presenze": det["matches"],
                "Titolarità Mod": det["titolarita_mod"],
                "Mod. Squadra": det["team_mod"],
                "Bonus Rigorista": det["bonus_rigorista"],
                "Malus Cartellini": det["malus_cartellini"],
                "Malus Rookie": det["malus_rookie"],
                "Bonus Preferito": det["preferito_mod"],
                "Listino": p.get("list_price", 1),
                "Stato": "Acquistato" if is_bought else "Libero"
            })
        
        df_all_players = pd.DataFrame(detailed_players_list)
        df_all_players = df_all_players.sort_values(by="Rating ⭐️", ascending=False).reset_index(drop=True)
        df_all_players.index += 1

        # Filtri rapidi per comodità
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            role_filter = st.selectbox("Filtra per Ruolo", ["Tutti", "P", "D", "C", "A"], key="tab3_role_filter")
        with col_f2:
            status_filter = st.selectbox("Filtra per Stato", ["Tutti", "Libero", "Acquistato"], key="tab3_status_filter")
        with col_f3:
            search_name = st.text_input("Cerca Giocatore per Nome", "", key="tab3_search_name")

        df_filtered = df_all_players.copy()
        if role_filter != "Tutti":
            df_filtered = df_filtered[df_filtered["Ruolo"] == role_filter]
        if status_filter != "Tutti":
            df_filtered = df_filtered[df_filtered["Stato"] == status_filter]
        if search_name:
            df_filtered = df_filtered[df_filtered["Giocatore"].str.contains(search_name, case=False, na=False)]

        st.dataframe(df_filtered, use_container_width=True)
    else:
        st.info("Nessun giocatore trovato nel database.")
