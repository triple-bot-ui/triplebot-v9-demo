# ============================================
# TRIPLE BOT V9
# Module 02 — Layout Generation Module
# UI: Clean B&W Architectural / CAD Style
# ============================================

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
import io


def generate_2d_layout(project_data):

    width         = project_data["building_width"]
    length        = project_data["building_length"]
    num_floors    = project_data["num_floors"]
    building_type = project_data["building_type"]
    project_name  = project_data["project_name"]

    rooms = _generate_room_layout(width, length, building_type)

    # ── Canvas ──
    fig, ax = plt.subplots(1, 1, figsize=(9, 9))
    ax.set_facecolor("#ffffff")
    fig.patch.set_facecolor("#ffffff")

    margin = 1.8
    ax.set_xlim(-margin, width + margin)
    ax.set_ylim(-margin, length + margin)
    ax.set_aspect("equal")
    ax.axis("off")

    # ── Hatch pattern for wall thickness ──
    WALL_T = 0.25  # wall thickness visual

    # Outer wall fill (hatch)
    outer = patches.Rectangle(
        (0, 0), width, length,
        linewidth=0, edgecolor="none",
        facecolor="#cccccc", zorder=1
    )
    ax.add_patch(outer)

    # Inner white area
    inner = patches.Rectangle(
        (WALL_T, WALL_T),
        width - 2*WALL_T,
        length - 2*WALL_T,
        linewidth=0, edgecolor="none",
        facecolor="#ffffff", zorder=2
    )
    ax.add_patch(inner)

    # Outer wall border
    outer_border = patches.Rectangle(
        (0, 0), width, length,
        linewidth=3.5, edgecolor="#111111",
        facecolor="none", zorder=5
    )
    ax.add_patch(outer_border)

    # Inner wall border
    inner_border = patches.Rectangle(
        (WALL_T, WALL_T),
        width - 2*WALL_T,
        length - 2*WALL_T,
        linewidth=0.8, edgecolor="#333333",
        facecolor="none", zorder=5
    )
    ax.add_patch(inner_border)

    # ── Room dividers ──
    for room in rooms:
        rect = patches.Rectangle(
            (room["x"], room["y"]),
            room["w"], room["h"],
            linewidth=1.8,
            edgecolor="#111111",
            facecolor="none",
            zorder=3
        )
        ax.add_patch(rect)

        # Room name
        cx = room["x"] + room["w"] / 2
        cy = room["y"] + room["h"] / 2
        area = round(room["w"] * room["h"], 1)

        ax.text(cx, cy + 0.18, room["name"],
                ha="center", va="center",
                fontsize=7.5, fontweight="500",
                color="#111111", zorder=6,
                fontfamily="monospace",
                linespacing=1.3)

        ax.text(cx, cy - 0.22, f"{area} m²",
                ha="center", va="center",
                fontsize=6.5, color="#777777",
                zorder=6, fontfamily="monospace")

    # ── Dimension lines ──
    DIM_COL = "#444444"
    DIM_OFF = 0.8

    # Width — bottom
    ax.annotate("", xy=(width, -DIM_OFF), xytext=(0, -DIM_OFF),
                arrowprops=dict(arrowstyle="<->", color=DIM_COL, lw=0.9))
    ax.plot([0, 0], [-DIM_OFF+0.12, -DIM_OFF-0.12],
            color=DIM_COL, lw=0.8)
    ax.plot([width, width], [-DIM_OFF+0.12, -DIM_OFF-0.12],
            color=DIM_COL, lw=0.8)
    ax.text(width/2, -DIM_OFF - 0.32, f"{width:.1f} m",
            ha="center", va="top", fontsize=7.5,
            color=DIM_COL, fontfamily="monospace")

    # Length — right
    ax.annotate("", xy=(width+DIM_OFF, length), xytext=(width+DIM_OFF, 0),
                arrowprops=dict(arrowstyle="<->", color=DIM_COL, lw=0.9))
    ax.plot([width+DIM_OFF-0.12, width+DIM_OFF+0.12], [0, 0],
            color=DIM_COL, lw=0.8)
    ax.plot([width+DIM_OFF-0.12, width+DIM_OFF+0.12], [length, length],
            color=DIM_COL, lw=0.8)
    ax.text(width+DIM_OFF+0.32, length/2, f"{length:.1f} m",
            ha="left", va="center", fontsize=7.5,
            color=DIM_COL, fontfamily="monospace", rotation=90)

    # ── North arrow ──
    na_x = width - 0.6
    na_y = length - 0.6
    circle = plt.Circle((na_x, na_y), 0.38,
                         fill=False, edgecolor="#222222", lw=1.0, zorder=7)
    ax.add_patch(circle)
    ax.annotate("", xy=(na_x, na_y+0.28), xytext=(na_x, na_y-0.08),
                arrowprops=dict(arrowstyle="-|>", color="#111111",
                                lw=1.2, mutation_scale=8), zorder=8)
    ax.text(na_x, na_y-0.52, "N",
            ha="center", va="top", fontsize=7,
            fontweight="bold", color="#222222",
            fontfamily="monospace", zorder=8)

    # ── Title strip ──
    ax.text(width/2, length + 0.55,
            f"{project_name}  —  Floor Plan (Floor 1 of {num_floors})",
            ha="center", va="bottom", fontsize=8.5,
            color="#111111", fontfamily="monospace", fontweight="bold")

    ax.text(width/2, length + 0.15,
            f"Building: {width}m × {length}m  |  Type: {building_type}",
            ha="center", va="bottom", fontsize=7,
            color="#777777", fontfamily="monospace")

    # ── Footer ──
    ax.text(width/2, -margin + 0.1,
            "2D FLOOR PLAN  —  AUTO GENERATED  ·  VISUALIZATION ONLY",
            ha="center", va="bottom", fontsize=6.5,
            color="#bbbbbb", fontfamily="monospace")

    plt.tight_layout(pad=0.5)

    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=150,
                bbox_inches="tight", facecolor="#ffffff")
    buf.seek(0)
    plt.close(fig)
    return buf


# ── Room layout generators (unchanged logic) ──

def _generate_room_layout(width, length, building_type):
    rooms = []
    margin = 0.3
    if building_type == "Residential":
        rooms = _residential_layout(width, length, margin)
    elif building_type == "Commercial":
        rooms = _commercial_layout(width, length, margin)
    elif building_type == "Industrial":
        rooms = _industrial_layout(width, length, margin)
    else:
        rooms = _mixed_layout(width, length, margin)
    return rooms


def _residential_layout(width, length, margin):
    w  = width  - 2 * margin
    l  = length - 2 * margin
    x0 = margin
    y0 = margin
    return [
        {"name": "Living Room",  "x": x0,           "y": y0,           "w": w*0.55, "h": l*0.45},
        {"name": "Kitchen",      "x": x0+w*0.55,    "y": y0,           "w": w*0.45, "h": l*0.30},
        {"name": "Dining Room",  "x": x0+w*0.55,    "y": y0+l*0.30,   "w": w*0.45, "h": l*0.15},
        {"name": "Bedroom",      "x": x0,           "y": y0+l*0.45,   "w": w*0.50, "h": l*0.55},
        {"name": "Bedroom",      "x": x0+w*0.50,    "y": y0+l*0.65,   "w": w*0.25, "h": l*0.35},
        {"name": "Bathroom",     "x": x0+w*0.75,    "y": y0+l*0.65,   "w": w*0.25, "h": l*0.35},
        {"name": "Storage",      "x": x0+w*0.55,    "y": y0+l*0.45,   "w": w*0.45, "h": l*0.20},
    ]


def _commercial_layout(width, length, margin):
    w  = width  - 2 * margin
    l  = length - 2 * margin
    x0 = margin
    y0 = margin
    return [
        {"name": "Lobby",    "x": x0,        "y": y0,         "w": w,      "h": l*0.20},
        {"name": "Office",   "x": x0,        "y": y0+l*0.20,  "w": w*0.60, "h": l*0.50},
        {"name": "Storage",  "x": x0+w*0.60, "y": y0+l*0.20,  "w": w*0.40, "h": l*0.50},
        {"name": "Corridor", "x": x0,        "y": y0+l*0.70,  "w": w,      "h": l*0.30},
    ]


def _industrial_layout(width, length, margin):
    w  = width  - 2 * margin
    l  = length - 2 * margin
    x0 = margin
    y0 = margin
    return [
        {"name": "Storage", "x": x0,        "y": y0,         "w": w,      "h": l*0.70},
        {"name": "Office",  "x": x0,        "y": y0+l*0.70,  "w": w*0.50, "h": l*0.30},
        {"name": "Lobby",   "x": x0+w*0.50, "y": y0+l*0.70,  "w": w*0.50, "h": l*0.30},
    ]


def _mixed_layout(width, length, margin):
    w  = width  - 2 * margin
    l  = length - 2 * margin
    x0 = margin
    y0 = margin
    return [
        {"name": "Lobby",       "x": x0,        "y": y0,         "w": w,      "h": l*0.15},
        {"name": "Office",      "x": x0,        "y": y0+l*0.15,  "w": w*0.50, "h": l*0.45},
        {"name": "Living Room", "x": x0+w*0.50, "y": y0+l*0.15,  "w": w*0.50, "h": l*0.45},
        {"name": "Bedroom",     "x": x0,        "y": y0+l*0.60,  "w": w*0.50, "h": l*0.40},
        {"name": "Storage",     "x": x0+w*0.50, "y": y0+l*0.60,  "w": w*0.50, "h": l*0.40},
    ]
