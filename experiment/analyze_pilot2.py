import json, os, itertools
from collections import defaultdict

HERE = os.path.dirname(__file__)
with open(os.path.join(HERE, "pilot2_raw_results.json"), encoding="utf-8") as f:
    raw = json.load(f)

LETTERS = ["T", "F", "I", "N", "U1", "U2", "U3", "U4", "U5"]
MIDDLE = ["I", "N", "U1", "U2", "U3", "U4", "U5"]

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

by_key = defaultdict(list)  # (item, model, version, letter) -> vals
for r in raw:
    key = (r["item_id"], r["model"], r["version"], r["letter"])
    by_key[key].append(parse_yesno(r["raw"]))

def mean_ignore_none(vals):
    vs = [v for v in vals if v is not None]
    if not vs:
        return None
    return sum(vs) / len(vs)

n_missing = sum(1 for v in itertools.chain.from_iterable(by_key.values()) if v is None)
print(f"Unparseable responses: {n_missing} / {len(raw)}")

sup = {}
for (item, model, version, letter), vals in by_key.items():
    sup.setdefault((item, model, version), {})[letter] = mean_ignore_none(vals)

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

ITEMS = sorted(set(k[0] for k in sup))
MODELS = sorted(set(k[1] for k in sup))
VERSIONS = sorted(set(k[2] for k in sup))

lines = []
lines.append("=== ord(item) per model x version (Arm 1, bug-fixed I, both controls) ===\n")
orders_table = {}
for item in ITEMS:
    lines.append(f"--- {item} ---")
    for model in MODELS:
        for version in VERSIONS:
            d = sup.get((item, model, version), {})
            vals_str = ", ".join(f"{L}={d.get(L):.2f}" if d.get(L) is not None else f"{L}=NA" for L in LETTERS)
            ordv, witnesses = order_of(d)
            orders_table[(item, model, version)] = ordv
            lines.append(f"  [{model} | {version}] {vals_str}")
            lines.append(f"    -> sigma_empty={g(d,'T')+g(d,'F'):.2f}  ord={ordv}  witnesses={witnesses}")
    lines.append("")

print("\n".join(lines))

print("\n=== H1 full stability: agreement across BOTH auditor (2 models) AND paraphrase (2 versions) = 4 conditions per item ===\n")
n_full_agree = 0
n_model_agree_within_version = 0
n_version_agree_within_model = 0
for item in ITEMS:
    conds = {(m, v): orders_table[(item, m, v)] for m in MODELS for v in VERSIONS}
    all_orders = set(conds.values())
    full_agree = len(all_orders) == 1
    if full_agree:
        n_full_agree += 1
    print(f"  {item}: {conds}  {'FULL AGREE (4/4)' if full_agree else 'DISAGREE somewhere'}")

print(f"\n  Items with full 4-way agreement (both models x both paraphrases): {n_full_agree}/{len(ITEMS)}")

# auditor agreement holding paraphrase fixed
for v in VERSIONS:
    agree = sum(1 for item in ITEMS if orders_table[(item, MODELS[0], v)] == orders_table[(item, MODELS[1], v)])
    print(f"  Auditor agreement (model1 vs model2), paraphrase={v}: {agree}/{len(ITEMS)}")
# paraphrase agreement holding model fixed
for m in MODELS:
    agree = sum(1 for item in ITEMS if orders_table[(item, m, VERSIONS[0])] == orders_table[(item, m, VERSIONS[1])])
    print(f"  Paraphrase agreement (v1 vs v2), model={m}: {agree}/{len(ITEMS)}")

print("\n=== H2: engineered stacked items (expect order 2 for stack_order2_design, order 3 for stack_order3_design) ===\n")
for item in ["stack_order2_design", "stack_order3_design"]:
    print(f"  {item}:")
    for model in MODELS:
        for version in VERSIONS:
            d = sup.get((item, model, version), {})
            ordv, witnesses = order_of(d)
            print(f"    [{model} | {version}] ord={ordv} witnesses={witnesses}")

out_summary = os.path.join(HERE, "pilot2_summary.txt")
with open(out_summary, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print(f"\nSaved to {out_summary}")
