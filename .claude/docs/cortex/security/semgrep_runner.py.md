# cortex/security/semgrep_runner.py

> ⚡ **Fresh** — analyzed 2026-03-21 21:55 UTC

> 🟡 **MEDIUM RISK** (score: 25/100) — no test coverage

## Overview
Language: python | Constructs: 2
Key imports: json, subprocess, shutil, dataclasses

## Key Constructs
- **SemgrepIssue** (class, line 9)
- **run_semgrep** (function, line 16) — Run semgrep if available. Returns [] otherwise.

## Related Files
- `.claude/docs/SUMMARY.md` [co-change: 100%]
- `cortex/cli.py` [co-change: 100%]
- `cortex/core.py` [co-change: 100%]
- `cortex/generators/markdown_gen.py` [co-change: 100%]
- `cortex/generators/summary_gen.py` [co-change: 100%]

## Security Notes
- ✅ No issues found
