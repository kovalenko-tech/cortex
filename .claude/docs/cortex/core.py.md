# cortex/core.py

> ⚡ **Fresh** — analyzed 2026-03-21 21:55 UTC

> 🟡 **MEDIUM RISK** (score: 35/100) — 2 bug fixes in history · no test coverage

## Overview
Language: python | Constructs: 10
Key imports: os, hashlib, json, concurrent.futures, pathlib

## Historical Insights
- [Bug Fix] 2026-03-21: perf+fix: parallel analysis, file caching, status/clean commands, fix imports, better secrets scanner, --no-llm/--max-files flags
  Change: cortex/core.py | 226 +++++++++++++++++++++++++++++++++++++--------------------
- [Bug Fix] 2026-03-21: fix: cortex diff — handle branch...HEAD and branch..HEAD syntax correctly
  Change: cortex/core.py | 16 ++++++++++++++--

## Key Constructs
- **load_cache** (function, line 39)
- **save_cache** (function, line 49)
- **file_hash** (function, line 56)
- **get_changed_files** (function, line 63) — Return set of relative file paths changed since `since`.

Supports:
- HEAD~10 (last 10 commits)
- main...HEAD (diff vs b
- **discover_files** (function, line 86) — Find all analyzable source files in repo.
- **Cortex** (class, line 136)
- **_analyze_file** (function, line 137) — Analyze a single file — runs in thread pool.
- **_print_completion** (function, line 215)

## Related Files
- `.claude/docs/cortex/__init__.py.md` [co-change: 100%]
- `.claude/docs/cortex/__main__.py.md` [co-change: 100%]
- `.claude/docs/cortex/analyzers/__init__.py.md` [co-change: 100%]
- `.claude/docs/cortex/analyzers/base.py.md` [co-change: 100%]
- `.claude/docs/cortex/analyzers/dart_analyzer.py.md` [co-change: 100%]

## Security Notes
- ✅ No issues found
