# SPDX-License-Identifier: Apache-2.0
<!-- This file was created or modified with the assistance of an AI (Large Language Model). Review for correctness and security. -->

# patchwork-beta

Data center rack patch panel allocation and cable management system.

[![CI](https://github.com/icecake0141/patchwork-beta/actions/workflows/ci.yml/badge.svg)](https://github.com/icecake0141/patchwork-beta/actions/workflows/ci.yml)
[![CodeQL](https://github.com/icecake0141/patchwork-beta/actions/workflows/codeql.yml/badge.svg)](https://github.com/icecake0141/patchwork-beta/actions/workflows/codeql.yml)

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

## Usage

```python
from patchwork import allocate_project, render_sessions_csv, render_svgs

# Define your project
project = {
    "racks": [{"id": "R01"}, {"id": "R02"}],
    "demands": [
        {"id": "D001", "src": "R01", "dst": "R02", "endpoint_type": "mmf_lc_duplex", "count": 24}
    ],
}

# Allocate resources
result = allocate_project(project)

# Export as CSV
csv_output = render_sessions_csv("proj-1", result.sessions)

# Generate SVG visualizations
svgs = render_svgs(result)
```

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

### Project Structure

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
