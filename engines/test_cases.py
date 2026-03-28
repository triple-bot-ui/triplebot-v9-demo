# ============================================
# TRIPLE BOT V9.9.4
# engines/test_cases.py
# Official Neo test library for Trust Layer
# CURRENT SCOPE:
# - CASE_01 / CASE_02 / CASE_03 only
# - OUT_OF_SCOPE still HOLD in this round
# IMPORTANT:
# - This file must NOT import from itself
# ============================================

TEST_CASES = [
    {
        "case_id": "CASE_01_BASELINE_SOIL_FAIL",
        "tag": "SOIL_DOMINANT",
        "inputs": {
            "building_width": 10.0,
            "building_length": 10.0,
            "num_floors": 2,
            "soil_capacity": 200.0,
            "foundation_width": 1.0,
            "foundation_length": 1.0,
            "column_capacity": 500.0,
            "engineering_load_per_storey": 750.0,
            "total_load": 1500.0,
        },
        "expected": {
            "status": "FAIL",
            "governing_mode": "SOIL",
            "soil_utilization": 7.5,
            "column_utilization": 3.0,
        },
    },
    {
        "case_id": "CASE_02_COLUMN_GOVERNING",
        "tag": "COLUMN_DOMINANT",
        "inputs": {
            "building_width": 10.0,
            "building_length": 10.0,
            "num_floors": 2,
            "soil_capacity": 200.0,
            "foundation_width": 3.0,
            "foundation_length": 3.0,
            "column_capacity": 500.0,
            "engineering_load_per_storey": 750.0,
            "total_load": 1500.0,
        },
        "expected": {
            "status": "FAIL",
            "governing_mode": "COLUMN",
            "soil_utilization": 0.833,
            "column_utilization": 3.0,
        },
    },
    {
        "case_id": "CASE_03_SAFE_NO_ACTION",
        "tag": "SAFE",
        "inputs": {
            "building_width": 10.0,
            "building_length": 10.0,
            "num_floors": 1,
            "soil_capacity": 200.0,
            "foundation_width": 2.5,
            "foundation_length": 2.5,
            "column_capacity": 1500.0,
            "engineering_load_per_storey": 750.0,
            "total_load": 750.0,
        },
        "expected": {
            "status": "PASS",
            "governing_mode": "SOIL",
            "soil_utilization": 0.6,
            "column_utilization": 0.5,
        },
    },
]