# -*- coding: utf-8 -*-

"""
TRIPLE BOT - FOUNDATION LAYOUT ENGINE
Version: V10 DEV

Purpose:
Generate foundation layout data based on foundation dimensions
and number of structural columns.

This engine does not generate diagrams.
It only produces deterministic layout coordinates.
"""


def generate_foundation_layout(
    foundation_width,
    foundation_length,
    column_count_x,
    column_count_y
):
    """
    Generate foundation column layout coordinates.

    Parameters
    ----------
    foundation_width : float
    foundation_length : float
    column_count_x : int
    column_count_y : int

    Returns
    -------
    layout : list
        List of column coordinates
    """

    if column_count_x < 2 or column_count_y < 2:
        raise ValueError("Column grid must be at least 2x2")

    spacing_x = foundation_width / (column_count_x - 1)
    spacing_y = foundation_length / (column_count_y - 1)

    layout = []

    for i in range(column_count_x):
        for j in range(column_count_y):
            x = round(i * spacing_x, 3)
            y = round(j * spacing_y, 3)

            layout.append({
                "column_id": f"C{i+1}{j+1}",
                "x": x,
                "y": y
            })

    return layout