// Cheap check: is Jev's calibrated output deterministic across repeated calls
// with the identical input, or does it vary? Run the paradox item's T probe
// (and the U choice probe) 5 times each and compare.

import { experimental_evaluate as evaluate } from 'ai';

const claim = 'This sentence is false.';
const negation = 'This sentence is not false.';

async function repeatBoolean(label, state, instructions, n = 5) {
  const results = [];
  for (let i = 0; i < n; i++) {
    const r = await evaluate({
      model: 'typesafe-ai/jev',
      state,
      questions: { [label]: { type: 'boolean', instructions } },
    });
    results.push(r.answers[label].probability);
  }
  return results;
}

async function repeatChoice(state, n = 5) {
  const results = [];
  for (let i = 0; i < n; i++) {
    const r = await evaluate({
      model: 'typesafe-ai/jev',
      state,
      questions: {
        U: {
          type: 'choice',
          instructions: 'If there is any uncertainty about whether this claim is true, what is the single most important reason for that uncertainty?',
          criteria: {
            aleatory: 'It depends on chance or a random process, even with perfect information.',
            epistemic: 'Some knowable fact that would resolve it is simply missing.',
            ambiguity: 'The wording of the claim could reasonably be read in more than one way.',
            vagueness: 'It turns on a graded concept with borderline cases, not a sharp cutoff.',
            measurement: 'It is something that, even in principle, cannot be directly measured or observed, only estimated indirectly.',
            none: 'There is no real uncertainty, or the uncertainty is for some other reason not listed.',
          },
        },
      },
    });
    results.push({ choice: r.answers.U.choice, probs: r.answers.U.probabilities });
  }
  return results;
}

async function main() {
  console.log('=== T (claim = "This sentence is false.") x5 ===');
  const tRuns = await repeatBoolean('T', claim,
    'Is this claim true, based only on general knowledge or the context given?');
  console.log(tRuns);

  console.log('\n=== F (claim = negation) x5 ===');
  const fRuns = await repeatBoolean('F', negation,
    'Is this claim true, based only on general knowledge or the context given?');
  console.log(fRuns);

  console.log('\n=== I x5 ===');
  const iRuns = await repeatBoolean('I', claim,
    'Using both general knowledge and any context given, can the question of whether this claim is true be answered with a definite yes or no?');
  console.log(iRuns);

  console.log('\n=== U (choice) x5 ===');
  const uRuns = await repeatChoice(claim);
  uRuns.forEach((r, i) => console.log(`  run ${i + 1}: choice=${r.choice}  probs=${JSON.stringify(r.probs)}`));

  const allSame = (arr) => arr.every((v) => v === arr[0]);
  console.log('\n=== Summary ===');
  console.log('T identical across 5 runs?', allSame(tRuns));
  console.log('F identical across 5 runs?', allSame(fRuns));
  console.log('I identical across 5 runs?', allSame(iRuns));
  console.log('U choice identical across 5 runs?', allSame(uRuns.map(r => r.choice)));
}

main();
