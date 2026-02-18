<!-- SPDX-License-Identifier: Apache-2.0 -->

# AI-Generated Content Notice

This file was created or modified with the assistance of an AI (Large Language Model). Review for correctness and security.

## Testing approach and coverage

The test suite is organized into unit, integration, and acceptance tests under `tests/` and targets the behaviors outlined in the design specification:

- **Unit tests** verify deterministic helpers (natural sorting and ID hashing).
- **Integration tests** exercise deterministic allocation, module/slot placement, session table export formatting, port alignment, and SVG output structure.
- **Acceptance tests** implement the §14 scenarios (LC breakout scaling, MPO slot capacity, UTP tail sharing, and mixed-in-U behavior).

Run the suite with:

```bash
python -m unittest discover
```
