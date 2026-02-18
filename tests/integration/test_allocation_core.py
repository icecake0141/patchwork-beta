# SPDX-License-Identifier: Apache-2.0
# This file was created or modified with the assistance of an AI (Large Language Model). Review for correctness and security.  # noqa: E501

import unittest

from patchwork import (
    LC_BREAKOUT_MODULE,
    MPO_PASS_THROUGH_MODULE,
    UTP_MODULE,
    allocate_project,
    export_session_table_csv,
    render_svgs,
)


class TestAllocationCore(unittest.TestCase):
    def setUp(self) -> None:
        self.project = {
            "racks": [{"id": "R01"}, {"id": "R02"}, {"id": "R03"}],
            "demands": [
                {
                    "id": "D01",
                    "src": "R01",
                    "dst": "R02",
                    "endpoint_type": "mpo12",
                    "count": 1,
                },
                {
                    "id": "D02",
                    "src": "R01",
                    "dst": "R02",
                    "endpoint_type": "mmf_lc_duplex",
                    "count": 2,
                },
                {
                    "id": "D03",
                    "src": "R01",
                    "dst": "R03",
                    "endpoint_type": "utp_rj45",
                    "count": 1,
                },
            ],
        }

    def test_allocation_deterministic_and_slots(self) -> None:
        result = allocate_project(self.project)
        second_result = allocate_project(self.project)
        self.assertEqual(result.sessions, second_result.sessions)

        r01_modules = [module for module in result.modules if module.rack_id == "R01"]
        r01_modules = sorted(r01_modules, key=lambda module: (module.panel_u, module.slot))
        self.assertEqual(
            [module.module_type for module in r01_modules[:3]],
            [MPO_PASS_THROUGH_MODULE, LC_BREAKOUT_MODULE, UTP_MODULE],
        )
        self.assertEqual(
            [(module.panel_u, module.slot) for module in r01_modules[:3]],
            [(1, 1), (1, 2), (1, 3)],
        )

    def test_session_export_and_alignment(self) -> None:
        result = allocate_project(self.project)
        mpo_sessions = [session for session in result.sessions if session.media == "mpo12"]
        lc_sessions = [session for session in result.sessions if session.media == "mmf_lc_duplex"]
        for session in mpo_sessions + lc_sessions:
            self.assertEqual(session.src_port, session.dst_port)

        csv_output = export_session_table_csv(project_id="proj-1", sessions=result.sessions)
        header = csv_output.splitlines()[0].split(",")
        self.assertEqual(header[0], "project_id")
        self.assertIn("label_a", header)
        self.assertIn("label_b", header)
        self.assertIn("proj-1", csv_output)

    def test_svg_output_structure(self) -> None:
        result = allocate_project(self.project)
        svgs = render_svgs(result)
        self.assertIn("topology", svgs)
        self.assertIn("rack_panels", svgs)
        self.assertIn("pair_detail", svgs)
        self.assertIn('data-kind="topology"', svgs["topology"])
        rack_panels = svgs["rack_panels"]
        assert isinstance(rack_panels, dict)
        for rack_svg in rack_panels.values():
            self.assertIn("<svg", rack_svg)
            self.assertIn('data-kind="rack-panels"', rack_svg)
        pair_detail = svgs["pair_detail"]
        assert isinstance(pair_detail, dict)
        for pair_svg in pair_detail.values():
            self.assertIn("<svg", pair_svg)
            self.assertIn('data-kind="pair-detail"', pair_svg)


if __name__ == "__main__":
    unittest.main()
