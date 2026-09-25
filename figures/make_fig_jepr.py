"""Figure for the JEPR note: sigma_empty = sup T + sup F per item and system (final protocol).
LLM values from experiment/recompute_fixI_results.json (pilot 3), Jev values from pilot 5 (k=5)."""
import json, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.join(HERE, "..", "experiment")
p3 = json.load(open(os.path.join(EXP, "recompute_fixI_results.json"), encoding="utf-8"))["pilot3"]
p5 = {r["id"]: r for r in json.load(open(os.path.join(EXP, "pilot5_jev_repeated_results.json"), encoding="utf-8"))}

ITEMS = ["unambig_true", "unambig_false", "paradox", "aleatory", "epistemic_missing", "ambiguous_wording",
         "vague_concept", "unmeasurable_aesthetic", "stack_order2_design", "stack_order3_design"]
LABELS = ["true fact", "false fact", "liar paradox", "aleatory", "epistemic", "ambiguity", "vagueness",
          "measurement", "stacked (2)", "stacked (3)"]
mean = lambda v: sum(v) / len(v)
series = {
    "deepseek-chat": [p3[i]["deepseek-chat"]["sup"]["T"] + p3[i]["deepseek-chat"]["sup"]["F"] for i in ITEMS],
    "gpt-4o-mini": [p3[i]["gpt-4o-mini"]["sup"]["T"] + p3[i]["gpt-4o-mini"]["sup"]["F"] for i in ITEMS],
    "Jev (mean of 5)": [mean(p5[i]["T"]) + mean(p5[i]["F"]) for i in ITEMS],
}
fig, ax = plt.subplots(figsize=(7.2, 3.6))
w = 0.27
colors = ["#3b6ea5", "#a53b3b", "#5a8f4e"]
for k, (name, vals) in enumerate(series.items()):
    ax.bar([x + (k - 1) * w for x in range(len(ITEMS))], vals, w, label=name, color=colors[k])
ax.axhline(1.0, color="gray", linestyle="--", linewidth=1)
ax.text(3.6, 1.03, "Order-0 threshold", ha="left", va="bottom", fontsize=7, color="gray")
ax.set_xticks(range(len(ITEMS)))
ax.set_xticklabels(LABELS, rotation=35, ha="right", fontsize=8)
ax.set_ylabel("sup T + sup F", fontsize=9)
ax.set_ylim(0, 2.15)
ax.legend(fontsize=7, loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=3, frameon=False)
fig.tight_layout()
fig.savefig(os.path.join(HERE, "fig_jepr_sigma0.png"), dpi=200)
for n, v in series.items():
    print(n, [round(x, 2) for x in v])
