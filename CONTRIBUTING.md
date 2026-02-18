# SPDX-License-Identifier: Apache-2.0
# This file was created or modified with the assistance of an AI (Large Language Model). Review for correctness and security.  # noqa: E501

# Contributing to patchwork-beta

Thank you for your interest in contributing to patchwork-beta! This document provides guidelines for contributing to the project.

## Code of Conduct

Be respectful, inclusive, and professional in all interactions within this project.

## Development Setup

### Prerequisites
- Python 3.11 or later
- pip
- git

### Setup Instructions

1. Clone the repository:
```bash
git clone https://github.com/icecake0141/patchwork-beta.git
cd patchwork-beta
```

2. Install development dependencies:
```bash
pip install -r requirements-dev.txt
```

3. Install pre-commit hooks:
```bash
pre-commit install
```

## Development Workflow

### Before Making Changes

1. Create a new branch for your work:
```bash
git checkout -b feature/your-feature-name
```

2. Make sure all existing tests pass:
```bash
pytest
```

### While Making Changes

1. Follow the project's code style:
   - Run `ruff check .` for linting
   - Run `ruff format .` for formatting
   - Run `mypy patchwork tests` for type checking

2. Write tests for new functionality

3. Keep commits focused and write clear commit messages

### Before Submitting

1. Run all quality checks:
```bash
# Linting
ruff check .

# Formatting
ruff format --check .

# Type checking
mypy patchwork tests

# Tests with coverage
pytest

# Pre-commit hooks
pre-commit run --all-files
```

2. Ensure all tests pass and coverage remains high (target: >95%)

## LLM Contribution Policy

### Using AI/LLM Tools

We welcome contributions created with the assistance of AI/Large Language Models (LLMs), but they must follow specific guidelines:

#### Required Attribution

**All files** created or significantly modified with LLM assistance MUST include:

1. **SPDX License Header**:
```python
# SPDX-License-Identifier: Apache-2.0
```

2. **LLM Attribution Comment** (on the next line):
```python
# This file was created or modified with the assistance of an AI (Large Language Model). Review for correctness and security.  # noqa: E501
```

For YAML files:
```yaml
# SPDX-License-Identifier: Apache-2.0
# This file was created or modified with the assistance of an AI (Large Language Model). Review for correctness and security.
```

#### Pull Request Requirements

When submitting a PR involving LLM assistance:

1. **Mark LLM involvement** in the PR template
2. **Describe the scope** of LLM assistance (e.g., "Generated test cases", "Refactored function X")
3. **Verification commands** must be provided so reviewers can test the changes
4. **Human review required** - all LLM-assisted PRs require thorough human review

#### Quality Standards

Code generated with LLM assistance must meet the same quality standards as human-written code:

- ✅ Pass all linting checks
- ✅ Pass all type checking
- ✅ Pass all tests
- ✅ Maintain or improve code coverage
- ✅ Follow project conventions
- ✅ Be well-documented
- ✅ Pass security scans (CodeQL, dependency checks)

#### Security Considerations

⚠️ **Extra vigilance required** for LLM-generated code:

- Review for security vulnerabilities
- Verify input validation
- Check for proper error handling
- Ensure no hardcoded secrets or credentials
- Validate all external dependencies

### Why This Policy?

1. **Transparency**: Users and contributors should know when AI was involved
2. **Accountability**: Human review ensures quality and security
3. **Learning**: Understanding AI limitations helps improve the codebase
4. **Legal**: Proper attribution helps with licensing and intellectual property

## Submitting Changes

1. Push your branch to GitHub:
```bash
git push origin feature/your-feature-name
```

2. Open a Pull Request on GitHub

3. Fill out the PR template completely:
   - Description of changes
   - LLM involvement (if any)
   - Testing performed
   - Verification commands

4. Wait for review and address feedback

## CI/CD Pipeline

All PRs automatically run:

- **Linting** (ruff)
- **Format checking** (ruff)
- **Type checking** (mypy)
- **Tests** (pytest with coverage)
- **Security scanning** (CodeQL)

PRs must pass all checks before merging.

## Questions?

If you have questions about contributing, please:
1. Check existing documentation
2. Review closed issues for similar questions
3. Open a new issue with the "question" label

## License

By contributing to this project, you agree that your contributions will be licensed under the Apache License 2.0.

---
*This contributing guide was created with the assistance of an AI (Large Language Model). Human review and updates are encouraged.*
