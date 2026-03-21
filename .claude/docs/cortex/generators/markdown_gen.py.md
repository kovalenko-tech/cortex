# cortex/generators/markdown_gen.py

## Overview
Language: python | Constructs: 2
Key imports: os, pathlib, miners.git_history, analyzers.base, security.bandit_runner

## Historical Insights
- [Bug Fix] 2026-03-21: perf+fix: parallel analysis, file caching, status/clean commands, fix imports, better secrets scanner, --no-llm/--max-files flags
  Change: cortex/generators/markdown_gen.py | 3 ++-

## Key Constructs
- **generate** (function, line 11)
- **write_doc** (function, line 102)

## Related Files
- `.claude/docs/SUMMARY.md` [co-change: 100%]
- `cortex/cli.py` [co-change: 100%]
- `cortex/core.py` [co-change: 100%]
- `cortex/security/secrets_scanner.py` [co-change: 100%]
- `cortex/__init__.py` [co-change: 100%]

## Security Notes
- ✅ No issues found
