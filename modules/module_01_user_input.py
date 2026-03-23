import streamlit as st

# ============================================
# TRIPLE BOT V9.9.1
# Module 01 — User Input
# UI: Command Center (not a form)
# UPDATE: Added Load Assumption Panel (Input Depth)
# FIX: Split CSS inject from HTML to fix raw-text rendering bug
# ============================================

CERTIFIED_MIN_STOREYS = 1
CERTIFIED_MAX_STOREYS = 4

DEAD_LOAD_KNM2 = 4.5
SAFETY_FACTOR  = 1.5

LIVE_LOAD_MAP = {
    "Residential": 3.0,
    "Commercial":  5.0,
    "Industrial":  7.5,
}


def render_user_input():

    # ── CSS inject (separate call, no HTML mixed in) ──
    st.markdown("""
<style>
.cmd-header{border:1px solid #e0e0de;border-radius:8px;overflow:hidden;margin-bottom:20px;font-family:'DM Mono',monospace}
.cmd-top{background:#f0f0ee;border-bottom:1px solid #e0e0de;padding:14px 20px;display:flex;justify-content:space-between;align-items:center}
.cmd-title{font-size:13px;font-weight:600;color:#111;letter-spacing:.04em}
.cmd-scope{font-size:10px;color:#aaa;letter-spacing:.08em;text-transform:uppercase}
.cmd-status{font-size:10px;color:#888;background:#fff;border:1px solid #ddd;padding:3px 10px;border-radius:3px;letter-spacing:.06em}
.cmd-info{display:grid;grid-template-columns:repeat(3,1fr);background:#fff}
.cmd-info-cell{padding:12px 20px;border-right:1px solid #f0f0ee}
.cmd-info-cell:last-child{border-right:none}
.cmd-info-label{font-size:9px;color:#bbb;letter-spacing:.1em;text-transform:uppercase;margin-bottom:3px}
.cmd-info-val{font-size:13px;color:#333;font-weight:400}
.inp-sec{font-family:'DM Mono',monospace;font-size:9px;font-weight:600;letter-spacing:.14em;text-transform:uppercase;color:#bbb;border-bottom:1px solid #eee;padding-bottom:6px;margin:20px 0 12px}
.lb-card{border:1px solid #e8e8e6;border-radius:6px;padding:12px 14px;font-family:'DM Mono',monospace;background:#fff;height:100%}
.lb-card-title{font-size:9px;color:#bbb;letter-spacing:.1em;text-transform:uppercase;margin-bottom:8px}
.lb-row{font-size:11px;color:#555;margin-bottom:4px}
.lb-row b{color:#222}
.lb-total{font-size:11px;color:#111;font-weight:700;border-top:1px solid #eee;padding-top:6px;margin-top:6px}
</style>
""", unsafe_allow_html=True)

    # ── Command Center Header ──
    st.markdown("""
<div class="cmd-header">
  <div class="cmd-top">
    <div>
      <div class="cmd-title">TRIPLEBOT V9 &nbsp;&mdash;&nbsp; Project Input</div>
      <div class="cmd-scope">Pre-Construction Decision Engine</div>
    </div>
    <div class="cmd-status">READY</div>
  </div>
  <div class="cmd-info">
    <div class="cmd-info-cell"><div class="cmd-info-label">Engine</div><div class="cmd-info-val">Deterministic</div></div>
    <div class="cmd-info-cell"><div class="cmd-info-label">Scope</div><div class="cmd-info-val">RC Frame &middot; 1&ndash;4 Floors</div></div>
    <div class="cmd-info-cell"><div class="cmd-info-label">Mode</div><div class="cmd-info-val">Structural Validation</div></div>
  </div>
</div>
""", unsafe_allow_html=True)

    # ── Project ──
    st.markdown('<div class="inp-sec">Project</div>', unsafe_allow_html=True)
    col1, col2, col_region = st.columns([2, 1, 1])
    with col1:
        project_name = st.text_input("Project Name", value="My Project")
    with col2:
        building_type = st.selectbox("Building Type", ["Residential", "Commercial", "Industrial"])
    with col_region:
        region = st.selectbox("Region", ["Thailand 🇹🇭", "China 🇨🇳", "United States 🇺🇸"])

    # ── Building Geometry ──
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

    # ── Structural Parameters ──
    st.markdown('<div class="inp-sec">Structural Parameters</div>', unsafe_allow_html=True)
    col7, col8 = st.columns(2)
    with col7:
        column_capacity = st.number_input("Column Capacity (kN)", min_value=1.0, value=500.0)
    with col8:
        soil_capacity = st.number_input("Soil Capacity (kN/m²)", min_value=50.0, value=200.0)

    # ── Foundation ──
    st.markdown('<div class="inp-sec">Initial Foundation</div>', unsafe_allow_html=True)
    col9, col10, col11 = st.columns(3)
    with col9:
        foundation_width = st.number_input("Foundation Width (m)", min_value=0.5, value=1.0)
    with col10:
        foundation_length = st.number_input("Foundation Length (m)", min_value=0.5, value=1.0)
    with col11:
        load_per_storey = st.number_input("Load per Storey (kN)", min_value=0.0, value=75.0, step=5.0, format="%.2f")

    # ── Calculations ──
    live_load                   = LIVE_LOAD_MAP.get(building_type, 3.0)
    eng_load                    = DEAD_LOAD_KNM2 + live_load
    floor_area                  = building_width * building_length
    engineering_load_per_storey = floor_area * eng_load
    total_load                  = engineering_load_per_storey * num_floors
    total_floor_area            = floor_area * num_floors
    found_area                  = foundation_width * foundation_length
    soil_pressure               = total_load / found_area if found_area > 0 else 0
    soil_util                   = soil_pressure / soil_capacity if soil_capacity > 0 else 0
    col_util                    = total_load / column_capacity if column_capacity > 0 else 0
    governing                   = "SOIL" if soil_util >= col_util else "COLUMN"
    pred_status                 = "FAIL — Correction required" if (soil_util > 1.0 or col_util > 1.0) else "PASS — Within limits"
    pred_color                  = "#888" if (soil_util > 1.0 or col_util > 1.0) else "#444"

    # ── Live Calculation Preview ──
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
    <span style="font-size:10px;color:#bbb">Floor Area <span style="color:#555">{floor_area:,.0f} m&#178;</span></span>
    <span style="font-size:10px;color:#bbb">Total Area <span style="color:#555">{total_floor_area:,.0f} m&#178;</span></span>
    <span style="font-size:10px;color:#bbb">Governing Mode <span style="color:#555">{governing}</span></span>
    <span style="font-size:10px;color:#bbb">Foundation Area <span style="color:#555">{found_area:.2f} m&#178;</span></span>
  </div>
</div>
""", unsafe_allow_html=True)

    # ============================================
    # LOAD BASIS & ASSUMPTIONS — 3 cards via st.columns
    # (avoids CSS class rendering bug)
    # ============================================

    st.markdown('<div class="inp-sec" style="margin-top:18px">Load Basis &amp; Assumptions</div>', unsafe_allow_html=True)

    ca, cb, cc = st.columns(3)

    with ca:
        st.markdown(f"""
<div class="lb-card">
  <div class="lb-card-title">Load Components</div>
  <div class="lb-row">Dead Load (DL) &nbsp;&nbsp;&nbsp; <b>{DEAD_LOAD_KNM2} kN/m&#178;</b></div>
  <div class="lb-row">Live Load (LL) &nbsp;&nbsp;&nbsp;&nbsp; <b>{live_load} kN/m&#178;</b></div>
  <div class="lb-total">Eng. Load &nbsp; {eng_load} kN/m&#178; &larr; used</div>
</div>
""", unsafe_allow_html=True)

    with cb:
        st.markdown(f"""
<div class="lb-card">
  <div class="lb-card-title">Assumptions</div>
  <div class="lb-row">Combination &nbsp;&nbsp;&nbsp; <b>DL + LL</b></div>
  <div class="lb-row">Safety Factor &nbsp;&nbsp; <b>{SAFETY_FACTOR}&times; (preliminary)</b></div>
  <div class="lb-row">Scope &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; <b>1&ndash;4 Floors &middot; RC Frame</b></div>
</div>
""", unsafe_allow_html=True)

    with cc:
        st.markdown(f"""
<div class="lb-card">
  <div class="lb-card-title">Source &amp; Standard</div>
  <div class="lb-row">Benchmark &nbsp;&nbsp; <b>Internal</b></div>
  <div class="lb-row">Building Type &nbsp; <b>{building_type}</b></div>
  <div class="lb-row">Load Ref. &nbsp;&nbsp;&nbsp;&nbsp; <b>ACI 318-19</b></div>
  <div class="lb-row">Local Ref. &nbsp;&nbsp;&nbsp; <b>EIT 1007-34 / มยผ.</b></div>
  <div class="lb-row" style="font-size:9px;color:#bbb;margin-top:4px">Preliminary only — not for construction sign-off</div>
</div>
""", unsafe_allow_html=True)

    st.caption("⚠ Load values are internal benchmarks for preliminary validation only. Actual loads must be determined per applicable structural design codes (มยผ., ACI 318-19, EIT 1007-34). Final engineering approval must be performed by a licensed structural engineer.")
    st.markdown("""
<div style="border:1px solid #e8e8e6;border-radius:6px;padding:10px 16px;margin-top:8px;font-family:'DM Mono',monospace;background:#fafaf8;">
  <span style="font-size:9px;color:#bbb;letter-spacing:.1em;text-transform:uppercase">System Positioning</span><br/>
  <span style="font-size:11px;color:#444;font-weight:600">Triple Bot V9 = Error-Detection &amp; Speed-Booster</span><br/>
  <span style="font-size:10px;color:#888">Not a replacement for engineers — a tool to eliminate repetitive checks and catch errors early.</span>
</div>
""", unsafe_allow_html=True)

    # ── Scope of Use ──
    st.markdown('<div class="inp-sec" style="margin-top:18px">Scope of Use</div>', unsafe_allow_html=True)

    cs1, cs2 = st.columns(2)
    with cs1:
        st.markdown("""
<div class="lb-card">
  <div class="lb-card-title" style="color:#4a7c59">&#10003; Applicable For</div>
  <div class="lb-row">&#10003; &nbsp; Reinforced Concrete (RC) Frame</div>
  <div class="lb-row">&#10003; &nbsp; 1&ndash;4 Storeys</div>
  <div class="lb-row">&#10003; &nbsp; Regular rectangular plan</div>
  <div class="lb-row">&#10003; &nbsp; Static gravity load only</div>
  <div class="lb-row">&#10003; &nbsp; Firm soil (bearing capacity known)</div>
  <div class="lb-row">&#10003; &nbsp; Pre-design / Feasibility stage</div>
</div>
""", unsafe_allow_html=True)
    with cs2:
        st.markdown("""
<div class="lb-card">
  <div class="lb-card-title" style="color:#a05050">&#10007; NOT Applicable For (Red Flags)</div>
  <div class="lb-row">&#10007; &nbsp; Seismic zone — no lateral load analysis</div>
  <div class="lb-row">&#10007; &nbsp; Soft clay / peat — high settlement risk</div>
  <div class="lb-row">&#10007; &nbsp; Wind load — not included</div>
  <div class="lb-row">&#10007; &nbsp; Irregular plan / complex geometry</div>
  <div class="lb-row">&#10007; &nbsp; Pile foundation</div>
  <div class="lb-row">&#10007; &nbsp; Steel / timber frame</div>
  <div class="lb-row" style="font-size:9px;color:#a05050;margin-top:4px;font-weight:600">Using outside scope = unsafe result</div>
</div>
""", unsafe_allow_html=True)

    project_data = {
        "project_name":                project_name,
        "building_type":               building_type,
        "region":                      region.replace(" 🇹🇭","").replace(" 🇨🇳","").replace(" 🇺🇸",""),
        "building_width":              building_width,
        "building_length":             building_length,
        "num_floors":                  num_floors,
        "floor_height_per_storey":     floor_height_per_storey,
        "column_capacity":             column_capacity,
        "soil_capacity":               soil_capacity,
        "load_per_storey":             load_per_storey,
        "engineering_load_per_storey": engineering_load_per_storey,
        "total_load":                  total_load,
        "foundation_width":            foundation_width,
        "foundation_length":           foundation_length,
        "total_floor_area":            total_floor_area,
        "dead_load_knm2":              DEAD_LOAD_KNM2,
        "live_load_knm2":              live_load,
        "engineering_load_knm2":       eng_load,
        "load_safety_factor":          SAFETY_FACTOR,
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
        errors.append(f"OUT OF SCOPE: Triple Bot V9 supports {CERTIFIED_MIN_STOREYS}–{CERTIFIED_MAX_STOREYS} storeys only.")
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
