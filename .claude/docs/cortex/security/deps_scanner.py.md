# cortex/security/deps_scanner.py

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

## Security Notes
- ✅ No issues found
