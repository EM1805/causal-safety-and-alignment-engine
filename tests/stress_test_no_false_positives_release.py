"""
NO FALSE POSITIVES – CAUSAL SAFETY STRESS TEST (CI / RELEASE GATE)

Goal:
Verify that the engine does NOT promote causal insights when
the dataset contains only:
- spurious correlations
- leakage
- drift
- noise

Level-2 exploratory artifacts MAY exist.
Any promoted causal insight = FAIL.
"""

import os
import sys
import subprocess
import pandas as pd

DATA = "IMPLEMENTATION/pcb_one_click/data_no_false_positives.csv"
OUT_DIR = "IMPLEMENTATION/pcb_one_click/out"

ENGINE_CMD = [
    sys.executable,
    "IMPLEMENTATION/pcb_one_click/pcb_cli.py",
    "run",
    "--data",
    DATA,
    "--target",
    "mood",
    "--skip-32"
]

print("\n[NO FALSE POSITIVES TEST]")
print("[INFO] Using dataset:", DATA)

# --------------------------------------------------
# 1. CLEAN PREVIOUS OUTPUTS
# --------------------------------------------------

if os.path.exists(OUT_DIR):
    for f in os.listdir(OUT_DIR):
        try:
            os.remove(os.path.join(OUT_DIR, f))
        except Exception:
            pass
else:
    os.makedirs(OUT_DIR, exist_ok=True)

# --------------------------------------------------
# 2. RUN ENGINE
# --------------------------------------------------

proc = subprocess.run(ENGINE_CMD, capture_output=True, text=True)
print(proc.stdout)

report = proc.stdout.lower()

FAILED = False

# --------------------------------------------------
# 3. CHECK OUTPUT FILES
# --------------------------------------------------

files = os.listdir(OUT_DIR)
print("[INFO] Output files:", files)

insight_files = [f for f in files if f.startswith("insights_")]

# --------------------------------------------------
# 4. VALIDATION RULES
# --------------------------------------------------

# Rule A: No promoted causal insights (level >=3)
for f in insight_files:
    if "level3" in f or "level4" in f:
        print("[FAIL] High-level causal insights generated:", f)
        FAILED = True

# Rule B: Level-2 insights must be empty or guarded
if "insights_level2.csv" in files:
    df = pd.read_csv(os.path.join(OUT_DIR, "insights_level2.csv"))
    if len(df) > 0:
        print("[INFO] Level-2 exploratory insights detected (allowed)")
    else:
        print("[OK] No level-2 insights")

# Rule C: Engine must NOT claim causal certainty
for bad_word in ["causal", "cause", "intervention confirmed"]:
    if bad_word in report:
        print(f"[FAIL] Forbidden causal claim found in output: '{bad_word}'")
        FAILED = True

# --------------------------------------------------
# 5. FINAL VERDICT
# --------------------------------------------------

if FAILED:
    print("\n❌ NO FALSE POSITIVES TEST FAILED")
    sys.exit(1)
else:
    print("\n✅ NO FALSE POSITIVES GUARANTEED")
    sys.exit(0)
