# ============================================
# TRIPLE BOT V9
# Module 04 — 3D Visualization Module
# UI: Blueprint Wireframe Style
# ============================================
# Visualization only — NO structural modification
# ============================================

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection, Line3DCollection
import numpy as np
import io


def generate_3d_visualization(project_data):

    width       = project_data["building_width"]
    length      = project_data["building_length"]
    num_floors  = project_data["num_floors"]
    floor_height = project_data["floor_height_per_storey"]
    building_type = project_data["building_type"]
    project_name  = project_data["project_name"]
    total_height  = num_floors * floor_height

    # ── Dark blueprint background ──
    BG      = "#0d1929"
    EDGE    = "#ffffff"
    SLAB    = "#1a3a5c"
    WALL    = "#0f2540"
    ACCENT  = "#4a9eff"
    DIMCOL  = "#4a6fa5"
    TEXTCOL = "#8aafd4"

    fig = plt.figure(figsize=(13, 7), facecolor=BG)

    # ── Perspective View ──
    ax1 = fig.add_subplot(121, projection="3d")
    ax1.set_facecolor(BG)
    _draw_blueprint(ax1, width, length, total_height, num_floors,
                    floor_height, BG, EDGE, SLAB, WALL, ACCENT)
    _style_ax(ax1, width, length, total_height, TEXTCOL, BG)
    ax1.view_init(elev=28, azim=45)
    ax1.set_title("Perspective View", color=TEXTCOL, fontsize=9,
                  pad=8, fontfamily="monospace")

    # ── Front Elevation ──
    ax2 = fig.add_subplot(122, projection="3d")
    ax2.set_facecolor(BG)
    _draw_blueprint(ax2, width, length, total_height, num_floors,
                    floor_height, BG, EDGE, SLAB, WALL, ACCENT)
    _style_ax(ax2, width, length, total_height, TEXTCOL, BG)
    ax2.view_init(elev=8, azim=0)
    ax2.set_title("Front Elevation", color=TEXTCOL, fontsize=9,
                  pad=8, fontfamily="monospace")

    # ── Title ──
    fig.suptitle(
        f"{project_name}  —  3D Visualization\n"
        f"{width}m × {length}m × {total_height}m  |  "
        f"{num_floors} Floor(s)  |  {building_type}",
        color=TEXTCOL, fontsize=10, fontfamily="monospace",
        y=1.01
    )

    # ── Footer ──
    total_area = round(width * length * num_floors, 1)
    info = (
        f"Total Area: {total_area} m²   ·   "
        f"Height: {total_height}m ({num_floors} × {floor_height}m)   ·   "
        f"Type: {building_type}   ·   "
        f"[Visualization only — no structural data modified]"
    )
    fig.text(0.5, -0.01, info, ha="center", color=DIMCOL,
             fontsize=7.5, fontfamily="monospace")

    plt.tight_layout(pad=1.5)

    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=150,
                bbox_inches="tight", facecolor=BG)
    buf.seek(0)
    plt.close(fig)
    return buf


def _draw_blueprint(ax, W, L, H, floors, fh, BG, EDGE, SLAB, WALL, ACCENT):
    """Draw clean wireframe building — blueprint style."""

    for f in range(floors):
        zb = f * fh
        zt = zb + fh

        # ── Wall faces (subtle fill) ──
        faces = [
            # Front
            [(0,0,zb),(W,0,zb),(W,0,zt),(0,0,zt)],
            # Back
            [(0,L,zb),(W,L,zb),(W,L,zt),(0,L,zt)],
            # Left
            [(0,0,zb),(0,L,zb),(0,L,zt),(0,0,zt)],
            # Right
            [(W,0,zb),(W,L,zb),(W,L,zt),(W,0,zt)],
        ]
        walls = Poly3DCollection(faces, alpha=0.12,
                                 facecolor=WALL, edgecolor="none")
        ax.add_collection3d(walls)

        # ── Floor slab ──
        slab_verts = [[(0,0,zb),(W,0,zb),(W,L,zb),(0,L,zb)]]
        slab = Poly3DCollection(slab_verts, alpha=0.25,
                                facecolor=SLAB, edgecolor="none")
        ax.add_collection3d(slab)

        # ── Wireframe edges — floor perimeter ──
        _draw_rect_edge(ax, 0, W, 0, L, zb, EDGE, lw=0.8)

        # ── Vertical corner lines ──
        corners = [(0,0),(W,0),(W,L),(0,L)]
        for (x,y) in corners:
            ax.plot([x,x],[y,y],[zb,zt], color=EDGE, lw=0.8, alpha=0.9)

        # ── Window grid on front face ──
        _draw_window_grid(ax, W, fh, zb, ACCENT)

    # ── Roof slab ──
    roof = [[(0,0,H),(W,0,H),(W,L,H),(0,L,H)]]
    roof_col = Poly3DCollection(roof, alpha=0.35,
                                facecolor=SLAB, edgecolor="none")
    ax.add_collection3d(roof_col)
    _draw_rect_edge(ax, 0, W, 0, L, H, EDGE, lw=1.2)

    # ── Top vertical edges ──
    corners = [(0,0),(W,0),(W,L),(0,L)]
    for (x,y) in corners:
        ax.plot([x,x],[y,y],[0,H], color=ACCENT, lw=0.5, alpha=0.4)


def _draw_rect_edge(ax, x0, x1, y0, y1, z, color, lw=1.0):
    """Draw rectangle edge at height z."""
    xs = [x0, x1, x1, x0, x0]
    ys = [y0, y0, y1, y1, y0]
    zs = [z,  z,  z,  z,  z ]
    ax.plot(xs, ys, zs, color=color, lw=lw, alpha=0.85)


def _draw_window_grid(ax, W, fh, zb, color, cols=3, rows=2):
    """Draw subtle window grid on front face (y=0)."""
    margin_x = W * 0.1
    margin_z = fh * 0.2
    win_w = (W - 2 * margin_x) / cols
    win_h = (fh - 2 * margin_z) / rows

    for c in range(cols):
        for r in range(rows):
            x0 = margin_x + c * win_w + win_w * 0.1
            x1 = margin_x + c * win_w + win_w * 0.9
            z0 = zb + margin_z + r * win_h + win_h * 0.1
            z1 = zb + margin_z + r * win_h + win_h * 0.9
            xs = [x0, x1, x1, x0, x0]
            ys = [0,  0,  0,  0,  0]
            zs = [z0, z0, z1, z1, z0]
            ax.plot(xs, ys, zs, color=color, lw=0.5, alpha=0.5)


def _style_ax(ax, W, L, H, textcol, bgcol):
    """Clean axis styling."""
    ax.set_xlim(0, W)
    ax.set_ylim(0, L)
    ax.set_zlim(0, H * 1.15)

    ax.set_xlabel("Length (m)", color=textcol, fontsize=7,
                  labelpad=4, fontfamily="monospace")
    ax.set_ylabel("Width (m)", color=textcol, fontsize=7,
                  labelpad=4, fontfamily="monospace")
    ax.set_zlabel("Height (m)", color=textcol, fontsize=7,
                  labelpad=4, fontfamily="monospace")

    ax.tick_params(colors=textcol, labelsize=6)

    # Transparent pane backgrounds
    ax.xaxis.pane.fill = False
    ax.yaxis.pane.fill = False
    ax.zaxis.pane.fill = False
    ax.xaxis.pane.set_edgecolor("#1a3a5c")
    ax.yaxis.pane.set_edgecolor("#1a3a5c")
    ax.zaxis.pane.set_edgecolor("#1a3a5c")

    # Grid lines subtle
    ax.xaxis._axinfo["grid"]["color"] = "#0f2540"
    ax.yaxis._axinfo["grid"]["color"] = "#0f2540"
    ax.zaxis._axinfo["grid"]["color"] = "#0f2540"
    ax.xaxis._axinfo["grid"]["linewidth"] = 0.4
    ax.yaxis._axinfo["grid"]["linewidth"] = 0.4
    ax.zaxis._axinfo["grid"]["linewidth"] = 0.4
