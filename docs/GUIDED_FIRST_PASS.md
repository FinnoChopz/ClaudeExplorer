# Guided first pass

Finn selected a slow walkthrough before using bounded research sessions as
the primary starter system. The aim is to understand the research moves and
their relevant implementation. Writing the code and mastering every line are
not prerequisites.

## How each step works

1. Explain what we are trying to learn and why this step helps.
2. Show one concrete example and the smallest relevant piece of code.
3. Discuss what that code establishes and what remains a judgment call.
4. Pause for conversation before introducing the next meaningful step.

This is the conversational pace; the session runner cannot enforce teaching
or certify understanding. Its one-run limit remains a separate compute limit.

## First distinction: system, measurement, interpretation

We need to keep three things separate:

| Thing | In the automata trial | In the later neural trial |
| --- | --- | --- |
| System | A row of cells changing under a fixed rule | A language model computing next-token scores |
| Measurement | How well the resulting grid compresses | How much an intervention changes an answer preference |
| Interpretation | Whether the pattern deserves to be called complex | What the score change tells us about the model's mechanism |

A measurement can be implemented correctly while its interpretation is wrong.
That is the central issue in the existing automata example. We will understand
the system first, then inspect the measurement, then discuss the inference.

## First tiny example: one update

A cellular automaton is a row of simple cells updated using a fixed rule.
Here a cell is just a bit: `0` is off and `1` is on. Rule 90 turns the next
cell on when its left and right neighbors differ, and off when they match.
The center cell's old value does not enter that particular rule.

```python
rows = ca.evolve(90, width=7, steps=1)
```

| Returned row | Cells |
| --- | --- |
| Initial state | `0001000` |
| After one update | `0010100` |

The inputs select rule 90, seven cells across, and one update. The default
initial state has one on cell in the center. The return value includes both
the initial state and the updated state; it is two rows of numbers, not an
image or a complexity score. Cells wrap around at the row's ends, although
that boundary does not affect this first example.

The next local implementation step, when we reach it, is the small rule table
and update function in `ca.py`. We will trace the neighbors of one cell before
discussing the compact indexing code. Do not introduce compression, algebraic
diagnostics, and neural hooks in the same teaching turn.

## Later checkpoints, one at a time

- Trace the original rule lookup and one update in `ca.py`.
- Understand what the grid contains before assigning it a score.
- Read the compression measurement and distinguish it from a definition of complexity.
- Inspect the existing configuration, source record, and raw result for one run.
- Discuss the bootstrap surprise and select a discriminating hypothesis test.
- On the M2 Max, trace a neural baseline before introducing an intervention.

The bootstrap measurements already exist. Use them as prior evidence; a
walkthrough or repetition is not a new discovery. Finn has selected the mode,
not yet a hypothesis, prediction, interpretation, or claim of understanding.

## Transition to bounded mode

Review the first pass together. The useful transition is when Finn is happy
to let the agent execute a small related set of tests while retaining control
over the question, interpretation, and next direction. There is no quiz,
automatic promotion, deadline, or requirement to become the programmer.
