# -*- coding: utf-8 -*-

"""
TRIPLE BOT - FOOTING SIZE ENGINE
Version: V10 DEV

Purpose:
Determine a preliminary square footing size based on
column load and allowable soil bearing capacity.

This engine returns deterministic footing dimensions
for pre-construction engineering drafting.
"""


def generate_footing_size(column_load, soil_capacity):
    """
    Generate preliminary square footing size.

    Parameters
    ----------
    column_load : float
        Load carried by one column in kN.
    soil_capacity : float
        Allowable soil bearing capacity in kN/m^2.

    Returns
    -------
    dict
        Footing size data
    """

    if column_load <= 0:
        raise ValueError("column_load must be positive")

    if soil_capacity <= 0:
        raise ValueError("soil_capacity must be positive")

    required_area = column_load / soil_capacity
    footing_size = required_area ** 0.5

    return {
        "column_load": round(column_load, 3),
        "soil_capacity": round(soil_capacity, 3),
        "required_area": round(required_area, 3),
        "footing_width": round(footing_size, 3),
        "footing_length": round(footing_size, 3)
    }
