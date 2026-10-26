# Three draft research environments

These are alternative operating modes for one small shared environment, not
three competing software stacks. The shared starter is implemented on a review
branch. Finn selected **draft 1 for a slow, in-depth first pass**, then **draft 2
as the intended primary starter system**. Draft 2 is not active yet. This
selects the collaboration approach, not a hypothesis or scientific conclusion.
Start with [the guided walkthrough](GUIDED_FIRST_PASS.md).

The aim is to learn how a model works while actively doing the investigation.
Claude/Codex contributes ideas, experiments, diagnostics, and criticism. Finn
supplies scientific taste, interpretation, and decisions about direction.

| Draft | How a session feels | Agent freedom | Finn's decision points | Main merit | Cost or weakness |
| --- | --- | --- | --- | --- | --- |
| **1. Guided bench** | Discuss every meaningful step, including purpose and local implementation. | One listed experiment, up to 10 compute minutes, with pauses before and within the investigation. | Understand each move; choose each hypothesis and next test; interpret each result. | **Selected first pass.** Best for building intuition. | More conversation between steps. |
| **2. Bounded research partner** | Choose a question together; let the agent work briefly; return to the evidence together. | Up to three listed related runs or 20 total compute minutes, whichever comes first. | Choose the question, falsifier, and permitted tests; decide what the evidence means and what happens next. | **Intended primary system after the guided pass.** | A surprising avenue outside the list waits for a scope decision. |
| **3. Branching expedition** | Agree on a small investigation tree, then review competing explanations together. | Up to eight listed runs or one total compute hour; agent chooses which authorized branches to pursue. | Approve the question/tree, decide when to narrow it, judge claims and next direction. | More room to investigate unexpected results and compare rival mechanisms. | More output and greater risk of arriving after the most instructive moments. |

Time caps cover runner compute, not the duration of a conversation. Output
caps are 8 MiB for drafts 1/2 and 16 MiB for draft 3. No mode downloads models,
spends money, or chooses a new scientific question automatically. The initial
runner accepts an exact authorized configuration list; it does not yet generate
or authorize new configurations on its own. Expanding that list is a scope
decision, not a reason to build a bigger agent framework.

## Draft 1: guided bench

**First automata session:** show why rule 90 looks incompressible. Ask what
kind of complexity Finn wants to distinguish. The agent proposes a controlled
comparison and explains what it can establish. After a run, discuss one plot
or table before choosing the next test.

**First neural session:** compare a clean and a name-swapped prompt. Look at
the model's two answer scores together before patching any activations. Finn
can suggest a layer, the agent explains controls, and they test it.

**Starting files:** `policies/1-guided.json`, a one-config decision file, the
shared journal, and the same experiment code used in the other drafts. Start
neural work with `configs/neural_baseline.json`, which stops after measuring
normal behavior. Finn then chooses a layer or sweep; the agent records a
new configuration/decision. Candidate layer subsets are supported in 0–10.

**When to choose it:** the priority is understanding each causal step while
learning the tooling. This would be a good first evening on the M2 Max.

## Draft 2: bounded research partner

**Illustrative automata session:** Finn could select "is this metric robust to the finite
simulation setup?" The agent proposes the existing baseline, width, and horizon
configuration cards. Finn can revise that scope. Within the selected cards the
agent chooses the order, inspects a surprise, and returns with the cheapest
next discriminating test. It does not decide that the metric is fixed.

**First neural session:** agree on the intervention and predicted outcome.
The agent checks normal behavior, runs the fixed development sweep, inspects
identity/random/unrelated-donor controls, and offers candidates with rival
explanations. Finn decides whether any candidate warrants held-out testing.

**Starting files:** `policies/2-bounded.json`, a decision listing up to the
desired follow-up cards, and the shared journal. The code stops on a failed
neural baseline/control rather than continuing through a budget.

**When to choose it:** the agent should have initiative, but Finn should still
be present at the points where scientific judgment changes the investigation.

## Draft 3: branching expedition

**First automata session:** authorize a small tree of tests for rival accounts
of the measurement: initial randomness, finite-ring effects, and algebraic
structure. The agent can prune redundant branches, check counterexamples, and
bring back evidence for each surviving explanation. Exact new cards still need
to be created and selected before this eight-run workflow is useful.

**First neural session:** the same fixed development experiment establishes
the tooling. Further branches might compare token positions or ablate attention
heads, but these are proposals, not capabilities already included in this patch.
They would require a new protocol and tests before running.

**Starting files:** `policies/3-expedition.json`, an agreed branch list and
stopping criteria, and the shared journal. This is a longer cooperative session,
not an overnight background service or an autonomous scientific authority.

**When to choose it:** after shorter sessions have established that the agent's
experiments and interpretations are reliable enough to merit wider scope.

## Common concrete deliverables

- Original `ca.py`, `index.html`, and `test_ca.py` preserved.
- Versioned JSON experiment cards, exact source/configuration hashes, Python
  and zlib versions, unique run folders, and a local session ledger.
- A compression ambiguity trial with an exact Boolean affine diagnostic and
  a finite-ring check. This is not a validated new measure of complexity.
- Standard-library tests and lightweight GitHub Actions checks.
- `AGENTS.md` and `CLAUDE.md`, a factual research journal, and empty decision
  templates that do not pretend Finn has already chosen anything.
- One implemented GPT-2 activation-patching protocol for later local use,
  with separate development and held-out stages. Its neural runtime and MPS
  compatibility remain unvalidated until the optional libraries are installed.

## Current evidence and limits

The automata experiment has actually run locally. See the bootstrap journal
for the final test count; the real neural hook test is skipped. No model
or neural library has been downloaded. GitHub Actions results are separate from
these local results and must be checked after publishing the review branch.

This demonstrates deterministic lightweight measurements and useful controls.
It does not demonstrate that an unattended agent can discover a neural circuit,
or that any neural intervention has worked. Those are future observations.

Read `START_HERE.md`, `NEURAL_EXPERIMENT.md`, and `journal/0001-bootstrap.md`
for commands, the precise experiment, and the actual trial outcome.
