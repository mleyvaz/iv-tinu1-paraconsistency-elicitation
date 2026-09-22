import json, os, itertools, re
from collections import defaultdict

HERE = os.path.dirname(__file__)
with open(os.path.join(HERE, "pilot_raw_results.json"), encoding="utf-8") as f:
    raw = json.load(f)

LETTERS = ["T", "F", "I", "N", "U1", "U2", "U3", "U4", "U5"]
MIDDLE = ["I", "N", "U1", "U2", "U3", "U4", "U5"]  # M, |M|=7

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

def parse_number(text):
    if text is None:
        return None
    m = re.search(r"\d+(\.\d+)?", text)
    if not m:
        return None
    v = float(m.group(0))
    return max(0.0, min(100.0, v)) / 100.0

# index raw results
by_key = defaultdict(list)  # (arm, item, model, letter) -> list of parsed values
for r in raw:
    arm, item, model, letter = r["arm"], r["item_id"], r["model"], r["letter"]
    if arm == "arm1":
        val = parse_yesno(r["raw"])
    else:  # arm2
        if letter in ("T", "F", "I", "N"):
            val = parse_number(r["raw"])
        else:
            val = parse_yesno(r["raw"])
    by_key[(arm, item, model, letter)].append(val)

def mean_ignore_none(vals):
    vs = [v for v in vals if v is not None]
    if not vs:
        return None
    return sum(vs) / len(vs)

# build sup tables: sup[(arm,item,model)][letter] = proportion/mean
sup = defaultdict(dict)
n_missing = 0
for (arm, item, model, letter), vals in by_key.items():
    m = mean_ignore_none(vals)
    sup[(arm, item, model)][letter] = m
    n_missing += sum(1 for v in vals if v is None)

print(f"Unparseable responses: {n_missing} / {len(raw)}")

def g(d, k):
    v = d.get(k)
    return v if v is not None else 0.0

def sigma(sup_dict, S):
    s0 = g(sup_dict, "T") + g(sup_dict, "F")
    return s0 + sum(g(sup_dict, x) for x in S)

def order_of(sup_dict):
    s0 = g(sup_dict, "T") + g(sup_dict, "F")
    if s0 > 1:
        return 0, []
    for d in range(1, len(MIDDLE) + 1):
        witnesses = []
        for S in itertools.combinations(MIDDLE, d):
            if sigma(sup_dict, S) > 1:
                # check minimality: no proper subset already >1 (guaranteed since we scan d ascending)
                witnesses.append(S)
        if witnesses:
            return d, witnesses
    return "TOP_CONSISTENT", []

ITEMS = sorted(set(k[1] for k in sup.keys()))
MODELS = sorted(set(k[2] for k in sup.keys()))

print("\n=== ARM 1 (primary, indirect probes): sup() values and declared order per item x model ===\n")
report_lines = []
for item in ITEMS:
    report_lines.append(f"\n--- {item} ---")
    for model in MODELS:
        d = sup.get(("arm1", item, model), {})
        vals_str = ", ".join(f"{L}={d.get(L):.2f}" if d.get(L) is not None else f"{L}=NA" for L in LETTERS)
        ordv, witnesses = order_of(d)
        report_lines.append(f"  [{model}] {vals_str}")
        report_lines.append(f"    -> sigma_empty(T+F)={g(d,'T')+g(d,'F'):.2f}  ord={ordv}  witnesses={witnesses}")

print("\n".join(report_lines))

print("\n=== H1: auditor stability (do the 2 models agree on ord(item)?) ===\n")
h1_rows = []
for item in ITEMS:
    orders = {}
    for model in MODELS:
        d = sup.get(("arm1", item, model), {})
        ordv, _ = order_of(d)
        orders[model] = ordv
    agree = len(set(orders.values())) == 1
    h1_rows.append((item, orders, agree))
    print(f"  {item}: {orders}  {'AGREE' if agree else 'DISAGREE'}")

n_agree = sum(1 for _, _, a in h1_rows if a)
print(f"\n  Agreement across {len(MODELS)} auditor models: {n_agree}/{len(ITEMS)} items")

print("\n=== H3: Arm1 vs Arm2 divergence (T,F,I,N; averaged across both models) ===\n")
for item in ITEMS:
    for L in ["T", "F", "I", "N"]:
        a1_vals = [sup.get(("arm1", item, m), {}).get(L) for m in MODELS]
        a2_vals = [sup.get(("arm2", item, m), {}).get(L) for m in MODELS]
        a1 = mean_ignore_none(a1_vals)
        a2 = mean_ignore_none(a2_vals)
        if a1 is not None and a2 is not None:
            print(f"  {item:25s} {L}: Arm1={a1:.2f}  Arm2={a2:.2f}  diff={a1-a2:+.2f}")

out_summary = os.path.join(HERE, "pilot_summary.txt")
with open(out_summary, "w", encoding="utf-8") as f:
    f.write("\n".join(report_lines))
print(f"\nSaved detailed summary to {out_summary}")
