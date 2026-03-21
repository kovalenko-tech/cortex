# codeprep/core.py

## Overview
Language: python | Constructs: 5
Key imports: os, pathlib, rich.console, rich.progress, miners

## Key Constructs
- **get_changed_files** (function, line 6) — Return set of relative file paths changed since `since` (e.g. HEAD~10, 2024-01-01).
- **discover_files** (function, line 45) — Find all analyzable source files in repo.
- **CodePrep** (class, line 75)
- **analyze** (function, line 76)
- **_write_helper** (function, line 175)

## Related Files
- `.claude/docs/SECURITY_REPORT.md` [co-change: 100%]
- `.claude/docs/SUMMARY.md` [co-change: 100%]
- `.claude/docs/codeprep/__init__.py.md` [co-change: 100%]
- `.claude/docs/codeprep/analyzers/__init__.py.md` [co-change: 100%]
- `.claude/docs/codeprep/analyzers/base.py.md` [co-change: 100%]

## Security Notes
- ✅ No issues found
