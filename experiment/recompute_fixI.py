"""Recompute pilots 2 and 3 with the I probe scored as intended (25-sep-2026).

The I probe asks "can the question be answered with a definite yes or no?", so sup(I) = P("no").
analyze_pilot2.py and analyze_pilot3.py used P("yes"); the Jev scripts (analyze_pilot4/5.py) already
use 1 - p. Raw data are untouched; this script only changes the scoring of I.
"""
import json, os, itertools
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
MIDDLE = ["I", "N", "U1", "U2", "U3", "U4", "U5"]
U_LABEL_MAP = {"aleatory": "U1", "epistemic": "U2", "ambiguity": "U3", "vagueness": "U4", "measurement": "U5"}


def parse_yesno(text):
    if text is None:
        return None
    t = text.strip().lower()
    if t.startswith("yes"):
        return 1
    if t.startswith("no"):
        return 0
    if "yes" in t and "no" not in t:
        return 1
    if "no" in t and "yes" not in t:
        return 0
    return None


def parse_choice(text):
    if text is None:
        return None
    t = text.strip().lower()
    for label in list(U_LABEL_MAP) + ["none"]:
        if t.startswith(label):
            return label
    return None


def mean(vals):
    vs = [v for v in vals if v is not None]
    return sum(vs) / len(vs) if vs else 0.0


def order_of(d):
    s0 = d["T"] + d["F"]
    if s0 > 1:
        return 0
    for k in range(1, len(MIDDLE) + 1):
        if any(s0 + sum(d[x] for x in S) > 1 for S in itertools.combinations(MIDDLE, k)):
            return k
    return "TOP"


def fix_I(d):
    d["I"] = 1 - d["I"]
    return d


out = {}
# Pilot 2: independent yes/no probes for every letter, 2 models x 2 wordings
raw = json.load(open(os.path.join(HERE, "pilot2_raw_results.json"), encoding="utf-8"))
vals = defaultdict(list)
for r in raw:
    vals[(r["item_id"], r["model"], r["version"], r["letter"])].append(parse_yesno(r["raw"]))
sup = defaultdict(dict)
for (item, model, ver, L), v in vals.items():
    sup[(item, model, ver)][L] = mean(v)
p2 = defaultdict(dict)
for (item, model, ver), d in sup.items():
    d = fix_I(dict(d))
    p2[item][model.split("/")[1] + "|" + ver] = {"ord": order_of(d), "sup": {k: round(v, 2) for k, v in d.items()}}
out["pilot2"] = p2

# Pilot 3: independent T/F/I/N, forced choice for U1-U5, 2 models, one wording
raw = json.load(open(os.path.join(HERE, "pilot3_raw_results.json"), encoding="utf-8"))
tfin, ch = defaultdict(list), defaultdict(list)
for r in raw:
    if r["kind"] == "tfin":
        tfin[(r["item_id"], r["model"], r["letter"])].append(parse_yesno(r["raw"]))
    else:
        ch[(r["item_id"], r["model"])].append(parse_choice(r["raw"]))
p3 = defaultdict(dict)
for item, model in sorted(set((k[0], k[1]) for k in tfin)):
    d = {L: mean(tfin[(item, model, L)]) for L in "TFIN"}
    labels = [x for x in ch[(item, model)] if x is not None]
    for lab, L in U_LABEL_MAP.items():
        d[L] = labels.count(lab) / len(labels) if labels else 0.0
    d = fix_I(d)
    p3[item][model.split("/")[1]] = {"ord": order_of(d), "sup": {k: round(v, 2) for k, v in d.items()}}
out["pilot3"] = p3

for name, res in out.items():
    print("===", name, "(I = P(no)) ===")
    stable = 0
    for item, conds in sorted(res.items()):
        ords = {c: v["ord"] for c, v in conds.items()}
        same = len(set(ords.values())) == 1
        stable += same
        print(f"  {item:24s} {ords} {'SAME' if same else ''}")
    print(f"  same order in all conditions: {stable}/{len(res)}")
json.dump(out, open(os.path.join(HERE, "recompute_fixI_results.json"), "w", encoding="utf-8"), indent=1)

# Sensitivity: the I probe tracks the answer to the embedded question for these two models
# (P("yes") on I correlates with sup(T)), so orders are also reported with I left out.
import statistics
print("\n=== sensitivity: I excluded ===")
for name, res in out.items():
    xs = [1 - v["sup"]["I"] for c in res.values() for v in c.values()]
    ts = [v["sup"]["T"] for c in res.values() for v in c.values()]
    stable = 0
    for item, conds in sorted(res.items()):
        ords = {c: order_of({**v["sup"], "I": 0.0}) for c, v in conds.items()}
        same = len(set(ords.values())) == 1
        stable += same
        print(f"  {name} {item:24s} {ords} {'SAME' if same else ''}")
    print(f"  {name}: corr(P(yes on I), sup T) = {statistics.correlation(xs, ts):.2f}; same order without I: {stable}/{len(res)}")
