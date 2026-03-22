import streamlit as st

# ============================================
# TRIPLE BOT V9.6
# Module 01 — User Input
# UI: Command Center (not a form)
# ============================================

CERTIFIED_MIN_STOREYS = 1
CERTIFIED_MAX_STOREYS = 4


def render_user_input():

    st.markdown("""
    <style>
    /* ── Command Center Header ── */
    .cmd-header {
        border: 1px solid #e0e0de;
        border-radius: 8px;
        overflow: hidden;
        margin-bottom: 20px;
        font-family: 'DM Mono', monospace;
    }
    .cmd-top {
        background: #f0f0ee;
        border-bottom: 1px solid #e0e0de;
        padding: 14px 20px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .cmd-title {
        font-size: 13px;
        font-weight: 600;
        color: #111;
        letter-spacing: .04em;
    }
    .cmd-scope {
        font-size: 10px;
        color: #aaa;
        letter-spacing: .08em;
        text-transform: uppercase;
    }
    .cmd-status {
        font-size: 10px;
        color: #888;
        background: #fff;
        border: 1px solid #ddd;
        padding: 3px 10px;
        border-radius: 3px;
        letter-spacing: .06em;
    }
    .cmd-info {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        background: #fff;
    }
    .cmd-info-cell {
        padding: 12px 20px;
        border-right: 1px solid #f0f0ee;
    }
    .cmd-info-cell:last-child { border-right: none; }
    .cmd-info-label {
        font-size: 9px;
        color: #bbb;
        letter-spacing: .1em;
        text-transform: uppercase;
        margin-bottom: 3px;
    }
    .cmd-info-val {
        font-size: 13px;
        color: #333;
        font-weight: 400;
    }

    /* ── Section dividers ── */
    .inp-sec {
        font-family: 'DM Mono', monospace;
        font-size: 9px;
        font-weight: 600;
        letter-spacing: .14em;
        text-transform: uppercase;
        color: #bbb;
        border-bottom: 1px solid #eee;
        padding-bottom: 6px;
        margin: 20px 0 12px;
    }

    /* ── Input label override ── */
    .stNumberInput label, .stTextInput label, .stSelectbox label {
        font-family: 'DM Mono', monospace !important;
        font-size: 10px !important;
        font-weight: 500 !important;
        color: #888 !important;
        letter-spacing: .08em !important;
        text-transform: uppercase !important;
    }

    /* ── Scope badge ── */
    .scope-badge {
        display: inline-block;
        font-family: 'DM Mono', monospace;
        font-size: 10px;
        color: #888;
        background: #f8f8f6;
        border: 1px solid #e0e0de;
        border-radius: 4px;
        padding: 4px 12px;
        margin-bottom: 20px;
        letter-spacing: .06em;
    }
    </style>
    """, unsafe_allow_html=True)

    # ── Command Center Header ──
    st.markdown("""
    <div class="cmd-header">
      <div class="cmd-top">
        <div>
          <div class="cmd-title">TRIPLEBOT V9 &nbsp;—&nbsp; Project Input</div>
          <div class="cmd-scope">Pre-Construction Decision Engine</div>
        </div>
        <div class="cmd-status">READY</div>
      </div>
      <div class="cmd-info">
        <div class="cmd-info-cell">
          <div class="cmd-info-label">Engine</div>
          <div class="cmd-info-val">Deterministic</div>
        </div>
        <div class="cmd-info-cell">
          <div class="cmd-info-label">Scope</div>
          <div class="cmd-info-val">RC Frame · 1–4 Floors</div>
        </div>
        <div class="cmd-info-cell">
          <div class="cmd-info-label">Mode</div>
          <div class="cmd-info-val">Structural Validation</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Section: Project ──
    st.markdown('<div class="inp-sec">Project</div>', unsafe_allow_html=True)

    col1, col2, col_region = st.columns([2, 1, 1])
    with col1:
        project_name = st.text_input("Project Name", value="My Project")
    with col2:
        building_type = st.selectbox("Building Type", ["Residential", "Commercial", "Industrial"])
    with col_region:
        region = st.selectbox("Region", ["Thailand 🇹🇭", "China 🇨🇳", "United States 🇺🇸"])

    # ── Section: Building Geometry ──
    st.markdown('<div class="inp-sec">Building Geometry</div>', unsafe_allow_html=True)

    col3, col4, col5, col6 = st.columns(4)
    with col3:
        building_width = st.number_input("Width (m)", min_value=1.0, value=10.0)
    with col4:
        building_length = st.number_input("Length (m)", min_value=1.0, value=10.0)
    with col5:
        num_floors = st.number_input("Floors", min_value=1, value=2)
    with col6:
        floor_height_per_storey = st.number_input("Floor Height (m)", min_value=2.0, value=3.0, step=0.1)

    # ── Section: Structural Parameters ──
    st.markdown('<div class="inp-sec">Structural Parameters</div>', unsafe_allow_html=True)

    col7, col8 = st.columns(2)
    with col7:
        column_capacity = st.number_input("Column Capacity (kN)", min_value=1.0, value=500.0)
    with col8:
        soil_capacity = st.number_input("Soil Capacity (kN/m²)", min_value=50.0, value=200.0)

    # ── Section: Foundation ──
    st.markdown('<div class="inp-sec">Initial Foundation</div>', unsafe_allow_html=True)

    col9, col10, col11 = st.columns(3)
    with col9:
        foundation_width = st.number_input("Foundation Width (m)", min_value=0.5, value=1.0)
    with col10:
        foundation_length = st.number_input("Foundation Length (m)", min_value=0.5, value=1.0)
    with col11:
        load_per_storey = st.number_input("Load per Storey (kN)", min_value=0.0, value=75.0, step=5.0, format="%.2f")

    # ── Live calculation preview ──
    floor_area = building_width * building_length
    engineering_load_per_storey = floor_area * 7.5
    total_load = engineering_load_per_storey * num_floors
    total_floor_area = floor_area * num_floors
    found_area = foundation_width * foundation_length
    soil_pressure = total_load / found_area if found_area > 0 else 0
    soil_util = soil_pressure / soil_capacity if soil_capacity > 0 else 0
    col_util = total_load / column_capacity if column_capacity > 0 else 0

    # Status prediction
    if soil_util > 1.0 or col_util > 1.0:
        pred_status = "FAIL — Correction required"
        pred_color = "#888"
    else:
        pred_status = "PASS — Within limits"
        pred_color = "#444"

    governing = "SOIL" if soil_util >= col_util else "COLUMN"

    st.markdown(f"""
    <div style="border:1px solid #e8e8e6;border-radius:6px;overflow:hidden;margin-top:20px;font-family:'DM Mono',monospace;">
      <div style="background:#f8f8f6;border-bottom:1px solid #e8e8e6;padding:8px 16px;">
        <span style="font-size:9px;color:#bbb;letter-spacing:.12em;text-transform:uppercase">Live Calculation Preview</span>
      </div>
      <div style="display:grid;grid-template-columns:repeat(4,1fr);background:#fff;">
        <div style="padding:10px 16px;border-right:1px solid #f0f0ee;">
          <div style="font-size:9px;color:#bbb;letter-spacing:.08em;text-transform:uppercase;margin-bottom:3px">Total Load</div>
          <div style="font-size:14px;color:#333">{total_load:,.0f} kN</div>
        </div>
        <div style="padding:10px 16px;border-right:1px solid #f0f0ee;">
          <div style="font-size:9px;color:#bbb;letter-spacing:.08em;text-transform:uppercase;margin-bottom:3px">Soil Util.</div>
          <div style="font-size:14px;color:{'#888' if soil_util > 1.0 else '#333'}">{soil_util:.3f}</div>
        </div>
        <div style="padding:10px 16px;border-right:1px solid #f0f0ee;">
          <div style="font-size:9px;color:#bbb;letter-spacing:.08em;text-transform:uppercase;margin-bottom:3px">Column Util.</div>
          <div style="font-size:14px;color:{'#888' if col_util > 1.0 else '#333'}">{col_util:.3f}</div>
        </div>
        <div style="padding:10px 16px;">
          <div style="font-size:9px;color:#bbb;letter-spacing:.08em;text-transform:uppercase;margin-bottom:3px">Predicted</div>
          <div style="font-size:12px;font-weight:500;color:{pred_color}">{pred_status}</div>
        </div>
      </div>
      <div style="background:#fafaf8;border-top:1px solid #f0f0ee;padding:6px 16px;display:flex;gap:20px;">
        <span style="font-size:10px;color:#bbb">Floor Area <span style="color:#555">{floor_area:,.0f} m²</span></span>
        <span style="font-size:10px;color:#bbb">Total Area <span style="color:#555">{total_floor_area:,.0f} m²</span></span>
        <span style="font-size:10px;color:#bbb">Governing Mode <span style="color:#555">{governing}</span></span>
        <span style="font-size:10px;color:#bbb">Foundation Area <span style="color:#555">{found_area:.2f} m²</span></span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    project_data = {
        "project_name": project_name,
        "building_type": building_type,
        "region": region.replace(" 🇹🇭","").replace(" 🇨🇳","").replace(" 🇺🇸",""),
        "building_width": building_width,
        "building_length": building_length,
        "num_floors": num_floors,
        "floor_height_per_storey": floor_height_per_storey,
        "column_capacity": column_capacity,
        "soil_capacity": soil_capacity,
        "load_per_storey": load_per_storey,
        "engineering_load_per_storey": engineering_load_per_storey,
        "total_load": total_load,
        "foundation_width": foundation_width,
        "foundation_length": foundation_length,
        "total_floor_area": total_floor_area
    }

    return project_data


def get_user_input(st_context):
    return render_user_input()


def validate_input(data):
    errors = []

    if data["building_width"] <= 0:
        errors.append("Building width must be greater than zero.")
    if data["building_length"] <= 0:
        errors.append("Building length must be greater than zero.")
    if data["num_floors"] <= 0:
        errors.append("Number of floors must be greater than zero.")
    if data["num_floors"] > CERTIFIED_MAX_STOREYS:
        errors.append(
            f"OUT OF SCOPE: Triple Bot V9 supports {CERTIFIED_MIN_STOREYS}–{CERTIFIED_MAX_STOREYS} storeys only."
        )
    if data["soil_capacity"] <= 0:
        errors.append("Soil capacity must be greater than zero.")
    if data["column_capacity"] <= 0:
        errors.append("Column capacity must be greater than zero.")
    if data["foundation_width"] <= 0:
        errors.append("Foundation width must be greater than zero.")
    if data["foundation_length"] <= 0:
        errors.append("Foundation length must be greater than zero.")

    if errors:
        return False, errors
    return True, []
