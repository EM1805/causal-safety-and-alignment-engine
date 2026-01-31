"""
CAUSAL SAFETY CERTIFICATION TEST – INDUSTRIAL GRADE
"""

import pandas as pd
import numpy as np
import subprocess
import sys
import os

np.random.seed(123)

DATA = "IMPLEMENTATION/pcb_one_click/data_causal_certification.csv"

# --------------------------------------------------
# 1. GENERATE SAFETY DATASET
# --------------------------------------------------

def generate_dataset(n=4000):

    H = np.random.normal(0, 1, n)

    # True causal chain
    X = 2 * H + np.random.normal(0, 0.5, n)
    Y = 4 * X + 3 * H + np.random.normal(0, 0.5, n)

    # Bias traps
    simpson = -1 * X + 2 * np.random.binomial(1, 0.5, n) + np.random.normal(0, 0.2, n)
    collider = X + Y + np.random.normal(0, 0.1, n)
    spurious = X + np.random.normal(0, 1.0, n)
    future = np.roll(Y, -1)
    future[-1] = np.nan
    trend = np.linspace(0, 5, n) + np.random.normal(0, 0.1, n)

    # Intervention (engine should be cautious)
    intervention = np.random.binomial(1, 0.1, n)
    X_do = X + intervention * 5
    Y_do = 4 * X_do + np.random.normal(0, 0.5, n)

    df = pd.DataFrame({
        "X": X_do,                 # potential causal, unstable
        "simpson": simpson,        # forbidden
        "collider": collider,      # forbidden
        "spurious": spurious,      # forbidden
        "future_leak": future,     # forbidden
        "trend": trend,            # forbidden
        "target": Y_do
    })

    return df.dropna().reset_index(drop=True)


os.makedirs("IMPLEMENTATION/pcb_one_click", exist_ok=True)
df = generate_dataset()
df.to_csv(DATA, index=False)

print("[TEST] Dataset generated")

# --------------------------------------------------
# 2. RUN ENGINE
# --------------------------------------------------

cmd = [
    sys.executable,
    "IMPLEMENTATION/pcb_one_click/demo.py",
    DATA,
    "target"
]

print("\n[TEST] Running CAUSAL SAFETY CERTIFICATION...\n")

proc = subprocess.run(cmd, capture_output=True, text=True)

with open("stress_result.txt", "w") as f:
    f.write(proc.stdout)

print(proc.stdout)

report = proc.stdout.lower()

# --------------------------------------------------
# 3. LOCATE OUTPUT
# --------------------------------------------------

OUT_DIR = None
for root, dirs, files in os.walk("."):
    if root.endswith("/out") or root.endswith("\\out"):
        OUT_DIR = root
        break

if OUT_DIR is None:
    print("[FAIL] Output folder not found")
    sys.exit(1)

print("[OK] Output folder:", OUT_DIR)

FAILED = False

# --------------------------------------------------
# 4. INSIGHTS MUST EXIST
# --------------------------------------------------

insight_files = [f for f in os.listdir(OUT_DIR) if f.startswith("insights_")]

if not insight_files:
    print("[FAIL] No insights produced")
    FAILED = True
else:
    print("[OK] Insights produced:", insight_files[0])
    insights = pd.read_csv(os.path.join(OUT_DIR, insight_files[0]))

    used_vars = set()
    if "source" in insights.columns:
        used_vars = set(insights["source"].astype(str).str.lower())

    print("[INFO] Variables used in insights:")
    for v in used_vars:
        print(" -", v)

# --------------------------------------------------
# 5. SAFETY GUARANTEES
# --------------------------------------------------

FORBIDDEN = ["simpson", "collider", "spurious", "future_leak", "trend"]

for bad in FORBIDDEN:
    if bad in report or bad in used_vars:
        print(f"[FAIL] Forbidden variable accepted: {bad}")
        FAILED = True
    else:
        print(f"[OK] {bad} correctly rejected")

# --------------------------------------------------
# 6. FINAL VERDICT
# --------------------------------------------------

if FAILED:
    print("\n❌ CAUSAL SAFETY CERTIFICATION FAILED")
    sys.exit(1)
else:
    print("\n🏆 CAUSAL SAFETY ENGINE CERTIFIED (INDUSTRIAL GRADE)")
    sys.exit(0)
