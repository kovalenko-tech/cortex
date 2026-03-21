# cortex/cli.py

## Overview
Language: python | Constructs: 13
Key imports: click, pathlib, rich.console, core, pathlib

## Historical Insights
- [Bug Fix] 2026-03-21: perf+fix: parallel analysis, file caching, status/clean commands, fix imports, better secrets scanner, --no-llm/--max-files flags
  Change: cortex/cli.py | 83 +++++++++++++++++++++++++++++++++++++++++++++++++++++++++--

## Key Constructs
- **cli** (function, line 11) — Cortex — generates .claude/docs/ context for Claude Code.
- **analyze** (function, line 23) — Analyze repository and generate .claude/docs/ context.
- **context** (function, line 34) — Print context for a specific file.
- **security** (function, line 46) — Run security audit only.
- **install_hook** (function, line 69) — Install git pre-commit hook to auto-update .claude/docs/ on each commit.
- **watch** (function, line 90) — Watch for file changes and auto-update context.
- **init** (function, line 117) — Generate CLAUDE.md for your project.
- **setup** (function, line 137) — Interactive setup wizard — analyze project and configure Claude Code integration.

## Related Files
- `.claude/docs/cortex/core.py.md` [co-change: 100%]
- `cortex/core.py` [co-change: 100%]
- `cortex/generators/markdown_gen.py` [co-change: 100%]
- `cortex/security/secrets_scanner.py` [co-change: 100%]
- `.claude/docs/cortex/__init__.py.md` [co-change: 100%]

## Security Notes
- ✅ No issues found
