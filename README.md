# SPDX-License-Identifier: Apache-2.0
<!-- This file was created or modified with the assistance of an AI (Large Language Model). Review for correctness and security. -->

# patchwork-beta

Data center rack patch panel allocation and cable management system.

[![CI](https://github.com/icecake0141/patchwork-beta/actions/workflows/ci.yml/badge.svg)](https://github.com/icecake0141/patchwork-beta/actions/workflows/ci.yml)
[![CodeQL](https://github.com/icecake0141/patchwork-beta/actions/workflows/codeql.yml/badge.svg)](https://github.com/icecake0141/patchwork-beta/actions/workflows/codeql.yml)
[![Dependabot Updates](https://github.com/icecake0141/patchwork-beta/actions/workflows/dependabot/dependabot-updates/badge.svg)](https://github.com/icecake0141/patchwork-beta/actions/workflows/dependabot/dependabot-updates)

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Requirements](#requirements)
- [Dependencies](#dependencies)
- [Installation](#installation)
- [Basic Usage](#basic-usage)
- [Input Schema](#input-schema)
- [Output Structure](#output-structure)
- [API Reference](#api-reference)
- [Complete Example with Sample Output](#complete-example-with-sample-output)
- [Configuration](#configuration)
- [Development](#development)
- [Project Structure](#project-structure)
- [CI/CD](#cicd)
- [Contributing](#contributing)
- [Issues and Support](#issues-and-support)
- [Documentation](#documentation)
- [License](#license)
- [Acknowledgments](#acknowledgments)
- [日本語 (Japanese Translation)](#日本語-japanese-translation)

## Overview

This project provides tools for allocating and managing patch panel modules and cables in data center racks. It helps optimize the placement of fiber optic, MPO, and UTP connections between racks.

## Features

- 🔧 Automated patch panel allocation
- 🔌 Support for multiple connection types (LC, MPO12, UTP/RJ45)
- 📊 Deterministic and reproducible allocations
- 📈 Session tracking and CSV export
- 🎨 SVG visualization generation
- ✅ Type-safe Python implementation

## Requirements

- Python 3.11 or later

## Dependencies

- Runtime dependencies: none (standard library only)
- Development dependencies: see [`requirements-dev.txt`](requirements-dev.txt)

## Installation

### For Development

```bash
# Clone the repository
git clone https://github.com/icecake0141/patchwork-beta.git
cd patchwork-beta

# Install development dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install
```

### For Use as a Library

```bash
pip install -e .
```

## Basic Usage

```python
from patchwork import allocate_project, export_session_table_csv, export_result_json, render_svgs

# 1. Define the project (racks and connection demands)
project = {
    "racks": [{"id": "R01"}, {"id": "R02"}],
    "demands": [
        {
            "id": "D001",
            "src": "R01",
            "dst": "R02",
            "endpoint_type": "mmf_lc_duplex",
            "count": 2,
        }
    ],
}

# 2. Run allocation
result = allocate_project(project)

# 3. Export session table as CSV
csv_output = export_session_table_csv(project_id="proj-1", sessions=result.sessions)

# 4. Export full result as JSON
json_output = export_result_json(project_id="proj-1", result=result)

# 5. Generate SVG visualizations
svgs = render_svgs(result)
```

## Input Schema

`allocate_project` accepts a Python `dict` (which can be loaded from JSON) with the following structure:

```python
project = {
    "racks": [
        {"id": "R01"},  # Each rack must have a unique string id
        {"id": "R02"},
    ],
    "demands": [
        {
            "id": "D001",           # str  – unique identifier for this demand
            "src": "R01",           # str  – source rack id (must exist in racks)
            "dst": "R02",           # str  – destination rack id (must exist in racks, != src)
            "endpoint_type": "mmf_lc_duplex",  # str – see table below
            "count": 2,             # int  – number of endpoint pairs (must be > 0)
        }
    ],
}
```

### Supported `endpoint_type` values

| Value | Description |
|---|---|
| `mmf_lc_duplex` | Multi-mode fiber LC duplex (uses LC breakout modules and MPO-12 trunk cables) |
| `smf_lc_duplex` | Single-mode fiber LC duplex (same physical layout as mmf, different fiber kind) |
| `mpo12` | MPO-12 pass-through (uses MPO pass-through modules and MPO-12 trunk cables) |
| `utp_rj45` | UTP / RJ-45 copper (uses UTP modules and UTP patch cables; modules may be shared between peers) |

### Validation rules

- `racks[].id` values must be unique.
- `demands[].src` and `demands[].dst` must reference existing rack ids and must not be equal.
- `demands[].count` must be a positive integer.
- Multiple demands between the same rack pair are merged before allocation.

## Output Structure

`allocate_project` returns an `AllocationResult` dataclass with four lists:

```
AllocationResult
├── panels   – list[Panel]   – one Panel per U row used in each rack
├── modules  – list[Module]  – one Module per physical patch-panel slot used
├── cables   – list[Cable]   – one Cable per physical cable run
└── sessions – list[Session] – one Session per individual port connection
```

### `Panel`

Represents a 1U patch-panel row installed in a rack.

| Field | Type | Description |
|---|---|---|
| `rack_id` | `str` | Rack where the panel is installed |
| `u` | `int` | Rack unit position (1-based) |
| `slots_per_u` | `int` | Number of module slots in this U (always 4) |

### `Module`

Represents a single module inserted into a panel slot.

| Field | Type | Description |
|---|---|---|
| `rack_id` | `str` | Rack where the module is installed |
| `panel_u` | `int` | Rack unit of the containing panel |
| `slot` | `int` | Slot index within the panel (1-based) |
| `module_type` | `str` | Physical module type (e.g. `lc_breakout_2xmpo12_to_12xlcduplex`) |
| `fiber_kind` | `str \| None` | Fiber type: `"mmf"`, `"smf"`, or `None` for copper/MPO |
| `polarity_variant` | `str \| None` | Polarity variant (`"A"`, `"AF"`, or `None`) |
| `peer_rack_id` | `str \| None` | Rack id this module is wired to, or `None` for shared UTP modules |
| `dedicated` | `bool` | `True` if exclusively used for one rack pair |

### `Cable`

Represents a physical cable between two racks.

| Field | Type | Description |
|---|---|---|
| `cable_id` | `str` | Deterministic 32-character hex ID |
| `cable_type` | `str` | `"mpo12_trunk"` or `"utp_cable"` |
| `fiber_kind` | `str \| None` | `"mmf"`, `"smf"`, or `None` |
| `polarity_type` | `str \| None` | `"A"`, `"B"`, or `None` |
| `src_rack` | `str` | Source rack id |
| `dst_rack` | `str` | Destination rack id |

### `Session`

Represents a single logical port-to-port connection (one row in the CSV export).

| Field | Type | Description |
|---|---|---|
| `session_id` | `str` | Deterministic 32-character hex ID |
| `media` | `str` | Endpoint type (e.g. `"mmf_lc_duplex"`) |
| `cable_id` | `str` | ID of the physical cable carrying this session |
| `adapter_type` | `str` | Module type used at both ends |
| `label_a` | `str` | Human-readable label for the source port — format: `{rack_id}U{u}S{slot}P{port}` (e.g. `R01U1S1P1`) |
| `label_b` | `str` | Human-readable label for the destination port — same format as `label_a` |
| `src_rack` | `str` | Source rack id |
| `src_face` | `str` | Panel face (`"front"`) |
| `src_u` | `int` | Source rack unit |
| `src_slot` | `int` | Source module slot |
| `src_port` | `int` | Source port number (1-based) |
| `dst_rack` | `str` | Destination rack id |
| `dst_face` | `str` | Panel face (`"front"`) |
| `dst_u` | `int` | Destination rack unit |
| `dst_slot` | `int` | Destination module slot |
| `dst_port` | `int` | Destination port number (1-based) |
| `fiber_a` | `int \| None` | Fiber strand A number in the MPO trunk, or `None` for copper |
| `fiber_b` | `int \| None` | Fiber strand B number in the MPO trunk, or `None` for copper |
| `notes` | `str \| None` | Optional free-text notes |

Label format: `{rack_id}U{u}S{slot}P{port}` — for example `R01U1S1P3` means Rack R01, U1, Slot 1, Port 3.

## API Reference

### `allocate_project(project: dict) -> AllocationResult`

Computes a deterministic patch-panel allocation from a project definition.  
Raises `ValueError` for invalid input (duplicate rack ids, unknown endpoint type, etc.).

### `export_session_table_csv(*, project_id, sessions, revision_id=None) -> str`

Returns a CSV string with one header row followed by one row per session.  
Columns: `project_id`, `revision_id`, `session_id`, `media`, `cable_id`, `adapter_type`,
`label_a`, `label_b`, `src_rack`, `src_face`, `src_u`, `src_slot`, `src_port`,
`dst_rack`, `dst_face`, `dst_u`, `dst_slot`, `dst_port`, `fiber_a`, `fiber_b`, `notes`.  
Sessions are sorted by `session_id` for stable, reproducible output.

### `export_result_json(*, project_id, result, revision_id=None) -> str`

Returns a JSON string with a top-level object containing:
- `project_id`, `revision_id`
- `metrics` — summary counts (total sessions, cables, modules, panels; breakdowns by type)
- `panels`, `modules`, `cables`, `sessions` — full lists as JSON objects
- `warnings` — reserved list (currently always empty)

### `render_svgs(result: AllocationResult) -> dict`

Returns a dictionary with three keys:
- `"topology"` — `str`: a single SVG placeholder for the whole topology view
- `"rack_panels"` — `dict[str, str]`: one SVG per rack, keyed by rack id
- `"pair_detail"` — `dict[str, str]`: one SVG per rack-pair, keyed by `"{rack_a}_{rack_b}"`

## Complete Example with Sample Output

```python
from patchwork import allocate_project, export_session_table_csv, export_result_json, render_svgs

project = {
    "racks": [{"id": "R01"}, {"id": "R02"}],
    "demands": [
        {
            "id": "D001",
            "src": "R01",
            "dst": "R02",
            "endpoint_type": "mmf_lc_duplex",
            "count": 2,
        }
    ],
}

result = allocate_project(project)
```

**`result.panels`**

```python
[Panel(rack_id='R01', u=1, slots_per_u=4),
 Panel(rack_id='R02', u=1, slots_per_u=4)]
```

**`result.modules`**

```python
[Module(rack_id='R01', panel_u=1, slot=1,
        module_type='lc_breakout_2xmpo12_to_12xlcduplex',
        fiber_kind='mmf', polarity_variant='AF',
        peer_rack_id='R02', dedicated=True),
 Module(rack_id='R02', panel_u=1, slot=1,
        module_type='lc_breakout_2xmpo12_to_12xlcduplex',
        fiber_kind='mmf', polarity_variant='AF',
        peer_rack_id='R01', dedicated=True)]
```

**`result.cables`**

```python
[Cable(cable_id='8707e28e...', cable_type='mpo12_trunk',
       fiber_kind='mmf', polarity_type='A',
       src_rack='R01', dst_rack='R02'),
 Cable(cable_id='8f3b41d8...', cable_type='mpo12_trunk',
       fiber_kind='mmf', polarity_type='A',
       src_rack='R01', dst_rack='R02')]
```

**`result.sessions`**

```python
[Session(session_id='b2d56de0...', media='mmf_lc_duplex',
         cable_id='8707e28e...', adapter_type='lc_breakout_2xmpo12_to_12xlcduplex',
         label_a='R01U1S1P1', label_b='R02U1S1P1',
         src_rack='R01', src_face='front', src_u=1, src_slot=1, src_port=1,
         dst_rack='R02', dst_face='front', dst_u=1, dst_slot=1, dst_port=1,
         fiber_a=1, fiber_b=2, notes=None),
 Session(session_id='1df763d4...', media='mmf_lc_duplex',
         cable_id='8707e28e...', adapter_type='lc_breakout_2xmpo12_to_12xlcduplex',
         label_a='R01U1S1P2', label_b='R02U1S1P2',
         src_rack='R01', src_face='front', src_u=1, src_slot=1, src_port=2,
         dst_rack='R02', dst_face='front', dst_u=1, dst_slot=1, dst_port=2,
         fiber_a=3, fiber_b=4, notes=None)]
```

**CSV export** (`export_session_table_csv(project_id="proj-1", sessions=result.sessions)`)

```
project_id,revision_id,session_id,media,cable_id,adapter_type,label_a,label_b,src_rack,src_face,src_u,src_slot,src_port,dst_rack,dst_face,dst_u,dst_slot,dst_port,fiber_a,fiber_b,notes
proj-1,,1df763d4...,mmf_lc_duplex,8707e28e...,lc_breakout_2xmpo12_to_12xlcduplex,R01U1S1P2,R02U1S1P2,R01,front,1,1,2,R02,front,1,1,2,3,4,
proj-1,,b2d56de0...,mmf_lc_duplex,8707e28e...,lc_breakout_2xmpo12_to_12xlcduplex,R01U1S1P1,R02U1S1P1,R01,front,1,1,1,R02,front,1,1,1,1,2,
```

**JSON export** (`export_result_json(project_id="proj-1", result=result)`)

```json
{
  "project_id": "proj-1",
  "revision_id": null,
  "metrics": {
    "total_sessions": 2,
    "sessions_by_media": {"mmf_lc_duplex": 2},
    "total_cables": 2,
    "cables_by_type": {"mpo12_trunk": 2},
    "total_modules": 2,
    "modules_by_type": {"lc_breakout_2xmpo12_to_12xlcduplex": 2},
    "total_panels": 2
  },
  "panels": [
    {"rack_id": "R01", "u": 1, "slots_per_u": 4},
    {"rack_id": "R02", "u": 1, "slots_per_u": 4}
  ],
  "modules": [ ... ],
  "cables": [ ... ],
  "sessions": [ ... ],
  "warnings": []
}
```

**SVG output** (`render_svgs(result)`)

```python
{
  "topology": '<svg xmlns="http://www.w3.org/2000/svg" data-kind="topology">...</svg>',
  "rack_panels": {
    "R01": '<svg xmlns="http://www.w3.org/2000/svg" data-kind="rack-panels" data-rack="R01">...</svg>',
    "R02": '<svg xmlns="http://www.w3.org/2000/svg" data-kind="rack-panels" data-rack="R02">...</svg>',
  },
  "pair_detail": {
    "R01_R02": '<svg xmlns="http://www.w3.org/2000/svg" data-kind="pair-detail" data-pair="R01_R02">...</svg>',
  },
}
```

## Configuration

The allocator expects a Python dictionary (or JSON) with these keys:

- `racks`: list of racks, each with a unique `id`
- `demands`: list of connection demands, each with:
  - `id`: unique demand identifier
  - `src`: source rack id
  - `dst`: destination rack id
  - `endpoint_type`: one of `mmf_lc_duplex`, `smf_lc_duplex`, `mpo12`, or `utp_rj45`
  - `count`: number of endpoints to allocate

No additional configuration files are required.

## Development

### Running Tests

```bash
# Run all tests with coverage
pytest

# Run specific test file
pytest tests/unit/test_ids_and_sorting.py

# Run with verbose output
pytest -v
```

### Code Quality Checks

```bash
# Linting
ruff check .

# Format checking
ruff format --check .

# Type checking
mypy patchwork tests

# Run all pre-commit hooks
pre-commit run --all-files
```

## Project Structure

```
patchwork-beta/
├── patchwork/              # Main package
│   ├── __init__.py
│   └── allocator.py        # Core allocation logic
├── tests/                  # Test suite
│   ├── unit/               # Unit tests
│   ├── integration/        # Integration tests
│   └── acceptance/         # Acceptance tests
├── docs/                   # Documentation
├── .github/                # GitHub Actions workflows
│   ├── workflows/
│   │   ├── ci.yml          # CI pipeline
│   │   └── codeql.yml      # Security scanning
│   └── dependabot.yml      # Dependency updates
├── pyproject.toml          # Project configuration
├── requirements.txt        # Runtime dependencies
├── requirements-dev.txt    # Development dependencies
└── .pre-commit-config.yaml # Pre-commit hooks
```

## CI/CD

This project uses GitHub Actions for continuous integration:

- **Linting**: Automated code style checks with ruff
- **Type Checking**: Static type analysis with mypy
- **Testing**: Automated test suite with pytest (98% coverage)
- **Security**: CodeQL analysis for vulnerability detection
- **Dependencies**: Automated updates via Dependabot

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

### LLM Contribution Policy

We welcome contributions created with AI/LLM assistance, but they must:

- Include proper attribution in file headers
- Be thoroughly reviewed by humans
- Pass all quality and security checks

See [CONTRIBUTING.md](CONTRIBUTING.md) for full details.

## Issues and Support

If you need help or want to report a bug:

1. Check the [documentation](#documentation) first.
2. Search existing GitHub issues.
3. Open a new issue with a clear description, steps to reproduce, and example input data.

## Documentation

Additional documentation available in the `docs/` directory:

- [Design Specification](docs/dc_rack_patch_design_spec_v0.md)
- [Testing Approach](docs/testing_approach.md)

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- This project uses AI/LLM assistance for development
- All AI-generated code is reviewed by humans for correctness and security

---
*This README was created with the assistance of an AI (Large Language Model). Human review and updates are encouraged.*

## 日本語 (Japanese Translation)

### 目次

- [概要](#概要)
- [特徴](#特徴)
- [動作環境](#動作環境)
- [依存関係](#依存関係)
- [インストール](#インストール)
- [基本的な使い方](#基本的な使い方)
- [入力スキーマ](#入力スキーマ)
- [出力の構造](#出力の構造)
- [API リファレンス](#api-リファレンス)
- [完全なサンプルと出力例](#完全なサンプルと出力例)
- [設定](#設定)
- [開発](#開発)
- [プロジェクト構成](#プロジェクト構成)
- [CI/CD](#cicd-1)
- [貢献方法](#貢献方法)
- [お問い合わせ・サポート](#お問い合わせサポート)
- [ドキュメント](#ドキュメント)
- [ライセンス](#ライセンス)
- [謝辞](#謝辞)

### 概要

このプロジェクトは、データセンターのラック内でパッチパネルモジュールとケーブルを割り当て・管理するためのツールを提供します。光ファイバー、MPO、UTP 接続の配置を最適化するのに役立ちます。

### 特徴

- 🔧 パッチパネルの自動割り当て
- 🔌 複数の接続方式に対応（LC、MPO12、UTP/RJ45）
- 📊 再現性のある決定的な割り当て
- 📈 セッション管理と CSV 出力
- 🎨 SVG 形式の可視化生成
- ✅ 型安全な Python 実装

### 動作環境

- Python 3.11 以上

### 依存関係

- 実行時依存: なし（標準ライブラリのみ）
- 開発依存: [`requirements-dev.txt`](requirements-dev.txt) を参照してください

### インストール

#### 開発用

```bash
# リポジトリをクローン
git clone https://github.com/icecake0141/patchwork-beta.git
cd patchwork-beta

# 開発用依存関係をインストール
pip install -r requirements-dev.txt

# pre-commit フックをインストール
pre-commit install
```

#### ライブラリとして利用する場合

```bash
pip install -e .
```

### 基本的な使い方

```python
from patchwork import allocate_project, export_session_table_csv, export_result_json, render_svgs

# 1. プロジェクトを定義する（ラックと接続要求）
project = {
    "racks": [{"id": "R01"}, {"id": "R02"}],
    "demands": [
        {
            "id": "D001",
            "src": "R01",
            "dst": "R02",
            "endpoint_type": "mmf_lc_duplex",
            "count": 2,
        }
    ],
}

# 2. 割り当てを実行する
result = allocate_project(project)

# 3. セッション一覧を CSV として出力する
csv_output = export_session_table_csv(project_id="proj-1", sessions=result.sessions)

# 4. 全結果を JSON として出力する
json_output = export_result_json(project_id="proj-1", result=result)

# 5. SVG 可視化を生成する
svgs = render_svgs(result)
```

### 入力スキーマ

`allocate_project` は以下の構造を持つ Python の `dict`（JSON からロード可）を受け取ります。

```python
project = {
    "racks": [
        {"id": "R01"},  # 各ラックには一意の文字列 id が必要
        {"id": "R02"},
    ],
    "demands": [
        {
            "id": "D001",           # str  – この要求の一意な識別子
            "src": "R01",           # str  – 送信元ラック id（racks に存在する必要あり）
            "dst": "R02",           # str  – 宛先ラック id（racks に存在し、src と異なる必要あり）
            "endpoint_type": "mmf_lc_duplex",  # str – 下表参照
            "count": 2,             # int  – 割り当てる端点ペア数（1 以上）
        }
    ],
}
```

#### `endpoint_type` に指定できる値

| 値 | 説明 |
|---|---|
| `mmf_lc_duplex` | マルチモードファイバー LC デュプレックス（LC ブレイクアウトモジュールと MPO-12 トランクケーブルを使用） |
| `smf_lc_duplex` | シングルモードファイバー LC デュプレックス（mmf と同じ物理構成、ファイバー種別が異なる） |
| `mpo12` | MPO-12 パススルー（MPO パススルーモジュールと MPO-12 トランクケーブルを使用） |
| `utp_rj45` | UTP / RJ-45 銅線（UTP モジュールと UTP パッチケーブルを使用。モジュールは複数のペアで共有される場合あり） |

#### バリデーションルール

- `racks[].id` は一意である必要があります。
- `demands[].src` および `demands[].dst` は存在するラック id を参照し、互いに異なる必要があります。
- `demands[].count` は正の整数である必要があります。
- 同じラックペア間の複数の要求は、割り当て前に統合されます。

### 出力の構造

`allocate_project` は 4 つのリストを持つ `AllocationResult` データクラスを返します。

```
AllocationResult
├── panels   – list[Panel]   – 各ラックで使用された U 行ごとに 1 つの Panel
├── modules  – list[Module]  – 使用された物理パッチパネルスロットごとに 1 つの Module
├── cables   – list[Cable]   – 物理ケーブルごとに 1 つの Cable
└── sessions – list[Session] – 個々のポート間接続ごとに 1 つの Session（CSV の 1 行に対応）
```

#### `Panel`（パネル）

ラックに取り付けられた 1U パッチパネル行を表します。

| フィールド | 型 | 説明 |
|---|---|---|
| `rack_id` | `str` | パネルが取り付けられているラック |
| `u` | `int` | ラックユニット位置（1 始まり） |
| `slots_per_u` | `int` | この U 内のモジュールスロット数（常に 4） |

#### `Module`（モジュール）

パネルスロットに挿入された単一モジュールを表します。

| フィールド | 型 | 説明 |
|---|---|---|
| `rack_id` | `str` | モジュールが取り付けられているラック |
| `panel_u` | `int` | 収容パネルのラックユニット |
| `slot` | `int` | パネル内のスロット番号（1 始まり） |
| `module_type` | `str` | 物理モジュール種別（例: `lc_breakout_2xmpo12_to_12xlcduplex`） |
| `fiber_kind` | `str \| None` | ファイバー種別: `"mmf"`、`"smf"`、または銅線/MPO の場合 `None` |
| `polarity_variant` | `str \| None` | 極性バリアント（`"A"`、`"AF"`、または `None`） |
| `peer_rack_id` | `str \| None` | このモジュールが接続されているラック id。共有 UTP モジュールの場合は `None` |
| `dedicated` | `bool` | 特定のラックペア専用の場合 `True` |

#### `Cable`（ケーブル）

2 つのラック間の物理ケーブルを表します。

| フィールド | 型 | 説明 |
|---|---|---|
| `cable_id` | `str` | 決定論的な 32 文字の 16 進 ID |
| `cable_type` | `str` | `"mpo12_trunk"` または `"utp_cable"` |
| `fiber_kind` | `str \| None` | `"mmf"`、`"smf"`、または `None` |
| `polarity_type` | `str \| None` | `"A"`、`"B"`、または `None` |
| `src_rack` | `str` | 送信元ラック id |
| `dst_rack` | `str` | 宛先ラック id |

#### `Session`（セッション）

個々のポート間論理接続を表します（CSV の 1 行に対応）。

| フィールド | 型 | 説明 |
|---|---|---|
| `session_id` | `str` | 決定論的な 32 文字の 16 進 ID |
| `media` | `str` | 端点種別（例: `"mmf_lc_duplex"`） |
| `cable_id` | `str` | このセッションを通す物理ケーブルの ID |
| `adapter_type` | `str` | 両端で使用されるモジュール種別 |
| `label_a` | `str` | 送信元ポートの人間可読ラベル — 形式: `{rack_id}U{u}S{slot}P{port}`（例: `R01U1S1P1`） |
| `label_b` | `str` | 宛先ポートの人間可読ラベル — `label_a` と同じ形式 |
| `src_rack` | `str` | 送信元ラック id |
| `src_face` | `str` | パネル面（`"front"`） |
| `src_u` | `int` | 送信元ラックユニット |
| `src_slot` | `int` | 送信元モジュールスロット |
| `src_port` | `int` | 送信元ポート番号（1 始まり） |
| `dst_rack` | `str` | 宛先ラック id |
| `dst_face` | `str` | パネル面（`"front"`） |
| `dst_u` | `int` | 宛先ラックユニット |
| `dst_slot` | `int` | 宛先モジュールスロット |
| `dst_port` | `int` | 宛先ポート番号（1 始まり） |
| `fiber_a` | `int \| None` | MPO トランク内のファイバーストランド A 番号。銅線の場合は `None` |
| `fiber_b` | `int \| None` | MPO トランク内のファイバーストランド B 番号。銅線の場合は `None` |
| `notes` | `str \| None` | 任意の自由記述メモ |

ラベル形式: `{rack_id}U{u}S{slot}P{port}` — 例えば `R01U1S1P3` は「ラック R01、U1、スロット 1、ポート 3」を意味します。

### API リファレンス

#### `allocate_project(project: dict) -> AllocationResult`

プロジェクト定義から決定論的なパッチパネル割り当てを計算します。  
無効な入力（重複ラック id、未知の endpoint_type など）の場合は `ValueError` を送出します。

#### `export_session_table_csv(*, project_id, sessions, revision_id=None) -> str`

1 行のヘッダーと、セッションごとに 1 行を含む CSV 文字列を返します。  
カラム: `project_id`、`revision_id`、`session_id`、`media`、`cable_id`、`adapter_type`、
`label_a`、`label_b`、`src_rack`、`src_face`、`src_u`、`src_slot`、`src_port`、
`dst_rack`、`dst_face`、`dst_u`、`dst_slot`、`dst_port`、`fiber_a`、`fiber_b`、`notes`。  
セッションは `session_id` でソートされ、安定した再現可能な出力を保証します。

#### `export_result_json(*, project_id, result, revision_id=None) -> str`

以下を含むトップレベルオブジェクトの JSON 文字列を返します:
- `project_id`、`revision_id`
- `metrics` — サマリー集計（セッション・ケーブル・モジュール・パネルの合計数と種別ごとの内訳）
- `panels`、`modules`、`cables`、`sessions` — 全リストを JSON オブジェクトで出力
- `warnings` — 予約済みリスト（現時点では常に空）

#### `render_svgs(result: AllocationResult) -> dict`

3 つのキーを持つ辞書を返します:
- `"topology"` — `str`: トポロジー全体ビューの SVG プレースホルダー
- `"rack_panels"` — `dict[str, str]`: ラック id をキーとしたラックごとの SVG
- `"pair_detail"` — `dict[str, str]`: `"{rack_a}_{rack_b}"` をキーとしたラックペアごとの SVG

### 完全なサンプルと出力例

```python
from patchwork import allocate_project, export_session_table_csv, export_result_json, render_svgs

project = {
    "racks": [{"id": "R01"}, {"id": "R02"}],
    "demands": [
        {
            "id": "D001",
            "src": "R01",
            "dst": "R02",
            "endpoint_type": "mmf_lc_duplex",
            "count": 2,
        }
    ],
}

result = allocate_project(project)
```

**`result.panels`**

```python
[Panel(rack_id='R01', u=1, slots_per_u=4),
 Panel(rack_id='R02', u=1, slots_per_u=4)]
```

**`result.modules`**

```python
[Module(rack_id='R01', panel_u=1, slot=1,
        module_type='lc_breakout_2xmpo12_to_12xlcduplex',
        fiber_kind='mmf', polarity_variant='AF',
        peer_rack_id='R02', dedicated=True),
 Module(rack_id='R02', panel_u=1, slot=1,
        module_type='lc_breakout_2xmpo12_to_12xlcduplex',
        fiber_kind='mmf', polarity_variant='AF',
        peer_rack_id='R01', dedicated=True)]
```

**`result.cables`**

```python
[Cable(cable_id='8707e28e...', cable_type='mpo12_trunk',
       fiber_kind='mmf', polarity_type='A',
       src_rack='R01', dst_rack='R02'),
 Cable(cable_id='8f3b41d8...', cable_type='mpo12_trunk',
       fiber_kind='mmf', polarity_type='A',
       src_rack='R01', dst_rack='R02')]
```

**`result.sessions`**

```python
[Session(session_id='b2d56de0...', media='mmf_lc_duplex',
         cable_id='8707e28e...', adapter_type='lc_breakout_2xmpo12_to_12xlcduplex',
         label_a='R01U1S1P1', label_b='R02U1S1P1',
         src_rack='R01', src_face='front', src_u=1, src_slot=1, src_port=1,
         dst_rack='R02', dst_face='front', dst_u=1, dst_slot=1, dst_port=1,
         fiber_a=1, fiber_b=2, notes=None),
 Session(session_id='1df763d4...', media='mmf_lc_duplex',
         cable_id='8707e28e...', adapter_type='lc_breakout_2xmpo12_to_12xlcduplex',
         label_a='R01U1S1P2', label_b='R02U1S1P2',
         src_rack='R01', src_face='front', src_u=1, src_slot=1, src_port=2,
         dst_rack='R02', dst_face='front', dst_u=1, dst_slot=1, dst_port=2,
         fiber_a=3, fiber_b=4, notes=None)]
```

**CSV 出力** (`export_session_table_csv(project_id="proj-1", sessions=result.sessions)`)

```
project_id,revision_id,session_id,media,cable_id,adapter_type,label_a,label_b,src_rack,src_face,src_u,src_slot,src_port,dst_rack,dst_face,dst_u,dst_slot,dst_port,fiber_a,fiber_b,notes
proj-1,,1df763d4...,mmf_lc_duplex,8707e28e...,lc_breakout_2xmpo12_to_12xlcduplex,R01U1S1P2,R02U1S1P2,R01,front,1,1,2,R02,front,1,1,2,3,4,
proj-1,,b2d56de0...,mmf_lc_duplex,8707e28e...,lc_breakout_2xmpo12_to_12xlcduplex,R01U1S1P1,R02U1S1P1,R01,front,1,1,1,R02,front,1,1,1,1,2,
```

**JSON 出力** (`export_result_json(project_id="proj-1", result=result)`)

```json
{
  "project_id": "proj-1",
  "revision_id": null,
  "metrics": {
    "total_sessions": 2,
    "sessions_by_media": {"mmf_lc_duplex": 2},
    "total_cables": 2,
    "cables_by_type": {"mpo12_trunk": 2},
    "total_modules": 2,
    "modules_by_type": {"lc_breakout_2xmpo12_to_12xlcduplex": 2},
    "total_panels": 2
  },
  "panels": [
    {"rack_id": "R01", "u": 1, "slots_per_u": 4},
    {"rack_id": "R02", "u": 1, "slots_per_u": 4}
  ],
  "modules": [ ... ],
  "cables": [ ... ],
  "sessions": [ ... ],
  "warnings": []
}
```

**SVG 出力** (`render_svgs(result)`)

```python
{
  "topology": '<svg xmlns="http://www.w3.org/2000/svg" data-kind="topology">...</svg>',
  "rack_panels": {
    "R01": '<svg xmlns="http://www.w3.org/2000/svg" data-kind="rack-panels" data-rack="R01">...</svg>',
    "R02": '<svg xmlns="http://www.w3.org/2000/svg" data-kind="rack-panels" data-rack="R02">...</svg>',
  },
  "pair_detail": {
    "R01_R02": '<svg xmlns="http://www.w3.org/2000/svg" data-kind="pair-detail" data-pair="R01_R02">...</svg>',
  },
}
```

### 設定

アロケータは以下のキーを含む Python の辞書（または JSON）を受け取ります。

- `racks`: `id` を持つラックの一覧（`id` は一意）
- `demands`: 接続要求の一覧。各要素は以下を含みます:
  - `id`: 要求の識別子
  - `src`: 送信元ラック ID
  - `dst`: 宛先ラック ID
  - `endpoint_type`: `mmf_lc_duplex`、`smf_lc_duplex`、`mpo12`、`utp_rj45` のいずれか
  - `count`: 割り当てる端点数

追加の設定ファイルは不要です。

### 開発

#### テストの実行

```bash
# すべてのテストをカバレッジ付きで実行
pytest

# 特定のテストファイルを実行
pytest tests/unit/test_ids_and_sorting.py

# 詳細出力で実行
pytest -v
```

#### コード品質チェック

```bash
# リント
ruff check .

# フォーマットチェック
ruff format --check .

# 型チェック
mypy patchwork tests

# pre-commit フックをすべて実行
pre-commit run --all-files
```

### プロジェクト構成

```
patchwork-beta/
├── patchwork/              # メインパッケージ
│   ├── __init__.py
│   └── allocator.py        # 割り当てロジック
├── tests/                  # テストスイート
│   ├── unit/               # ユニットテスト
│   ├── integration/        # 統合テスト
│   └── acceptance/         # 受け入れテスト
├── docs/                   # ドキュメント
├── .github/                # GitHub Actions ワークフロー
│   ├── workflows/
│   │   ├── ci.yml          # CI パイプライン
│   │   └── codeql.yml      # セキュリティスキャン
│   └── dependabot.yml      # 依存関係の更新
├── pyproject.toml          # プロジェクト設定
├── requirements.txt        # 実行時依存
├── requirements-dev.txt    # 開発用依存
└── .pre-commit-config.yaml # pre-commit フック
```

### CI/CD

このプロジェクトは GitHub Actions による継続的インテグレーションを使用しています。

- **Linting**: ruff によるコードスタイルチェック
- **Type Checking**: mypy による静的型解析
- **Testing**: pytest による自動テスト（カバレッジ 98%）
- **Security**: CodeQL による脆弱性検出
- **Dependencies**: Dependabot による依存関係の更新

### 貢献方法

貢献に関する詳細は [CONTRIBUTING.md](CONTRIBUTING.md) をご確認ください。行動規範やプルリクエストの手順が記載されています。

#### LLM 生成コードに関する方針

AI/LLM の支援を受けた貢献も歓迎しますが、以下を満たす必要があります。

- ファイルヘッダーに適切な帰属表記を含める
- 人による十分なレビューを行う
- 品質・セキュリティチェックをすべて通過する

詳細は [CONTRIBUTING.md](CONTRIBUTING.md) を参照してください。

### お問い合わせ・サポート

質問や不具合報告がある場合は、次の手順をお試しください。

1. まず [ドキュメント](#ドキュメント) を確認する
2. 既存の GitHub Issues を検索する
3. 新しい Issue を作成し、状況の説明、再現手順、入力データ例を記載する

### ドキュメント

`docs/` ディレクトリに追加のドキュメントがあります。

- [設計仕様](docs/dc_rack_patch_design_spec_v0.md)
- [テスト方針](docs/testing_approach.md)

### ライセンス

このプロジェクトは Apache License 2.0 で提供されています。詳細は [LICENSE](LICENSE) を参照してください。

### 謝辞

- このプロジェクトは AI/LLM の支援を受けて開発されています
- AI が生成したコードは、人が確認し、正確性と安全性を担保しています

---
*この README は AI（Large Language Model）の支援を受けて作成されました。人によるレビューと更新を歓迎します。*
