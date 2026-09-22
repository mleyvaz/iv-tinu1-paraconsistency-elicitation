"""Pilot 5: Jev with k=5 repeats per letter, all 10 items -- the reliable
reading of Jev (supersedes pilot 4's single-call pass)."""
import json, os, itertools

HERE = os.path.dirname(__file__)
with open(os.path.join(HERE, "pilot5_jev_repeated_results.json"), encoding="utf-8") as f:
    data = json.load(f)

MIDDLE = ["I", "N", "U1", "U2", "U3", "U4", "U5"]
LABEL_MAP = {"aleatory": "U1", "epistemic": "U2", "ambiguity": "U3", "vagueness": "U4", "measurement": "U5"}

def mean(xs):
    return sum(xs) / len(xs)

def order_of(d):
    s0 = d["T"] + d["F"]
    if s0 > 1:
        return 0, []
    for dd in range(1, len(MIDDLE) + 1):
        witnesses = [S for S in itertools.combinations(MIDDLE, dd) if s0 + sum(d.get(x, 0) for x in S) > 1]
        if witnesses:
            return dd, witnesses
    return "TOP", []

print(f"{'item':25s} {'T':>6} {'F':>6} {'I':>6} {'N':>6}  sigma0  ord  witnesses")
for r in data:
    d = {"T": mean(r["T"]), "F": mean(r["F"]), "I": 1 - mean(r["I"]), "N": mean(r["N"])}
    n = len(r["U"])
    for lab, letter in LABEL_MAP.items():
        d[letter] = r["U"].count(lab) / n
    ordv, witnesses = order_of(d)
    print(f"{r['id']:25s} {d['T']:.3f} {d['F']:.3f} {d['I']:.3f} {d['N']:.3f}  {d['T']+d['F']:.3f}  {str(ordv):>3}  {witnesses[:3]}")
    crossings = sum(1 for t, f in zip(r["T"], r["F"]) if t + f > 1)
    print(f"    -> T+F>1 in {crossings}/{len(r['T'])} individual runs")
