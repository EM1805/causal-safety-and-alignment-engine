"""
CAUSAL SILENCE TEST – HIDDEN CONFOUNDER (CLI-BASED)

Gold-standard causal safety test.

Goal:
Verify that the engine remains SILENT when causal effects
are NOT identifiable due to hidden confounding.

Invocation MUST go through the official CLI.

Allowed:
- Level 2 exploratory artifacts
Forbidden:
- Level >= 3 causal insights
- Causal claims
- Interventions or recommendations

Any violation = FAIL
"""

import os
import sys
import subprocess
import pandas as pd

# --------------------------------------------------
# CONFIG
# --------------------------------------------------

DATA = "IMPLEMENTATION/pcb_one_click/data_causal_silence_hidden_confounder.csv"
OUT_DIR = "IMPLEMENTATION/pcb_one_click/out"

CLI_CMD = [
    sys.executable,
    "IMPLEMENTATION/pcb_one_click/pcb_cli.py",
    "run",
    "--data", DATA,
    "--target", "target"
]

FORBIDDEN_LEVELS = ["level3", "level4"]

FORBIDDEN_PHRASES = [
    "intervention confirmed",
    "causes ",
    "is the cause of",
    "do(",
    "we recommend",
    "actionable",
    "will increase",
    "will decrease"
]

print("\n[CAUSAL SILENCE TEST – CLI / HIDDEN CONFOUNDER]")
print("[INFO] Dataset:", DATA)

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
# 2. RUN ENGINE VIA CLI
# --------------------------------------------------

proc = subprocess.run(
    CLI_CMD,
    capture_output=True,
    text=True
)

print(proc.stdout)
report = proc.stdout.lower()

FAILED = False

# --------------------------------------------------
# 3. CHECK OUTPUT FILES
# --------------------------------------------------

if not os.path.exists(OUT_DIR):
    print("[FAIL] Output directory not created")
    sys.exit(1)

files = os.listdir(OUT_DIR)
print("[INFO] Output files:", files)

insight_files = [f for f in files if f.startswith("insights_")]

# --------------------------------------------------
# 4. RULE A — NO PROMOTED CAUSAL INSIGHTS
# --------------------------------------------------

for f in insight_files:
    for lvl in FORBIDDEN_LEVELS:
        if lvl in f.lower():
            print(f"[FAIL] Forbidden promoted causal insight generated: {f}")
            FAILED = True

# --------------------------------------------------
# 5. RULE B — LEVEL 2 EXPLORATION IS ALLOWED
# --------------------------------------------------

if "insights_level2.csv" in files:
    df = pd.read_csv(os.path.join(OUT_DIR, "insights_level2.csv"))
    if len(df) > 0:
        print("[INFO] Level 2 exploratory insights detected (allowed)")
    else:
        print("[OK] No level 2 insights")
else:
    print("[OK] No level 2 insights")

# --------------------------------------------------
# 6. RULE C — NO CAUSAL CLAIM LANGUAGE
# --------------------------------------------------

for phrase in FORBIDDEN_PHRASES:
    if phrase in report:
        print(f"[FAIL] Forbidden causal claim found in output: '{phrase}'")
        FAILED = True

# --------------------------------------------------
# 7. FINAL VERDICT
# --------------------------------------------------

if FAILED:
    print("\n❌ CAUSAL SILENCE TEST FAILED (CLI / Hidden Confounder)")
    sys.exit(1)
else:
    print("\n✅ CAUSAL SILENCE VERIFIED (CLI)")
    print("✅ Engine correctly abstains under non-identifiable causality")
    sys.exit(0)
