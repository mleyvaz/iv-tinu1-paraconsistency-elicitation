"""Generates the two figures referenced in paper_v0.1.md. Run from this
directory: python make_figures.py"""
import json, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from math import comb

HERE = os.path.dirname(__file__)
EXP = os.path.join(HERE, "..", "..", "experiment")

# ---------------------------------------------------------------------------
# Figure 1: combinatorial distribution of order-d subtypes for n=5 (Table 3.1),
# the n=5 instantiation used throughout Section 4 and Section 9.
# ---------------------------------------------------------------------------
n = 5
orders = list(range(0, n + 3))  # 0..7
counts = [comb(n + 2, d) for d in orders]

fig, ax = plt.subplots(figsize=(6, 4))
bars = ax.bar(orders, counts, color="#3b6ea5", edgecolor="black", linewidth=0.5)
for x, c in zip(orders, counts):
    ax.text(x, c + max(counts) * 0.02, str(c), ha="center", va="bottom", fontsize=9)
ax.set_xlabel("Order d")
ax.set_ylabel("Number of order-d subtypes  C(n+2, d)")
ax.set_title("Table 3.1: order-d partial-paraconsistency subtypes (n=5, |M|=7)\ntotal = 128 = 2^7 (row 7 of Pascal's triangle)")
ax.set_xticks(orders)
fig.tight_layout()
fig.savefig(os.path.join(HERE, "fig1_order_subtypes.png"), dpi=150)
plt.close(fig)
print("Saved fig1_order_subtypes.png")

# ---------------------------------------------------------------------------
# Figure 2: Jev's declared T, F across 5 identical repeated calls on the liar
# paradox item -- shows T+F>1 (Order-0) on every one of the 5 runs (pilot 5),
# vs. the single, misleadingly boundary-only reading from pilot 4.
# ---------------------------------------------------------------------------
with open(os.path.join(EXP, "pilot5_jev_repeated_results.json"), encoding="utf-8") as f:
    pilot5 = json.load(f)
paradox = next(r for r in pilot5 if r["id"] == "paradox")
T = paradox["T"]
F = paradox["F"]
runs = list(range(1, len(T) + 1))
sums = [t + f for t, f in zip(T, F)]

fig, ax = plt.subplots(figsize=(6, 4))
width = 0.35
ax.bar([r - width / 2 for r in runs], T, width, label="T (declared)", color="#3b6ea5")
ax.bar([r + width / 2 for r in runs], F, width, label="F (declared)", color="#a53b3b")
ax.plot(runs, sums, color="black", marker="o", linewidth=1.5, label="T + F")
ax.axhline(1.0, color="gray", linestyle="--", linewidth=1, label="threshold (>1 declares Order-0)")
ax.set_xlabel("Repeat (identical call, k=1..5)")
ax.set_ylabel("Declared probability")
ax.set_title('Jev on the liar paradox ("This sentence is false."), 5 identical calls\nT+F > 1 on 5/5 runs -- reliably declares Order-0 once repeated')
ax.set_xticks(runs)
ax.legend(fontsize=8, loc="upper left")
fig.tight_layout()
fig.savefig(os.path.join(HERE, "fig2_jev_paradox_repeats.png"), dpi=150)
plt.close(fig)
print("Saved fig2_jev_paradox_repeats.png")
