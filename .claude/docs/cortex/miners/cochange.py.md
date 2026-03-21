# cortex/miners/cochange.py

> ⚡ **Fresh** — analyzed 2026-03-21 21:55 UTC

> 🟡 **MEDIUM RISK** (score: 25/100) — no test coverage

## Overview
Language: python | Constructs: 2
Key imports: collections, git

## Key Constructs
- **get_cochange_map** (function, line 6) — Return {file: {related_file: score}} for the whole repo.
- **get_related_files** (function, line 45) — Return top N related files for a given file, sorted by score desc.

## Related Files
- `.claude/docs/SUMMARY.md` [co-change: 100%]
- `cortex/cli.py` [co-change: 100%]
- `cortex/core.py` [co-change: 100%]
- `cortex/generators/markdown_gen.py` [co-change: 100%]
- `cortex/generators/summary_gen.py` [co-change: 100%]

## Security Notes
- ✅ No issues found
