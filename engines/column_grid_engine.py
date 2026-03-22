# -*- coding: utf-8 -*-

"""
TRIPLE BOT - COLUMN GRID ENGINE
Version: V10 DEV

Purpose:
Automatically determine structural column grid
based on building dimensions and target spacing.
"""


def generate_column_grid(
    building_width,
    building_length,
    target_spacing=6.0
):
    """
    Generate column grid parameters.

    Parameters
    ----------
    building_width : float
    building_length : float
    target_spacing : float

    Returns
    -------
    dict
        Grid configuration
    """

    if building_width <= 0 or building_length <= 0:
        raise ValueError("Building dimensions must be positive")

    if target_spacing <= 0:
        raise ValueError("Target spacing must be positive")

    # determine number of grid divisions
    count_x = max(2, round(building_width / target_spacing) + 1)
    count_y = max(2, round(building_length / target_spacing) + 1)

    # compute actual spacing
    spacing_x = building_width / (count_x - 1)
    spacing_y = building_length / (count_y - 1)

    return {
        "column_count_x": count_x,
        "column_count_y": count_y,
        "spacing_x": round(spacing_x, 3),
        "spacing_y": round(spacing_y, 3)
    }