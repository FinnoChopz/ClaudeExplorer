"""Local GPT-2 causal activation patching. Heavy imports happen only on request.

No model fetch occurs during a run. Development and confirmation are separate.
This is runnable scaffolding until checked against pretrained GPT-2 on the Mac.
"""
import argparse
import importlib.metadata
import json
import re
import shutil
import statistics
import time
from pathlib import Path

from research.common import ROOT, check_deadline, digest, read_config, save_run
from research.hooks import hidden_output, last_token_patch, temporary_hooks


def validate(config):
    if config.get("kind") != "neural_ioi":
        raise ValueError("Expected kind=neural_ioi")
    if config.get("model_id") != "openai-community/gpt2":
        raise ValueError("This first experiment supports only GPT-2 small")
    if not re.fullmatch(r"[0-9a-f]{40}", config.get("model_revision", "")):
        raise ValueError("Use an immutable model revision")
    if config.get("device") not in ("cpu", "mps"):
        raise ValueError("Select cpu or mps explicitly")
    if config.get("phase") != "exploratory":
        raise ValueError("Use the confirmation command for the held-out split")
    if config.get("dtype") != "float32":
        raise ValueError("First intervention experiment uses float32")
    for key in ("development", "held_out"):
        split = config.get(key, {})
        if not 1 <= len(split.get("templates", [])) <= 4:
            raise ValueError("Each split needs one to four templates")
        if not 1 <= len(split.get("name_pairs", [])) <= 4:
            raise ValueError("Each split needs one to four name pairs")
        for pair in split["name_pairs"]:
            if (not isinstance(pair, list) or len(pair) != 2
                    or any(not isinstance(n, str) or not n for n in pair)
                    or pair[0] == pair[1]):
                raise ValueError("Use pairs of distinct names")
    if set(config["development"]["templates"]) & set(config["held_out"]["templates"]):
        raise ValueError("Hold out different templates")
    dev_names = {n for pair in config["development"]["name_pairs"] for n in pair}
    held_names = {n for pair in config["held_out"]["name_pairs"] for n in pair}
    if dev_names & held_names:
        raise ValueError("Hold out different names")
    layers = config.get("candidate_layers")
    if (not isinstance(layers, list) or not layers
            or any(type(layer) is not int or not 0 <= layer <= 10 for layer in layers)
            or len(set(layers)) != len(layers)):
        raise ValueError("Choose unique blocks in 0..10; block 11 is a positive control")
    if config.get("run_stage", "intervention") not in ("baseline", "intervention"):
        raise ValueError("run_stage must be baseline or intervention")
    if config.get("random_seeds") != [17, 23, 41]:
        raise ValueError("Keep the three preregistered random controls")
    if not 0 < config.get("baseline_min_fraction", 0) <= 1:
        raise ValueError("Invalid baseline gate")
    if not 0 < config.get("control_tolerance", 0) < 0.01:
        raise ValueError("Invalid control tolerance")


def prompts(config, split):
    items = []
    specification = config[split]
    for t, template in enumerate(specification["templates"]):
        for n, (a, b) in enumerate(specification["name_pairs"]):
            for order, (subject, recipient) in enumerate(((a, b), (b, a))):
                values = {"a": a, "b": b}
                items.append({
                    "id": f"{split}-t{t}-n{n}-o{order}",
                    "template_id": t, "name_pair_id": n,
                    "clean": template.format(**values, subject=subject),
                    "corrupt": template.format(**values, subject=recipient),
                    "clean_answer": recipient, "corrupt_answer": subject,
                })
    return items


def recovery(clean, corrupt, patched):
    denominator = clean - corrupt
    return (patched - corrupt) / denominator if denominator > 1e-6 else None


def summarize(records, key="patched_margin"):
    return [{"layer": layer,
             "mean_delta": statistics.mean(r[key] - r["corrupt_margin"]
                                           for r in records if r["layer"] == layer),
             "mean_random_delta": statistics.mean(
                 statistics.mean(r["random_margins"]) - r["corrupt_margin"]
                 for r in records if r["layer"] == layer),
             "mean_unrelated_delta": statistics.mean(
                 r["unrelated_margin"] - r["corrupt_margin"]
                 for r in records if r["layer"] == layer)}
            for layer in sorted({r["layer"] for r in records})]


def model_dir(config):
    return ROOT / ".models" / ("gpt2-" + config["model_revision"])


def fetch(config, allow_download=False):
    validate(config)
    if not allow_download:
        raise ValueError("Model download requires the explicit --allow-download flag")
    if shutil.disk_usage(ROOT).free < 2 * 2**30:
        raise ValueError("Keep at least 2 GiB free before fetching this model")
    from huggingface_hub import snapshot_download
    destination = model_dir(config)
    snapshot_download(
        repo_id=config["model_id"], revision=config["model_revision"],
        local_dir=str(destination), token=False,
        allow_patterns=["config.json", "model.safetensors", "tokenizer.json",
                        "tokenizer_config.json", "vocab.json", "merges.txt",
                        "generation_config.json"],
    )
    hashes = {str(p.relative_to(destination)): digest(p.read_bytes())
              for p in sorted(destination.glob("*"))
              if p.is_file() and p.name != "research-checkpoint.json"}
    (destination / "research-checkpoint.json").write_text(json.dumps({
        "model_id": config["model_id"], "revision": config["model_revision"],
        "sha256": hashes}, indent=2) + "\n")
    return destination


def validate_selection(selection, config, development_result, development_sha):
    if (selection.get("status") != "approved" or selection.get("decision_maker") != "Finn"
            or selection.get("layer") not in config["candidate_layers"]
            or not isinstance(selection.get("reason"), str) or not selection["reason"].strip()):
        raise ValueError("Record Finn's layer selection and scientific reason")
    if development_result.get("status") != "development_complete":
        raise ValueError("Development must pass its behavior and hook controls first")
    if selection.get("development_results_sha256") != development_sha:
        raise ValueError("Selection must identify its exact development result")
    expected = digest(json.dumps(config, sort_keys=True).encode())
    if development_result.get("config_sha256") != expected:
        raise ValueError("Confirm the same configuration used in development")
    if development_result.get("protocol_sha256") != protocol_hash():
        raise ValueError("Protocol code changed; start a new development experiment")


def protocol_hash():
    return digest((ROOT / "research/neural.py").read_bytes()
                  + (ROOT / "research/hooks.py").read_bytes())


def compute(config, deadline=None, selection=None, development=None, development_sha=None):
    validate(config)
    if selection is not None:
        validate_selection(selection, config, development, development_sha)
    check_deadline(deadline)
    destination = model_dir(config)
    checkpoint = destination / "research-checkpoint.json"
    if not checkpoint.exists():
        raise FileNotFoundError("No local checkpoint. Fetch explicitly on the M2 Max first.")
    recorded = json.loads(checkpoint.read_text())
    if (recorded.get("revision") != config["model_revision"]
            or recorded.get("model_id") != config["model_id"]):
        raise ValueError("Checkpoint provenance does not match the configuration")
    for name, expected in recorded["sha256"].items():
        check_deadline(deadline)
        if digest((destination / name).read_bytes()) != expected:
            raise ValueError("Checkpoint file changed: " + name)
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    if config["device"] == "mps" and not torch.backends.mps.is_available():
        raise RuntimeError("MPS unavailable; select cpu explicitly in a new configuration")
    torch.manual_seed(0)
    torch.set_num_threads(2)
    model = AutoModelForCausalLM.from_pretrained(
        str(destination), local_files_only=True, trust_remote_code=False,
        use_safetensors=True, torch_dtype=torch.float32,
        attn_implementation="eager").to(config["device"]).eval()
    tokenizer = AutoTokenizer.from_pretrained(
        str(destination), local_files_only=True, trust_remote_code=False)
    if len(model.transformer.h) != 12:
        raise ValueError("Expected twelve GPT-2 small blocks")
    versions = {name: importlib.metadata.version(name)
                for name in ("torch", "transformers", "tokenizers", "safetensors",
                             "huggingface-hub", "numpy")}
    if selection is not None and development.get("versions") != versions:
        raise ValueError("Dependency versions changed between development and confirmation")

    def forward(text, capture=False, injection=None):
        check_deadline(deadline)
        tokens = tokenizer(text, return_tensors="pt", add_special_tokens=False)
        if tokens["input_ids"].shape[1] > 128:
            raise ValueError("Prompt exceeds the bounded first experiment")
        tokens = {k: v.to(config["device"]) for k, v in tokens.items()}
        cache, hooks = {}, []
        if capture:
            for layer, block in enumerate(model.transformer.h):
                def collect(module, inputs, output, layer=layer):
                    cache[layer] = hidden_output(output)[:, -1, :].detach().clone()
                hooks.append((block, collect))
        if injection is not None:
            layer, vector = injection
            hooks.append((model.transformer.h[layer], last_token_patch(vector)))
        with torch.inference_mode(), temporary_hooks(hooks):
            logits = model(**tokens, use_cache=False).logits[0, -1].detach()
        check_deadline(deadline)
        if not torch.isfinite(logits).all().item():
            raise ValueError("Non-finite model outputs")
        return logits, cache

    split = "held_out" if selection is not None else "development"
    items = prompts(config, split)
    baselines, cached = [], []
    for item in items:
        answer_tokens = [tokenizer.encode(" " + item[k], add_special_tokens=False)
                         for k in ("clean_answer", "corrupt_answer")]
        if any(len(t) != 1 for t in answer_tokens):
            raise ValueError("Names must each be a single token, including leading space")
        clean_ids = tokenizer.encode(item["clean"], add_special_tokens=False)
        corrupt_ids = tokenizer.encode(item["corrupt"], add_special_tokens=False)
        if (len(clean_ids) != len(corrupt_ids)
                or sum(a != b for a, b in zip(clean_ids, corrupt_ids)) != 1):
            raise ValueError("Clean/corrupt prompts must differ at exactly one token")
        yes, no = [t[0] for t in answer_tokens]
        clean_logits, clean_cache = forward(item["clean"], capture=True)
        corrupt_logits, corrupt_cache = forward(item["corrupt"], capture=True)
        clean_margin = (clean_logits[yes] - clean_logits[no]).item()
        corrupt_margin = (corrupt_logits[yes] - corrupt_logits[no]).item()
        baselines.append({**item, "clean_margin": clean_margin,
                          "corrupt_margin": corrupt_margin,
                          "both_correct": clean_margin > 0 and corrupt_margin < 0})
        cached.append((yes, no, clean_cache, corrupt_cache))
    fraction = statistics.mean(row["both_correct"] for row in baselines)
    result = {"status": "baseline_failed", "split": split,
              "config_sha256": digest(json.dumps(config, sort_keys=True).encode()),
              "protocol_sha256": protocol_hash(),
              "versions": versions, "device": config["device"],
              "baseline_both_correct_fraction": fraction, "baselines": baselines,
              "records": [], "human_interpretation": None,
              "claim_limit": "A whole-vector patch localizes causal influence on this task; "
              "it identifies neither a unique feature nor a complete circuit."}
    if fraction < config["baseline_min_fraction"]:
        return result
    if config.get("run_stage") == "baseline":
        result["status"] = "baseline_ready"
        result["next_decision"] = "Discuss normal behavior with Finn before selecting an intervention."
        return result
    _, unrelated_cache = forward(config["unrelated_prompt"], capture=True)
    layers = [selection["layer"]] if selection is not None else config["candidate_layers"]
    tolerance = config["control_tolerance"]
    controls = []
    for base, (yes, no, clean_cache, corrupt_cache) in zip(baselines, cached):
        def margin(layer, vector):
            logits, _ = forward(base["corrupt"], injection=(layer, vector))
            return (logits[yes] - logits[no]).item()
        positive = margin(11, clean_cache[11])
        controls.append({"prompt_id": base["id"],
                         "final_block_positive_error": abs(positive - base["clean_margin"])})
        for layer in layers:
            patched = margin(layer, clean_cache[layer])
            identity = margin(layer, corrupt_cache[layer])
            unrelated = margin(layer, unrelated_cache[layer])
            delta = clean_cache[layer] - corrupt_cache[layer]
            random_margins = []
            for seed in config["random_seeds"]:
                generator = torch.Generator(device="cpu").manual_seed(seed)
                vector = torch.randn(delta.shape, generator=generator).to(config["device"])
                perturbation = vector * (delta.norm() / vector.norm().clamp_min(1e-12))
                random_margins.append(margin(layer, corrupt_cache[layer] + perturbation))
            result["records"].append({
                "prompt_id": base["id"], "layer": layer,
                "clean_margin": base["clean_margin"],
                "corrupt_margin": base["corrupt_margin"],
                "patched_margin": patched, "identity_margin": identity,
                "unrelated_margin": unrelated, "random_margins": random_margins,
                "identity_error": abs(identity - base["corrupt_margin"]),
                "normalized_recovery": recovery(base["clean_margin"], base["corrupt_margin"], patched),
            })
    result["controls"] = controls
    controls_ok = (all(r["final_block_positive_error"] <= tolerance for r in controls)
                   and all(r["identity_error"] <= tolerance for r in result["records"]))
    result["status"] = (("confirmation_complete" if selection else "development_complete")
                        if controls_ok else "hook_controls_failed")
    result["summary"] = summarize(result["records"])
    result["layer_selection"] = selection
    if selection is None and controls_ok:
        result["candidate_shortlist"] = sorted(result["summary"],
                                                key=lambda r: r["mean_delta"], reverse=True)[:3]
        result["next_decision"] = "Finn chooses whether any candidate warrants held-out confirmation."
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    download = sub.add_parser("fetch")
    download.add_argument("config")
    download.add_argument("--allow-download", action="store_true")
    develop = sub.add_parser("develop")
    develop.add_argument("config")
    confirm = sub.add_parser("confirm")
    confirm.add_argument("config")
    confirm.add_argument("selection")
    confirm.add_argument("development_results")
    args = parser.parse_args()
    config = read_config(args.config)
    if args.command == "fetch":
        print(fetch(config, args.allow_download))
        return
    kwargs = {}
    if args.command == "confirm":
        raw = Path(args.development_results).read_bytes()
        kwargs = {"selection": read_config(args.selection),
                  "development": json.loads(raw), "development_sha": digest(raw)}
    result = compute(config, deadline=time.monotonic() + 1200, **kwargs)
    effective = {**config, "run_phase": args.command}
    if kwargs:
        effective["layer_selection"] = kwargs["selection"]
    print(save_run(effective, result))


if __name__ == "__main__":
    main()
