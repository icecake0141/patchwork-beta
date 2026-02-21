# SPDX-License-Identifier: Apache-2.0
# This file was created or modified with the assistance of an AI (Large Language Model). Review for correctness and security.  # noqa: E501

from __future__ import annotations

import csv
import hashlib
import html
import io
import json
import math
import re
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from typing import Any

SLOTS_PER_U_DEFAULT = 4
DEFAULT_ID_LENGTH = 32

LC_BREAKOUT_MODULE = "lc_breakout_2xmpo12_to_12xlcduplex"
UTP_MODULE = "utp_6xrj45"
MPO_PASS_THROUGH_MODULE = "mpo12_pass_through_12port"

KNOWN_ENDPOINT_TYPES = frozenset({"mmf_lc_duplex", "smf_lc_duplex", "mpo12", "utp_rj45"})


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
        if count <= 0:
            raise ValueError("demand count must be a positive integer")
        media = demand["endpoint_type"]
        if media not in KNOWN_ENDPOINT_TYPES:
            raise ValueError(
                f"unknown endpoint_type {media!r}; must be one of {sorted(KNOWN_ENDPOINT_TYPES)}"
            )
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


def export_result_json(
    *,
    project_id: str,
    result: AllocationResult,
    revision_id: str | None = None,
    input_hash: str | None = None,
) -> str:
    sessions_by_media: dict[str, int] = {}
    for session in result.sessions:
        sessions_by_media[session.media] = sessions_by_media.get(session.media, 0) + 1
    cables_by_type: dict[str, int] = {}
    for cable in result.cables:
        cables_by_type[cable.cable_type] = cables_by_type.get(cable.cable_type, 0) + 1
    modules_by_type: dict[str, int] = {}
    for module in result.modules:
        modules_by_type[module.module_type] = modules_by_type.get(module.module_type, 0) + 1
    payload: dict[str, Any] = {
        "project_id": project_id,
        "revision_id": revision_id,
        "input_hash": input_hash,
        "metrics": {
            "total_sessions": len(result.sessions),
            "sessions_by_media": sessions_by_media,
            "total_cables": len(result.cables),
            "cables_by_type": cables_by_type,
            "total_modules": len(result.modules),
            "modules_by_type": modules_by_type,
            "total_panels": len(result.panels),
        },
        "panels": [asdict(panel) for panel in result.panels],
        "modules": [asdict(module) for module in result.modules],
        "cables": [asdict(cable) for cable in result.cables],
        "sessions": [asdict(session) for session in result.sessions],
        "warnings": [],
    }
    return json.dumps(payload, indent=2)


def render_svgs(result: AllocationResult) -> dict[str, str | dict[str, str]]:
    topology = _render_topology_svg(result)
    rack_svgs: dict[str, str] = {}
    racks = {panel.rack_id for panel in result.panels}
    for rack_id in sorted(racks, key=natural_sort_key):
        rack_svgs[rack_id] = _render_rack_panels_svg(rack_id, result)
    pair_svgs: dict[str, str] = {}
    pairs = sorted(
        {(session.src_rack, session.dst_rack) for session in result.sessions},
        key=lambda pair: (natural_sort_key(pair[0]), natural_sort_key(pair[1])),
    )
    for rack_a, rack_b in pairs:
        key = f"{rack_a}_{rack_b}"
        pair_svgs[key] = _render_pair_detail_svg(rack_a, rack_b, result)
    return {
        "topology": topology,
        "rack_panels": rack_svgs,
        "pair_detail": pair_svgs,
    }


_MEDIA_COLORS: dict[str, str] = {
    "mmf_lc_duplex": "#4a90d9",
    "smf_lc_duplex": "#9b59b6",
    "mpo12": "#7b68ee",
    "utp_rj45": "#5cb85c",
}

_MODULE_FILL: dict[str, str] = {
    LC_BREAKOUT_MODULE: "#d0e8ff",
    MPO_PASS_THROUGH_MODULE: "#e0d8ff",
    UTP_MODULE: "#d8f0d8",
}


def _media_abbrev(media: str) -> str:
    return (
        media.replace("mmf_lc_duplex", "MMF-LC")
        .replace("smf_lc_duplex", "SMF-LC")
        .replace("mpo12", "MPO12")
        .replace("utp_rj45", "UTP")
    )


def _module_abbrev(module_type: str, fiber_kind: str | None) -> str:
    if module_type == LC_BREAKOUT_MODULE:
        return f"LC-{(fiber_kind or '').upper()}"
    if module_type == MPO_PASS_THROUGH_MODULE:
        return "MPO-PT"
    if module_type == UTP_MODULE:
        return "UTP"
    return module_type[:8]


def _render_topology_svg(result: AllocationResult) -> str:
    racks = sorted({panel.rack_id for panel in result.panels}, key=natural_sort_key)
    if not racks:
        return _render_svg_root("topology", {"data-kind": "topology"}, ["Topology (empty)"])

    pair_summary: dict[tuple[str, str], dict[str, int]] = {}
    for session in result.sessions:
        a, b = sorted((session.src_rack, session.dst_rack), key=natural_sort_key)
        pair: tuple[str, str] = (a, b)
        pair_summary.setdefault(pair, {})
        pair_summary[pair][session.media] = pair_summary[pair].get(session.media, 0) + 1

    rack_w, rack_h = 90, 36
    h_gap, v_gap = 50, 80
    margin = 30
    title_h = 40
    cols = min(len(racks), 6)
    total_rows = math.ceil(len(racks) / cols)
    svg_w = margin * 2 + cols * rack_w + max(cols - 1, 0) * h_gap
    svg_h = title_h + margin * 2 + total_rows * rack_h + max(total_rows - 1, 0) * v_gap + 20

    pos: dict[str, tuple[int, int]] = {}
    for idx, rack_id in enumerate(racks):
        col = idx % cols
        row = idx // cols
        x = margin + col * (rack_w + h_gap)
        y = title_h + margin + row * (rack_h + v_gap)
        pos[rack_id] = (x, y)

    parts: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" data-kind="topology"'
        f' width="{svg_w}" height="{svg_h}"'
        f' style="font-family:monospace;font-size:12px;background:#fff;">',
        "<title>Topology</title>",
        f'<text x="{svg_w // 2}" y="26" text-anchor="middle"'
        f' style="font-size:15px;font-weight:bold;">Topology</text>',
    ]

    for (ra, rb), media_counts in pair_summary.items():
        x1 = pos[ra][0] + rack_w // 2
        y1 = pos[ra][1] + rack_h // 2
        x2 = pos[rb][0] + rack_w // 2
        y2 = pos[rb][1] + rack_h // 2
        label = " | ".join(
            f"{_media_abbrev(m)}×{c}" for m, c in sorted(media_counts.items())
        )
        mx, my = (x1 + x2) // 2, (y1 + y2) // 2 - 6
        parts.append(
            f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}"'
            f' stroke="#aaa" stroke-width="2"/>'
        )
        parts.append(
            f'<text x="{mx}" y="{my}" text-anchor="middle"'
            f' style="font-size:10px;fill:#444;">{html.escape(label)}</text>'
        )

    for rack_id in racks:
        x, y = pos[rack_id]
        safe_id = html.escape(rack_id)
        parts.append(
            f'<rect x="{x}" y="{y}" width="{rack_w}" height="{rack_h}"'
            f' rx="5" fill="#e8f0fe" stroke="#4a90d9" stroke-width="2"/>'
        )
        parts.append(
            f'<text x="{x + rack_w // 2}" y="{y + rack_h // 2 + 5}"'
            f' text-anchor="middle"'
            f' style="font-weight:bold;">{safe_id}</text>'
        )

    parts.append("</svg>")
    return "".join(parts)


def _render_rack_panels_svg(rack_id: str, result: AllocationResult) -> str:
    rack_modules = sorted(
        [m for m in result.modules if m.rack_id == rack_id],
        key=lambda m: (m.panel_u, m.slot),
    )
    max_u = max((m.panel_u for m in rack_modules), default=0)
    if max_u == 0:
        return _render_svg_root(
            "rack-panels",
            {"data-kind": "rack-panels", "data-rack": rack_id},
            [f"Rack {rack_id} (empty)"],
        )

    mod_map: dict[tuple[int, int], Module] = {
        (m.panel_u, m.slot): m for m in rack_modules
    }

    slot_w, slot_h = 130, 34
    label_w = 38
    margin = 20
    title_h = 44
    legend_h = 28
    svg_w = margin * 2 + label_w + SLOTS_PER_U_DEFAULT * slot_w
    svg_h = title_h + max_u * slot_h + margin * 2 + legend_h
    safe_rack = html.escape(rack_id)

    parts: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" data-kind="rack-panels"'
        f' data-rack="{safe_rack}" width="{svg_w}" height="{svg_h}"'
        f' style="font-family:monospace;font-size:11px;background:#fff;">',
        f"<title>Rack {safe_rack}</title>",
        f'<text x="{svg_w // 2}" y="26" text-anchor="middle"'
        f' style="font-size:14px;font-weight:bold;">Rack {safe_rack} — Panel Layout</text>',
    ]

    for slot in range(1, SLOTS_PER_U_DEFAULT + 1):
        hx = margin + label_w + (slot - 1) * slot_w + slot_w // 2
        parts.append(
            f'<text x="{hx}" y="42" text-anchor="middle"'
            f' style="font-size:10px;fill:#666;">Slot {slot}</text>'
        )

    for u in range(1, max_u + 1):
        ry = title_h + (u - 1) * slot_h + margin
        parts.append(
            f'<text x="{margin + label_w // 2}" y="{ry + slot_h // 2 + 4}"'
            f' text-anchor="middle" style="font-size:10px;fill:#666;">U{u}</text>'
        )
        for slot in range(1, SLOTS_PER_U_DEFAULT + 1):
            sx = margin + label_w + (slot - 1) * slot_w
            module = mod_map.get((u, slot))
            if module:
                fill = _MODULE_FILL.get(module.module_type, "#f5f5f5")
                abbrev = _module_abbrev(module.module_type, module.fiber_kind)
                peer = module.peer_rack_id or "shared"
                parts.append(
                    f'<rect x="{sx}" y="{ry}" width="{slot_w}" height="{slot_h}"'
                    f' fill="{fill}" stroke="#888" stroke-width="1"/>'
                )
                parts.append(
                    f'<text x="{sx + slot_w // 2}" y="{ry + slot_h // 2 - 4}"'
                    f' text-anchor="middle"'
                    f' style="font-size:9px;font-weight:bold;">'
                    f"{html.escape(abbrev)}</text>"
                )
                parts.append(
                    f'<text x="{sx + slot_w // 2}" y="{ry + slot_h // 2 + 9}"'
                    f' text-anchor="middle" style="font-size:9px;">'
                    f"→{html.escape(peer)}</text>"
                )
            else:
                parts.append(
                    f'<rect x="{sx}" y="{ry}" width="{slot_w}" height="{slot_h}"'
                    f' fill="#fafafa" stroke="#ccc" stroke-width="1"'
                    f' stroke-dasharray="4 2"/>'
                )

    ly = title_h + max_u * slot_h + margin + 8
    lx = margin
    for mtype, label in [
        (LC_BREAKOUT_MODULE, "LC Breakout"),
        (MPO_PASS_THROUGH_MODULE, "MPO Pass-Through"),
        (UTP_MODULE, "UTP"),
    ]:
        fill = _MODULE_FILL.get(mtype, "#f5f5f5")
        parts.append(
            f'<rect x="{lx}" y="{ly}" width="12" height="12"'
            f' fill="{fill}" stroke="#888" stroke-width="1"/>'
        )
        parts.append(
            f'<text x="{lx + 16}" y="{ly + 10}"'
            f' style="font-size:10px;">{html.escape(label)}</text>'
        )
        lx += 145

    parts.append("</svg>")
    return "".join(parts)


def _render_pair_detail_svg(rack_a: str, rack_b: str, result: AllocationResult) -> str:
    sessions = sorted(
        [s for s in result.sessions if s.src_rack == rack_a and s.dst_rack == rack_b],
        key=lambda s: (s.src_u, s.src_slot, s.src_port),
    )
    safe_key = html.escape(f"{rack_a}_{rack_b}")
    if not sessions:
        return _render_svg_root(
            "pair-detail",
            {"data-kind": "pair-detail", "data-pair": f"{rack_a}_{rack_b}"},
            [f"Pair {rack_a}-{rack_b} (no sessions)"],
        )

    row_h = 18
    title_h = 48
    port_col_w = 150
    mid_w = 100
    margin = 20
    svg_w = margin * 2 + port_col_w + mid_w + port_col_w
    svg_h = title_h + len(sessions) * row_h + margin * 2
    safe_a = html.escape(rack_a)
    safe_b = html.escape(rack_b)

    parts: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" data-kind="pair-detail"'
        f' data-pair="{safe_key}" width="{svg_w}" height="{svg_h}"'
        f' style="font-family:monospace;font-size:11px;background:#fff;">',
        f"<title>Pair {safe_a}-{safe_b}</title>",
        f'<text x="{svg_w // 2}" y="22" text-anchor="middle"'
        f' style="font-size:14px;font-weight:bold;">'
        f"Pair Detail: {safe_a} ↔ {safe_b}</text>",
        f'<text x="{margin + port_col_w // 2}" y="40" text-anchor="middle"'
        f' style="font-size:11px;font-weight:bold;">{safe_a}</text>',
        f'<text x="{margin + port_col_w + mid_w + port_col_w // 2}" y="40"'
        f' text-anchor="middle"'
        f' style="font-size:11px;font-weight:bold;">{safe_b}</text>',
    ]

    x_src_right = margin + port_col_w
    x_dst_left = margin + port_col_w + mid_w
    for i, session in enumerate(sessions):
        cy = title_h + i * row_h + margin + row_h // 2
        color = _MEDIA_COLORS.get(session.media, "#999")
        src_label = f"U{session.src_u}S{session.src_slot}P{session.src_port}"
        dst_label = f"U{session.dst_u}S{session.dst_slot}P{session.dst_port}"
        fiber_info = (
            f" f{session.fiber_a}/{session.fiber_b}"
            if session.fiber_a is not None and session.fiber_b is not None
            else ""
        )
        mid_label = html.escape(_media_abbrev(session.media) + fiber_info)
        parts.append(
            f'<text x="{x_src_right - 4}" y="{cy + 4}" text-anchor="end"'
            f' style="font-size:10px;">{html.escape(src_label)}</text>'
        )
        parts.append(
            f'<line x1="{x_src_right}" y1="{cy}" x2="{x_dst_left}" y2="{cy}"'
            f' stroke="{color}" stroke-width="1.5"/>'
        )
        parts.append(
            f'<text x="{x_src_right + mid_w // 2}" y="{cy - 2}" text-anchor="middle"'
            f' style="font-size:8px;fill:#555;">{mid_label}</text>'
        )
        parts.append(
            f'<text x="{x_dst_left + 4}" y="{cy + 4}" text-anchor="start"'
            f' style="font-size:10px;">{html.escape(dst_label)}</text>'
        )

    parts.append("</svg>")
    return "".join(parts)



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
