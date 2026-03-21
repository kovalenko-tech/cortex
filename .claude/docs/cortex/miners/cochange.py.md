# cortex/miners/cochange.py

## Overview
Language: python | Constructs: 2
Key imports: collections, git

## Key Constructs
- **get_cochange_map** (function, line 6) — Return {file: {related_file: score}} for the whole repo.
- **get_related_files** (function, line 45) — Return top N related files for a given file, sorted by score desc.

## Related Files
- `PLAN.md` [co-change: 100%]
- `cortex/cli.py` [co-change: 100%]
- `cortex/core.py` [co-change: 100%]
- `README.md` [co-change: 100%]
- `.claude/docs/SECURITY_REPORT.md` [co-change: 100%]

## Security Notes
- ✅ No issues found
