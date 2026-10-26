"""Explicit session decisions, finite compute budgets, and a local run ledger.

This is a cooperative runner, not a security sandbox or identity verifier.
Only commands routed through it consume its budget.
"""
import argparse
import json
import os
import time
from contextlib import contextmanager
from pathlib import Path

from research.common import ROOT, digest, read_config, save_run


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")
    os.replace(temporary, path)


@contextmanager
def lock(path):
    target = Path(str(path) + ".lock")
    fd = os.open(target, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    try:
        yield
    finally:
        os.close(fd)
        target.unlink()


def start(policy_path, decision_path, output):
    policy, decision = read_config(policy_path), read_config(decision_path)
    if (decision.get("status") != "approved" or decision.get("decision_maker") != "Finn"
            or decision.get("policy_id") != policy["id"]):
        raise ValueError("A recorded Finn decision and matching policy are required")
    for key in ("question", "prediction", "what_would_change_my_mind"):
        if not isinstance(decision.get(key), str) or not decision[key].strip():
            raise ValueError(f"Record Finn's {key} before starting")
    if not decision.get("allowed_configs"):
        raise ValueError("List the exact configurations within scope")
    allowed = {}
    for config_path in decision["allowed_configs"]:
        resolved = (ROOT / config_path).resolve()
        resolved.relative_to(ROOT)
        allowed[str(resolved)] = digest(resolved.read_bytes())
    state = {"policy": policy, "decision": decision, "allowed": allowed,
             "runs": [], "wall_seconds": 0.0, "output_bytes": 0,
             "status": "ready"}
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x") as handle:
        json.dump(state, handle, indent=2)
    return state


def run(state_path, config_path, output_root="runs"):
    state_path, config_path = Path(state_path), Path(config_path).resolve()
    with lock(state_path):
        state = json.loads(state_path.read_text())
        policy = state["policy"]
        if state["status"] != "ready":
            raise ValueError("Session requires review before another run")
        if len(state["runs"]) >= policy["max_runs"]:
            raise ValueError("Run budget exhausted; return to Finn")
        remaining = policy["max_wall_seconds"] - state["wall_seconds"]
        remaining_bytes = policy["max_output_bytes"] - state["output_bytes"]
        if remaining <= 0 or remaining_bytes <= 0:
            raise ValueError("Session resource budget exhausted")
        if state["allowed"].get(str(config_path)) != digest(config_path.read_bytes()):
            raise ValueError("Configuration is outside the recorded decision")
        config = read_config(config_path)
        if config.get("phase") != "exploratory":
            raise ValueError("Confirmation requires a separate Finn decision and command")
        record = {"config": str(config_path.relative_to(ROOT)), "status": "running"}
        state["runs"].append(record)
        state["status"] = "running"
        write_json(state_path, state)
    began = time.monotonic()
    try:
        if config["kind"] == "ca":
            from research.ca_trial import compute
            result = compute(config, began + remaining)
        elif config["kind"] == "neural_ioi":
            from research.neural import compute
            result = compute(config, deadline=began + remaining)
        else:
            raise ValueError("Unsupported experiment kind")
        path = save_run(config, result, output_root, max_bytes=remaining_bytes)
        output_bytes = sum(p.stat().st_size for p in path.iterdir() if p.is_file())
        record.update(status="complete", run=str(path), result_status=result["status"])
        return path
    except BaseException as error:
        record.update(status="failed", error=f"{type(error).__name__}: {error}")
        raise
    finally:
        state["wall_seconds"] += time.monotonic() - began
        state["output_bytes"] += locals().get("output_bytes", 0)
        exhausted = (len(state["runs"]) >= policy["max_runs"]
                     or state["wall_seconds"] >= policy["max_wall_seconds"]
                     or state["output_bytes"] >= policy["max_output_bytes"])
        invalid_science = record.get("result_status") in ("baseline_failed", "hook_controls_failed")
        state["status"] = ("awaiting_Finn" if exhausted or record["status"] == "failed" or invalid_science
                           else "ready")
        with lock(state_path):
            write_json(state_path, state)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    create = commands.add_parser("start")
    create.add_argument("policy")
    create.add_argument("decision")
    create.add_argument("output")
    execute = commands.add_parser("run")
    execute.add_argument("session")
    execute.add_argument("config")
    args = parser.parse_args()
    if args.command == "start":
        start(args.policy, args.decision, args.output)
        print(args.output)
    else:
        print(run(args.session, args.config))


if __name__ == "__main__":
    main()
