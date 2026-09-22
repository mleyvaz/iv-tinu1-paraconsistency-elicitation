"""
Pilot 3: applies the lesson from Jev's own experiments (forced single-choice
separates cleanly where independent boolean probes collapse) to the U1-U5
channels specifically. T, F, I, N stay as independent probes (Arm1 v1,
unchanged) -- that is where genuine paraconsistency (order 0) showed up in
pilot 1/2 and forcing a single choice across ALL 9 letters would make
sigma > 1 structurally impossible, destroying the phenomenon we most want
to keep measuring. Only U1-U5 move to a forced single-choice ("what is the
PRIMARY reason for uncertainty, if any") repeated k times.
"""
import os, json, time, itertools
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from requests.adapters import HTTPAdapter

KEY = os.environ["OPENROUTER_API_KEY"]
URL = "https://openrouter.ai/api/v1/chat/completions"
HEADERS = {"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"}

SESSION = requests.Session()
SESSION.mount("https://", HTTPAdapter(pool_connections=20, pool_maxsize=20))

MODELS = ["openai/gpt-4o-mini", "deepseek/deepseek-chat"]
K_REPEATS = 8  # more repeats since this is now the only arm run; still cheap
TEMPERATURE = 0.7

ITEMS = [
    dict(id="unambig_true", claim="The Pacific Ocean is the largest ocean on Earth by surface area.",
         negation="The Pacific Ocean is not the largest ocean on Earth by surface area.",
         question="Is the Pacific Ocean the largest ocean on Earth by surface area?"),
    dict(id="unambig_false", claim="The Mediterranean Sea is larger than the Pacific Ocean.",
         negation="The Mediterranean Sea is not larger than the Pacific Ocean.",
         question="Is the Mediterranean Sea larger than the Pacific Ocean?"),
    dict(id="paradox", claim="This sentence is false.",
         negation="This sentence is not false.",
         question="Is the sentence \"This sentence is false\" false?"),
    dict(id="aleatory", claim="A fair six-sided die that is about to be rolled once will land showing a 4.",
         negation="A fair six-sided die that is about to be rolled once will not land showing a 4.",
         question="Will a fair six-sided die that is about to be rolled once land showing a 4?"),
    dict(id="epistemic_missing", claim="The person mentioned in the note referred to above prefers tea over coffee.",
         negation="The person mentioned in the note referred to above does not prefer tea over coffee.",
         question="Does the person mentioned in the note referred to above prefer tea over coffee?"),
    dict(id="ambiguous_wording", claim="Visiting relatives can be exhausting.",
         negation="Visiting relatives cannot be exhausting.",
         question="Is it true that visiting relatives can be exhausting?"),
    dict(id="vague_concept", claim="A man with 4,000 hairs remaining on his head is bald.",
         negation="A man with 4,000 hairs remaining on his head is not bald.",
         question="Is a man with 4,000 hairs remaining on his head bald?"),
    dict(id="unmeasurable_aesthetic", claim="Beethoven's 9th Symphony is more emotionally profound than his 5th Symphony.",
         negation="Beethoven's 9th Symphony is not more emotionally profound than his 5th Symphony.",
         question="Is Beethoven's 9th Symphony more emotionally profound than his 5th Symphony?"),
    dict(id="stack_order2_design",
         claim="Based on the note referenced earlier (not shown here), the meeting outcome was widely seen as a compromise.",
         negation="Based on the note referenced earlier (not shown here), the meeting outcome was not widely seen as a compromise.",
         question="Was the meeting outcome, based on the note referenced earlier, widely seen as a compromise?"),
    dict(id="stack_order3_design",
         claim="Depending on how the unreleased lottery draws go and how organizers choose to interpret the loosely worded eligibility rule, the third-place contestant will qualify for the final.",
         negation="Depending on how the unreleased lottery draws go and how organizers choose to interpret the loosely worded eligibility rule, the third-place contestant will not qualify for the final.",
         question="Will the third-place contestant qualify for the final, given the unreleased lottery draws and the loosely worded eligibility rule?"),
]

def tfin_prompts(it):
    """T, F, I, N: unchanged from pilot 1/2 v1 (independent probes, bug-fixed I)."""
    c, neg, q = it["claim"], it["negation"], it["question"]
    return {
        "T": f"Is the following claim true, based only on your general knowledge or the context given? Answer with exactly one word, Yes or No.\n\nClaim: {c}",
        "F": f"Is the following claim true, based only on your general knowledge or the context given? Answer with exactly one word, Yes or No.\n\nClaim: {neg}",
        "I": f"Using both your general knowledge and any context given below, can the following question be answered with a definite yes or no? Do NOT say no merely because no extra context was pasted in -- your own general knowledge counts as information. Answer with exactly one word, Yes or No.\n\nQuestion: {q}",
        "N": f"Taken as a whole, is the evidence or general knowledge relevant to this claim evenly balanced between supporting it and supporting its negation -- could it genuinely go either way? Answer with exactly one word, Yes or No.\n\nClaim: {c}",
    }

U_LABELS = ["ALEATORY", "EPISTEMIC", "AMBIGUITY", "VAGUENESS", "MEASUREMENT", "NONE"]

def forced_choice_prompt(it):
    c = it["claim"]
    return (
        "Consider the following claim. If there is any uncertainty about whether it is true, "
        "what is the SINGLE most important reason for that uncertainty? Reply with exactly one "
        "of these six words and nothing else:\n"
        "ALEATORY (it depends on chance or a random process, even with perfect information)\n"
        "EPISTEMIC (some knowable fact is simply missing)\n"
        "AMBIGUITY (the wording could reasonably be read in more than one way)\n"
        "VAGUENESS (it turns on a graded concept with borderline cases, not a sharp cutoff)\n"
        "MEASUREMENT (it is something that, even in principle, cannot be directly measured or observed)\n"
        "NONE (there is no real uncertainty, or the uncertainty is for some other reason not listed)\n\n"
        f"Claim: {c}\n\nAnswer with exactly one word from the list above."
    )

def call_model(model, prompt, max_tokens=8):
    payload = {"model": model, "messages": [{"role": "user", "content": prompt}],
               "temperature": TEMPERATURE, "max_tokens": max_tokens}
    for attempt in range(3):
        try:
            r = SESSION.post(URL, headers=HEADERS, json=payload, timeout=30)
            if r.status_code == 200:
                data = r.json()
                return data["choices"][0]["message"]["content"], data.get("usage", {}).get("cost", 0)
            time.sleep(1.0)
        except Exception:
            time.sleep(1.0)
    return None, 0

def main():
    tasks = []
    for it in ITEMS:
        tfin = tfin_prompts(it)
        fc_prompt = forced_choice_prompt(it)
        for model in MODELS:
            for letter, prompt in tfin.items():
                for rep in range(K_REPEATS):
                    tasks.append(("tfin", it["id"], model, letter, rep, prompt))
            for rep in range(K_REPEATS):
                tasks.append(("forced_choice", it["id"], model, "U", rep, fc_prompt))

    print(f"Total calls: {len(tasks)}")
    results = []
    total_cost = 0.0

    def worker(task):
        kind, item_id, model, letter, rep, prompt = task
        text, cost = call_model(model, prompt)
        return dict(kind=kind, item_id=item_id, model=model, letter=letter, rep=rep, raw=text, cost=cost)

    with ThreadPoolExecutor(max_workers=15) as ex:
        futs = [ex.submit(worker, t) for t in tasks]
        done = 0
        for f in as_completed(futs):
            res = f.result()
            results.append(res)
            total_cost += res["cost"] or 0
            done += 1
            if done % 150 == 0:
                print(f"  {done}/{len(tasks)} done, running cost ${total_cost:.4f}")

    print(f"Total cost: ${total_cost:.4f}")
    out_raw = os.path.join(os.path.dirname(__file__), "pilot3_raw_results.json")
    with open(out_raw, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print("Saved raw results to", out_raw)

if __name__ == "__main__":
    main()
