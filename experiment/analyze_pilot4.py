"""Pilot 4: Jev, single call per letter (superseded by pilot 5's k=5 repeats --
kept for the record and reproducibility, not as the reliable reading)."""
import json, os, itertools

HERE = os.path.dirname(__file__)
with open(os.path.join(HERE, "pilot4_jev_raw_results.json"), encoding="utf-8") as f:
    data = json.load(f)

MIDDLE = ["I", "N", "U1", "U2", "U3", "U4", "U5"]
LABEL_MAP = {"aleatory": "U1", "epistemic": "U2", "ambiguity": "U3", "vagueness": "U4", "measurement": "U5"}

def order_of(d):
    s0 = d["T"] + d["F"]
    if s0 > 1:
        return 0, []
    for dd in range(1, len(MIDDLE) + 1):
        witnesses = [S for S in itertools.combinations(MIDDLE, dd) if s0 + sum(d.get(x, 0) for x in S) > 1]
        if witnesses:
            return dd, witnesses
    return "TOP", []

for r in data:
    if "error" in r:
        print(r["id"], "ERROR", r["error"])
        continue
    d = {"T": r["T"], "F": r["F"], "I": 1 - r["I"], "N": r["N"]}
    for label, letter in LABEL_MAP.items():
        d[letter] = r["U_probabilities"].get(label, 0)
    ordv, witnesses = order_of(d)
    sup_str = ", ".join(f"{k}={v:.2f}" for k, v in d.items())
    print(f"{r['id']:25s} {sup_str}  sigma0={d['T']+d['F']:.2f}  ord={ordv}  witnesses(min)={witnesses[:3]}")
