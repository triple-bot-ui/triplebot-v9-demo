# ============================================
# TRIPLE BOT V9
# Main Application — UI Redesign (Clean)
# triplebot_v9_app.py
# ============================================

import streamlit as st
import sys
import os
from datetime import datetime

# ============================================
# PATH SETUP
# ============================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.join(BASE_DIR, "..")

sys.path.insert(0, os.path.join(ROOT_DIR, "modules"))
sys.path.insert(0, os.path.join(ROOT_DIR, "engines"))

# ============================================
# MODULE IMPORTS
# ============================================

from module_01_user_input import get_user_input, validate_input
from module_02_layout_generation import generate_2d_layout, _generate_room_layout
from module_03_layout_editing import get_layout_edits, validate_edited_layout
from module_04_3d_visualization import generate_3d_visualization
from module_05_design_confirmation import get_design_confirmation, summarize_confirmed_design
from module_06_engineering_validation import run_engineering_validation, display_validation_results, extract_validation_for_decision
from module_07_decision_intelligence import run_decision_intelligence, display_decision_results, extract_decision_for_output
from module_08_construction_output import run_construction_output, display_construction_output

# ============================================
# PAGE CONFIG
# ============================================

st.set_page_config(
    page_title="Triple Bot V9",
    layout="wide",
    page_icon="🏗️"
)

# ============================================
# GLOBAL CSS — Clean UI
# ============================================

st.markdown("""
<style>
/* ── Font & Base ── */
html, body, [class*="css"] {
    font-family: 'Inter', 'DM Sans', sans-serif;
    font-size: 13px;
    color: #1a1a1a;
}

/* ── Remove Streamlit default top padding ── */
.block-container {
    padding-top: 1.5rem;
    padding-bottom: 2rem;
    max-width: 860px;
}

/* ── Hide hamburger & footer ── */
#MainMenu, footer { visibility: hidden; }

/* ── Page title ── */
h1 {
    font-size: 1.15rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.02em;
    margin-bottom: 0 !important;
    color: #111;
}

/* ── Section headers (st.header) ── */
h2 {
    font-size: 0.95rem !important;
    font-weight: 600 !important;
    color: #222;
    margin-top: 1rem !important;
    margin-bottom: 0.4rem !important;
    border-bottom: 1px solid #e8e8e6;
    padding-bottom: 4px;
}

/* ── Sub headers (st.subheader) ── */
h3 {
    font-size: 0.85rem !important;
    font-weight: 600 !important;
    color: #333;
    margin-top: 0.8rem !important;
    margin-bottom: 0.3rem !important;
}

/* ── Metric — uniform size ── */
[data-testid="stMetricValue"] {
    font-size: 1.1rem !important;
    font-weight: 600 !important;
    color: #111;
}
[data-testid="stMetricLabel"] {
    font-size: 0.72rem !important;
    font-weight: 400 !important;
    color: #888;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}
[data-testid="stMetricDelta"] {
    font-size: 0.72rem !important;
}

/* ── Caption & small text ── */
small, .caption, [data-testid="stCaptionContainer"] {
    font-size: 0.72rem !important;
    color: #999;
}

/* ── Info / warning boxes ── */
[data-testid="stAlert"] {
    font-size: 0.78rem !important;
    padding: 8px 12px !important;
    border-radius: 6px !important;
}

/* ── Buttons ── */
[data-testid="stButton"] > button {
    font-size: 0.78rem !important;
    font-weight: 600;
    padding: 6px 16px !important;
    border-radius: 5px !important;
}

/* ── Input labels ── */
label {
    font-size: 0.78rem !important;
    font-weight: 500 !important;
    color: #555 !important;
}

/* ── Input fields ── */
input, select, textarea {
    font-size: 0.82rem !important;
}

/* ── Dataframe / table ── */
[data-testid="stDataFrame"] {
    font-size: 0.82rem !important;
}

/* ── Before vs After table values ── */
[data-testid="stDataFrame"] td {
    font-size: 0.82rem !important;
    font-weight: 500 !important;
    padding: 6px 14px !important;
}
[data-testid="stDataFrame"] th {
    font-size: 0.78rem !important;
    font-weight: 600 !important;
    padding: 6px 14px !important;
}

/* ── Column padding for Before vs After layout ── */
[data-testid="column"] > div {
    padding: 0 10px !important;
}

/* ── Divider tight ── */
hr {
    margin: 0.6rem 0 !important;
    border-color: #eee;
}

/* ── Stage indicator badges ── */
.stage-bar {
    display: flex;
    gap: 6px;
    margin: 6px 0 10px 0;
    flex-wrap: wrap;
}
.stage-chip {
    font-size: 0.68rem;
    font-weight: 600;
    letter-spacing: 0.04em;
    padding: 3px 10px;
    border-radius: 20px;
    border: 1px solid #ddd;
    color: #aaa;
    background: #fafaf8;
    white-space: nowrap;
}
.stage-chip.done {
    background: #f0f0ee;
    color: #555;
    border-color: #ccc;
}
.stage-chip.active {
    background: #111;
    color: #fff;
    border-color: #111;
}

/* ── Progress bar color ── */
[data-testid="stProgress"] > div > div {
    background: #333 !important;
}

/* ── Reduce column gap ── */
[data-testid="column"] {
    padding: 0 6px !important;
}
</style>
""", unsafe_allow_html=True)

# ============================================
# SESSION STATE INIT
# ============================================

if "stage" not in st.session_state:
    st.session_state.stage = "input"
if "project_data" not in st.session_state:
    st.session_state.project_data = None
if "rooms" not in st.session_state:
    st.session_state.rooms = None
if "validation_results" not in st.session_state:
    st.session_state.validation_results = None
if "decision_results" not in st.session_state:
    st.session_state.decision_results = None

# ============================================
# SYSTEM HEADER — compact
# ============================================

col_logo, col_meta = st.columns([3, 1])
with col_logo:
    st.markdown("### TRIPLEBOT &nbsp;<span style='font-size:0.7rem;font-weight:400;color:#aaa'>V9</span>", unsafe_allow_html=True)
    st.caption("Pre-Construction Engineering Intelligence · Deterministic Engine · Patent Pending")
with col_meta:
    st.caption(f"🕐 {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC")

st.divider()

# ============================================
# STAGE INDICATOR — single row chips
# ============================================

stage_map = {
    "input":     0,
    "layout":    1,
    "edit":      2,
    "visualize": 3,
    "confirm":   4,
    "validate":  5,
    "decision":  6,
    "output":    7
}

stage_labels = ["1·Input","2·Layout","3·Edit","4·3D","5·Confirm","6·Validate","7·Decision","8·Output"]
current_idx  = stage_map.get(st.session_state.stage, 0)

chips_html = '<div class="stage-bar">'
for i, label in enumerate(stage_labels):
    if i < current_idx:
        chips_html += f'<span class="stage-chip done">{label}</span>'
    elif i == current_idx:
        chips_html += f'<span class="stage-chip active">{label}</span>'
    else:
        chips_html += f'<span class="stage-chip">{label}</span>'
chips_html += '</div>'

st.markdown(chips_html, unsafe_allow_html=True)
st.divider()

# ============================================
# STAGE 1 — USER INPUT
# ============================================

if st.session_state.stage == "input":

    project_data = get_user_input(st)

    if st.button("Generate Layout →", type="primary"):
        is_valid, errors = validate_input(project_data)
        if not is_valid:
            for e in errors:
                st.error(e)
        else:
            st.session_state.project_data = project_data
            st.session_state.stage = "layout"
            st.rerun()

# ============================================
# STAGE 2 — LAYOUT GENERATION
# ============================================

elif st.session_state.stage == "layout":

    project_data = st.session_state.project_data
    st.header("Generated Floor Plan")

    rooms = _generate_room_layout(
        project_data["building_width"],
        project_data["building_length"],
        project_data["building_type"]
    )
    st.session_state.rooms = rooms

    layout_img = generate_2d_layout(project_data)
    st.image(layout_img, caption="2D Floor Plan — Auto Generated", use_column_width=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("✏️ Edit Layout", type="primary"):
            st.session_state.stage = "edit"
            st.rerun()
    with col2:
        if st.button("→ Proceed to 3D View"):
            st.session_state.stage = "visualize"
            st.rerun()

# ============================================
# STAGE 3 — LAYOUT EDITING
# ============================================

elif st.session_state.stage == "edit":

    project_data = st.session_state.project_data
    rooms        = st.session_state.rooms

    edited_data, edited_rooms = get_layout_edits(st, project_data, rooms)

    if edited_rooms is None:
        edited_rooms = _generate_room_layout(
            edited_data["building_width"],
            edited_data["building_length"],
            edited_data["building_type"]
        )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Preview Updated Layout", type="primary"):
            st.session_state.project_data = edited_data
            st.session_state.rooms = edited_rooms
            layout_img = generate_2d_layout(edited_data)
            st.image(layout_img, caption="Updated Floor Plan", use_column_width=True)
    with col2:
        if st.button("→ Proceed to 3D View"):
            is_valid, errors = validate_edited_layout(edited_data, edited_rooms)
            if not is_valid:
                for e in errors:
                    st.error(e)
            else:
                st.session_state.project_data = edited_data
                st.session_state.rooms = edited_rooms
                st.session_state.stage = "visualize"
                st.rerun()

# ============================================
# STAGE 4 — 3D VISUALIZATION
# ============================================

elif st.session_state.stage == "visualize":

    project_data = st.session_state.project_data
    st.header("3D Building Visualization")
    st.caption("Visualization only — structural parameters are not modified here.")

    render = generate_3d_visualization(project_data)
    st.image(render, caption="3D Building Render", use_column_width=True)

    layout_img = generate_2d_layout(project_data)
    st.image(layout_img, caption="2D Floor Plan Reference", use_column_width=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Back to Edit"):
            st.session_state.stage = "edit"
            st.rerun()
    with col2:
        if st.button("✅ Confirm Design", type="primary"):
            st.session_state.stage = "confirm"
            st.rerun()

# ============================================
# STAGE 5 — DESIGN CONFIRMATION
# ============================================

elif st.session_state.stage == "confirm":

    project_data = st.session_state.project_data
    decision = get_design_confirmation(st, project_data)

    if decision == "proceed":
        confirmed = summarize_confirmed_design(project_data)
        st.session_state.project_data = confirmed
        st.session_state.stage = "validate"
        st.rerun()
    elif decision == "edit":
        st.session_state.stage = "edit"
        st.rerun()
    elif decision == "regenerate":
        st.session_state.stage = "input"
        st.session_state.rooms = None
        st.rerun()

# ============================================
# STAGE 6 — ENGINEERING VALIDATION
# ============================================

elif st.session_state.stage == "validate":

    project_data = st.session_state.project_data

    with st.spinner("Running structural validation..."):
        results = run_engineering_validation(project_data)
        st.session_state.validation_results = results

    display_validation_results(st, results)

    if st.button("→ Proceed to Engineering Decision", type="primary"):
        st.session_state.stage = "decision"
        st.rerun()

# ============================================
# STAGE 7 — DECISION INTELLIGENCE
# ============================================

elif st.session_state.stage == "decision":

    results      = st.session_state.validation_results
    project_data = st.session_state.project_data

    validation_package = extract_validation_for_decision(results)

    decision_options = [
        {"option_type": "FOUNDATION_INCREASE", "description": "Increase foundation area"},
        {"option_type": "COLUMN_UPGRADE",       "description": "Upgrade column capacity"},
        {"option_type": "LOAD_REDUCTION",        "description": "Reduce structural load"}
    ]

    with st.spinner("Generating engineering decision..."):
        decision_results = run_decision_intelligence(
            validation_package,
            decision_options
        )
        st.session_state.decision_results = decision_results

    display_decision_results(st, decision_results)

    if st.button("→ Generate Construction Package", type="primary"):
        st.session_state.stage = "output"
        st.rerun()

# ============================================
# STAGE 8 — CONSTRUCTION OUTPUT
# ============================================

elif st.session_state.stage == "output":

    decision_results = st.session_state.decision_results
    project_data     = st.session_state.project_data

    decision_package = extract_decision_for_output(decision_results)

    with st.spinner("Generating construction package..."):
        output = run_construction_output(decision_package, project_data)

    display_construction_output(st, output, project_data)
