# ============================================
# TRIPLE BOT V9.9.5
# API Layer — for FlutterFlow / Mobile App
# api.py
# NEW FILE — ไม่แตะไฟล์เดิมใดๆ
# ============================================

import sys
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ── PATH SETUP ──────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE_DIR, "engines"))
sys.path.insert(0, os.path.join(BASE_DIR, "modules"))

# ── ENGINE IMPORTS ───────────────────────────
from triplebot_master_engine import run_triplebot_analysis
from design_solver_engine import run_design_solver

# ── APP SETUP ────────────────────────────────
app = FastAPI(
    title="Triple Bot V9.9.5 API",
    description="Deterministic Structural Validation & Decision Engine",
    version="9.9.5"
)

# ── CORS (อนุญาตให้ FlutterFlow เรียกได้) ──
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── INPUT MODELS ─────────────────────────────

class ValidateInput(BaseModel):
    foundation_width: float       # ความกว้างฐานราก (เมตร)
    foundation_length: float      # ความยาวฐานราก (เมตร)
    load_per_storey: float        # น้ำหนักต่อชั้น (kN)
    storeys: int                  # จำนวนชั้น
    soil_capacity: float          # ความสามารถรับน้ำหนักดิน (kN/m²)
    column_capacity: float        # ความสามารถรับน้ำหนักเสา (kN)

class SolveInput(BaseModel):
    total_load: float             # น้ำหนักรวม (kN)
    column_capacity: float        # ความสามารถรับน้ำหนักเสา (kN)
    soil_capacity: float          # ความสามารถรับน้ำหนักดิน (kN/m²)
    foundation_area: float        # พื้นที่ฐานราก (m²)
    target_utilization: float = 0.8

# ── ENDPOINTS ────────────────────────────────

@app.get("/")
def root():
    return {
        "system": "Triple Bot V9.9.5",
        "status": "ready",
        "engine": "deterministic",
        "endpoints": ["/validate", "/solve", "/health"]
    }

@app.get("/health")
def health():
    return {"status": "ok", "version": "9.9.5"}

@app.post("/validate")
def validate(data: ValidateInput):
    result = run_triplebot_analysis(
        foundation_width=data.foundation_width,
        foundation_length=data.foundation_length,
        load_per_storey=data.load_per_storey,
        storeys=data.storeys,
        soil_capacity=data.soil_capacity,
        column_capacity=data.column_capacity
    )
    return {
        "status": "success",
        "input": data.dict(),
        "result": result
    }

@app.post("/solve")
def solve(data: SolveInput):
    result = run_design_solver(
        total_load=data.total_load,
        column_capacity=data.column_capacity,
        soil_capacity=data.soil_capacity,
        foundation_area=data.foundation_area,
        target_utilization=data.target_utilization
    )
    return {
        "status": "success",
        "input": data.dict(),
        "result": result
    }
