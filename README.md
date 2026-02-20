# SPDX-License-Identifier: Apache-2.0
<!-- This file was created or modified with the assistance of an AI (Large Language Model). Review for correctness and security. -->

# patchwork-beta

Data center rack patch panel allocation and cable management system.

[![CI](https://github.com/icecake0141/patchwork-beta/actions/workflows/ci.yml/badge.svg)](https://github.com/icecake0141/patchwork-beta/actions/workflows/ci.yml)
[![CodeQL](https://github.com/icecake0141/patchwork-beta/actions/workflows/codeql.yml/badge.svg)](https://github.com/icecake0141/patchwork-beta/actions/workflows/codeql.yml)

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Requirements](#requirements)
- [Dependencies](#dependencies)
- [Installation](#installation)
- [Basic Usage](#basic-usage)
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
from patchwork import allocate_project, export_session_table_csv, render_svgs

project = {
    "racks": [{"id": "R01"}, {"id": "R02"}],
    "demands": [
        {
            "id": "D001",
            "src": "R01",
            "dst": "R02",
            "endpoint_type": "mmf_lc_duplex",
            "count": 24,
        }
    ],
}

result = allocate_project(project)

csv_output = export_session_table_csv("proj-1", result.sessions)

svgs = render_svgs(result)
```

## Configuration

The allocator expects a Python dictionary (or JSON) with these keys:

- `racks`: list of racks, each with a unique `id`
- `demands`: list of connection demands, each with:
  - `id`: unique demand identifier
  - `src`: source rack id
  - `dst`: destination rack id
  - `endpoint_type`: one of `mmf_lc_duplex`, `mpo12`, or `utp_rj45`
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
from patchwork import allocate_project, export_session_table_csv, render_svgs

project = {
    "racks": [{"id": "R01"}, {"id": "R02"}],
    "demands": [
        {
            "id": "D001",
            "src": "R01",
            "dst": "R02",
            "endpoint_type": "mmf_lc_duplex",
            "count": 24,
        }
    ],
}

result = allocate_project(project)

csv_output = export_session_table_csv("proj-1", result.sessions)

svgs = render_svgs(result)
```

### 設定

アロケータは以下のキーを含む Python の辞書（または JSON）を受け取ります。

- `racks`: `id` を持つラックの一覧（`id` は一意）
- `demands`: 接続要求の一覧。各要素は以下を含みます:
  - `id`: 要求の識別子
  - `src`: 送信元ラック ID
  - `dst`: 宛先ラック ID
  - `endpoint_type`: `mmf_lc_duplex`、`mpo12`、`utp_rj45` のいずれか
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
