"""
Feasibility pilot for Section 9 (IV-TINU1 paper).
NOT the full pre-registered study: small item bank (8 items), k=5 repeats,
2 auditor models, no paraphrase crossover yet. Purpose: validate the
elicitation mechanics (parseable yes/no, sensible sup() values) and get a
first, low-confidence read on H1 (auditor stability) and H3 (Arm1 vs Arm2
divergence) before committing to the full n=100-200 pre-registered run.
"""
import os, json, time, itertools
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests

KEY = os.environ["OPENROUTER_API_KEY"]
URL = "https://openrouter.ai/api/v1/chat/completions"
HEADERS = {"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"}

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
]

def arm1_prompts(it):
    c, neg, q = it["claim"], it["negation"], it["question"]
    return {
        "T": f"Is the following claim true, based only on your general knowledge or the context given? Answer with exactly one word, Yes or No.\n\nClaim: {c}",
        "F": f"Is the following claim true, based only on your general knowledge or the context given? Answer with exactly one word, Yes or No.\n\nClaim: {neg}",
        "I": f"Based only on the information given, can the following question be answered with a definite yes or no? Answer with exactly one word, Yes or No.\n\nQuestion: {q}",
        "N": f"Taken as a whole, is the evidence or general knowledge relevant to this claim evenly balanced between supporting it and supporting its negation -- could it genuinely go either way? Answer with exactly one word, Yes or No.\n\nClaim: {c}",
        "U1": f"Even with complete and perfect information about every relevant current fact, would the truth of the following claim still be genuinely uncertain because it depends on chance or a random process? Answer with exactly one word, Yes or No.\n\nClaim: {c}",
        "U2": f"Is there additional information -- not given here -- that, if provided, would resolve whether the following claim is true or false? Answer with exactly one word, Yes or No.\n\nClaim: {c}",
        "U3": f"Could the following claim reasonably be read in more than one way because of how it is worded, such that different readings would lead to different true/false answers? Answer with exactly one word, Yes or No.\n\nClaim: {c}",
        "U4": f"Does the following claim depend on a concept with borderline cases and no sharp cutoff (a matter of degree), rather than a precise criterion? Answer with exactly one word, Yes or No.\n\nClaim: {c}",
        "U5": f"Is the following claim about something that, even in principle, cannot be directly measured or observed -- only estimated indirectly? Answer with exactly one word, Yes or No.\n\nClaim: {c}",
    }

def arm2_prompts(it):
    c = it["claim"]
    return {
        "T": f"On a scale of 0 to 100, how true do you think the following claim is? Answer with just the number.\n\nClaim: {c}",
        "F": f"On a scale of 0 to 100, how false do you think the following claim is? Answer with just the number.\n\nClaim: {c}",
        "I": f"On a scale of 0 to 100, how uncertain or undetermined is the following claim to you? Answer with just the number.\n\nClaim: {c}",
        "N": f"On a scale of 0 to 100, how neutral or balanced does the evidence for the following claim feel to you? Answer with just the number.\n\nClaim: {c}",
        "U1": f"Is your uncertainty about the following claim due to randomness in the world? Answer with exactly one word, Yes or No.\n\nClaim: {c}",
        "U2": f"Is your uncertainty about the following claim due to missing information? Answer with exactly one word, Yes or No.\n\nClaim: {c}",
        "U3": f"Is your uncertainty about the following claim due to unclear wording? Answer with exactly one word, Yes or No.\n\nClaim: {c}",
        "U4": f"Is your uncertainty about the following claim due to a vague concept? Answer with exactly one word, Yes or No.\n\nClaim: {c}",
        "U5": f"Is your uncertainty about the following claim due to something unmeasurable? Answer with exactly one word, Yes or No.\n\nClaim: {c}",
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
            r = requests.post(URL, headers=HEADERS, json=payload, timeout=30)
            if r.status_code == 200:
                data = r.json()
                content = data["choices"][0]["message"]["content"]
                cost = data.get("usage", {}).get("cost", 0)
                return content, cost
            else:
                time.sleep(1.5)
        except Exception:
            time.sleep(1.5)
    return None, 0

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
    import re
    m = re.search(r"\d+(\.\d+)?", text)
    if not m:
        return None
    try:
        v = float(m.group(0))
        return max(0.0, min(100.0, v)) / 100.0
    except Exception:
        return None

def main():
    tasks = []
    for it in ITEMS:
        a1 = arm1_prompts(it)
        a2 = arm2_prompts(it)
        for model in MODELS:
            for letter, prompt in a1.items():
                for rep in range(K_REPEATS):
                    tasks.append(("arm1", it["id"], model, letter, rep, prompt))
            for letter, prompt in a2.items():
                for rep in range(K_REPEATS):
                    tasks.append(("arm2", it["id"], model, letter, rep, prompt))

    print(f"Total calls: {len(tasks)}")
    results = []
    total_cost = 0.0

    def worker(task):
        arm, item_id, model, letter, rep, prompt = task
        text, cost = call_model(model, prompt)
        return dict(arm=arm, item_id=item_id, model=model, letter=letter, rep=rep, raw=text, cost=cost)

    with ThreadPoolExecutor(max_workers=10) as ex:
        futs = [ex.submit(worker, t) for t in tasks]
        done = 0
        for f in as_completed(futs):
            res = f.result()
            results.append(res)
            total_cost += res["cost"] or 0
            done += 1
            if done % 100 == 0:
                print(f"  {done}/{len(tasks)} done, running cost ${total_cost:.4f}")

    print(f"Total cost: ${total_cost:.4f}")

    out_raw = os.path.join(os.path.dirname(__file__), "pilot_raw_results.json")
    with open(out_raw, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print("Saved raw results to", out_raw)

if __name__ == "__main__":
    main()
