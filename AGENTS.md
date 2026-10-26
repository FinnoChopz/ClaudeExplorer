# Research collaboration contract

Read `docs/THREE_DRAFTS.md`, `docs/START_HERE.md`, the latest journal entry,
and the real decision record before starting research. No operating mode is
selected yet. All three policy files are drafts for Finn to compare.

## Finn's role

Finn selects the research question, decides whether a proposed test addresses
it, interprets the evidence with the agent, and decides what deserves pursuit.
Offer your own hypotheses and disagree when the evidence warrants it. Invite
a prediction before showing the result when useful; do not make participation
a quiz or require a particular answer. Record only what Finn actually says.

## Working loop

1. Present a small hypothesis card: question, mechanism, prediction, strongest
   rival explanation, cheapest discriminating test, and what would falsify it.
2. Record Finn's selected scope, prediction (including uncertainty or no
   prediction), and what would change his mind in a decision file. No invented
   approvals, observations, or scientific conclusions.
3. Propose an exact list of lightweight configurations that fits that scope.
   Once selected, the session runner checks their hashes and the run, compute
   time, and output budgets. Choose and order those tests autonomously.
4. Investigate surprises with an already authorized diagnostic if possible.
   An unlisted configuration, new metric/model/dataset, different hypothesis,
   or changed protocol is a proposed new branch requiring Finn's decision.
   Do not silently revise the test until the result looks persuasive.
5. Return the observation, a competing explanation, your interpretation
   explicitly labeled as such, and one scientific decision worth discussing.
   Append the actual commands, run paths, failures, and unresolved questions
   to the journal. Preserve null human fields until Finn responds.

## Boundaries

- Use the existing Claude/Codex interactive session as the collaborator. This
  starter has no API agent, unattended daemon, schedule, or automatic model calls.
  Agent tool use still depends on the user's actual Claude/Codex permissions.
- No API spending, rented compute, dependencies, model downloads, uploads, or
  publishing/merging research results without the corresponding user direction.
  Initial setup is standard-library Python. Later model fetching is a separate
  explicit command. Do not acquire OpenAI/Anthropic credentials for this starter.
- Scientific autonomy is bounded by the recorded question, not just the clock.
  Stop for failed baselines/controls, exhausted budgets, or a change of premise.
  A run ending is not a reason to manufacture a conclusion.
- Neural development selects candidates. Finn chooses a candidate and rationale
  before the held-out command. Do not tune on held-out outcomes or treat a
  final-layer readout copy as a discovered circuit. Any reused holdout becomes
  development data for subsequent work.
- Keep raw runs, model files, and personal conversations untracked. The repo
  is public; commit only deliberate, appropriate summaries and configurations.
- Preserve the original automata library, browser visualization, and tests.
  Run `python -m unittest -v` after code edits; report skipped tests separately.
- The runner is cooperative: it enforces its own counters/configuration list,
  checks time between work units, and limits saved artifact bytes. It does not
  authenticate a human, police an agent's judgment, cap all machine resources,
  or prevent shell commands that bypass it. Instructions are not a security
  boundary. A crash can leave a session marked running; inspect it with Finn
  before any manual reset.

## What to show Finn at a check-in

Keep it short: "We observed __. This supports __, but __ could also explain
it. The most useful next choice is __." Link the evidence; distinguish a test
failure from a falsified hypothesis. A surprise can be more useful than a win.
