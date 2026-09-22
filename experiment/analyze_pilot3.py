import json, os, itertools
from collections import defaultdict

HERE = os.path.dirname(__file__)
with open(os.path.join(HERE, "pilot3_raw_results.json"), encoding="utf-8") as f:
    raw = json.load(f)

MIDDLE = ["I", "N", "U1", "U2", "U3", "U4", "U5"]
U_LABEL_MAP = {"ALEATORY": "U1", "EPISTEMIC": "U2", "AMBIGUITY": "U3", "VAGUENESS": "U4", "MEASUREMENT": "U5"}

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
    t = text.strip().upper()
    for label in ["ALEATORY", "EPISTEMIC", "AMBIGUITY", "VAGUENESS", "MEASUREMENT", "NONE"]:
        if t.startswith(label):
            return label
    return None

tfin_vals = defaultdict(list)   # (item, model, letter) -> [0/1,...]
choice_vals = defaultdict(list) # (item, model) -> [label,...]

n_unparsed_tfin = 0
n_unparsed_choice = 0
for r in raw:
    if r["kind"] == "tfin":
        v = parse_yesno(r["raw"])
        tfin_vals[(r["item_id"], r["model"], r["letter"])].append(v)
        if v is None:
            n_unparsed_tfin += 1
    else:
        v = parse_choice(r["raw"])
        choice_vals[(r["item_id"], r["model"])].append(v)
        if v is None:
            n_unparsed_choice += 1

print(f"Unparsed T/F/I/N: {n_unparsed_tfin}; unparsed forced-choice: {n_unparsed_choice}")

def mean_ignore_none(vals):
    vs = [v for v in vals if v is not None]
    return sum(vs) / len(vs) if vs else None

ITEMS = sorted(set(k[0] for k in tfin_vals))
MODELS = sorted(set(k[1] for k in tfin_vals))

sup = {}
for item in ITEMS:
    for model in MODELS:
        d = {}
        for L in ["T", "F", "I", "N"]:
            d[L] = mean_ignore_none(tfin_vals.get((item, model, L), []))
        labels = [lab for lab in choice_vals.get((item, model), []) if lab is not None]
        n = len(labels)
        for lab, letter in U_LABEL_MAP.items():
            d[letter] = (labels.count(lab) / n) if n else None
        sup[(item, model)] = d

def g(d, k):
    v = d.get(k)
    return v if v is not None else 0.0

def sigma(d, S):
    return g(d, "T") + g(d, "F") + sum(g(d, x) for x in S)

def order_of(d):
    s0 = g(d, "T") + g(d, "F")
    if s0 > 1:
        return 0, []
    for dd in range(1, len(MIDDLE) + 1):
        witnesses = [S for S in itertools.combinations(MIDDLE, dd) if sigma(d, S) > 1]
        if witnesses:
            return dd, witnesses
    return "TOP", []

print("\n=== Pilot 3 (forced-choice U): sup() and ord(item) per item x model ===\n")
lines = []
for item in ITEMS:
    lines.append(f"--- {item} ---")
    for model in MODELS:
        d = sup[(item, model)]
        vals_str = ", ".join(f"{L}={d.get(L):.2f}" if d.get(L) is not None else f"{L}=NA"
                              for L in ["T", "F", "I", "N", "U1", "U2", "U3", "U4", "U5"])
        ordv, witnesses = order_of(d)
        lines.append(f"  [{model}] {vals_str}")
        lines.append(f"    -> sigma_empty={g(d,'T')+g(d,'F'):.2f}  ord={ordv}  witnesses={witnesses}")
    lines.append("")
print("\n".join(lines))

print("\n=== H1 (auditor agreement, forced-choice design) ===")
n_agree = 0
for item in ITEMS:
    orders = {m: order_of(sup[(item, m)])[0] for m in MODELS}
    agree = len(set(orders.values())) == 1
    if agree:
        n_agree += 1
    print(f"  {item}: {orders}  {'AGREE' if agree else 'DISAGREE'}")
print(f"  Auditor agreement: {n_agree}/{len(ITEMS)}")

print("\n=== H2 focus: stack_order2_design / stack_order3_design ===")
for item in ["stack_order2_design", "stack_order3_design"]:
    print(f"  {item}:")
    for model in MODELS:
        d = sup[(item, model)]
        ordv, witnesses = order_of(d)
        u_str = ", ".join(f"U{i}={g(d, f'U{i}'):.2f}" for i in range(1, 6))
        print(f"    [{model}] {u_str}  -> ord={ordv} witnesses={witnesses}")

out_summary = os.path.join(HERE, "pilot3_summary.txt")
with open(out_summary, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print(f"\nSaved to {out_summary}")
