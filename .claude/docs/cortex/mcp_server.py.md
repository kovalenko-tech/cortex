# cortex/mcp_server.py

> ⚡ **Fresh** — analyzed 2026-03-21 21:55 UTC

> 🟡 **MEDIUM RISK** (score: 25/100) — no test coverage

## Overview
Language: python | Constructs: 4
Key imports: json, sys, os, pathlib

## Key Constructs
- **get_context_for_file** (function, line 20) — Read .claude/docs/<file>.md if it exists.
- **run_mcp_server** (function, line 28) — Run MCP server on stdio.
- **send** (function, line 32)
- **error_response** (function, line 36)

## Related Files
- `.claude/docs/SUMMARY.md` [co-change: 100%]
- `.claude/docs/cortex/__init__.py.md` [co-change: 100%]
- `.claude/docs/cortex/__main__.py.md` [co-change: 100%]
- `.claude/docs/cortex/analyzers/__init__.py.md` [co-change: 100%]
- `.claude/docs/cortex/analyzers/base.py.md` [co-change: 100%]

## Security Notes
- ✅ No issues found
