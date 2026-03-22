# -*- coding: utf-8 -*-

"""
Triple Bot Load Combination Engine
Version: V4.2

Purpose
-------
Provide engineering load combinations while keeping the core
deterministic validation engine unchanged.

This module converts multiple load inputs into a single
total_load value that the existing core engines already use.

Design Principle
----------------
NON_INTRUSIVE_LAYER

User Input
    ->
Load Combination Engine
    ->
Total Load
    ->
Triple Bot Core Engine (UNCHANGED)

This guarantees backward compatibility with V4.1.
"""


def combine_loads(
    dead_load: float = 0.0,
    live_load: float = 0.0,
    wind_load: float = 0.0,
    mode: str = "simple"
):

    if mode == "simple":
        total_load = dead_load + live_load

    elif mode == "ultimate":
        total_load = 1.2 * dead_load + 1.6 * live_load

    elif mode == "wind":
        total_load = 1.2 * dead_load + 1.0 * live_load + 1.0 * wind_load

    else:
        raise ValueError(
            "Invalid load combination mode. Use: simple, ultimate, wind."
        )

    return total_load


def describe_mode(mode: str):

    descriptions = {
        "simple": "Total Load = Dead Load + Live Load",
        "ultimate": "Total Load = 1.2 Dead + 1.6 Live",
        "wind": "Total Load = 1.2 Dead + 1.0 Live + 1.0 Wind",
    }

    return descriptions.get(mode, "Unknown load combination")