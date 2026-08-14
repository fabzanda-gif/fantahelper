import random
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

# --- FUNZIONI ---
def play_sound(sound_url):
    sound_html = f"""<audio autoplay><source src="{sound_url}" type="audio/mp3"></audio>"""
    components.html(sound_html, height=0, width=0)

def calculate_player_rating(p, preferred_players_set=None):
    rating = 6.5 
    listino = p.get("list_price", 1)
    if listino >= 30: rating += 3.5
    elif listino >= 20: rating += 2.5
    elif listino >= 10: rating += 1.0
    elif listino >= 5: rating += 0.5
    if p.get("status_titolarita") == "Titolare": rating += 1.5
    elif p.get("status_titolarita") == "Riserva": rating -= 1.5
    if p.get("rigorista"): rating += 1.5
    if p.get("propensione_cartellini") == "A rischio malus": rating -= 0.3
    if p.get("primo_anno_serie_a"): rating -= 0.2
    if preferred_players_set and p.get("id") in preferred_players_set: rating += 0.8
    return round(max(0, min(10, rating)), 1)

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

# --- GESTIONE FESTA (PRIMA DI TUTTO) ---
if st.session_state.show_celebration:
    st.balloons(); st.snow()
    play_sound(st.session_state.audio_url)
    st.success(st.session_state.show_celebration)
    if st.button("Continua Asta"):
        st.session_state.show_celebration = None
        st.rerun()
    st.stop()

# --- INTERFACCIA ---
tab1, tab2 = st.tabs(["🎯 Live Asta", "📋 Rose & Analisi"])

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

        # CRUSCOTTO RISCHI EMOJI
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

                        # --- ATTIVAZIONE FESTA E JOHN CENA IMMEDIATA ---
                        p_rtg = calculate_player_rating(selected_player, st.session_state.preferred_players)
                        
                        if target_team == "Escanyol" and p_rtg >= 8.0:
                            st.balloons()
                            st.snow()
                            play_sound("https://www.myinstants.com/media/sounds/john-cena-sound-effect.mp3")
                            st.success(f"🔥 MASSIVE COLPO! **{selected_player['name']}** (Rating {p_rtg})! AND HIS NAME IS JOHN CENA! 🎺")
                            if st.button("🎉 Clicca qui per continuare l'asta"):
                                st.rerun()
                        elif target_team == "Escanyol" and p_rtg >= 7.0:
                            st.balloons()
                            play_sound("https://www.myinstants.com/media/sounds/ta-da.mp3")
                            st.success(f"🎉 Gran colpo! **{selected_player['name']}** (Rating {p_rtg}) per l'Escanyol!")
                            if st.button("🎉 Clicca qui per continuare l'asta"):
                                st.rerun()
                        else:
                            st.success(f"✅ Acquistato **{selected_player['name']}** per **{target_team}** a {purchase_price} crediti!")
                            if st.button("Continua"):
                                st.rerun()
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
            club_players_map = {}
            for p in t_players:
                if p.get("role") != "P":
                    club = p.get("team_nfl")
                    if club:
                        nfl_counts[club] = nfl_counts.get(club, 0) + 1
                        club_players_map.setdefault(club, []).append(f"{p.get('name')} [{p.get('role')}]")
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
    st.info("🛠️ [MOCKUP] Qui sotto puoi anche eliminare i giocatori dalle rose per fare prove. Questa funzione di rimozione andrà rimossa il giorno dell'asta.")

    if rosters_data:
        formatted_rosters = []
        for r in rosters_data:
            if r["teams"] and r["players"]:
                p = r["players"]
                listino = p.get("list_price") or 1
                player_score = calculate_player_rating(p, st.session_state.preferred_players)
                formatted_rosters.append({
                    "🗑️ Elimina": False, # Funzione mockup rimozione
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
        
        # Gestione Salvataggio Preferiti ed eventuale rimozione Mockup
        rosters_to_delete = []
        for _, row in edited_df.iterrows():
            if row["⭐ Preferito"]: st.session_state.preferred_players.add(row["_player_id"])
            else: st.session_state.preferred_players.discard(row["_player_id"])
            
            if row["🗑️ Elimina"]:
                rosters_to_delete.append(row["_roster_id"])

        if rosters_to_delete:
            if st.button("Conferma eliminazione selezionati (Mockup)", type="primary"):
                for r_id in rosters_to_delete:
                    # Recuperiamo l'acquisto per ripristinare il budget
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
