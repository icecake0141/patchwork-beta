# SPDX-License-Identifier: Apache-2.0
# This file was created or modified with the assistance of an AI (Large Language Model). Review for correctness and security.  # noqa: E501

import unittest

from patchwork import deterministic_id, natural_sort_key


class TestDeterministicHelpers(unittest.TestCase):
    def test_natural_sort_key_trailing_digits(self) -> None:
        values = ["R10", "R2", "R1", "RackA"]
        sorted_values = sorted(values, key=natural_sort_key)
        self.assertEqual(sorted_values, ["R1", "R2", "R10", "RackA"])

    def test_deterministic_id_stability(self) -> None:
        canonical = "media|R01|1|1|1|R02|1|1|1|cable|"
        self.assertEqual(deterministic_id(canonical), deterministic_id(canonical))
        self.assertNotEqual(deterministic_id(canonical), deterministic_id(canonical + "x"))


if __name__ == "__main__":
    unittest.main()
