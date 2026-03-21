# cortex/risk.py

> ⚡ **Fresh** — analyzed 2026-03-21 21:55 UTC

> 🟡 **MEDIUM RISK** (score: 25/100) — no test coverage

## Overview
Language: python | Constructs: 4
Key imports: os, dataclasses, pathlib, git

## Key Constructs
- **RiskScore** (class, line 8)
- **compute_risk_score** (function, line 21) — Compute risk score 0-100 based on multiple factors.
- **get_change_count** (function, line 96) — Count total number of commits that touched this file.
- **build_dependents_map** (function, line 107) — Build a map of {file: number_of_other_files_that_import_it}.

## Security Notes
- ✅ No issues found
