# cortex/cli.py

> ⚡ **Fresh** — analyzed 2026-03-21 21:55 UTC

> 🟡 **MEDIUM RISK** (score: 25/100) — no test coverage

## Overview
Language: python | Constructs: 15
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
- **risks** (function, line 90) — Show risk scores for all analyzed files.
- **freshness** (function, line 176) — Show how fresh the context is for each file.
- **watch** (function, line 247) — Watch for file changes and auto-update context.

## Related Files
- `.claude/docs/cortex/__init__.py.md` [co-change: 100%]
- `.claude/docs/cortex/__main__.py.md` [co-change: 100%]
- `.claude/docs/cortex/analyzers/__init__.py.md` [co-change: 100%]
- `.claude/docs/cortex/analyzers/base.py.md` [co-change: 100%]
- `.claude/docs/cortex/analyzers/dart_analyzer.py.md` [co-change: 100%]

## Security Notes
- ✅ No issues found
