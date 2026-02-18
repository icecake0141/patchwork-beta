<!--
SPDX-License-Identifier: Apache-2.0
-->

# AI-Generated Content Notice

This file was created or modified with the assistance of an AI (Large Language Model). Review for correctness and security.

---

# Data Center Rack-to-Rack Patch Cabling Design Assistant — Design Specification (v0)

## 0. Purpose

Build a WebUI tool (Flask + SQLite) that takes a single `project.yaml` describing racks and required inter-rack connectivity and produces:

- An optimized, operations-friendly physical termination plan:
  - Patch panel U/slot allocation per rack (front/back aware)
  - Module (adapter) allocation per slot
  - Port-level session table (1 row per endpoint port)
- Wiring diagrams (SVG):
  - Rack topology
  - Rack panel occupancy (front/back)
  - Pair link detail (rack-pair slot/port mapping)
- Persisted projects and saved revisions, with diff between revisions.

Optimization is **not based on distance** in v0.

---

## 1. Scope (v0)

### 1.1 Included
- Rack-to-rack cabling only (intra-rack cabling excluded).
- Media types supported in demands:
  - `mmf_lc_duplex`
  - `smf_lc_duplex`
  - `mpo12` (end-to-end)
  - `utp_rj45`
- Automated generation of:
  - Patch panels (1U panels, 4 slots per U) per rack, added as needed.
  - Modules (adapters) per slot.
  - Trunks/cables and port-level sessions.
- Polarity types support:
  - MTP/MPO trunk: `A`, `B`, `C`
  - LC breakout module variant: `A`, `AF`
  - MPO pass-through module variant: `A`

### 1.2 Excluded
- Physical pathway routing (tray/floor/ceiling), length estimation, loss budgets.
- Device-level port inventories (ToR/leaf/etc. ports not modeled in v0).
- Multi-user concurrency beyond "single user" assumption.

---

## 2. Core Physical Model

### 2.1 Faces (front/back)
- Rack-to-rack trunk/cable side is **back**.
- Equipment-facing terminations are **front**.
- Modules are modeled as **bi-faced** components:
  - Trunk-side ports: `back`
  - Equipment-side ports: `front`

### 2.2 Patch Panel
- Panels are created automatically.
- Each panel is **1U** and has **4 slots**.
- Panels are assigned in ascending U order **from top** (U1, U2, ...).

### 2.3 Modules (slot-installed)
Slots contain exactly one module. Module types:

#### 2.3.1 LC Breakout Module (for LC demands)
- Type: `lc_breakout_2xmpo12_to_12xlcduplex`
- Variants by fiber type:
  - `mmf` variant (MMF-compatible optics/adapter)
  - `smf` variant (SMF-compatible optics/adapter)
- Variant by polarity: `AF` (default for LC demands)
- Ports:
  - Back: `MPO12#1`, `MPO12#2`
  - Front: `LC_DUPLEX#1 .. #12`
- Slot usage rule: **Dedicated to a single peer rack** (one module serves only one opposite rack).
- If required LC duplex count to a peer rack exceeds 12:
  - Multiple modules are used: `ceil(lc_count / 12)`.

#### 2.3.2 UTP Module (for UTP demands)
- Type: `utp_6xrj45`
- Ports (front): `RJ45#1 .. #6`
- Slot usage rule: **Not dedicated** to a single peer rack.
- Port assignment grouping:
  - Within a module, allocate contiguous port ranges per peer rack.
  - Across modules, "strong grouping" per peer rack is preferred, but partial mixing is allowed to reduce waste.

#### 2.3.3 MPO Pass-Through Module (for MPO end-to-end demands)
- Type: `mpo12_pass_through_12port`
- Polarity variant: `A` (fixed for v0)
- Ports:
  - Back: `MPO12#1 .. #12` (12 independent MPO-12 pass-through ports)
  - Front: `MPO12#1 .. #12` (equipment-facing side)
- Slot usage rule: **Dedicated to a single peer rack**.
- Port assignment requires **port-number alignment** across both racks:
  - `port k` on rack A connects to `port k` on rack B.

---

## 3. Polarity / Method Rules

### 3.1 LC demands (MMF/SMF LC duplex)
- Rack-to-rack backbone is always MPO-12 trunks (MTP).
- Default polarity profile:
  - Trunk: `Type A`
  - LC breakout module: `Type AF`
- Breakout mapping is **fixed by module type** (see §4).

### 3.2 MPO end-to-end demands (`endpoint_type: mpo12`)
- Always terminated via patch panel (no direct device-to-device trunk in v0).
- Channel polarity profile (Method-B):
  - Rack-to-rack trunk: `Type B`
  - Pass-through module: `Type A`
- Slot dedicated per peer rack, with strict slot pairing and port-number alignment.

---

## 4. Fixed Port Mappings

### 4.1 LC breakout mapping (per MPO-12)
Assume LC duplex uses **2 fibers** per LC port.

For a given MPO-12 connector, fiber index `1..12` maps to LC duplex ports as fixed pairs:

- LC#1  ⇐⇒ fibers (1,2)
- LC#2  ⇐⇒ fibers (3,4)
- LC#3  ⇐⇒ fibers (5,6)
- LC#4  ⇐⇒ fibers (7,8)
- LC#5  ⇐⇒ fibers (9,10)
- LC#6  ⇐⇒ fibers (11,12)

Module has two MPO-12 back ports:
- MPO#1 serves LC#1..LC#6
- MPO#2 serves LC#7..LC#12 (same mapping repeated, offset by 6)

### 4.2 Alignment rules
- LC breakout:
  - MPO#1 ↔ MPO#1, MPO#2 ↔ MPO#2 across racks (fixed).
  - LC#n ↔ LC#n across racks (fixed).
- MPO pass-through:
  - MPO#k ↔ MPO#k across racks (fixed).
- UTP:
  - Attempt RJ45#k ↔ RJ45#k alignment for each peer rack group as much as possible.

---

## 5. Optimization Objectives (v0, strict priority)

1. **Constraint satisfaction**
   - Module/slot rules, face rules, dedicated/non-dedicated rules, capacity limits.
2. **Peer alignment**
   - Number-aligned port pairing (LC/MPO/RJ45 where applicable).
3. **Grouping**
   - Media grouping, peer rack natural-sort ordering, UTP contiguous ranges.
4. **Panel U minimization**
   - Allow mixed media in a U to avoid unused slots (subject to category order).
5. **Label stability**
   - Deterministic ordering and deterministic IDs.

No distance/length is considered.

---

## 6. Allocation Rules (Deterministic)

### 6.1 Global slot allocation category priority
For each rack, allocate slots in this order:
1. MPO end-to-end pass-through modules
2. LC breakout modules (media order fixed: MMF → SMF)
3. UTP modules

### 6.2 "Mixed-in-U" rule
Media grouping is attempted, but **mixing within the same U is allowed** to reduce wasted slots:
- While processing a category, fill slots sequentially.
- If a category finishes and the current U has remaining slots, the next category may consume them.

### 6.3 Natural sort of peer racks
Peer ordering uses "natural sort":
- Extract trailing digits; compare numerically.
- If no trailing digits, compare lexicographically.
- Tie-break by full string lexicographic.

### 6.4 LC breakout module requirements
For each rack pair (A,B) and fiber type (MMF/SMF):
- Demand is LC duplex count `N`.
- Required modules per rack side: `M = ceil(N / 12)`
- Each module provides 12 LC duplex ports and 2 MPO-12 back ports.
- For each module index `i` (1..M):
  - Pair module `i` on A with module `i` on B.
  - Within each paired module:
    - LC#1..#12 aligned and used in order until N is satisfied.
    - MPO#1 and MPO#2 aligned.

Backbone trunks for LC demands:
- Each module pair requires 2 MPO-12 trunk cables (for MPO#1 and MPO#2).
- Trunk polarity type: `A`.
- For each module pair i:
  - Create trunk cables `T(i, mpo=1)` and `T(i, mpo=2)` and connect both racks' module MPO ports.

### 6.5 MPO end-to-end module requirements
For each rack pair (A,B):
- Demand is MPO12 count `N`.
- Required slots per rack side: `S = ceil(N / 12)` (12 MPO pass-through ports per slot)
- For each slot index `i` (1..S):
  - Pair slot i on A with slot i on B.
  - Allocate port numbers 1..12 aligned; use first `min(12, remaining)` ports.
- Create MPO-12 trunk cables per used port:
  - Each used pass-through port consumes 1 MPO-12 trunk cable.
  - Trunk polarity type: `B`.

### 6.6 UTP module requirements
For each rack:
- Aggregate UTP demands by peer rack.
- Allocate RJ45 ports into modules (6 ports each) using:
  - Primary: strong grouping by peer rack (fill full modules if possible).
  - Secondary: allow splitting the final partially-used module between current and next peer rack to reduce waste.
- For each peer rack pair, attempt RJ45#k ↔ RJ45#k alignment:
  - Achieved by symmetric allocation order on both racks.

Rack-to-rack UTP cables:
- One cable per RJ45 port session (no internal fibers).
- Consider these as "trunks" but not MTP.

---

## 7. Output Definitions

### 7.1 Session Table CSV (mandatory export)
**One row per endpoint port** session. Required columns (set B):

- `project_id`
- `revision_id` (blank/null for Trial view; present for saved revisions)
- `session_id` (deterministic)
- `media` (`mmf_lc_duplex`, `smf_lc_duplex`, `mpo12`, `utp_rj45`)
- `cable_id` (deterministic; MPO/UTP trunk identifier)
- `adapter_type` (module type)
- `label_a`, `label_b`
- `src_rack`, `src_face`, `src_u`, `src_slot`, `src_port`
- `dst_rack`, `dst_face`, `dst_u`, `dst_slot`, `dst_port`
- `fiber_a`, `fiber_b` (only for LC sessions; else blank)
- `notes` (warnings/flags)

Label format (B, fixed):
- `label_a = {src_rack}U{src_u}S{src_slot}P{src_port}`
- `label_b = {dst_rack}U{dst_u}S{dst_slot}P{dst_port}`

### 7.2 result.json (mandatory export)
Machine-readable full result including internal keys:
- Project metadata
- Input snapshot hash
- Generated panels, modules, ports
- Generated cables/trunks (including polarity types)
- Sessions
- Warnings/errors
- Metrics

### 7.3 SVG diagrams (mandatory export)
1. `topology.svg`
2. `rack_{rack_id}_panels.svg` (front/back, U/slot/port occupancy)
3. `pair_{rackA}_{rackB}_detail.svg` (slot-slot and port-port mapping for the pair)

---

## 8. Deterministic IDs

### 8.1 Policy
IDs are deterministic: same input + same allocation rules ⇒ same IDs.

### 8.2 Method
- Define a canonical string for each entity (session, cable, module allocation).
- Compute `sha256(canonical_string)`; use first 16 hex chars (configurable).
- Entities:
  - `session_id`
  - `cable_id` (MPO-12 trunk or UTP cable)
  - `project_id` can be user-specified or derived from name; v0 recommends user-provided name + deterministic hash.

Example canonical components (illustrative):
- LC session:
  - `media|src_rack|src_u|src_slot|src_port|dst_rack|dst_u|dst_slot|dst_port|cable_id|fiberpair`
- MPO E2E:
  - `media=mpo12|src_rack|src_u|src_slot|src_port|dst_rack|dst_u|dst_slot|dst_port|cable_id`
- UTP:
  - `media=utp_rj45|src_rack|src_u|src_slot|src_port|dst_rack|dst_u|dst_slot|dst_port|cable_id`

---

## 9. Persistence Model (SQLite)

### 9.1 Project/Revision lifecycle
- Trial results are stored **in server memory only**, keyed by `trial_id` in Flask session.
- "Save" creates a new **Revision** row with:
  - frozen input `project.yaml` snapshot
  - computed results (sessions, modules, cables)
- Saved revisions are browsable and exportable.

### 9.2 Suggested SQLite schema (DDL)

```sql
-- Projects
CREATE TABLE project (
  project_id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

-- Revisions
CREATE TABLE revision (
  revision_id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  created_at TEXT NOT NULL,
  note TEXT,
  input_yaml TEXT NOT NULL,
  input_hash TEXT NOT NULL,
  FOREIGN KEY(project_id) REFERENCES project(project_id)
);

-- Generated panels (1U each)
CREATE TABLE panel (
  panel_id TEXT PRIMARY KEY,
  revision_id TEXT NOT NULL,
  rack_id TEXT NOT NULL,
  u INTEGER NOT NULL,
  slots_per_u INTEGER NOT NULL DEFAULT 4,
  FOREIGN KEY(revision_id) REFERENCES revision(revision_id)
);

-- Slot-installed modules
CREATE TABLE module (
  module_id TEXT PRIMARY KEY,
  revision_id TEXT NOT NULL,
  rack_id TEXT NOT NULL,
  panel_u INTEGER NOT NULL,
  slot INTEGER NOT NULL,
  module_type TEXT NOT NULL,
  fiber_kind TEXT,             -- mmf/smf/null
  polarity_variant TEXT,       -- A/AF/etc
  peer_rack_id TEXT,           -- for dedicated modules (LC breakout, MPO pass-through)
  dedicated INTEGER NOT NULL DEFAULT 0,
  FOREIGN KEY(revision_id) REFERENCES revision(revision_id)
);

-- Cables / trunks
CREATE TABLE cable (
  cable_id TEXT PRIMARY KEY,
  revision_id TEXT NOT NULL,
  cable_type TEXT NOT NULL,    -- mpo12_trunk / utp_cable
  fiber_kind TEXT,             -- mmf/smf/null
  polarity_type TEXT,          -- A/B/C for MPO, null for UTP
  FOREIGN KEY(revision_id) REFERENCES revision(revision_id)
);

-- Sessions (export table)
CREATE TABLE session (
  session_id TEXT PRIMARY KEY,
  revision_id TEXT NOT NULL,
  media TEXT NOT NULL,
  cable_id TEXT NOT NULL,
  adapter_type TEXT NOT NULL,
  label_a TEXT NOT NULL,
  label_b TEXT NOT NULL,
  src_rack TEXT NOT NULL,
  src_face TEXT NOT NULL,
  src_u INTEGER NOT NULL,
  src_slot INTEGER NOT NULL,
  src_port INTEGER NOT NULL,
  dst_rack TEXT NOT NULL,
  dst_face TEXT NOT NULL,
  dst_u INTEGER NOT NULL,
  dst_slot INTEGER NOT NULL,
  dst_port INTEGER NOT NULL,
  fiber_a INTEGER,
  fiber_b INTEGER,
  notes TEXT,
  FOREIGN KEY(revision_id) REFERENCES revision(revision_id),
  FOREIGN KEY(cable_id) REFERENCES cable(cable_id)
);

-- Optional: indexes
CREATE INDEX idx_session_revision ON session(revision_id);
CREATE INDEX idx_module_revision_rack ON module(revision_id, rack_id);
CREATE INDEX idx_panel_revision_rack ON panel(revision_id, rack_id);
```

Notes:
- This v0 schema stores *generated results* per revision.
- It does not store port-graph edges or closure tables. Those can be added later if interactive tracing is needed.

---

## 10. WebUI Specification (Flask)

### 10.1 Pages (minimum v0)
1. **Upload**
   - Upload `project.yaml`
   - Validate schema
   - Run Trial allocation
   - Redirect to Trial page
2. **Trial**
   - Display summary metrics and warnings
   - Tabs:
     - Session table preview
     - Rack panel occupancy previews
     - Pair detail previews
   - Buttons:
     - "Save"
     - "Back / Upload another"
3. **Save**
   - Enter project name (or confirm)
   - Enter revision note (optional)
   - Persist project + revision + results
4. **Project Detail**
   - Project info
   - Revision list
   - Revision detail (session table + SVG previews)
   - Diff view between two revisions (see §11)
   - Export buttons for selected revision

### 10.2 No CLI options
All "modes" are fixed by the spec; UI shows all relevant outputs rather than requiring switches.

---

## 11. Diff Specification (Two Tabs, fixed)

Diff is available on Project Detail page between two saved revisions.

### 11.1 Logical Diff (session_id-based)
- Added sessions: in rev2 not in rev1
- Removed sessions: in rev1 not in rev2
- Modified sessions: same `session_id` exists but row differs in key fields (should be rare if deterministic canonical string includes those fields; if included, modifications become add/remove instead)

### 11.2 Physical Diff (location-based)
- Key: `(media, src_rack, src_face, src_u, src_slot, src_port, dst_rack, dst_face, dst_u, dst_slot, dst_port)`
- Report:
  - Added/Removed physical terminations
  - Collisions (same physical key but different session_id)

Both diffs are always shown as two fixed tabs.

---

## 12. project.yaml Specification

### 12.1 Top-level structure

```yaml
version: 1
project:
  name: "example-dc-cabling"
  note: "optional"
racks:
  - id: "R01"
    name: "Rack-01"
  - id: "R02"
    name: "Rack-02"
demands:
  - id: "D001"
    src: "R01"
    dst: "R02"
    endpoint_type: "mmf_lc_duplex"
    count: 17
  - id: "D002"
    src: "R01"
    dst: "R03"
    endpoint_type: "utp_rj45"
    count: 8
  - id: "D003"
    src: "R02"
    dst: "R04"
    endpoint_type: "mpo12"
    count: 10
settings:
  fixed_profiles:
    lc_demands:
      trunk_polarity: "A"
      breakout_module_variant: "AF"
    mpo_e2e:
      trunk_polarity: "B"
      pass_through_variant: "A"
  ordering:
    slot_category_priority:
      - "mpo_e2e"
      - "lc_mmf"
      - "lc_smf"
      - "utp"
    peer_sort: "natural_trailing_digits"
  panel:
    slots_per_u: 4
    allocation_direction: "top_down"   # fixed in v0
```

### 12.2 Constraints / validation
- `racks[*].id` must be unique.
- `demands[*].src/dst` must refer to existing rack ids.
- `endpoint_type` must be one of:
  - `mmf_lc_duplex`, `smf_lc_duplex`, `mpo12`, `utp_rj45`
- `count` must be positive integer.
- Demands are treated as undirected connectivity unless explicitly needed; v0 treats as bidirectional physical connectivity.

---

## 13. Allocation Pseudocode (High Level)

```text
parse project.yaml
validate

normalize demands:
  for each demand:
    ensure src != dst
    build rack_pair = ordered(src, dst) using natural sort or stable ordering

for each rack:
  init empty panel list

allocate MPO E2E:
  for each rack_pair with mpo12 count N:
    slots_needed = ceil(N/12) per side
    reserve slots_needed slots on both racks (category mpo_e2e)
    pair slots by index
    within each paired slot, assign ports 1..12 aligned
    create mpo12 trunk cable per used port, polarity B
    create session row per used MPO port (media=mpo12)

allocate LC breakout (MMF then SMF):
  for each fiber_kind in [mmf, smf]:
    for each rack_pair with lc count N:
      modules_needed = ceil(N/12) per side
      reserve modules_needed slots on both racks (category lc_kind)
      pair modules by index
      within each paired module:
        assign LC ports 1..12 aligned for up to remaining N
        for each used LC port:
          determine MPO port (1 or 2) and fiber pair mapping
          create corresponding mpo12 trunk cable if not already created for that module+mpo_port, polarity A
          create session row per used LC port (media=*_lc_duplex with fiber pair columns)

allocate UTP:
  for each rack:
    aggregate outgoing+incoming utp demand counts by peer (treated symmetrically)
    build peer list sorted natural
    allocate RJ45 ports into 6-port modules using rule C (strong grouping + tail sharing)
  for each UTP session between rack_pair:
    attempt RJ45 number alignment by constructing both sides allocation deterministically
    create utp cable per RJ45 session
    create session row per used RJ45 port

generate SVGs:
  topology.svg from sessions aggregated by rack_pair and media
  rack panels SVGs from module placements and port occupancy
  pair detail SVGs from paired slots/modules and port alignments

trial result => store in memory keyed by trial_id
on save => persist project + revision + generated tables
```

---

## 14. Acceptance Tests (Given/When/Then)

### 14.1 LC breakout scaling
- Given: R01↔R02, `mmf_lc_duplex count=13`
- When: allocate
- Then:
  - Each rack gets `ceil(13/12)=2` MMF breakout modules (2 slots).
  - Total LC sessions = 13 rows
  - Module pair #1 uses LC#1-#12, module pair #2 uses LC#1 only.
  - MPO trunks created: 2 trunks per module pair => 4 total.

### 14.2 MPO E2E pass-through slot capacity
- Given: R01↔R02, `mpo12 count=14`
- When: allocate
- Then:
  - Slots needed per rack: `ceil(14/12)=2`
  - Slot pair #1 uses ports 1-12; slot pair #2 uses ports 1-2
  - 14 MPO trunk cables, polarity B
  - All sessions have port-number alignment.

### 14.3 UTP grouping with tail sharing
- Given: In rack R01, demands:
  - to R02: 7
  - to R03: 2
- When: allocate UTP modules
- Then:
  - Module#1 ports 1-6 => R02
  - Module#2 ports 1 => R02, ports 2-3 => R03 (tail sharing), remaining empty

### 14.4 Mixed-in-U behavior
- Given: Rack requires 3 MPO E2E slots and 1 MMF breakout slot
- When: allocate
- Then:
  - U1 slots filled by MPO E2E (slots 1-3)
  - Remaining slot in U1 may be consumed by MMF breakout (slot 4), avoiding a new U.

---

## 15. Implementation Notes

### 15.1 Flask structure (suggested)
- `app.py` (routes)
- `services/allocator.py` (deterministic allocation engine)
- `services/render_svg.py`
- `services/export.py`
- `db.py` (SQLite connection, migrations)
- `models.py` (dataclasses or pydantic models for YAML)

### 15.2 Security/limits (v0)
- Upload size limits for YAML.
- YAML parsing using safe loader.
- Single-user assumption; no hard multi-session guarantees.

---

## 16. Open Items (Explicitly out of v0)
- Device port inventories and patch cords from device to panel.
- Physical length estimation and route constraints.
- Interactive path tracing requiring closure tables.
