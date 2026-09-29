import unittest

import ca


class TestCA(unittest.TestCase):
    def test_rule_table(self):
        self.assertEqual(ca.rule_table(30), [0, 1, 1, 1, 1, 0, 0, 0])
        with self.assertRaises(ValueError):
            ca.rule_table(256)

    def test_rule_90_is_sierpinski(self):
        rows = ca.evolve(90, 33, 4)
        self.assertEqual([sum(r) for r in rows], [1, 2, 2, 4, 2])

    def test_rule_30_first_rows(self):
        rows = ca.evolve(30, 9, 2)
        self.assertEqual(rows[1], [0, 0, 0, 1, 1, 1, 0, 0, 0])
        self.assertEqual(rows[2], [0, 0, 1, 1, 0, 0, 1, 0, 0])

    def test_wraparound(self):
        self.assertEqual(ca.step([1, 0, 0], ca.rule_table(2)), [0, 0, 1])

    def test_symmetries(self):
        self.assertEqual(ca.equivalents(110), [110, 124, 137, 193])
        self.assertEqual(ca.equivalents(30), [30, 86, 135, 149])
        for r in range(256):
            self.assertEqual(ca.mirror(ca.mirror(r)), r)
            self.assertEqual(ca.complement(ca.complement(r)), r)

    def test_88_classes(self):
        self.assertEqual(len(ca.canonical_rules()), 88)

    def test_mirror_evolution_matches(self):
        a = ca.evolve(110, 21, 10)
        b = ca.evolve(ca.mirror(110), 21, 10)
        self.assertEqual([r[::-1] for r in a], b)

    def test_survey_orders_trivial_last(self):
        ranked = ca.survey(width=64, steps=100)
        self.assertEqual(ranked[-1][1], 0)
        self.assertGreater(ranked[0][0], 0.5)


if __name__ == "__main__":
    unittest.main()
