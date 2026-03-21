# cortex/core.py

## Overview
Language: python | Constructs: 5
Key imports: os, pathlib, rich.console, rich.progress, miners

## Key Constructs
- **get_changed_files** (function, line 6) — Return set of relative file paths changed since `since` (e.g. HEAD~10, 2024-01-01).
- **discover_files** (function, line 45) — Find all analyzable source files in repo.
- **Cortex** (class, line 95)
- **analyze** (function, line 96)
- **_write_helper** (function, line 196)

## Related Files
- `.cortexignore.example` [co-change: 100%]
- `CLAUDE.md` [co-change: 100%]
- `PLAN.md` [co-change: 100%]
- `cortex/cli.py` [co-change: 100%]
- `cortex/generators/claude_md_gen.py` [co-change: 100%]

## Security Notes
- ✅ No issues found
