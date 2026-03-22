# ============================================
# TRIPLE BOT V6
# ENGINEERING CONSTANTS
# Deterministic Engineering Baseline
# ============================================


# ------------------------------------------------
# LOAD FACTORS
# ------------------------------------------------

# Structural load amplification factor
LOAD_FACTOR = 1.2


# ------------------------------------------------
# STRUCTURAL LIMITS
# ------------------------------------------------

# Utilization threshold for structural feasibility
UTILIZATION_LIMIT = 1.0

# Threshold where structure is considered near limit
NEAR_LIMIT_THRESHOLD = 0.9


# ------------------------------------------------
# ENGINEERING SAFETY TARGETS
# ------------------------------------------------

# Target safety factor for column capacity
COLUMN_SAFETY_TARGET = 1.5

# Target safety factor for soil bearing
SOIL_SAFETY_TARGET = 3.0


# ------------------------------------------------
# RISK INTERPRETATION BANDS
# ------------------------------------------------

# These values classify utilization levels
# into qualitative engineering risk categories

RISK_LOW_THRESHOLD = 0.3
RISK_MODERATE_THRESHOLD = 0.6
RISK_HIGH_THRESHOLD = 0.9


# ------------------------------------------------
# RISK LABELS
# ------------------------------------------------

RISK_LOW = "LOW"
RISK_MODERATE = "MODERATE"
RISK_HIGH = "HIGH"
RISK_CRITICAL = "CRITICAL"


# ------------------------------------------------
# STRUCTURAL STATUS LABELS
# ------------------------------------------------

STATUS_SAFE = "SAFE"
STATUS_FAIL = "FAIL"


# ------------------------------------------------
# GOVERNING MODES
# ------------------------------------------------

GOVERNING_COLUMN = "COLUMN"
GOVERNING_SOIL = "SOIL"


# ------------------------------------------------
# ENGINEERING DECISION LABELS
# ------------------------------------------------

DECISION_SAFE = "STRUCTURE SAFE"
DECISION_NEAR_LIMIT = "STRUCTURE NEAR LIMIT"
DECISION_UNSAFE = "STRUCTURE UNSAFE"