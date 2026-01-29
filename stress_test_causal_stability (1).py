
import os
import sys
import subprocess
import pandas as pd
from collections import Counter

RUNS = 5

ENGINE_CMD = [
    sys.executable,
    "IMPLEMENTATION/pcb_one_click/demo.py",
    "IMPLEMENTATION/pcb_one_click/data.csv",
    "target"
]

OUT_DIR = "IMPLEMENTATION/pcb_one_click/out"
INSIGHTS_FILE = "insights_level2.csv"

print("\n[STABILITY TEST] Multi-Insight Causal Stability Certification\n")

crashes = 0
all_features = []

def read_top_features(path, k=4):
    df = pd.read_csv(path)
    if "source" in df.columns:
        feats = df["source"].astype(str).str.lower().tolist()
    elif "feature" in df.columns:
        feats = df["feature"].astype(str).str.lower().tolist()
    else:
        feats = df.iloc[:, 0].astype(str).str.lower().tolist()
    return feats[:k]

for i in range(RUNS):
    print(f"--- RUN {i+1}/{RUNS} ---")

    # clean previous outputs
    if os.path.exists(OUT_DIR):
        for f in os.listdir(OUT_DIR):
            try:
                os.remove(os.path.join(OUT_DIR, f))
            except:
                pass
    else:
        os.makedirs(OUT_DIR, exist_ok=True)

    proc = subprocess.run(ENGINE_CMD, capture_output=True, text=True)

    insights_path = os.path.join(OUT_DIR, INSIGHTS_FILE)

    if not os.path.exists(insights_path):
        print("[FAIL] No insights produced")
        crashes += 1
        continue

    try:
        feats = read_top_features(insights_path, k=4)
        print("[OK] Insights:", feats)
        all_features.extend(feats)
    except Exception as e:
        print("[FAIL] Insights unreadable:", e)
        crashes += 1

# ---------------- REPORT ----------------

print("\n=========== STABILITY REPORT ===========")
print("Runs executed:", RUNS)
print("Engine crashes:", crashes)

counter = Counter(all_features)
print("Feature recurrence:")
for k, v in counter.items():
    print(f" - {k}: {v}/{RUNS}")

stable = [k for k, v in counter.items() if v / RUNS >= 0.6]

print("Stable causal features (>=60%):", stable)

FAILED = False

if crashes > 0:
    print("❌ Engine is NOT stable (crashes detected)")
    FAILED = True

if len(stable) < 2:
    print("❌ Not enough stable causal features (need >=2)")
    FAILED = True

if FAILED:
    print("\n❌ MULTI-INSIGHT STABILITY CERTIFICATION FAILED")
    sys.exit(1)
else:
    print("\n🏆 MULTI-INSIGHT STABILITY CERTIFICATION PASSED")
    sys.exit(0)
