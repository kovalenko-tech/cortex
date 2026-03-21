# cortex/miners/cochange.py

## Overview
Language: python | Constructs: 2
Key imports: collections, git

## Key Constructs
- **get_cochange_map** (function, line 6) — Return {file: {related_file: score}} for the whole repo.
- **get_related_files** (function, line 45) — Return top N related files for a given file, sorted by score desc.

## Related Files
- `.claude/docs/SECURITY_REPORT.md` [co-change: 100%]
- `.claude/docs/SUMMARY.md` [co-change: 100%]
- `.claude/docs/cortex/__init__.py.md` [co-change: 100%]
- `.claude/docs/cortex/analyzers/__init__.py.md` [co-change: 100%]
- `.claude/docs/cortex/analyzers/base.py.md` [co-change: 100%]

## Security Notes
- ✅ No issues found
