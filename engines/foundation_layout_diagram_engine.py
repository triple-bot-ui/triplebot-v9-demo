"""
TRIPLE BOT – FOUNDATION LAYOUT DIAGRAM ENGINE
Version: V10 DEV

Purpose:
Convert deterministic foundation layout coordinates into
a PNG engineering diagram.

This engine receives layout data generated from
foundation_layout_engine.py and renders a simple
foundation plan drawing using matplotlib.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Dict, Optional

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle


def generate_foundation_layout_diagram(
    foundation_width: float,
    foundation_length: float,
    layout: List[Dict[str, float]],
    output_path: str,
    project_name: str = "Triple Bot V10",
    show_column_labels: bool = True,
    footing_size: Optional[float] = None,
) -> str:
    """
    Generate a foundation layout PNG diagram.

    Parameters
    ----------
    foundation_width : float
        Overall foundation width in meters.
    foundation_length : float
        Overall foundation length in meters.
    layout : list[dict]
        Layout data from foundation_layout_engine.generate_foundation_layout().
        Each item must contain:
            - column_id
            - x
            - y
    output_path : str
        Target PNG file path.
    project_name : str, optional
        Title shown on the diagram.
    show_column_labels : bool, optional
        If True, draw column IDs near each column.
    footing_size : float | None, optional
        If provided, draw a square footing centered at each column.
        Value is in meters.

    Returns
    -------
    str
        Absolute path to the generated PNG file.
    """

    _validate_inputs(
        foundation_width=foundation_width,
        foundation_length=foundation_length,
        layout=layout,
        output_path=output_path,
        footing_size=footing_size,
    )

    output_file = Path(output_path).expanduser().resolve()
    output_file.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(10, 8))

    # Foundation boundary
    boundary = Rectangle(
        (0, 0),
        foundation_width,
        foundation_length,
        fill=False,
        linewidth=2.0,
    )
    ax.add_patch(boundary)

    # Sort layout for consistent drawing order
    sorted_layout = sorted(
        layout,
        key=lambda item: (float(item["x"]), float(item["y"]), str(item["column_id"]))
    )

    # Draw grid lines based on unique x and y
    unique_x = sorted({round(float(item["x"]), 6) for item in sorted_layout})
    unique_y = sorted({round(float(item["y"]), 6) for item in sorted_layout})

    for x in unique_x:
        ax.plot([x, x], [0, foundation_length], linewidth=1.0, linestyle="--")

    for y in unique_y:
        ax.plot([0, foundation_width], [y, y], linewidth=1.0, linestyle="--")

    # Draw footings and columns
    for item in sorted_layout:
        column_id = str(item["column_id"])
        x = float(item["x"])
        y = float(item["y"])

        if footing_size is not None and footing_size > 0:
            half = footing_size / 2.0
            footing = Rectangle(
                (x - half, y - half),
                footing_size,
                footing_size,
                fill=False,
                linewidth=1.2,
            )
            ax.add_patch(footing)

        column = Circle((x, y), radius=_column_radius(foundation_width, foundation_length))
        ax.add_patch(column)

        if show_column_labels:
            ax.text(
                x + foundation_width * 0.01,
                y + foundation_length * 0.01,
                column_id,
                fontsize=9,
                ha="left",
                va="bottom",
            )

    # Title / metadata
    ax.set_title(
        f"{project_name} – Foundation Layout Plan\n"
        f"Foundation: {foundation_width:.2f} m × {foundation_length:.2f} m",
        pad=14,
    )
    ax.set_xlabel("Width (m)")
    ax.set_ylabel("Length (m)")

    # Padding around foundation
    pad_x = max(foundation_width * 0.08, 0.5)
    pad_y = max(foundation_length * 0.08, 0.5)

    ax.set_xlim(-pad_x, foundation_width + pad_x)
    ax.set_ylim(-pad_y, foundation_length + pad_y)
    ax.set_aspect("equal", adjustable="box")

    # Add dimension notes
    ax.text(
        foundation_width / 2.0,
        -pad_y * 0.55,
        f"{foundation_width:.2f} m",
        ha="center",
        va="center",
        fontsize=10,
    )
    ax.text(
        -pad_x * 0.55,
        foundation_length / 2.0,
        f"{foundation_length:.2f} m",
        ha="center",
        va="center",
        rotation=90,
        fontsize=10,
    )

    ax.grid(False)
    plt.tight_layout()
    fig.savefig(output_file, dpi=200, bbox_inches="tight")
    plt.close(fig)

    return str(output_file)


def _validate_inputs(
    foundation_width: float,
    foundation_length: float,
    layout: List[Dict[str, float]],
    output_path: str,
    footing_size: Optional[float],
) -> None:
    """
    Validate diagram engine inputs.
    """

    if foundation_width <= 0:
        raise ValueError("foundation_width must be greater than 0")

    if foundation_length <= 0:
        raise ValueError("foundation_length must be greater than 0")

    if not layout:
        raise ValueError("layout must not be empty")

    if not output_path or not str(output_path).strip():
        raise ValueError("output_path must not be empty")

    if footing_size is not None and footing_size <= 0:
        raise ValueError("footing_size must be greater than 0 when provided")

    required_keys = {"column_id", "x", "y"}

    for index, item in enumerate(layout):
        if not isinstance(item, dict):
            raise TypeError(f"layout item at index {index} must be a dict")

        missing = required_keys - set(item.keys())
        if missing:
            raise KeyError(
                f"layout item at index {index} is missing required keys: {sorted(missing)}"
            )

        x = float(item["x"])
        y = float(item["y"])

        if x < 0 or x > foundation_width:
            raise ValueError(
                f"layout item at index {index} has x={x}, outside foundation width"
            )

        if y < 0 or y > foundation_length:
            raise ValueError(
                f"layout item at index {index} has y={y}, outside foundation length"
            )


def _column_radius(foundation_width: float, foundation_length: float) -> float:
    """
    Compute a reasonable drawing radius for columns.
    """

    base = min(foundation_width, foundation_length)
    radius = base * 0.015
    return max(0.08, min(radius, 0.25))
