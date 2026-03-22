# ============================================
# TRIPLE BOT V9
# Module 03 — Layout Editing Module
# ============================================

def get_layout_edits(st, project_data, rooms):
    """
    Allow user to adjust the layout.
    Returns updated project_data and rooms.
    """

    st.header("Layout Editing")
    st.caption("Adjust your floor plan before proceeding to 3D visualization.")

    edited_data = project_data.copy()

    # ============================================
    # BUILDING SIZE ADJUSTMENT
    # ============================================

    st.subheader("Adjust Building Size")

    col1, col2 = st.columns(2)

    with col1:
        new_width = st.slider(
            "Building Width (m)",
            min_value=5.0,
            max_value=200.0,
            value=float(project_data["building_width"]),
            step=0.5
        )

    with col2:
        new_length = st.slider(
            "Building Length (m)",
            min_value=5.0,
            max_value=200.0,
            value=float(project_data["building_length"]),
            step=0.5
        )

    edited_data["building_width"] = new_width
    edited_data["building_length"] = new_length

    # ============================================
    # FLOOR COUNT ADJUSTMENT
    # ============================================

    st.subheader("Adjust Number of Floors")

    new_floors = st.slider(
        "Number of Floors",
        min_value=1,
        max_value=50,
        value=int(project_data["num_floors"]),
        step=1
    )

    edited_data["num_floors"] = new_floors

    # ============================================
    # ROOM ADJUSTMENT
    # ============================================

    st.subheader("Adjust Rooms")

    edited_rooms = []

    for i, room in enumerate(rooms):
        with st.expander(f"Room {i+1} — {room['name']}"):

            col3, col4 = st.columns(2)

            with col3:
                new_name = st.selectbox(
                    "Room Type",
                    ["Living Room", "Bedroom", "Kitchen",
                     "Bathroom", "Dining Room", "Office",
                     "Lobby", "Storage", "Corridor"],
                    index=_get_room_index(room["name"]),
                    key=f"room_name_{i}"
                )

                new_w = st.slider(
                    "Width (m)",
                    min_value=1.0,
                    max_value=float(new_width),
                    value=min(float(room["w"]), float(new_width)),
                    step=0.5,
                    key=f"room_w_{i}"
                )

            with col4:
                new_x = st.slider(
                    "Position X (m)",
                    min_value=0.0,
                    max_value=float(new_width),
                    value=min(float(room["x"]), float(new_width)),
                    step=0.5,
                    key=f"room_x_{i}"
                )

                new_h = st.slider(
                    "Height (m)",
                    min_value=1.0,
                    max_value=float(new_length),
                    value=min(float(room["h"]), float(new_length)),
                    step=0.5,
                    key=f"room_h_{i}"
                )

            new_y = st.slider(
                "Position Y (m)",
                min_value=0.0,
                max_value=float(new_length),
                value=min(float(room["y"]), float(new_length)),
                step=0.5,
                key=f"room_y_{i}"
            )

            edited_rooms.append({
                "name": new_name,
                "x": new_x,
                "y": new_y,
                "w": new_w,
                "h": new_h
            })

    # ============================================
    # BUILDING TYPE
    # ============================================

    st.subheader("Building Type")

    new_type = st.selectbox(
        "Building Type",
        ["Residential", "Commercial", "Industrial", "Mixed Use"],
        index=_get_type_index(project_data["building_type"])
    )

    edited_data["building_type"] = new_type

    # ============================================
    # REGENERATE LAYOUT OPTION
    # ============================================

    st.subheader("Regenerate Layout")

    regenerate = st.checkbox(
        "Regenerate layout from scratch (resets all room edits)",
        value=False
    )

    if regenerate:
        edited_rooms = None
        st.info("Layout will be regenerated from building size and type.")

    # ============================================
    # SUMMARY
    # ============================================

    st.subheader("Edit Summary")

    col5, col6, col7 = st.columns(3)

    col5.metric(
        "Building Size",
        f"{new_width}m × {new_length}m"
    )

    col6.metric(
        "Total Area",
        f"{round(new_width * new_length, 1)} m²"
    )

    col7.metric(
        "Floors",
        f"{new_floors}"
    )

    return edited_data, edited_rooms


def _get_room_index(room_name):
    """Get selectbox index for room type."""
    options = [
        "Living Room", "Bedroom", "Kitchen",
        "Bathroom", "Dining Room", "Office",
        "Lobby", "Storage", "Corridor"
    ]
    if room_name in options:
        return options.index(room_name)
    return 0


def _get_type_index(building_type):
    """Get selectbox index for building type."""
    options = ["Residential", "Commercial", "Industrial", "Mixed Use"]
    if building_type in options:
        return options.index(building_type)
    return 0


def validate_edited_layout(edited_data, edited_rooms):
    """
    Validate edited layout before proceeding.
    Returns (is_valid, error_messages)
    """

    errors = []

    if edited_data["building_width"] <= 0:
        errors.append("Building width must be greater than zero.")

    if edited_data["building_length"] <= 0:
        errors.append("Building length must be greater than zero.")

    if edited_data["num_floors"] <= 0:
        errors.append("Number of floors must be at least 1.")

    if edited_rooms:
        for i, room in enumerate(edited_rooms):
            if room["w"] <= 0 or room["h"] <= 0:
                errors.append(f"Room {i+1} ({room['name']}) has invalid size.")
            if room["x"] < 0 or room["y"] < 0:
                errors.append(f"Room {i+1} ({room['name']}) has invalid position.")

    if errors:
        return False, errors

    return True, []
