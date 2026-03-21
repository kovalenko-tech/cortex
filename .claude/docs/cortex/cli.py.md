# cortex/cli.py

## Overview
Language: python | Constructs: 10
Key imports: click, pathlib, rich.console, core, pathlib

## Key Constructs
- **cli** (function, line 11) — Cortex — generates .claude/docs/ context for Claude Code.
- **analyze** (function, line 20) — Analyze repository and generate .claude/docs/ context.
- **context** (function, line 28) — Print context for a specific file.
- **security** (function, line 40) — Run security audit only.
- **install_hook** (function, line 63) — Install git pre-commit hook to auto-update .claude/docs/ on each commit.
- **watch** (function, line 84) — Watch for file changes and auto-update context.
- **init** (function, line 111) — Generate CLAUDE.md for your project.
- **mcp** (function, line 130) — Start Cortex MCP server (for Claude Code integration).

## Related Files
- `.cortexignore.example` [co-change: 100%]
- `CLAUDE.md` [co-change: 100%]
- `PLAN.md` [co-change: 100%]
- `cortex/core.py` [co-change: 100%]
- `cortex/generators/claude_md_gen.py` [co-change: 100%]

## Security Notes
- ✅ No issues found
