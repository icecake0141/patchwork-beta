# SPDX-License-Identifier: Apache-2.0
# This file was created or modified with the assistance of an AI (Large Language Model). Review for correctness and security.  # noqa: E501

from __future__ import annotations

import csv
import hashlib
import html
import io
import math
import re
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

SLOTS_PER_U_DEFAULT = 4
DEFAULT_ID_LENGTH = 32

LC_BREAKOUT_MODULE = "lc_breakout_2xmpo12_to_12xlcduplex"
UTP_MODULE = "utp_6xrj45"
MPO_PASS_THROUGH_MODULE = "mpo12_pass_through_12port"


@dataclass(frozen=True)
class Panel:
    rack_id: str
    u: int
    slots_per_u: int


@dataclass(frozen=True)
class Module:
    rack_id: str
    panel_u: int
    slot: int
    module_type: str
    fiber_kind: str | None
    polarity_variant: str | None
    peer_rack_id: str | None
    dedicated: bool


@dataclass(frozen=True)
class Cable:
    cable_id: str
    cable_type: str
    fiber_kind: str | None
    polarity_type: str | None
    src_rack: str
    dst_rack: str


@dataclass(frozen=True)
class Session:
    session_id: str
    media: str
    cable_id: str
    adapter_type: str
    label_a: str
    label_b: str
    src_rack: str
    src_face: str
    src_u: int
    src_slot: int
    src_port: int
    dst_rack: str
    dst_face: str
    dst_u: int
    dst_slot: int
    dst_port: int
    fiber_a: int | None
    fiber_b: int | None
    notes: str | None = None


@dataclass(frozen=True)
class AllocationResult:
    panels: list[Panel]
    modules: list[Module]
    cables: list[Cable]
    sessions: list[Session]


@dataclass
class _SlotCursor:
    slots_per_u: int = SLOTS_PER_U_DEFAULT
    index: int = 0

    def next_slot(self) -> tuple[int, int]:
        u = self.index // self.slots_per_u + 1
        slot = self.index % self.slots_per_u + 1
        self.index += 1
        return u, slot


def natural_sort_key(value: str) -> tuple[str, int, int, str]:
    match = re.match(r"^(.*?)(\d+)$", value)
    if match:
        prefix, digits = match.groups()
        return (prefix, 0, int(digits), value)
    return (value, 1, 0, value)


def deterministic_id(canonical: str, length: int = DEFAULT_ID_LENGTH) -> str:
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:length]


def allocate_project(project: dict[str, Any]) -> AllocationResult:
    racks = [rack["id"] for rack in project.get("racks", [])]
    rack_set = set(racks)
    if len(rack_set) != len(racks):
        raise ValueError("rack ids must be unique")
    demands = project.get("demands", [])
    pair_demands: dict[tuple[str, str], dict[str, int]] = {}
    for demand in demands:
        src = demand["src"]
        dst = demand["dst"]
        if src == dst:
            raise ValueError("src and dst must differ")
        if src not in rack_set or dst not in rack_set:
            raise ValueError("demand racks must exist")
        count = int(demand["count"])
        media = demand["endpoint_type"]
        pair = tuple(sorted((src, dst), key=natural_sort_key))
        pair_demands.setdefault(pair, {})
        pair_demands[pair][media] = pair_demands[pair].get(media, 0) + count

    slot_cursors = {rack_id: _SlotCursor() for rack_id in racks}
    modules: list[Module] = []
    sessions: list[Session] = []
    cables: list[Cable] = []

    def add_session(
        *,
        media: str,
        cable_id: str,
        adapter_type: str,
        src_rack: str,
        src_u: int,
        src_slot: int,
        src_port: int,
        dst_rack: str,
        dst_u: int,
        dst_slot: int,
        dst_port: int,
        fiber_a: int | None = None,
        fiber_b: int | None = None,
    ) -> None:
        label_a = f"{src_rack}U{src_u}S{src_slot}P{src_port}"
        label_b = f"{dst_rack}U{dst_u}S{dst_slot}P{dst_port}"
        fiber_pair = "" if fiber_a is None else f"{fiber_a}-{fiber_b}"
        canonical = "|".join(
            [
                media,
                src_rack,
                str(src_u),
                str(src_slot),
                str(src_port),
                dst_rack,
                str(dst_u),
                str(dst_slot),
                str(dst_port),
                cable_id,
                fiber_pair,
            ]
        )
        session_id = deterministic_id(canonical)
        sessions.append(
            Session(
                session_id=session_id,
                media=media,
                cable_id=cable_id,
                adapter_type=adapter_type,
                label_a=label_a,
                label_b=label_b,
                src_rack=src_rack,
                src_face="front",
                src_u=src_u,
                src_slot=src_slot,
                src_port=src_port,
                dst_rack=dst_rack,
                dst_face="front",
                dst_u=dst_u,
                dst_slot=dst_slot,
                dst_port=dst_port,
                fiber_a=fiber_a,
                fiber_b=fiber_b,
            )
        )

    def add_cable(
        *,
        canonical: str,
        cable_type: str,
        fiber_kind: str | None,
        polarity_type: str | None,
        src_rack: str,
        dst_rack: str,
    ) -> str:
        cable_id = deterministic_id(canonical)
        cables.append(
            Cable(
                cable_id=cable_id,
                cable_type=cable_type,
                fiber_kind=fiber_kind,
                polarity_type=polarity_type,
                src_rack=src_rack,
                dst_rack=dst_rack,
            )
        )
        return cable_id

    pair_list = sorted(
        pair_demands.keys(),
        key=lambda pair: (natural_sort_key(pair[0]), natural_sort_key(pair[1])),
    )

    for pair in pair_list:
        count = pair_demands[pair].get("mpo12", 0)
        if count <= 0:
            continue
        slots_needed = math.ceil(count / 12)
        remaining = count
        for slot_index in range(1, slots_needed + 1):
            src_rack, dst_rack = pair
            src_u, src_slot = slot_cursors[src_rack].next_slot()
            dst_u, dst_slot = slot_cursors[dst_rack].next_slot()
            modules.append(
                Module(
                    rack_id=src_rack,
                    panel_u=src_u,
                    slot=src_slot,
                    module_type=MPO_PASS_THROUGH_MODULE,
                    fiber_kind=None,
                    polarity_variant="A",
                    peer_rack_id=dst_rack,
                    dedicated=True,
                )
            )
            modules.append(
                Module(
                    rack_id=dst_rack,
                    panel_u=dst_u,
                    slot=dst_slot,
                    module_type=MPO_PASS_THROUGH_MODULE,
                    fiber_kind=None,
                    polarity_variant="A",
                    peer_rack_id=src_rack,
                    dedicated=True,
                )
            )
            ports_this_slot = min(12, remaining)
            for port in range(1, ports_this_slot + 1):
                cable_id = add_cable(
                    canonical=f"mpo12|{src_rack}|{dst_rack}|slot{slot_index}|port{port}",
                    cable_type="mpo12_trunk",
                    fiber_kind=None,
                    polarity_type="B",
                    src_rack=src_rack,
                    dst_rack=dst_rack,
                )
                add_session(
                    media="mpo12",
                    cable_id=cable_id,
                    adapter_type=MPO_PASS_THROUGH_MODULE,
                    src_rack=src_rack,
                    src_u=src_u,
                    src_slot=src_slot,
                    src_port=port,
                    dst_rack=dst_rack,
                    dst_u=dst_u,
                    dst_slot=dst_slot,
                    dst_port=port,
                )
            remaining -= ports_this_slot

    fiber_media = {"mmf": "mmf_lc_duplex", "smf": "smf_lc_duplex"}
    fiber_pairs = [(1, 2), (3, 4), (5, 6), (7, 8), (9, 10), (11, 12)]
    for fiber_kind in ("mmf", "smf"):
        media = fiber_media[fiber_kind]
        for pair in pair_list:
            count = pair_demands[pair].get(media, 0)
            if count <= 0:
                continue
            modules_needed = math.ceil(count / 12)
            remaining = count
            for module_index in range(1, modules_needed + 1):
                src_rack, dst_rack = pair
                src_u, src_slot = slot_cursors[src_rack].next_slot()
                dst_u, dst_slot = slot_cursors[dst_rack].next_slot()
                modules.append(
                    Module(
                        rack_id=src_rack,
                        panel_u=src_u,
                        slot=src_slot,
                        module_type=LC_BREAKOUT_MODULE,
                        fiber_kind=fiber_kind,
                        polarity_variant="AF",
                        peer_rack_id=dst_rack,
                        dedicated=True,
                    )
                )
                modules.append(
                    Module(
                        rack_id=dst_rack,
                        panel_u=dst_u,
                        slot=dst_slot,
                        module_type=LC_BREAKOUT_MODULE,
                        fiber_kind=fiber_kind,
                        polarity_variant="AF",
                        peer_rack_id=src_rack,
                        dedicated=True,
                    )
                )
                cable_ids = {}
                for mpo_port in (1, 2):
                    cable_ids[mpo_port] = add_cable(
                        canonical=(
                            f"lc_trunk|{fiber_kind}|{src_rack}|{dst_rack}|module{module_index}|mpo{mpo_port}"
                        ),
                        cable_type="mpo12_trunk",
                        fiber_kind=fiber_kind,
                        polarity_type="A",
                        src_rack=src_rack,
                        dst_rack=dst_rack,
                    )
                ports_this_module = min(12, remaining)
                for port in range(1, ports_this_module + 1):
                    mpo_port = 1 if port <= 6 else 2
                    fiber_index = port - 1 if port <= 6 else port - 7
                    fiber_a, fiber_b = fiber_pairs[fiber_index]
                    add_session(
                        media=media,
                        cable_id=cable_ids[mpo_port],
                        adapter_type=LC_BREAKOUT_MODULE,
                        src_rack=src_rack,
                        src_u=src_u,
                        src_slot=src_slot,
                        src_port=port,
                        dst_rack=dst_rack,
                        dst_u=dst_u,
                        dst_slot=dst_slot,
                        dst_port=port,
                        fiber_a=fiber_a,
                        fiber_b=fiber_b,
                    )
                remaining -= ports_this_module

    utp_peer_counts: dict[str, dict[str, int]] = {rack_id: {} for rack_id in racks}
    for pair in pair_list:
        count = pair_demands[pair].get("utp_rj45", 0)
        if count <= 0:
            continue
        src_rack, dst_rack = pair
        utp_peer_counts[src_rack][dst_rack] = utp_peer_counts[src_rack].get(dst_rack, 0) + count
        utp_peer_counts[dst_rack][src_rack] = utp_peer_counts[dst_rack].get(src_rack, 0) + count

    utp_port_map: dict[tuple[str, str], list[tuple[int, int, int]]] = {}
    for rack_id, peers in utp_peer_counts.items():
        open_module: dict[str, int] | None = None
        for peer_rack in sorted(peers.keys(), key=natural_sort_key):
            remaining = peers[peer_rack]
            if open_module and open_module["used"] < 6 and remaining > 0:
                available = 6 - open_module["used"]
                fill = min(remaining, available)
                for _ in range(fill):
                    port = open_module["used"] + 1
                    utp_port_map.setdefault((rack_id, peer_rack), []).append(
                        (open_module["u"], open_module["slot"], port)
                    )
                    open_module["used"] += 1
                remaining -= fill
                if open_module["used"] == 6:
                    open_module = None
            while remaining >= 6:
                u, slot = slot_cursors[rack_id].next_slot()
                modules.append(
                    Module(
                        rack_id=rack_id,
                        panel_u=u,
                        slot=slot,
                        module_type=UTP_MODULE,
                        fiber_kind=None,
                        polarity_variant=None,
                        peer_rack_id=None,
                        dedicated=False,
                    )
                )
                for port in range(1, 7):
                    utp_port_map.setdefault((rack_id, peer_rack), []).append((u, slot, port))
                remaining -= 6
            if remaining > 0:
                if open_module is None:
                    u, slot = slot_cursors[rack_id].next_slot()
                    modules.append(
                        Module(
                            rack_id=rack_id,
                            panel_u=u,
                            slot=slot,
                            module_type=UTP_MODULE,
                            fiber_kind=None,
                            polarity_variant=None,
                            peer_rack_id=None,
                            dedicated=False,
                        )
                    )
                    open_module = {"u": u, "slot": slot, "used": 0}
                for _ in range(remaining):
                    port = open_module["used"] + 1
                    utp_port_map.setdefault((rack_id, peer_rack), []).append(
                        (open_module["u"], open_module["slot"], port)
                    )
                    open_module["used"] += 1

    for pair in pair_list:
        count = pair_demands[pair].get("utp_rj45", 0)
        if count <= 0:
            continue
        src_rack, dst_rack = pair
        src_ports = utp_port_map.get((src_rack, dst_rack), [])
        dst_ports = utp_port_map.get((dst_rack, src_rack), [])
        for index in range(count):
            src_u, src_slot, src_port = src_ports[index]
            dst_u, dst_slot, dst_port = dst_ports[index]
            cable_id = add_cable(
                canonical=f"utp|{src_rack}|{dst_rack}|port{index + 1}",
                cable_type="utp_cable",
                fiber_kind=None,
                polarity_type=None,
                src_rack=src_rack,
                dst_rack=dst_rack,
            )
            add_session(
                media="utp_rj45",
                cable_id=cable_id,
                adapter_type=UTP_MODULE,
                src_rack=src_rack,
                src_u=src_u,
                src_slot=src_slot,
                src_port=src_port,
                dst_rack=dst_rack,
                dst_u=dst_u,
                dst_slot=dst_slot,
                dst_port=dst_port,
            )

    panels: list[Panel] = []
    for rack_id in racks:
        max_u = max((module.panel_u for module in modules if module.rack_id == rack_id), default=0)
        panels.extend(
            Panel(rack_id=rack_id, u=u, slots_per_u=SLOTS_PER_U_DEFAULT)
            for u in range(1, max_u + 1)
        )

    return AllocationResult(panels=panels, modules=modules, cables=cables, sessions=sessions)


def export_session_table_csv(
    *,
    project_id: str,
    sessions: Iterable[Session],
    revision_id: str | None = None,
) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    header = [
        "project_id",
        "revision_id",
        "session_id",
        "media",
        "cable_id",
        "adapter_type",
        "label_a",
        "label_b",
        "src_rack",
        "src_face",
        "src_u",
        "src_slot",
        "src_port",
        "dst_rack",
        "dst_face",
        "dst_u",
        "dst_slot",
        "dst_port",
        "fiber_a",
        "fiber_b",
        "notes",
    ]
    writer.writerow(header)
    for session in sorted(sessions, key=lambda item: item.session_id):
        writer.writerow(
            [
                project_id,
                revision_id or "",
                session.session_id,
                session.media,
                session.cable_id,
                session.adapter_type,
                session.label_a,
                session.label_b,
                session.src_rack,
                session.src_face,
                session.src_u,
                session.src_slot,
                session.src_port,
                session.dst_rack,
                session.dst_face,
                session.dst_u,
                session.dst_slot,
                session.dst_port,
                "" if session.fiber_a is None else session.fiber_a,
                "" if session.fiber_b is None else session.fiber_b,
                session.notes or "",
            ]
        )
    return output.getvalue()


def render_svgs(result: AllocationResult) -> dict[str, str | dict[str, str]]:
    topology = _render_svg_root("topology", {"data-kind": "topology"}, ["Topology"])
    rack_svgs = {}
    racks = {panel.rack_id for panel in result.panels}
    for rack_id in sorted(racks, key=natural_sort_key):
        rack_svgs[rack_id] = _render_svg_root(
            "rack-panels", {"data-kind": "rack-panels", "data-rack": rack_id}, [f"Rack {rack_id}"]
        )
    pair_svgs = {}
    pairs = sorted(
        {(session.src_rack, session.dst_rack) for session in result.sessions},
        key=lambda pair: (natural_sort_key(pair[0]), natural_sort_key(pair[1])),
    )
    for rack_a, rack_b in pairs:
        key = f"{rack_a}_{rack_b}"
        pair_svgs[key] = _render_svg_root(
            "pair-detail",
            {"data-kind": "pair-detail", "data-pair": key},
            [f"Pair {rack_a}-{rack_b}"],
        )
    return {
        "topology": topology,
        "rack_panels": rack_svgs,
        "pair_detail": pair_svgs,
    }


def _render_svg_root(title: str, attributes: dict[str, str], text_lines: list[str]) -> str:
    attrs = " ".join(
        [f'{html.escape(key)}="{html.escape(value)}"' for key, value in attributes.items()]
    )
    text_markup = "".join([f"<text>{html.escape(line)}</text>" for line in text_lines])
    safe_title = html.escape(title)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" {attrs}>'
        f"<title>{safe_title}</title>{text_markup}</svg>"
    )
