"""
Pilot 2: fixes the I-probe bug found in pilot 1 (ambiguous whether general
knowledge counts as "information given" -> inflated I on unambiguous facts),
adds the mandatory paraphrase crossover (2 independent wordings per probe),
and adds 2 engineered items designed to test H2 (order-2 and order-3
stacking, mirroring Tuples D and E of the base paper). Arm1 only (indirect
probes) -- Arm1 vs Arm2 divergence was already established clearly in pilot 1
and is not re-tested here to keep cost/time down.
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
K_REPEATS = 5
TEMPERATURE = 0.7

ITEMS = [
    dict(id="unambig_true", category="unambiguous_true",
         claim="The Pacific Ocean is the largest ocean on Earth by surface area.",
         negation="The Pacific Ocean is not the largest ocean on Earth by surface area.",
         question="Is the Pacific Ocean the largest ocean on Earth by surface area?"),
    dict(id="unambig_false", category="unambiguous_false",
         claim="The Mediterranean Sea is larger than the Pacific Ocean.",
         negation="The Mediterranean Sea is not larger than the Pacific Ocean.",
         question="Is the Mediterranean Sea larger than the Pacific Ocean?"),
    dict(id="paradox", category="paradox",
         claim="This sentence is false.",
         negation="This sentence is not false.",
         question="Is the sentence \"This sentence is false\" false?"),
    dict(id="aleatory", category="aleatory",
         claim="A fair six-sided die that is about to be rolled once will land showing a 4.",
         negation="A fair six-sided die that is about to be rolled once will not land showing a 4.",
         question="Will a fair six-sided die that is about to be rolled once land showing a 4?"),
    dict(id="epistemic_missing", category="epistemic",
         claim="The person mentioned in the note referred to above prefers tea over coffee.",
         negation="The person mentioned in the note referred to above does not prefer tea over coffee.",
         question="Does the person mentioned in the note referred to above prefer tea over coffee?"),
    dict(id="ambiguous_wording", category="ambiguity",
         claim="Visiting relatives can be exhausting.",
         negation="Visiting relatives cannot be exhausting.",
         question="Is it true that visiting relatives can be exhausting?"),
    dict(id="vague_concept", category="vagueness",
         claim="A man with 4,000 hairs remaining on his head is bald.",
         negation="A man with 4,000 hairs remaining on his head is not bald.",
         question="Is a man with 4,000 hairs remaining on his head bald?"),
    dict(id="unmeasurable_aesthetic", category="measurement",
         claim="Beethoven's 9th Symphony is more emotionally profound than his 5th Symphony.",
         negation="Beethoven's 9th Symphony is not more emotionally profound than his 5th Symphony.",
         question="Is Beethoven's 9th Symphony more emotionally profound than his 5th Symphony?"),
    # Engineered for H2: designed to need TWO channels stacked (epistemic + ambiguity/vagueness),
    # mirroring Tuple D (order-2, unique witness pair).
    dict(id="stack_order2_design", category="engineered_order2",
         claim="Based on the note referenced earlier (not shown here), the meeting outcome was widely seen as a compromise.",
         negation="Based on the note referenced earlier (not shown here), the meeting outcome was not widely seen as a compromise.",
         question="Was the meeting outcome, based on the note referenced earlier, widely seen as a compromise?"),
    # Engineered for H2: designed to need THREE channels stacked (aleatory + epistemic + ambiguity/vagueness),
    # mirroring Tuple E (order-3, unique witness triple).
    dict(id="stack_order3_design", category="engineered_order3",
         claim="Depending on how the unreleased lottery draws go and how organizers choose to interpret the loosely worded eligibility rule, the third-place contestant will qualify for the final.",
         negation="Depending on how the unreleased lottery draws go and how organizers choose to interpret the loosely worded eligibility rule, the third-place contestant will not qualify for the final.",
         question="Will the third-place contestant qualify for the final, given the unreleased lottery draws and the loosely worded eligibility rule?"),
]

def arm1_prompts_v1(it):
    """v1: same as pilot 1, but with the I-probe bug fixed."""
    c, neg, q = it["claim"], it["negation"], it["question"]
    return {
        "T": f"Is the following claim true, based only on your general knowledge or the context given? Answer with exactly one word, Yes or No.\n\nClaim: {c}",
        "F": f"Is the following claim true, based only on your general knowledge or the context given? Answer with exactly one word, Yes or No.\n\nClaim: {neg}",
        "I": f"Using both your general knowledge and any context given below, can the following question be answered with a definite yes or no? Do NOT say no merely because no extra context was pasted in -- your own general knowledge counts as information. Answer with exactly one word, Yes or No.\n\nQuestion: {q}",
        "N": f"Taken as a whole, is the evidence or general knowledge relevant to this claim evenly balanced between supporting it and supporting its negation -- could it genuinely go either way? Answer with exactly one word, Yes or No.\n\nClaim: {c}",
        "U1": f"Even with complete and perfect information about every relevant current fact, would the truth of the following claim still be genuinely uncertain because it depends on chance or a random process? Answer with exactly one word, Yes or No.\n\nClaim: {c}",
        "U2": f"Is there additional information -- not given here -- that, if provided, would resolve whether the following claim is true or false? Answer with exactly one word, Yes or No.\n\nClaim: {c}",
        "U3": f"Could the following claim reasonably be read in more than one way because of how it is worded, such that different readings would lead to different true/false answers? Answer with exactly one word, Yes or No.\n\nClaim: {c}",
        "U4": f"Does the following claim depend on a concept with borderline cases and no sharp cutoff (a matter of degree), rather than a precise criterion? Answer with exactly one word, Yes or No.\n\nClaim: {c}",
        "U5": f"Is the following claim about something that, even in principle, cannot be directly measured or observed -- only estimated indirectly? Answer with exactly one word, Yes or No.\n\nClaim: {c}",
    }

def arm1_prompts_v2(it):
    """v2: independent paraphrase of every probe, same target letter, bug-fixed I."""
    c, neg, q = it["claim"], it["negation"], it["question"]
    return {
        "T": f"Considering everything you know plus any context provided, would you say the following statement holds? Answer with exactly one word, Yes or No.\n\nStatement: {c}",
        "F": f"Considering everything you know plus any context provided, would you say the following statement holds? Answer with exactly one word, Yes or No.\n\nStatement: {neg}",
        "I": f"Suppose you may draw on everything you already know, not just what is written here. Is that enough to settle the following question one way or the other, with a definite yes or no? Answer with exactly one word, Yes or No.\n\nQuestion: {q}",
        "N": f"Weighing everything relevant that you know about it, does the case for the following claim point clearly one way, or is it roughly a toss-up between the claim and its opposite? Answer Yes if it is roughly a toss-up, No if it clearly leans one way. Answer with exactly one word, Yes or No.\n\nClaim: {c}",
        "U1": f"Suppose every current fact relevant to this were known with certainty. Would real uncertainty still be left over, purely because of chance or randomness? Answer with exactly one word, Yes or No.\n\nClaim: {c}",
        "U2": f"If someone handed you one more fact that is not included here, could that single additional fact settle whether the following claim is true or false? Answer with exactly one word, Yes or No.\n\nClaim: {c}",
        "U3": f"Could two careful readers reasonably disagree about what the following claim is even saying, purely because of how it is worded? Answer with exactly one word, Yes or No.\n\nClaim: {c}",
        "U4": f"Is there a borderline case where reasonable people would disagree on whether the following claim applies, because the underlying concept comes in degrees rather than a sharp yes/no? Answer with exactly one word, Yes or No.\n\nClaim: {c}",
        "U5": f"Is the following claim about something you could only ever estimate or judge, never directly measure or observe? Answer with exactly one word, Yes or No.\n\nClaim: {c}",
    }

def call_model(model, prompt, max_tokens=8):
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": TEMPERATURE,
        "max_tokens": max_tokens,
    }
    for attempt in range(3):
        try:
            r = SESSION.post(URL, headers=HEADERS, json=payload, timeout=30)
            if r.status_code == 200:
                data = r.json()
                content = data["choices"][0]["message"]["content"]
                cost = data.get("usage", {}).get("cost", 0)
                return content, cost
            else:
                time.sleep(1.0)
        except Exception:
            time.sleep(1.0)
    return None, 0

def main():
    tasks = []
    for it in ITEMS:
        for version, prompts_fn in [("v1", arm1_prompts_v1), ("v2", arm1_prompts_v2)]:
            prompts = prompts_fn(it)
            for model in MODELS:
                for letter, prompt in prompts.items():
                    for rep in range(K_REPEATS):
                        tasks.append(("arm1", version, it["id"], model, letter, rep, prompt))

    print(f"Total calls: {len(tasks)}")
    results = []
    total_cost = 0.0

    def worker(task):
        arm, version, item_id, model, letter, rep, prompt = task
        text, cost = call_model(model, prompt)
        return dict(arm=arm, version=version, item_id=item_id, model=model, letter=letter, rep=rep, raw=text, cost=cost)

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

    out_raw = os.path.join(os.path.dirname(__file__), "pilot2_raw_results.json")
    with open(out_raw, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print("Saved raw results to", out_raw)

if __name__ == "__main__":
    main()
