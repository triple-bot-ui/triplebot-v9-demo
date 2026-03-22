# ============================================
# TRIPLE BOT V5
# Structural Diagram Engine
# ============================================

import matplotlib.pyplot as plt
from io import BytesIO


def generate_conceptual_diagram(
    foundation_width,
    foundation_length,
    load,
    soil_pressure
):

    fig, ax = plt.subplots(figsize=(5,5))

    # --------------------------------
    # DRAW FOUNDATION
    # --------------------------------

    footing = plt.Rectangle(
        (-foundation_width/2, -0.2),
        foundation_width,
        0.2,
        fill=False,
        linewidth=2
    )

    ax.add_patch(footing)

    # --------------------------------
    # DRAW COLUMN
    # --------------------------------

    column = plt.Rectangle(
        (-0.05, 0),
        0.1,
        0.6,
        fill=False,
        linewidth=2
    )

    ax.add_patch(column)

    # --------------------------------
    # DRAW LOAD ARROW
    # --------------------------------

    ax.arrow(
        0,
        0.9,
        0,
        -0.25,
        head_width=0.05,
        head_length=0.05,
        length_includes_head=True
    )

    ax.text(
        0,
        0.95,
        f"Load = {load} kN",
        ha="center"
    )

    # --------------------------------
    # LABEL FOUNDATION
    # --------------------------------

    ax.text(
        0,
        -0.3,
        f"Foundation {foundation_width} m",
        ha="center"
    )

    # --------------------------------
    # SOIL LABEL
    # --------------------------------

    ax.text(
        0,
        -0.5,
        f"Soil Pressure = {soil_pressure} kN/m²",
        ha="center"
    )

    # --------------------------------
    # AXIS SETTINGS
    # --------------------------------

    ax.set_xlim(-1,1)
    ax.set_ylim(-1,1)

    ax.axis("off")

    # --------------------------------
    # EXPORT IMAGE
    # --------------------------------

    buffer = BytesIO()

    plt.savefig(buffer, format="png", bbox_inches="tight")

    buffer.seek(0)

    plt.close()

    return buffer