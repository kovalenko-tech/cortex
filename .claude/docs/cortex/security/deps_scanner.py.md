# cortex/security/deps_scanner.py

> ⚡ **Fresh** — analyzed 2026-03-21 21:55 UTC

> 🟡 **MEDIUM RISK** (score: 25/100) — no test coverage

## Overview
Language: python | Constructs: 6
Key imports: subprocess, json, shutil, os, pathlib

## Key Constructs
- **DepIssue** (class, line 11)
- **scan_python_deps** (function, line 19) — Run pip-audit if available.
- **scan_node_deps** (function, line 54) — Run npm audit if package.json exists.
- **scan_flutter_deps** (function, line 80) — Check flutter pub outdated for outdated packages.
- **scan_all_deps** (function, line 107)
- **write_deps_report** (function, line 111) — Write .claude/docs/DEPENDENCIES.md

## Related Files
- `.claude/docs/SUMMARY.md` [co-change: 100%]
- `.claude/docs/cortex/__init__.py.md` [co-change: 100%]
- `.claude/docs/cortex/__main__.py.md` [co-change: 100%]
- `.claude/docs/cortex/analyzers/__init__.py.md` [co-change: 100%]
- `.claude/docs/cortex/analyzers/base.py.md` [co-change: 100%]

## Security Notes
- ✅ No issues found
