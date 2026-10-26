import importlib.util
import json
import random
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

import ca
from research import ca_trial, neural, session
from research.common import ROOT, digest, read_config, save_run
from research.hooks import last_token_patch, temporary_hooks


class TestAffineDiagnostic(unittest.TestCase):
    def test_all_truth_tables_reconstruct_exactly(self):
        for rule in range(256):
            coefficients = ca_trial.algebraic_coefficients(rule)
            for inputs in range(8):
                value = 0
                for mask, coefficient in enumerate(coefficients):
                    if inputs & mask == mask:
                        value ^= coefficient
                self.assertEqual(value, ca.rule_table(rule)[inputs])

    def test_exactly_sixteen_affine_rules(self):
        self.assertEqual(sum(ca_trial.algebraic_degree(r) <= 1 for r in range(256)), 16)

    def test_reference_rules_and_affine_constant(self):
        for rule in (0, 204, 60, 90, 105, 150):
            self.assertLessEqual(ca_trial.algebraic_degree(rule), 1)
        self.assertEqual(ca_trial.algebraic_coefficients(105)[0], 1)
        self.assertEqual(ca_trial.algebraic_degree(30), 2)
        self.assertEqual(ca_trial.algebraic_degree(110), 3)

    def test_affine_identity_over_multiple_time_steps(self):
        a = [random.Random(i).getrandbits(1) for i in range(31)]
        b = [random.Random(i + 101).getrandbits(1) for i in range(31)]
        for rule in range(256):
            if ca_trial.algebraic_degree(rule) <= 1:
                self.assertEqual(ca_trial.superposition_defect(rule, a, b, 12), 0)
        self.assertGreater(ca_trial.superposition_defect(30, a, b, 12), 0)

    def test_rule90_finite_ring_annihilation(self):
        for seed in range(4):
            rng = random.Random(seed)
            initial = [rng.getrandbits(1) for _ in range(128)]
            self.assertEqual(sum(ca.evolve(90, 128, 64, initial)[-1]), 0)

    def test_deterministic_results(self):
        config = read_config(ROOT / "configs/ca_baseline.json")
        config.update(width=31, steps=16, seeds=[2, 7])
        self.assertEqual(ca_trial.compute(config), ca_trial.compute(config))

    def test_invalid_configs_and_deadline(self):
        config = read_config(ROOT / "configs/ca_baseline.json")
        for field, value in (("width", 0), ("rules", [256]), ("seeds", [1, 1]),
                             ("steps", 99999), ("width", True)):
            bad = {**config, field: value}
            with self.assertRaises(ValueError):
                ca_trial.compute(bad)
        with self.assertRaises(TimeoutError):
            ca_trial.compute(config, deadline=time.monotonic() - 1)


class TestRunArtifacts(unittest.TestCase):
    def test_unique_artifacts_include_provenance(self):
        with tempfile.TemporaryDirectory() as directory:
            first = save_run({"x": 1}, {"status": "test"}, directory)
            second = save_run({"x": 1}, {"status": "test"}, directory)
            self.assertNotEqual(first, second)
            manifest = json.loads((first / "manifest.json").read_text())
            self.assertIn("ca.py", manifest["source_sha256"])
            self.assertEqual(json.loads((first / "config.json").read_text()), {"x": 1})

    def test_oversized_artifact_is_rejected_before_writing(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                save_run({}, {"lots": "a" * 1000}, directory, max_bytes=10)
            self.assertFalse(list(Path(directory).iterdir()))


class TestSession(unittest.TestCase):
    def setup_session(self, directory, policy="1-guided.json"):
        decision = {"schema_version": 1, "status": "approved", "decision_maker": "Finn",
                    "policy_id": "guided" if policy.startswith("1") else "bounded",
                    "question": "Synthetic unit-test decision, not a real approval",
                    "prediction": "Synthetic test", "what_would_change_my_mind": "Synthetic test",
                    "allowed_configs": ["configs/ca_baseline.json"]}
        decision_path = Path(directory) / "decision.json"
        decision_path.write_text(json.dumps(decision))
        state_path = Path(directory) / "session.json"
        session.start(ROOT / "policies" / policy, decision_path, state_path)
        return state_path

    def test_pending_human_decision_blocks_start(self):
        with tempfile.TemporaryDirectory() as directory, self.assertRaises(ValueError):
            session.start(ROOT / "policies/1-guided.json",
                          ROOT / "decisions/session.example.json", Path(directory) / "s.json")

    def test_budget_and_recorded_artifact(self):
        with tempfile.TemporaryDirectory() as directory:
            state = self.setup_session(directory)
            with patch("research.ca_trial.compute", return_value={"status": "test_result"}):
                path = session.run(state, ROOT / "configs/ca_baseline.json", Path(directory) / "runs")
            self.assertTrue((path / "results.json").exists())
            saved = json.loads(state.read_text())
            self.assertEqual(saved["status"], "awaiting_Finn")
            self.assertGreater(saved["output_bytes"], 0)
            with self.assertRaises(ValueError):
                session.run(state, ROOT / "configs/ca_baseline.json")

    def test_unlisted_config_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            state = self.setup_session(directory)
            with self.assertRaises(ValueError):
                session.run(state, ROOT / "configs/ca_boundary.json")

    def test_changed_config_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            state = self.setup_session(directory)
            saved = json.loads(state.read_text())
            saved["allowed"][str(ROOT / "configs/ca_baseline.json")] = "bad-sha"
            state.write_text(json.dumps(saved))
            with self.assertRaises(ValueError):
                session.run(state, ROOT / "configs/ca_baseline.json")

    def test_error_stops_session_and_consumes_attempt(self):
        with tempfile.TemporaryDirectory() as directory:
            state = self.setup_session(directory, "2-bounded.json")
            with patch("research.ca_trial.compute", side_effect=TimeoutError("test")):
                with self.assertRaises(TimeoutError):
                    session.run(state, ROOT / "configs/ca_baseline.json")
            saved = json.loads(state.read_text())
            self.assertEqual(saved["status"], "awaiting_Finn")
            self.assertEqual(len(saved["runs"]), 1)
            self.assertEqual(saved["runs"][0]["status"], "failed")

    def test_exhausted_time_and_output_block_run(self):
        for field, amount in (("wall_seconds", 600), ("output_bytes", 8_388_608)):
            with tempfile.TemporaryDirectory() as directory:
                state = self.setup_session(directory)
                saved = json.loads(state.read_text())
                saved[field] = amount
                state.write_text(json.dumps(saved))
                with self.assertRaises(ValueError):
                    session.run(state, ROOT / "configs/ca_baseline.json")

    def test_running_session_blocks_parallel_claim(self):
        with tempfile.TemporaryDirectory() as directory:
            state = self.setup_session(directory)
            saved = json.loads(state.read_text())
            saved["status"] = "running"
            state.write_text(json.dumps(saved))
            with self.assertRaises(ValueError):
                session.run(state, ROOT / "configs/ca_baseline.json")


class TestNeuralPlan(unittest.TestCase):
    def setUp(self):
        self.config = read_config(ROOT / "configs/neural_ioi.json")

    def test_fixed_revision_and_disjoint_splits(self):
        neural.validate(self.config)
        development = neural.prompts(self.config, "development")
        held_out = neural.prompts(self.config, "held_out")
        self.assertEqual(len(development), 8)
        self.assertEqual(len(held_out), 8)
        self.assertFalse({x["clean"] for x in development} & {x["clean"] for x in held_out})
        for prompt in development + held_out:
            self.assertNotEqual(prompt["clean"], prompt["corrupt"])
            self.assertNotEqual(prompt["clean_answer"], prompt["corrupt_answer"])

    def test_metric_does_not_hide_overshoot_or_invalid_denominator(self):
        self.assertEqual(neural.recovery(3, -1, 5), 1.5)
        self.assertIsNone(neural.recovery(1, 1, 3))
        self.assertIsNone(neural.recovery(-1, 2, 3))

    def test_unpinned_revision_is_rejected(self):
        self.config["model_revision"] = "main"
        with self.assertRaises(ValueError):
            neural.validate(self.config)

    def test_guided_subset_supported_and_final_layer_excluded(self):
        self.config["candidate_layers"] = [5]
        neural.validate(self.config)
        self.config["candidate_layers"] = [11]
        with self.assertRaises(ValueError):
            neural.validate(self.config)

    def test_held_out_overlap_is_rejected(self):
        self.config["held_out"]["name_pairs"] = [["John", "Bob"]]
        with self.assertRaises(ValueError):
            neural.validate(self.config)

    def test_model_download_is_opt_in(self):
        with self.assertRaises(ValueError):
            neural.fetch(self.config)

    def test_missing_local_checkpoint_fails_before_heavy_imports(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch("research.neural.model_dir", return_value=Path(directory)):
                with self.assertRaises(FileNotFoundError):
                    neural.compute(self.config)

    def test_confirmation_needs_a_real_recorded_selection(self):
        selection = read_config(ROOT / "decisions/neural_layer.example.json")
        with self.assertRaises(ValueError):
            neural.validate_selection(selection, self.config, {}, "unused")

    def test_confirmation_tied_to_successful_unchanged_development(self):
        selection = {"status": "approved", "decision_maker": "Finn", "layer": 4,
                     "reason": "Synthetic test, not a human decision",
                     "development_results_sha256": "abc"}
        development = {"status": "development_complete",
                       "config_sha256": digest(json.dumps(self.config, sort_keys=True).encode()),
                       "protocol_sha256": neural.protocol_hash()}
        neural.validate_selection(selection, self.config, development, "abc")
        for key, value in (("status", "baseline_failed"), ("protocol_sha256", "changed"),
                           ("config_sha256", "changed")):
            with self.assertRaises(ValueError):
                neural.validate_selection(selection, self.config, {**development, key: value}, "abc")
        with self.assertRaises(ValueError):
            neural.validate_selection(selection, self.config, development, "different-result")


class TestHookLifetime(unittest.TestCase):
    class Module:
        def __init__(self, fail=False):
            self.fail, self.active = fail, 0

        def register_forward_hook(self, hook):
            if self.fail:
                raise RuntimeError("synthetic registration failure")
            self.active += 1
            module = self
            class Handle:
                def remove(self):
                    module.active -= 1
            return Handle()

    def test_cleanup_after_forward_failure(self):
        module = self.Module()
        with self.assertRaises(RuntimeError):
            with temporary_hooks([(module, None)]):
                self.assertEqual(module.active, 1)
                raise RuntimeError("synthetic forward failure")
        self.assertEqual(module.active, 0)

    def test_cleanup_after_partial_registration(self):
        module = self.Module()
        with self.assertRaises(RuntimeError):
            with temporary_hooks([(module, None), (self.Module(fail=True), None)]):
                pass
        self.assertEqual(module.active, 0)


@unittest.skipUnless(importlib.util.find_spec("torch") and importlib.util.find_spec("transformers"),
                     "Optional neural dependencies absent; no downloads are made")
class TestOptionalRealHooks(unittest.TestCase):
    def test_tiny_random_gpt2_positive_and_identity_controls(self):
        import torch
        from transformers import GPT2Config, GPT2LMHeadModel
        torch.manual_seed(0)
        model = GPT2LMHeadModel(GPT2Config(vocab_size=32, n_positions=16, n_embd=16,
                                         n_layer=2, n_head=2)).eval()
        clean, corrupt = torch.tensor([[1, 2, 3, 4]]), torch.tensor([[1, 2, 7, 4]])
        cache = {}
        def capture(module, inputs, output):
            from research.hooks import hidden_output
            cache["vector"] = hidden_output(output)[:, -1, :].clone()
        with torch.inference_mode():
            with temporary_hooks([(model.transformer.h[-1], capture)]):
                clean_logits = model(clean, use_cache=False).logits[0, -1]
            vector = cache["vector"].clone()
            with temporary_hooks([(model.transformer.h[-1], last_token_patch(vector))]):
                patched_logits = model(corrupt, use_cache=False).logits[0, -1]
            torch.testing.assert_close(clean_logits, patched_logits, atol=1e-6, rtol=1e-5)
            with temporary_hooks([(model.transformer.h[-1], capture)]):
                corrupt_logits = model(corrupt, use_cache=False).logits[0, -1]
            with temporary_hooks([(model.transformer.h[-1], last_token_patch(cache["vector"]))]):
                identity_logits = model(corrupt, use_cache=False).logits[0, -1]
            torch.testing.assert_close(corrupt_logits, identity_logits)
        self.assertEqual(len(model.transformer.h[-1]._forward_hooks), 0)


if __name__ == "__main__":
    unittest.main()
