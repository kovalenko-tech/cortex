# cortex/freshness.py

> ⚡ **Fresh** — analyzed 2026-03-21 21:55 UTC

> 🟡 **MEDIUM RISK** (score: 25/100) — no test coverage

## Overview
Language: python | Constructs: 5
Key imports: os, json, datetime, pathlib, dataclasses

## Key Constructs
- **FreshnessInfo** (class, line 11)
- **get_commits_since** (function, line 20) — Count commits to a file since a given ISO timestamp.
- **compute_freshness** (function, line 39) — Return (score, icon) based on age and commits since analysis.
- **get_file_freshness** (function, line 60) — Get freshness info for a single file.
- **load_cortex_cache** (function, line 109)

## Related Files
- `.claude/docs/SUMMARY.md` [co-change: 100%]
- `.claude/docs/cortex/__init__.py.md` [co-change: 100%]
- `.claude/docs/cortex/__main__.py.md` [co-change: 100%]
- `.claude/docs/cortex/analyzers/__init__.py.md` [co-change: 100%]
- `.claude/docs/cortex/analyzers/base.py.md` [co-change: 100%]

## Security Notes
- ✅ No issues found
