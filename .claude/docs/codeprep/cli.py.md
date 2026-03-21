# cortex/cli.py

## Overview
Language: python | Constructs: 6
Key imports: click, pathlib, rich.console, core, pathlib

## Key Constructs
- **cli** (function, line 11) — Cortex — generates .claude/docs/ context for Claude Code.
- **analyze** (function, line 20) — Analyze repository and generate .claude/docs/ context.
- **context** (function, line 28) — Print context for a specific file.
- **security** (function, line 40) — Run security audit only.
- **install_hook** (function, line 63) — Install git pre-commit hook to auto-update .claude/docs/ on each commit.
- **watch** (function, line 84) — Watch for file changes and auto-update context.

## Related Files
- `.claude/docs/SECURITY_REPORT.md` [co-change: 100%]
- `.claude/docs/SUMMARY.md` [co-change: 100%]
- `.claude/docs/cortex/__init__.py.md` [co-change: 100%]
- `.claude/docs/cortex/analyzers/__init__.py.md` [co-change: 100%]
- `.claude/docs/cortex/analyzers/base.py.md` [co-change: 100%]

## Security Notes
- ✅ No issues found
