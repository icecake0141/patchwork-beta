# SPDX-License-Identifier: Apache-2.0
# This file was created or modified with the assistance of an AI (Large Language Model). Review for correctness and security.  # noqa: E501

import unittest

from patchwork import (
    LC_BREAKOUT_MODULE,
    MPO_PASS_THROUGH_MODULE,
    UTP_MODULE,
    allocate_project,
)


class TestSpecAcceptance(unittest.TestCase):
    def test_lc_breakout_scaling(self) -> None:
        project = {
            "racks": [{"id": "R01"}, {"id": "R02"}],
            "demands": [
                {
                    "id": "D001",
                    "src": "R01",
                    "dst": "R02",
                    "endpoint_type": "mmf_lc_duplex",
                    "count": 13,
                }
            ],
        }
        result = allocate_project(project)
        modules = [
            module
            for module in result.modules
            if module.module_type == LC_BREAKOUT_MODULE and module.fiber_kind == "mmf"
        ]
        by_rack = {rack: [m for m in modules if m.rack_id == rack] for rack in ("R01", "R02")}
        self.assertEqual(len(by_rack["R01"]), 2)
        self.assertEqual(len(by_rack["R02"]), 2)
        lc_sessions = [session for session in result.sessions if session.media == "mmf_lc_duplex"]
        self.assertEqual(len(lc_sessions), 13)

        r01_modules = sorted(by_rack["R01"], key=lambda module: (module.panel_u, module.slot))
        first_ports = sorted(
            session.src_port
            for session in lc_sessions
            if session.src_u == r01_modules[0].panel_u and session.src_slot == r01_modules[0].slot
        )
        second_ports = sorted(
            session.src_port
            for session in lc_sessions
            if session.src_u == r01_modules[1].panel_u and session.src_slot == r01_modules[1].slot
        )
        self.assertEqual(first_ports, list(range(1, 13)))
        self.assertEqual(second_ports, [1])

        mmf_trunks = [
            cable
            for cable in result.cables
            if cable.cable_type == "mpo12_trunk" and cable.fiber_kind == "mmf"
        ]
        self.assertEqual(len(mmf_trunks), 4)

    def test_mpo_e2e_slot_capacity(self) -> None:
        project = {
            "racks": [{"id": "R01"}, {"id": "R02"}],
            "demands": [
                {"id": "D002", "src": "R01", "dst": "R02", "endpoint_type": "mpo12", "count": 14}
            ],
        }
        result = allocate_project(project)
        mpo_modules = [
            module for module in result.modules if module.module_type == MPO_PASS_THROUGH_MODULE
        ]
        self.assertEqual(len([m for m in mpo_modules if m.rack_id == "R01"]), 2)
        self.assertEqual(len([m for m in mpo_modules if m.rack_id == "R02"]), 2)

        mpo_sessions = [session for session in result.sessions if session.media == "mpo12"]
        self.assertEqual(len(mpo_sessions), 14)
        r01_modules = sorted(
            [module for module in mpo_modules if module.rack_id == "R01"],
            key=lambda module: (module.panel_u, module.slot),
        )
        first_ports = sorted(
            session.src_port
            for session in mpo_sessions
            if session.src_u == r01_modules[0].panel_u and session.src_slot == r01_modules[0].slot
        )
        second_ports = sorted(
            session.src_port
            for session in mpo_sessions
            if session.src_u == r01_modules[1].panel_u and session.src_slot == r01_modules[1].slot
        )
        self.assertEqual(first_ports, list(range(1, 13)))
        self.assertEqual(second_ports, [1, 2])

        trunks = [cable for cable in result.cables if cable.cable_type == "mpo12_trunk"]
        self.assertEqual(len(trunks), 14)
        for session in mpo_sessions:
            self.assertEqual(session.src_port, session.dst_port)

    def test_utp_grouping_tail_sharing(self) -> None:
        project = {
            "racks": [{"id": "R01"}, {"id": "R02"}, {"id": "R03"}],
            "demands": [
                {"id": "D003", "src": "R01", "dst": "R02", "endpoint_type": "utp_rj45", "count": 7},
                {"id": "D004", "src": "R01", "dst": "R03", "endpoint_type": "utp_rj45", "count": 2},
            ],
        }
        result = allocate_project(project)
        r01_modules = sorted(
            [
                module
                for module in result.modules
                if module.rack_id == "R01" and module.module_type == UTP_MODULE
            ],
            key=lambda module: (module.panel_u, module.slot),
        )
        self.assertEqual(len(r01_modules), 2)
        module_one, module_two = r01_modules

        r02_ports_module_one = sorted(
            session.src_port
            for session in result.sessions
            if session.media == "utp_rj45"
            and session.dst_rack == "R02"
            and session.src_u == module_one.panel_u
            and session.src_slot == module_one.slot
        )
        self.assertEqual(r02_ports_module_one, [1, 2, 3, 4, 5, 6])

        r02_ports_module_two = sorted(
            session.src_port
            for session in result.sessions
            if session.media == "utp_rj45"
            and session.dst_rack == "R02"
            and session.src_u == module_two.panel_u
            and session.src_slot == module_two.slot
        )
        r03_ports_module_two = sorted(
            session.src_port
            for session in result.sessions
            if session.media == "utp_rj45"
            and session.dst_rack == "R03"
            and session.src_u == module_two.panel_u
            and session.src_slot == module_two.slot
        )
        self.assertEqual(r02_ports_module_two, [1])
        self.assertEqual(r03_ports_module_two, [2, 3])

    def test_mixed_in_u_behavior(self) -> None:
        project = {
            "racks": [{"id": "R01"}, {"id": "R02"}],
            "demands": [
                {
                    "id": "D005",
                    "src": "R01",
                    "dst": "R02",
                    "endpoint_type": "mpo12",
                    "count": 36,
                },
                {
                    "id": "D006",
                    "src": "R01",
                    "dst": "R02",
                    "endpoint_type": "mmf_lc_duplex",
                    "count": 1,
                },
            ],
        }
        result = allocate_project(project)
        r01_modules = sorted(
            [module for module in result.modules if module.rack_id == "R01"],
            key=lambda module: (module.panel_u, module.slot),
        )
        self.assertEqual(
            [module.module_type for module in r01_modules[:4]],
            [
                MPO_PASS_THROUGH_MODULE,
                MPO_PASS_THROUGH_MODULE,
                MPO_PASS_THROUGH_MODULE,
                LC_BREAKOUT_MODULE,
            ],
        )
        self.assertEqual(
            [(module.panel_u, module.slot) for module in r01_modules[:4]],
            [(1, 1), (1, 2), (1, 3), (1, 4)],
        )

    def test_utp_tail_module_exact_fill(self) -> None:
        """Covers the open_module reset when fill brings used count to exactly 6 (line 382)."""
        project = {
            "racks": [{"id": "R01"}, {"id": "R02"}, {"id": "R03"}],
            "demands": [
                {"id": "D007", "src": "R01", "dst": "R02", "endpoint_type": "utp_rj45", "count": 4},
                {"id": "D008", "src": "R01", "dst": "R03", "endpoint_type": "utp_rj45", "count": 2},
            ],
        }
        result = allocate_project(project)
        r01_modules = sorted(
            [
                module
                for module in result.modules
                if module.rack_id == "R01" and module.module_type == UTP_MODULE
            ],
            key=lambda module: (module.panel_u, module.slot),
        )
        # R01 should share a single module between R02 (ports 1-4) and R03 (ports 5-6)
        self.assertEqual(len(r01_modules), 1)
        r02_ports = sorted(
            session.src_port
            for session in result.sessions
            if session.media == "utp_rj45"
            and session.dst_rack == "R02"
            and session.src_u == r01_modules[0].panel_u
            and session.src_slot == r01_modules[0].slot
        )
        r03_ports = sorted(
            session.src_port
            for session in result.sessions
            if session.media == "utp_rj45"
            and session.dst_rack == "R03"
            and session.src_u == r01_modules[0].panel_u
            and session.src_slot == r01_modules[0].slot
        )
        self.assertEqual(r02_ports, [1, 2, 3, 4])
        self.assertEqual(r03_ports, [5, 6])


if __name__ == "__main__":
    unittest.main()
