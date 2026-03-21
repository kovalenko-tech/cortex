# cortex/freshness.py

> ⚡ **Fresh** — analyzed 2026-03-21 21:50 UTC

## Overview
Language: python | Constructs: 5
Key imports: os, json, datetime, pathlib, dataclasses

## Key Constructs
- **FreshnessInfo** (class, line 11)
- **get_commits_since** (function, line 20) — Count commits to a file since a given ISO timestamp.
- **compute_freshness** (function, line 39) — Return (score, icon) based on age and commits since analysis.
- **get_file_freshness** (function, line 60) — Get freshness info for a single file.
- **load_cortex_cache** (function, line 109)

## Security Notes
- ✅ No issues found
