import streamlit as st


# ============================================
# TRIPLE BOT V9.7
# Module 05 — Design Confirmation
# FIXED:
# - Restore summarize_confirmed_design() for app compatibility
# - Soil Capacity display must use project_data["soil_capacity"]
# - Unit must be kN/m²
# - Keep behavior simple, no extra styling
# ============================================


def _safe_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def summarize_confirmed_design(project_data, *args, **kwargs):
    """
    Compatibility function required by triplebot_v9_app.py

    Returns a normalized design summary dict while preserving original keys.
    """
    data = dict(project_data) if isinstance(project_data, dict) else {}

    building_width = _safe_float(data.get("building_width", 0.0))
    building_length = _safe_float(data.get("building_length", 0.0))
    num_floors = _safe_int(data.get("num_floors", 0))
    floor_height = _safe_float(data.get("floor_height_per_storey", 0.0))

    foundation_width = _safe_float(data.get("foundation_width", 0.0))
    foundation_length = _safe_float(data.get("foundation_length", 0.0))
    foundation_area = round(foundation_width * foundation_length, 3)

    load_per_storey = _safe_float(data.get("load_per_storey", 0.0))
    soil_capacity = _safe_float(data.get("soil_capacity", 0.0))
    column_capacity = _safe_float(data.get("column_capacity", 0.0))

    total_floor_area = data.get("total_floor_area")
    if total_floor_area in (None, ""):
        total_floor_area = round(building_width * building_length * max(num_floors, 1), 3)
    else:
        total_floor_area = _safe_float(
            total_floor_area,
            round(building_width * building_length * max(num_floors, 1), 3)
        )

    engineering_load_per_storey = data.get("engineering_load_per_storey")
    if engineering_load_per_storey in (None, ""):
        engineering_load_per_storey = round(load_per_storey * building_width * building_length, 3)
    else:
        engineering_load_per_storey = _safe_float(engineering_load_per_storey, 0.0)

    total_load = data.get("total_load")
    if total_load in (None, ""):
        total_load = round(engineering_load_per_storey * max(num_floors, 1), 3)
    else:
        total_load = _safe_float(total_load, 0.0)

    summary = dict(data)
    summary.update(
        {
            "project_name": str(data.get("project_name", "My Project")),
            "building_type": str(data.get("building_type", "Residential")),
            "building_width": building_width,
            "building_length": building_length,
            "num_floors": num_floors,
            "floor_height_per_storey": floor_height,
            "total_floor_area": total_floor_area,
            "foundation_width": foundation_width,
            "foundation_length": foundation_length,
            "foundation_area": foundation_area,
            "column_capacity": column_capacity,
            "soil_capacity": soil_capacity,
            "load_per_storey": load_per_storey,
            "engineering_load_per_storey": engineering_load_per_storey,
            "total_load": total_load,
        }
    )
    return summary


def render_design_confirmation(st_context, project_data):
    summary = summarize_confirmed_design(project_data)

    st_context.header("Design Confirmation")
    st_context.subheader("Project Summary")

    col1, col2, col3 = st_context.columns(3)

    with col1:
        st_context.metric("Project Name", summary.get("project_name", "N/A"))
        st_context.metric("Building Type", summary.get("building_type", "N/A"))
        st_context.metric(
            "Building Size",
            f"{summary.get('building_width', 0):.1f} m × {summary.get('building_length', 0):.1f} m"
        )

    with col2:
        st_context.metric("Number of Floors", summary.get("num_floors", "N/A"))
        st_context.metric(
            "Floor Height per Storey (m)",
            f"{summary.get('floor_height_per_storey', 0):.1f}"
        )
        st_context.metric(
            "Total Floor Area (m²)",
            f"{summary.get('total_floor_area', 0):.1f}"
        )

    with col3:
        st_context.metric(
            "Foundation Size (m)",
            f"{summary.get('foundation_width', 0):.1f} × {summary.get('foundation_length', 0):.1f}"
        )
        st_context.metric(
            "Column Capacity (kN)",
            f"{summary.get('column_capacity', 0):.1f}"
        )
        st_context.metric(
            "Soil Capacity (kN/m²)",
            f"{summary.get('soil_capacity', 0):.1f}"
        )

    st_context.subheader("Load Summary")

    load_col1, load_col2, load_col3 = st_context.columns(3)

    with load_col1:
        st_context.metric(
            "Load per Storey (kN)",
            f"{summary.get('load_per_storey', 0):.1f}"
        )

    with load_col2:
        st_context.metric(
            "Engineering Load per Storey (kN)",
            f"{summary.get('engineering_load_per_storey', 0):.1f}"
        )

    with load_col3:
        st_context.metric(
            "Total Load (kN)",
            f"{summary.get('total_load', 0):.1f}"
        )

    st_context.subheader("Confirm Next Action")

    decision = st_context.radio(
        "Choose action",
        [
            "Proceed to Engineering Validation",
            "Go Back and Edit Input",
            "Regenerate / Review Again",
        ],
        index=0,
    )

    confirmed = st_context.button("Confirm Decision", type="primary")

    if confirmed:
        if decision.startswith("Proceed"):
            return "proceed"
        if decision.startswith("Go Back"):
            return "edit"
        if decision.startswith("Regenerate"):
            return "regenerate"

    return None


def get_design_confirmation(st_context, project_data):
    return render_design_confirmation(st_context, project_data)