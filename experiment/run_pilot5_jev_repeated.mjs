// Pilot 5: Jev with k=5 repeats per letter per item (not a single call), now that
// check_jev_determinism.mjs confirmed Jev's calibrated outputs are NOT deterministic.
// Same 10 items as pilots 1-4. sup(letter) = mean probability across k repeats for
// T/F/I/N (boolean); sup(Uk) = proportion of repeats choosing that label (choice).

import { experimental_evaluate as evaluate } from 'ai';
import fs from 'node:fs/promises';

const K = 5;

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

async function boolCall(label, state, instructions) {
  const r = await evaluate({ model: 'typesafe-ai/jev', state, questions: { [label]: { type: 'boolean', instructions } } });
  return r.answers[label].probability;
}

async function choiceCall(state) {
  const r = await evaluate({
    model: 'typesafe-ai/jev',
    state,
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
  });
  return r.answers.U.choice;
}

async function runItem(item) {
  const T_INSTR = 'Is this claim true, based only on general knowledge or the context given? General knowledge counts as information even if no extra context is supplied.';
  const I_INSTR = 'Using both general knowledge and any context given, can the question of whether this claim is true be answered with a definite yes or no? Do not answer no merely because no extra context text was supplied -- general knowledge counts.';
  const N_INSTR = 'Taken as a whole, is the evidence or general knowledge relevant to this claim evenly balanced between supporting it and supporting its negation -- could it genuinely go either way?';

  const T = [], F = [], I = [], N = [], U = [];
  for (let k = 0; k < K; k++) {
    T.push(await boolCall('T', item.claim, T_INSTR));
    F.push(await boolCall('F', item.negation, T_INSTR));
    I.push(await boolCall('I', item.claim, I_INSTR));
    N.push(await boolCall('N', item.claim, N_INSTR));
    U.push(await choiceCall(item.claim));
  }
  return { id: item.id, T, F, I, N, U };
}

async function main() {
  if (!process.env.AI_GATEWAY_API_KEY) {
    console.error('Falta AI_GATEWAY_API_KEY en el entorno.');
    process.exit(1);
  }
  console.log(`Corriendo ${ITEMS.length} items x k=${K} contra typesafe-ai/jev (${ITEMS.length * K * 5} llamadas)...\n`);
  const results = [];
  for (const item of ITEMS) {
    const r = await runItem(item);
    results.push(r);
    const mean = (arr) => arr.reduce((a, b) => a + b, 0) / arr.length;
    console.log(`[${r.id}] T=${mean(r.T).toFixed(3)} F=${mean(r.F).toFixed(3)} I=${mean(r.I).toFixed(3)} N=${mean(r.N).toFixed(3)}  U=${JSON.stringify(r.U)}`);
  }
  await fs.writeFile('pilot5_jev_repeated_results.json', JSON.stringify(results, null, 2), 'utf-8');
  console.log('\nResultados guardados en pilot5_jev_repeated_results.json');
}

main();
