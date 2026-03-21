# cortex/security/secrets_scanner.py

> ⚡ **Fresh** — analyzed 2026-03-21 21:50 UTC

## Overview
Language: python | Constructs: 2
Key imports: re, git, dataclasses

## Historical Insights
- [Bug Fix] 2026-03-21: perf+fix: parallel analysis, file caching, status/clean commands, fix imports, better secrets scanner, --no-llm/--max-files flags
  Change: cortex/security/secrets_scanner.py | 24 +++++++++++++++++++++---

## Key Constructs
- **SecretFinding** (class, line 33)
- **scan_git_history** (function, line 39)

## Related Files
- `.claude/docs/SUMMARY.md` [co-change: 100%]
- `cortex/cli.py` [co-change: 100%]
- `cortex/core.py` [co-change: 100%]
- `cortex/generators/markdown_gen.py` [co-change: 100%]
- `cortex/__init__.py` [co-change: 100%]

## Security Notes
- ✅ No issues found
