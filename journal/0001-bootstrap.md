# 0001 — a compression ambiguity and a finite-ring surprise

- Date: October 26, 2026
- Author: Codex
- Stage: engineering bootstrap and exploratory measurements
- Human-selected research question/mode: **not yet recorded**
- Finn's interpretation: **not recorded**

## Initial test

The existing README reports that XOR automata can score as maximally complex
under zlib compression. I reproduced the measurements on nine rules, eight
fixed seeds, and a ring of 101 cells for 200 steps. Every raw measurement is
retained in [bootstrap-ca.json](../evidence/bootstrap-ca.json), with copied
configuration and source/environment provenance. These are local working-tree
runs, not a claim that the upstream commit contained this infrastructure.

The proposed diagnostic expresses a Boolean rule as a polynomial using XOR
for addition. Degree at most one means **affine**: a constant XOR some inputs.
An exhaustive test reconstructs every truth table for all 256 rules and finds
16 affine rules. The second diagnostic evolves two initial rows, their XOR,
and an all-zero row. Their four-way XOR must vanish for an affine evolution.

| Rule | Mean compression ratio, 101 cells / 200 steps | Affine? | Mean superposition defect |
| --- | ---: | --- | ---: |
| 0 | 0.015404 | Yes | 0 |
| 204 | 0.016504 | Yes | 0 |
| 60 | 1.004210 | Yes | 0 |
| 90 | 1.004210 | Yes | 0 |
| 105 | 1.004210 | Yes | 0 |
| 150 | 1.004210 | Yes | 0 |
| 30 | 1.004210 | No | 0.498282 |
| 54 | 0.757750 | No | 0.498165 |
| 110 | 0.767509 | No | 0.494224 |

Compression ratios can slightly exceed one because compressed files include
overhead. The affine test separates the XOR cases from rule 30, despite
identical compression scores in this setup. It also labels trivial rules
0 and 204 affine: it is not a ranking of interesting computation. Rule 105
includes a constant, so the affine correction matters.

## Unexpected observation and controlled follow-up

Changing both width and horizon first produced a large score change. Because
that changed two variables at once, I added the other two cells of the 2×2
comparison before attributing it to either factor. The agent pursued this as
a cheap setup diagnostic; it was not a research direction selected by Finn.

| Ring width | Steps | Rule 90 mean compression ratio |
| ---: | ---: | ---: |
| 101 | 200 | 1.004210 |
| 128 | 200 | 0.245180 |
| 101 | 256 | 1.003292 |
| 128 | 256 | 0.193002 |

The width change is sufficient to produce the large effect in these tests;
the longer run strengthens it on the 128-cell ring. Across the four setups,
the exact affine classification and zero affine superposition defect persist.
There are 288 rule-seed measurements in total, not 288 independent discoveries.

**Agent interpretation:** rule 90 on a periodic ring of width 128 reaches all
zeros after 64 steps for every initial row. To see why, write its update as
left shift XOR right shift. After 64 updates the intermediate terms cancel,
leaving a 64-cell left shift XOR a 64-cell right shift. On this ring these are
the same shift, so they cancel too. Tests confirm the predicted zero row for
four random starts. This is a finite-boundary effect, not a general claim that
the rule is unable to generate complicated-looking patterns.

The two widths also differ in byte padding in the existing compression
encoding. The all-zero dynamical result establishes a real boundary mechanism,
but this experiment does not apportion every compression change between that
mechanism and encoding choices. A metric aimed at transient structures would
need separate, explicitly selected validation.

## Validation and what remains untested

- Local Python 3.12.14: **35 tests passed, 1 optional test skipped**.
- All eight original automata tests pass; original library, browser viewer,
  and original tests are unchanged.
- All four configuration cards executed successfully, with source/config
  hashes and Python/zlib versions recorded.
- Repeated seeded measurements are equal; exhaustive polynomial reconstruction,
  affine identities, timeout/config rejection, output limits, session accounting,
  and hook cleanup on errors are tested.
- The skipped test requires PyTorch/Transformers and checks hooks on a tiny
  randomly initialized GPT-2. It downloads no weights when eventually run.
- No neural dependencies or model weights were installed/downloaded. Actual
  pretrained behavior, tokenizer constraints, hook integration, and MPS remain
  **unvalidated**. The optional dependency combination is not a tested Mac lock.
- Local tests do not establish that an AI agent can conduct reliable autonomous
  science. Session decisions and scientific interpretation are still human work.

## Next decision

Finn selects the collaboration mode. For the first actual research session,
the agent should offer a choice between investigating measurement robustness
and beginning the neural causal experiment, with a short hypothesis card for
each. Finn's interest should determine the direction; the bootstrap does not.
