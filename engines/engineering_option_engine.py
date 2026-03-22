# ============================================
# TRIPLE BOT V8
# ENGINE 1 — ENGINEERING OPTION GENERATOR
# Deterministic Engineering Option Exploration
# ============================================

import math

MIN_FOUNDATION_SIZE = 1.0
MAX_FOUNDATION_SIZE = 10.0
FOUNDATION_STEP = 0.5

MIN_SOIL_UTILIZATION = 0.10

# BUG FIX: original list [200,300,400,500,800,1000] cannot handle
# loads above 1000 kN — no COLUMN_UPGRADE option is ever generated,
# causing the engine to incorrectly recommend FOUNDATION_INCREASE
# even when governing mode is COLUMN.
# Extended list + dynamic fallback covers any load.
COLUMN_OPTIONS = [
    200,
    300,
    400,
    500,
    800,
    1000,
    1200,
    1500,
    2000,
    2500,
    3000,
    5000
]

LOAD_REDUCTION_OPTIONS = [
    0.00,
    0.05,
    0.10,
    0.20
]


def generate_engineering_options(engineering_results, input_data):

    options = []

    foundation_width = input_data["foundation_width"]
    foundation_length = input_data["foundation_length"]

    load_per_storey = input_data["load_per_storey"]
    storeys = input_data["storeys"]

    soil_capacity = input_data["soil_capacity"]
    column_capacity = input_data["column_capacity"]

    total_load = load_per_storey * storeys

    column_utilization = engineering_results["column_utilization"]
    soil_utilization = engineering_results["soil_utilization"]

    foundation_area = foundation_width * foundation_length

    # ============================================
    # COLUMN FAILURE OPTION
    # ============================================

    if column_utilization > 1.0:

        column_found = False

        for capacity in COLUMN_OPTIONS:

            new_util = total_load / capacity

            if new_util <= 1.0:

                options.append({
                    "option_type": "COLUMN_UPGRADE",
                    "column_capacity": capacity,
                    "column_utilization": round(new_util, 3),
                    "status": "REQUIRED"
                })
                column_found = True

        # BUG FIX: if total_load exceeds all preset options,
        # calculate the minimum required capacity dynamically
        if not column_found:
            min_required = math.ceil(total_load / 100) * 100
            options.append({
                "option_type": "COLUMN_UPGRADE",
                "column_capacity": min_required,
                "column_utilization": round(total_load / min_required, 3),
                "status": "REQUIRED"
            })

    # ============================================
    # SOIL FAILURE OPTION
    # ============================================

    if soil_utilization > 1.0:

        foundation_found = False
        size = MIN_FOUNDATION_SIZE

        while size <= MAX_FOUNDATION_SIZE:

            area = size * size

            soil_pressure = total_load / area

            new_util = soil_pressure / soil_capacity

            if new_util <= 1.0 and new_util >= MIN_SOIL_UTILIZATION:

                options.append({
                    "option_type": "FOUNDATION_INCREASE",
                    "foundation_size": round(size, 2),
                    "soil_utilization": round(new_util, 3),
                    "status": "REQUIRED"
                })
                foundation_found = True

            size += FOUNDATION_STEP

        # BUG FIX: if required foundation exceeds MAX_FOUNDATION_SIZE,
        # calculate minimum required size dynamically
        # e.g. load=100000, soil=100 → required area=1000 → side=31.63 m
        if not foundation_found and soil_capacity > 0:
            required_area = total_load / soil_capacity
            required_side = math.ceil(math.sqrt(required_area) * 100) / 100
            new_util = (total_load / (required_side * required_side)) / soil_capacity
            options.append({
                "option_type": "FOUNDATION_INCREASE",
                "foundation_size": round(required_side, 2),
                "soil_utilization": round(new_util, 3),
                "status": "REQUIRED"
            })

    # ============================================
    # LOAD REDUCTION OPTIONS (ONLY IF SAFE)
    # ============================================

    if column_utilization < 0.8 and soil_utilization < 0.8:

        for reduction in LOAD_REDUCTION_OPTIONS:

            if reduction == 0:
                continue

            reduced_load = total_load * (1 - reduction)

            new_column_util = reduced_load / column_capacity

            soil_pressure = reduced_load / foundation_area
            new_soil_util = soil_pressure / soil_capacity

            if new_column_util <= 1.0 and new_soil_util <= 1.0:

                options.append({
                    "option_type": "LOAD_REDUCTION",
                    "load_reduction": reduction,
                    "column_utilization": round(new_column_util, 3),
                    "soil_utilization": round(new_soil_util, 3),
                    "status": "ACCEPTABLE"
                })

    return options
