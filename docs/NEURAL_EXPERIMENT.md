# NN-001: can a causal activation swap transfer a name preference?

This is a concrete starter experiment for after the M2 Max arrives. The code
exists in `research/neural.py`; no pretrained neural result has been observed.

## Question and prediction to discuss

An activation is a model's internal numeric state while processing a prompt.
A causal intervention deliberately changes that state to see what happens.

Example clean prompt:

> When John and Mary went to the store, John gave a book to

The intended next name is Mary. Change only the second John to Mary, and the
intended next name becomes John. We first check that GPT-2 actually makes both
preferences; a sensible sentence does not guarantee the model performs the task.

**Agent's proposed hypothesis, not Finn's selected belief:** replacing the
corrupt prompt's internal state with the clean prompt's state at certain
intermediate layers will move its next-name preference toward the clean answer.
Ask Finn what he expects and what would count against that interpretation.

This adapts the established indirect-object-identification task, which has
been studied using causal interventions. It is a small learning experiment,
not a claim to reproduce the full published circuit.

## Fixed protocol

| Item | Setting |
| --- | --- |
| Model | `openai-community/gpt2`, revision `607a30d783dfa663caf39e06633721c8d4cfcd7e` |
| Runtime | Optional PyTorch + Transformers, float32, MPS by default |
| Task | Eight clean/corrupt prompt pairs in development, eight held out |
| Split | Held-out templates and names differ from development |
| Alignment | Equal prompt token lengths, exactly one changed token, single-token answer names |
| Site | Final prompt-token activation **after** a transformer block, before later blocks/final normalization |
| Development | Sweep blocks 0–10, zero-based; preserve every prompt result |
| Guided alternative | Run the baseline-only config first, discuss it, then select layer(s) in a new config |
| Held-out | One layer selected by Finn; no held-out layer search |
| Baseline gate | At least 75% of pairs favor the intended name in both conditions; otherwise stop |
| Primary measurement | Patched clean-answer-minus-other-name score minus the corrupt baseline score |
| Secondary measurement | Fraction of clean/corrupt score difference restored, only when denominator is positive and nonzero |

A logit is the model's score for a possible next token before probabilities
are computed. The answer margin is `logit(clean answer) - logit(other name)`.
It measures the preference between these two names, not total task accuracy or
the probability that either name is generated among every possible token.
Recovery can exceed 100% or be negative; we do not clip inconvenient values.
All examples remain in the result, including failures. There is no post hoc
selection of only successful prompts.

## Controls that can invalidate an interpretation

1. **Identity:** put a corrupt activation back into the same corrupt run.
   Its score should stay the same. A change suggests broken instrumentation.
2. **Known positive:** copy the clean final-token state after block 11, the
   final block. This should reproduce the clean next-token scores because
   only the shared final normalization and output mapping remain. This is
   a plumbing check; it is deliberately excluded from discovery candidates.
3. **Random perturbations:** change the corrupt state in three seeded random
   directions, each with the same length as the clean-minus-corrupt change.
   Compare the clean patch with equally large nonspecific changes.
4. **Unrelated donor:** patch from a fixed weather prompt. This tests whether
   arbitrary donor replacement also changes the answer margin.
5. **Held-out evaluation:** test Finn's selected layer on new names/templates
   without retuning. A development-only effect may fail to generalize.

Identity and known-positive errors must stay within 0.001 answer-score units.
The code records raw random and unrelated results; it does not silently turn
them into a pass/fail scientific judgment. Finn and the agent discuss whether
they undermine specificity. A large whole-vector patch can carry many things.

## What the first result can establish

A robust patch effect supports causal influence of information available at
that layer/position on this narrow answer preference. It does not identify a
unique "Mary neuron," prove necessity of the whole activation, isolate a
semantic direction, establish a complete circuit, or explain selfhood.

A zero result could mean that the relevant information is elsewhere, that the
patch is too broad, that the task is poorly elicited, or that the hypothesis
is wrong. Inspect the controls before choosing an explanation. Follow-up head
ablation or position-specific patches require a new experiment, not a rewritten
conclusion from the same data.

## Primary references

- Wang et al., [Interpretability in the Wild: a Circuit for Indirect Object
  Identification in GPT-2 small](https://arxiv.org/abs/2211.00593).
- [GPT-2 model and revision metadata](https://huggingface.co/api/models/openai-community/gpt2).
- [Transformers GPT-2 documentation](https://huggingface.co/docs/transformers/en/model_doc/gpt2).
- [PyTorch forward-hook API](https://docs.pytorch.org/docs/stable/generated/torch.nn.Module.html).
- [PyTorch MPS backend](https://docs.pytorch.org/docs/stable/notes/mps.html).

Dependencies and weight availability were checked against primary metadata.
Actual pretrained execution, tokenization checks, and MPS behavior remain to
be validated on the target machine.
