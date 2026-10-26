# Start small, then move to the M2 Max

The default path needs only Python 3.11 or 3.12 and Git. It installs nothing,
starts no server, and makes no API calls. The existing automata explorer still
works with its original commands.

## Current route: guided first pass

Finn selected a slow first pass: understand each big-picture move and the
relevant local implementation without having to write or master all the code.
Begin with [GUIDED_FIRST_PASS.md](GUIDED_FIRST_PASS.md). Discuss one step at a
time. Bounded mode is the intended primary system once we have walked through
the process together; do not activate it automatically.

## Reference commands: reproduce the lightweight trial later

These are reference commands, not a batch to execute at the beginning of the
guided session. Existing measurements are already in the bootstrap evidence.

From the repository root:

```bash
python3 -m unittest -v
python3 -m research.ca_trial configs/ca_baseline.json
python3 -m research.ca_trial configs/ca_width.json
python3 -m research.ca_trial configs/ca_horizon.json
python3 -m research.ca_trial configs/ca_boundary.json
```

Each command saves `config.json`, `manifest.json`, and `results.json` in a new
ignored `runs/` subfolder. Results include every rule/seed measurement, not
only selected successes. Source/configuration hashes survive an uncommitted
working tree. Compression bytes can depend on the recorded zlib version.

The bootstrap evidence in `evidence/bootstrap-ca.json` was measured with local
source hashes, not a fictitious clean upstream checkout. Use it with the
journal and source provenance. Future runs should start from a committed tree.

## Start an experiment after discussing its question and scope

The operating mode is guided. Finn still selects the scientific question and
scope when we reach an actual hypothesis test. The
agent writes the actual answers into a new decision JSON using
`decisions/session.example.json` as its schema. Keep real working decisions
under ignored `sessions/`, unless Finn deliberately wants to publish one.

The populated record needs `status: "approved"`, `decision_maker: "Finn"`,
the selected `policy_id`, question, prediction (or "no prediction"), falsifier,
and exact `allowed_configs` paths. The field values are a record of the
conversation, not proof of a person's identity. An agent must not set these
without a real matching decision. No real decision record is included yet.

For the selected guided mode, once the actual experiment decision exists:

```bash
python3 -m research.session start policies/1-guided.json sessions/decision.json sessions/current.json
python3 -m research.session run sessions/current.json configs/ca_baseline.json
```

The same session file counts runs, total compute time, and saved bytes across
commands. A config not in the selected list, a changed config, concurrent use,
exhausted budget, or failed run stops the workflow. The agent then checks in
with Finn. It must not create a fresh session to evade a stopping condition.
Time is checked between work units, not by a process-killing watchdog.

## M2 Max: install the optional neural environment

Do this on the new machine, no earlier than its arrival. Keep several GiB
free for the Python environment, model files, and temporary installation space.
The core setup has no dependence on this step.

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-neural.txt
mkdir -p sessions
python -m pip freeze > sessions/requirements-mac.lock.txt
python -m unittest -v
python -m research.neural fetch configs/neural_ioi.json --allow-download
python -m research.neural develop configs/neural_baseline.json
```

The last command deliberately stops after measuring normal behavior. Discuss
that with Finn before selecting the intervention. Draft 2 can subsequently use
`python -m research.neural develop configs/neural_ioi.json` for the fixed sweep;
draft 1 can use a selected layer subset in its own configuration.
The model-fetch command is the only experiment command that permits a model
download. It uses a fixed model revision and fetches one safetensors weights
file plus configuration/tokenizer files. The run commands use local files
only. No training, large dataset, full activation dump, or GPU service is used.

`requirements-neural.txt` pins direct dependencies. The resolved Mac lock and
the result's exact package versions record transitive dependencies; a fully
resolved and validated macOS lock is not supplied before testing there. The
optional random tiny-model hook test exercises the real hook API without
fetching pretrained weights. It is a plumbing test, not scientific evidence.

The default device is `mps`, PyTorch's Apple GPU backend. It fails explicitly
if unavailable. A deliberate config copy selecting `cpu` provides a slower
diagnostic path; there is no silent device fallback. Exact cross-device bitwise
reproducibility is not promised.

## First check-in after development

Read baseline accuracy and all controls together. If they fail, diagnose that
before making a mechanism claim. If they pass, discuss the candidate layers
with Finn. Only after his actual selection should the agent populate a new
selection file from `decisions/neural_layer.example.json` and run:

```bash
python -m research.neural confirm configs/neural_ioi.json sessions/neural-layer.json runs/DEVELOPMENT_RUN/results.json
```

Replace `DEVELOPMENT_RUN` with the returned run folder. The selection records
the SHA-256 of the exact development results file, selected zero-based layer,
and Finn's reason. Confirmation refuses changed config, protocol code, package
versions, failed development controls, or an incomplete selection.

Bring the held-out observation back for interpretation. It is eight small,
correlated prompt pairs: useful for a first causal test, insufficient for a
broad generalization claim. Repeatedly using that split makes it development
data; reserve new examples for another confirmation.
