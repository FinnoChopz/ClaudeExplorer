"""Reproduce the compression ambiguity and test an exact affine diagnostic."""
import argparse
import json
import random
import statistics
import time

import ca
from research.common import check_deadline, read_config, save_run


def algebraic_coefficients(rule):
    """Boolean polynomial coefficients (XOR addition), indexed by input mask.

    Bits 0/1/2 denote right/centre/left. Degree <= 1 means affine: a
    constant XOR a subset of inputs. Rule 105 has a constant and is affine,
    not strictly linear. This is an algebraic diagnostic, not a richness score.
    """
    coefficients = ca.rule_table(rule)
    for bit in (1, 2, 4):
        for mask in range(8):
            if mask & bit:
                coefficients[mask] ^= coefficients[mask ^ bit]
    return coefficients


def algebraic_degree(rule):
    return max((mask.bit_count() for mask, c in
                enumerate(algebraic_coefficients(rule)) if c), default=0)


def superposition_defect(rule, a, b, steps):
    """Fraction violating the affine identity over ALL rows and cells.

    F(a) XOR F(b) XOR F(a XOR b) XOR F(0) must vanish for an affine F.
    The zero baseline corrects the otherwise misleading test for rule 105.
    """
    width = len(a)
    if width == 0 or len(b) != width:
        raise ValueError("Need two nonempty rows of equal width")
    histories = [ca.evolve(rule, width, steps, init) for init in
                 (a, b, [x ^ y for x, y in zip(a, b)], [0] * width)]
    failures = sum(x ^ y ^ xy ^ zero
                   for rows in zip(*histories)
                   for x, y, xy, zero in zip(*rows))
    return failures / (width * (steps + 1))


def validate(config):
    if config.get("kind") != "ca":
        raise ValueError("Expected kind=ca")
    for key, low, high in (("width", 8, 512), ("steps", 1, 512)):
        if type(config.get(key)) is not int or not low <= config[key] <= high:
            raise ValueError(f"{key} must be in {low}..{high}")
    for key, limit, low, high in (("rules", 32, 0, 255),
                                  ("seeds", 32, 0, 2**32 - 1)):
        values = config.get(key)
        if (not isinstance(values, list) or not 1 <= len(values) <= limit
                or any(type(v) is not int or not low <= v <= high for v in values)
                or len(set(values)) != len(values)):
            raise ValueError(f"Invalid or duplicate {key}")
    if config.get("phase") not in ("exploratory", "confirmatory"):
        raise ValueError("phase must be exploratory or confirmatory")


def compute(config, deadline=None):
    validate(config)
    records = []
    for seed in config["seeds"]:
        rng = random.Random(seed)
        a, b = [[rng.getrandbits(1) for _ in range(config["width"])]
                for _ in range(2)]
        for rule in config["rules"]:
            check_deadline(deadline)
            degree = algebraic_degree(rule)
            rows = ca.evolve(rule, config["width"], config["steps"], a)
            records.append({"seed": seed, "rule": rule,
                            "compression_ratio": ca.compressibility(rows),
                            "algebraic_degree": degree, "is_affine": degree <= 1,
                            "superposition_defect": superposition_defect(
                                rule, a, b, config["steps"])})
    summary = []
    for rule in config["rules"]:
        selected = [r for r in records if r["rule"] == rule]
        summary.append({"rule": rule,
                        "is_affine": selected[0]["is_affine"],
                        "algebraic_degree": selected[0]["algebraic_degree"],
                        "compression_mean": statistics.mean(
                            r["compression_ratio"] for r in selected),
                        "compression_min": min(r["compression_ratio"] for r in selected),
                        "compression_max": max(r["compression_ratio"] for r in selected),
                        "defect_mean": statistics.mean(
                            r["superposition_defect"] for r in selected)})
    return {"status": "exploratory_measurements", "records": records,
            "summary": summary,
            "claim_limit": "Affine structure is not computational richness. "
            "No replacement complexity metric has been validated.",
            "human_interpretation": None}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config")
    parser.add_argument("--output-root", default="runs")
    args = parser.parse_args()
    config = read_config(args.config)
    results = compute(config, time.monotonic() + 120)
    path = save_run(config, results, args.output_root)
    print(json.dumps({"run": str(path), "summary": results["summary"]}, indent=2))


if __name__ == "__main__":
    main()
