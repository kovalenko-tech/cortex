# cortex/security/bandit_runner.py

## Overview
Language: python | Constructs: 3
Key imports: json, subprocess, shutil, dataclasses, bandit

## Key Constructs
- **SecurityIssue** (class, line 9)
- **run_bandit** (function, line 16) — Run bandit on a Python file. Returns [] if bandit not installed.
- **_bandit_available** (function, line 40)

## Related Files
- `README.md` [co-change: 100%]
- `.claude/docs/SUMMARY.md` [co-change: 100%]
- `cortex/cli.py` [co-change: 100%]
- `cortex/core.py` [co-change: 100%]
- `cortex/generators/markdown_gen.py` [co-change: 100%]

## Security Notes
- ✅ No issues found
