// IV-TINU1 paper (Florentin + Leyva-Vazquez), Section 9: runs the same 10 pilot items
// against typesafe-ai/jev instead of OpenRouter models. T,F,I,N via boolean (one call each,
// native calibrated probability, no repeats needed); U1-U5 via a single Choice call with
// named escape categories, mirroring Jev's own Experiment 2 design (which separated
// TORN/SILENT perfectly, p=1.0, vs. the boolean design that collapsed them).

import { experimental_evaluate as evaluate } from 'ai';
import fs from 'node:fs/promises';

const ITEMS = [
  { id: 'unambig_true', claim: 'The Pacific Ocean is the largest ocean on Earth by surface area.',
    negation: 'The Pacific Ocean is not the largest ocean on Earth by surface area.' },
  { id: 'unambig_false', claim: 'The Mediterranean Sea is larger than the Pacific Ocean.',
    negation: 'The Mediterranean Sea is not larger than the Pacific Ocean.' },
  { id: 'paradox', claim: 'This sentence is false.',
    negation: 'This sentence is not false.' },
  { id: 'aleatory', claim: 'A fair six-sided die that is about to be rolled once will land showing a 4.',
    negation: 'A fair six-sided die that is about to be rolled once will not land showing a 4.' },
  { id: 'epistemic_missing', claim: 'The person mentioned in the note referred to above prefers tea over coffee.',
    negation: 'The person mentioned in the note referred to above does not prefer tea over coffee.' },
  { id: 'ambiguous_wording', claim: 'Visiting relatives can be exhausting.',
    negation: 'Visiting relatives cannot be exhausting.' },
  { id: 'vague_concept', claim: 'A man with 4,000 hairs remaining on his head is bald.',
    negation: 'A man with 4,000 hairs remaining on his head is not bald.' },
  { id: 'unmeasurable_aesthetic', claim: "Beethoven's 9th Symphony is more emotionally profound than his 5th Symphony.",
    negation: "Beethoven's 9th Symphony is not more emotionally profound than his 5th Symphony." },
  { id: 'stack_order2_design', claim: 'Based on the note referenced earlier (not shown here), the meeting outcome was widely seen as a compromise.',
    negation: 'Based on the note referenced earlier (not shown here), the meeting outcome was not widely seen as a compromise.' },
  { id: 'stack_order3_design', claim: 'Depending on how the unreleased lottery draws go and how organizers choose to interpret the loosely worded eligibility rule, the third-place contestant will qualify for the final.',
    negation: 'Depending on how the unreleased lottery draws go and how organizers choose to interpret the loosely worded eligibility rule, the third-place contestant will not qualify for the final.' },
];

async function runOne(item) {
  const [tRes, fRes, iRes, nRes, uRes] = await Promise.all([
    evaluate({
      model: 'typesafe-ai/jev',
      state: item.claim,
      questions: { T: { type: 'boolean',
        instructions: 'Is this claim true, based only on general knowledge or the context given? General knowledge counts as information even if no extra context is supplied.' } },
    }),
    evaluate({
      model: 'typesafe-ai/jev',
      state: item.negation,
      questions: { F: { type: 'boolean',
        instructions: 'Is this claim true, based only on general knowledge or the context given? General knowledge counts as information even if no extra context is supplied.' } },
    }),
    evaluate({
      model: 'typesafe-ai/jev',
      state: item.claim,
      questions: { I: { type: 'boolean',
        instructions: 'Using both general knowledge and any context given, can the question of whether this claim is true be answered with a definite yes or no? Do not answer no merely because no extra context text was supplied -- general knowledge counts.' } },
    }),
    evaluate({
      model: 'typesafe-ai/jev',
      state: item.claim,
      questions: { N: { type: 'boolean',
        instructions: 'Taken as a whole, is the evidence or general knowledge relevant to this claim evenly balanced between supporting it and supporting its negation -- could it genuinely go either way?' } },
    }),
    evaluate({
      model: 'typesafe-ai/jev',
      state: item.claim,
      questions: {
        U: {
          type: 'choice',
          instructions: 'If there is any uncertainty about whether this claim is true, what is the single most important reason for that uncertainty?',
          criteria: {
            aleatory: 'It depends on chance or a random process, even with perfect information about every current fact.',
            epistemic: 'Some knowable fact that would resolve it is simply missing.',
            ambiguity: 'The wording of the claim could reasonably be read in more than one way.',
            vagueness: 'It turns on a graded concept with borderline cases, not a sharp yes/no cutoff.',
            measurement: 'It is something that, even in principle, cannot be directly measured or observed, only estimated indirectly.',
            none: 'There is no real uncertainty, or the uncertainty is for some other reason not listed.',
          },
        },
      },
    }),
  ]);
  return {
    id: item.id,
    T: tRes.answers.T.probability,
    F: fRes.answers.F.probability,
    I: iRes.answers.I.probability,
    N: nRes.answers.N.probability,
    U_choice: uRes.answers.U.choice,
    U_probabilities: uRes.answers.U.probabilities,
  };
}

async function main() {
  if (!process.env.AI_GATEWAY_API_KEY) {
    console.error('Falta AI_GATEWAY_API_KEY en el entorno.');
    process.exit(1);
  }
  console.log(`Corriendo ${ITEMS.length} items del paper IV-TINU1 contra typesafe-ai/jev...\n`);
  const results = [];
  for (const item of ITEMS) {
    try {
      const r = await runOne(item);
      results.push(r);
      console.log(`[${r.id}] T=${r.T} F=${r.F} I=${r.I} N=${r.N}  U=${r.U_choice} ${JSON.stringify(r.U_probabilities)}`);
    } catch (err) {
      console.error(`[${item.id}] ERROR:`, err.message || err);
      results.push({ id: item.id, error: String(err.message || err) });
    }
  }
  await fs.writeFile('iv_tinu1_jev_results.json', JSON.stringify(results, null, 2), 'utf-8');
  console.log('\nResultados guardados en iv_tinu1_jev_results.json');
}

main();
