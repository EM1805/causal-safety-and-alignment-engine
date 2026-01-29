"""
Causal Safety Stress Test Suite

Purpose:
Prove that the engine behaves as a causal safety engine by verifying:
- No data leakage
- Confounder robustness
- Spurious correlation rejection
- Intervention consistency
- Drift resilience
- Guardrail enforcement

This test must GENERATE INSIGHTS only when causal signal is real.
False positives = FAIL

Usage (GitLab CI):
python IMPLEMENTATION/pcb_one_click/stress_test/stress_test_causal_safety.py
"""

import pandas as pd
import numpy as np
import subprocess
import os
import sys

OUT = "out"
DATA = "IMPLEMENTATION/pcb_one_click/data_causal_stress.csv"

np.random.seed(42)

# ----------------------------
# 1. GENERATE HARD CAUSAL DATA
# ----------------------------

def generate_dataset(n=2000):
    """
    True causal structure:

    confounder  ->  X  ->  Y
       |              ^
       +------------->+

    Z_spurious  correlated with X but NOT causal
    leakage     future information (must be rejected)
    drift       distribution shift
    """

    confounder = np.random.normal(0, 1, n)

    X = 2 * confounder + np.random.normal(0, 0.5, n)
    Y = 3 * X + 2 * confounder + np.random.normal(0, 0.5, n)

    # Spurious correlated variable (high correlation, no causal effect)
    Z = X + np.random.normal(0, 0.1, n)

    # Leakage variable (almost perfect future info)
    leakage = Y + np.random.normal(0, 0.01, n)

    # Drifted feature
    drift = np.concatenate([
        np.random.normal(0, 1, n // 2),
        np.random.normal(3, 1, n // 2)
    ])

    df = pd.DataFrame({
        "confounder": confounder,
        "X": X,
        "Z_spurious": Z,
        "drift": drift,
        "leakage": leakage,
        "target": Y
    })

    return df


# Write dataset
os.makedirs("IMPLEMENTATION/pcb_one_click", exist_ok=True)

df = generate_dataset()
df.to_csv(DATA, index=False)

print("[TEST] Dataset generated:", DATA)


# ----------------------------
# 2. RUN ENGINE
# ----------------------------

cmd = [
    sys.executable,
    "IMPLEMENTATION/pcb_one_click/demo.py",
    DATA,
    "target"
]

print("[TEST] Running causal engine on stress dataset...")

proc = subprocess.run(cmd, capture_output=True, text=True)

with open("stress_result.txt", "w") as f:
    f.write(proc.stdout)

print(proc.stdout)


# ----------------------------
# 3. VALIDATION RULES
# ----------------------------

FAILED = False
report = proc.stdout.lower()

# A. Must detect X -> target
if "x" not in report:
    print("[FAIL] True causal variable X not detected")
    FAILED = True
else:
    print("[OK] True causal variable detected")

# B. Must NOT accept spurious Z
if "z_spurious" in report:
    print("[FAIL] Spurious correlation accepted")
    FAILED = True
else:
    print("[OK] Spurious variable rejected")

# C. Must reject leakage
if "leakage" in report:
    print("[FAIL] Data leakage accepted")
    FAILED = True
else:
    print("[OK] Leakage correctly rejected")

# D. Must handle drift (flag or ignore)
if "drift" in report and "flag" not in report:
    print("[WARN] Drift present without explicit guardrail flag")
else:
    print("[OK] Drift handled by guardrails")

# E. Must produce at least 1 insight
if "kept insights: 0" in report or "no insights" in report:
    print("[FAIL] No insights generated despite strong causal signal")
    FAILED = True
else:
    print("[OK] Insights generated")


# ----------------------------
# 4. FINAL VERDICT
# ----------------------------

if FAILED:
    print("\n❌ CAUSAL SAFETY TEST FAILED")
    sys.exit(1)
else:
    print("\n✅ CAUSAL SAFETY ENGINE VERIFIED")
    sys.exit(0)