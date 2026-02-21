# SPDX-License-Identifier: Apache-2.0
# This file was created or modified with the assistance of an AI (Large Language Model). Review for correctness and security.  # noqa: E501

import unittest

from patchwork import allocate_project, deterministic_id, natural_sort_key


class TestDeterministicHelpers(unittest.TestCase):
    def test_natural_sort_key_trailing_digits(self) -> None:
        values = ["R10", "R2", "R1", "RackA"]
        sorted_values = sorted(values, key=natural_sort_key)
        self.assertEqual(sorted_values, ["R1", "R2", "R10", "RackA"])

    def test_deterministic_id_stability(self) -> None:
        canonical = "media|R01|1|1|1|R02|1|1|1|cable|"
        self.assertEqual(deterministic_id(canonical), deterministic_id(canonical))
        self.assertNotEqual(deterministic_id(canonical), deterministic_id(canonical + "x"))


class TestInputValidation(unittest.TestCase):
    def _base_project(self, endpoint_type: str = "mpo12", count: int = 1) -> dict:
        return {
            "racks": [{"id": "R01"}, {"id": "R02"}],
            "demands": [
                {
                    "id": "D01",
                    "src": "R01",
                    "dst": "R02",
                    "endpoint_type": endpoint_type,
                    "count": count,
                }
            ],
        }

    def test_unknown_endpoint_type_raises(self) -> None:
        with self.assertRaises(ValueError):
            allocate_project(self._base_project(endpoint_type="fiber_100g"))

    def test_count_zero_raises(self) -> None:
        with self.assertRaises(ValueError):
            allocate_project(self._base_project(count=0))

    def test_count_negative_raises(self) -> None:
        with self.assertRaises(ValueError):
            allocate_project(self._base_project(count=-1))

    def test_all_known_endpoint_types_accepted(self) -> None:
        for ep_type in ("mpo12", "mmf_lc_duplex", "smf_lc_duplex", "utp_rj45"):
            result = allocate_project(self._base_project(endpoint_type=ep_type))
            self.assertEqual(len(result.sessions), 1)

    def test_duplicate_rack_ids_raises(self) -> None:
        project = {
            "racks": [{"id": "R01"}, {"id": "R01"}],
            "demands": [],
        }
        with self.assertRaises(ValueError):
            allocate_project(project)

    def test_src_equals_dst_raises(self) -> None:
        project = {
            "racks": [{"id": "R01"}, {"id": "R02"}],
            "demands": [
                {"id": "D01", "src": "R01", "dst": "R01", "endpoint_type": "mpo12", "count": 1}
            ],
        }
        with self.assertRaises(ValueError):
            allocate_project(project)

    def test_demand_references_unknown_rack_raises(self) -> None:
        project = {
            "racks": [{"id": "R01"}, {"id": "R02"}],
            "demands": [
                {"id": "D01", "src": "R01", "dst": "R99", "endpoint_type": "mpo12", "count": 1}
            ],
        }
        with self.assertRaises(ValueError):
            allocate_project(project)


if __name__ == "__main__":
    unittest.main()
