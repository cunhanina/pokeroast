import streamlit as st
import pyttsx3
import threading
import sys
import os
import plotly.graph_objects as go
import pandas as pd

from pokeroast.roaster import generate_roast_data
from pokeroast.utils import (
    get_pokemon_by_game, 
    get_pokemon_details, 
    save_shame_entry, 
    load_shame_history, 
    get_type_matchups, 
    get_counter_pokemon,
    GAME_DEX_MAP,
)

# --- PATH SETUP ---
current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.dirname(current_dir)
if src_path not in sys.path: sys.path.append(src_path)

st.set_page_config(page_title="Team Rocket Terminal", page_icon="🚀", layout="wide", initial_sidebar_state="collapsed")

# --- CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=VT323&display=swap');
    
    /* GLOBAL FONTS & COLORS */
    .stApp { background-color: #202020; font-family: 'VT323', monospace; }
    
    /* BASE TEXT SIZE */
    html, body, p, div, span, label, input { 
        font-family: 'VT323', monospace !important; 
        font-size: 22px !important; 
    }
    
    /* HEADERS */
    h1 { font-size: 60px !important; line-height: 1 !important; margin-bottom: 0px !important; }
    h2 { font-size: 35px !important; color: #d67ae6 !important; margin-top: 0px !important; }
    h3 { font-size: 28px !important; color: #aaa !important; margin-bottom: 10px !important; }
    
    /* LAYOUT TWEAKS */
    .stColumn > div > div > div { gap: 0px !important; }
    
    /* POKEMON CARD */
    .pokemon-card { 
        background: #303030; 
        border: 2px solid #555; 
        border-bottom: none; 
        border-radius: 8px 8px 0 0; 
        padding: 10px; 
        text-align: center; 
        height: 180px; 
    }
    
    /* BUTTONS */
    .stButton>button { 
        border-radius: 0 0 8px 8px; 
        border: 2px solid #555; 
        border-top: none; 
        background-color: #444; 
        color: #ff4b4b; 
        font-size: 22px !important; 
        height: 45px; 
        transition: 0.2s; 
        width: 100%; 
    }
    .stButton>button:hover { background-color: #ff4b4b; color: white; border-color: #ff4b4b; }

    /* RPG DIALOG BOX */
    .rpg-box { 
        background-color: #f8f8f8; 
        border: 4px solid #333; 
        border-radius: 5px; 
        padding: 20px; 
        font-size: 26px !important; 
        color: #000; 
        box-shadow: 6px 6px 0px rgba(0,0,0,0.5); 
        line-height: 1.2;
    }
    
    /* HR RECOMMENDATION BOX */
    .hr-box { 
        border: 3px dashed #444; 
        background: #151515; 
        padding: 15px; 
        border-radius: 5px; 
        margin-top: 15px;
        display: flex; 
        flex-direction: column;
        gap: 10px;
    }
    .rec-row { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #333; padding-bottom: 5px;}
    .rec-label { color: #888; font-size: 20px; text-transform: uppercase; }
    .rec-val-red { color: #ff4b4b; font-size: 26px; text-transform: uppercase; font-weight: bold; }
    .rec-val-green { color: #00ff00; font-size: 26px; text-transform: uppercase; font-weight: bold; }
    .rec-val-orange { color: orange; font-size: 26px; text-transform: uppercase; font-weight: bold; }
    
    /* BILL'S PC GRID (NEW TAB STYLE) */
    .pc-grid-item {
        background-color: #111;
        border: 2px solid #444;
        border-radius: 5px;
        padding: 10px;
        text-align: center;
        margin-bottom: 10px;
    }
    .pc-grid-item:hover { border-color: #d67ae6; }
    .pc-name { font-size: 18px; color: #888; text-transform: uppercase; margin-top: 5px;}
    
    /* INPUT FIELDS */
    .stSelectbox div[data-baseweb="select"] > div { font-size: 22px !important; height: 45px; }
</style>
""", unsafe_allow_html=True)

# --- INIT STATE ---
if 'team' not in st.session_state: st.session_state.team = [None] * 6
if 'hr_data' not in st.session_state: st.session_state.hr_data = None 

def add_pokemon_callback():
    selected = st.session_state.get("pokemon_selector")
    if selected:
        if None in st.session_state.team:
            idx = st.session_state.team.index(None)
            st.session_state.team[idx] = selected
            get_pokemon_details(selected) 
            st.session_state["pokemon_selector"] = ""
        else:
            st.toast("ERROR: PARTY IS FULL!", icon="🚫")

# --- HEADER ---
c1, c2 = st.columns([1, 10])
with c1: st.markdown("<h1 style='color:red;'>R</h1>", unsafe_allow_html=True)
with c2: st.markdown(f"# TERMINAL ")

# ==========================================
# 1. GAME SELECTOR (Top)
# ==========================================
st.markdown("### 1. MISSION PARAMETERS (GAME VERSION)")
selected_game = st.selectbox("SELECT GAME", list(GAME_DEX_MAP.keys()), index=9, label_visibility="collapsed")
valid_pokemon = get_pokemon_by_game(selected_game)

# ==========================================
# 2. POKEMON SELECTOR
# ==========================================
st.markdown("### 2. RECRUITMENT (SEARCH)")
col_search, col_clear = st.columns([5, 1])
with col_search:
    st.selectbox(
        "QUICK CAPTURE", 
        [""] + sorted(valid_pokemon), 
        key="pokemon_selector", 
        on_change=add_pokemon_callback, 
        label_visibility="collapsed"
    )
with col_clear:
    if st.button("💀 FLUSH", use_container_width=True):
        # FULL RESET LOGIC
        st.session_state.team = [None] * 6
        st.session_state.hr_data = None
        if 'last_roast' in st.session_state:
            del st.session_state['last_roast']
        st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

# ==========================================
# 3. TEAM VISUALIZER
# ==========================================
cols = st.columns(6)
current_stats = [] 
current_team_names = []
team_types = [] 

for i, col in enumerate(cols):
    name = st.session_state.team[i]
    with col:
        if name:
            details = get_pokemon_details(name)
            if details:
                current_stats.append(details['stats'])
                team_types.append({'name': name, 'types': details['types']}) 
                st.markdown(f"<div class='pokemon-card'><img src='{details['sprite']}' style='height:120px; object-fit:contain;'><div style='color:white; font-size:24px; text-transform:uppercase;'>{name}</div></div>", unsafe_allow_html=True)
                if st.button("RELEASE", key=f"rem_{i}", use_container_width=True):
                    st.session_state.team[i] = None
                    st.rerun()
                current_team_names.append(name)
        else:
            st.markdown("""<div class="pokemon-card" style="opacity:0.3; border-style:dashed; border-bottom:3px dashed #555;"><div style="font-size:60px; margin-top:30px;">●</div></div>""", unsafe_allow_html=True)
            st.button("EMPTY", key=f"empty_{i}", disabled=True, use_container_width=True)

# ==========================================
# 4. TABS & ANALYSIS
# ==========================================
st.markdown("<br>", unsafe_allow_html=True)
tab1, tab2, tab3 = st.tabs(["🚀 TACTICAL REPORT", "📊 MATRIX & METRICS", "💾 BILL'S PC"])

# --- TAB 1: REPORT ---
with tab1:
    c_left, c_right = st.columns([1, 1], gap="large")
    
    # LEFT: ROAST
    with c_left:
        st.markdown("### AI ASSESSMENT")
        if st.button("INITIATE ANALYSIS", type="primary", use_container_width=True):
            if not current_team_names:
                st.error("NO DATA.")
            else:
                with st.spinner(f"PROCESSING {selected_game.upper()} META..."):
                    # 1. Roast
                    data = generate_roast_data(current_team_names, game_context=selected_game)
                    st.session_state['last_roast'] = data.get("roast", "Error.")
                    save_shame_entry(current_team_names, data)
                    
                    # 2. HR Logic
                    master_chart = get_type_matchups()
                    all_attacking_types = list(master_chart.keys())
                    type_totals = {t: 0 for t in all_attacking_types}
                    
                    for member in team_types:
                        for atk_type in all_attacking_types:
                            multiplier = 1.0
                            for my_t in member['types']: multiplier *= master_chart.get(my_t, {}).get(atk_type, 1.0)
                            if multiplier >= 2.0: type_totals[atk_type] += (multiplier * 2)
                    
                    worst_weakness = max(type_totals, key=type_totals.get)
                    
                    liability_mon = "None"; max_mul = 0
                    for member in team_types:
                        mul = 1.0
                        for t in member['types']: mul *= master_chart.get(t, {}).get(worst_weakness, 1.0)
                        if mul > max_mul: max_mul = mul; liability_mon = member['name']
                    
                    hire_name = get_counter_pokemon(worst_weakness, valid_pokemon)
                    hire_details = get_pokemon_details(hire_name)
                    
                    st.session_state.hr_data = {
                        "threat_type": worst_weakness,
                        "fire_name": liability_mon,
                        "fire_score": max_mul,
                        "hire_name": hire_name,
                        "hire_sprite": hire_details['sprite'] if hire_details else ""
                    }
                    
                    # 3. Audio
                    def play_audio_safely():
                        try:
                            engine = pyttsx3.init(); engine.setProperty('rate', 155)
                            if engine._inLoop: engine.endLoop()
                            engine.say(st.session_state['last_roast'].replace("*", "").replace("\n", " "))
                            engine.runAndWait(); engine.stop()
                        except: pass
                    threading.Thread(target=play_audio_safely, daemon=True).start()
                    st.rerun()

        if 'last_roast' in st.session_state:
            st.markdown(f"<div class='rpg-box'>{st.session_state['last_roast']}</div>", unsafe_allow_html=True)
            
    # RIGHT: GRAPH + HR
    with c_right:
        st.markdown("### SQUAD STATS")
        if current_stats:
            df = pd.DataFrame(current_stats)
            avg_stats = df.mean().to_dict()
            cats = ['hp', 'attack', 'defense', 'special-attack', 'special-defense', 'speed']
            vals = [avg_stats.get(c, 0) for c in cats]; vals.append(vals[0]); cats.append(cats[0])
            fig = go.Figure(go.Scatterpolar(r=vals, theta=[c.upper() for c in cats], fill='toself', line_color='#00ff00'))
            fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 150], showticklabels=False), bgcolor='#262626'), paper_bgcolor='rgba(0,0,0,0)', font=dict(color='white', family="Courier New", size=14), margin=dict(t=20, b=20), showlegend=False, height=350)
            st.plotly_chart(fig, use_container_width=True)
            
            hr = st.session_state.hr_data
            if hr:
                st.markdown(f"""
                <div class='hr-box'>
                    <div style='text-align:center; color:#fff; border-bottom:1px solid #333; padding-bottom:5px;'>⚠️ TACTICAL ADVISOR</div>
                    <div class='rec-row'><div class='rec-label'>THREAT</div><div class='rec-val-orange'>{hr['threat_type']}</div></div>
                    <div class='rec-row'><div class='rec-label'>FIRE</div><div class='rec-val-red'>{hr['fire_name']} ({hr['fire_score']}x)</div></div>
                    <div class='rec-row'><div class='rec-label'>HIRE</div><div style='display:flex; align-items:center; gap:10px'><img src='{hr['hire_sprite']}' height='40'><div class='rec-val-green'>{hr['hire_name']}</div></div></div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("AWAITING DATA...")

# --- TAB 2: MATRIX ---
with tab2:
    if team_types:
        st.markdown("### DEFENSIVE MATRIX")
        master_chart = get_type_matchups()
        all_attacking_types = list(master_chart.keys())
        heatmap_data = []
        for member in team_types:
            row = []
            for atk_type in all_attacking_types:
                multiplier = 1.0
                for my_t in member['types']: multiplier *= master_chart.get(my_t, {}).get(atk_type, 1.0)
                row.append(multiplier)
            heatmap_data.append(row)
            
        colorscale = [[0.0, "black"], [0.05, "black"], [0.05, "#0d3d0d"], [0.15, "#0d3d0d"], [0.15, "green"], [0.20, "green"], 
                      [0.20, "#333333"], [0.40, "#333333"], [0.40, "orange"], [0.60, "orange"], [0.60, "#ff0000"], [1.0, "#ff0000"]]
        
        fig_heat = go.Figure(data=go.Heatmap(z=heatmap_data, x=[t.upper() for t in all_attacking_types], y=[m['name'].upper() for m in team_types], colorscale=colorscale, zmin=0, zmax=4, xgap=1, ygap=1))
        fig_heat.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='white', family="VT323", size=18), height=500)
        st.plotly_chart(fig_heat, use_container_width=True)
    else:
        st.info("ADD POKEMON TO GENERATE MATRIX.")

# --- TAB 3: BILL'S PC ---
with tab3:
    st.markdown("### 💾 HALL OF SHAME")
    history = load_shame_history()
    
    if history:
        # Create a Grid Layout for the history
        cols = st.columns(6)
        for i, entry in enumerate(history):
            worst_mon = entry.get('worst_pokemon')
            if worst_mon:
                with cols[i % 6]:
                    details = get_pokemon_details(worst_mon)
                    sprite = details['sprite'] if details else ""
                    st.markdown(f"""
                    <div class='pc-grid-item' title='Weakest Link in Team {i+1}'>
                        <img src='{sprite}' style='height:80px; image-rendering:pixelated;'>
                        <div class='pc-name'>{worst_mon[:10]}</div>
                    </div>
                    """, unsafe_allow_html=True)
    else:
        st.info("PC STORAGE EMPTY.")