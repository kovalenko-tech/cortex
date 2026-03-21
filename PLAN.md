# CodePrep — Project Knowledge Base Generator for Claude Code

> runs locally, free, supports Python / TypeScript / Dart / Go.  
> Generates `.claude/docs/` context files used by Claude Code on every session.

---

## Goal

When Claude Code opens a file it should immediately know:
- Which bugs occurred in this file and how they were fixed
- Which tests to run after making changes
- Which pitfalls and hidden dependencies exist
- Which files historically break together (co-change)
- Whether there are security issues in this file

---

## Algorithm (4 modules)

### 1. Git History Mining

**What we do:** analyze every commit that touched each file.

```bash
git log --follow --diff-filter=M --format="%H|%s|%ae|%ad" -- <file>
git show <commit> -- <file>   # get the diff
```

**We extract:**
- Bug fix commits — keywords: `fix`, `bug`, `hotfix`, `patch`, `resolve`
- Refactor commits — keywords: `refactor`, `cleanup`, `improve`
- Root cause from commit message
- Actual diff — what exactly changed

**Output:**
```markdown
### Historical Insights
- [Bug Fix] 2024-03-15: Null pointer on session init
  Commit: "fix: session fails on UTC+0 timezone"
  Change: Added .timezone.utc to datetime comparison
```

---

### 2. Co-change Analysis

**What we do:** find files that changed together.

```bash
git log --name-only --format=""   # list of files per commit
```

**Algorithm:**
1. For each commit — collect the list of changed files
2. Build a co-change matrix: how many times did file A and file B change together
3. Normalize: `score = co_changes / min(changes_A, changes_B)`
4. If score > 0.3 — files are related

**Output:**
```markdown
### Related Files
- `auth/session.py` [co-change: 78%] — if you touch auth.py, review session.py
- `tests/test_auth.py` [co-change: 92%] — tests for this file
```

---

### 3. Static Analysis (AST + Call Graph)

**What we do:** analyze code structure without executing it.

**Per language:**
| Language | Tool |
|----------|------|
| Python | `ast` + `rope` / `jedi` |
| TypeScript / JS | `tree-sitter` + `madge` |
| Dart / Flutter | `tree-sitter-dart` + `dart analyze` |
| Go | `go/ast` + `go/callgraph` |

**We extract:**
- Functions and their callers / callees
- Imports and module dependencies
- Public API surface of the file
- Tests that cover this file

**Output:**
```markdown
### Key Constructs
- **authenticate(email, password)** → JWT token
  Called by: api/routes.py:42 (login_handler)
  Tests: tests/test_auth.py::test_login_success

### Edit Checklist
- Run: `pytest tests/test_auth.py -q`
- Check constant: SESSION_TIMEOUT in config/settings.py
```

---

### 4. Security Audit

**What we do:** SAST analysis per file.

**Tools per language:**
| Language | Tool | Detects |
|----------|------|---------|
| Python | `bandit` | SQL injection, unsafe eval, hardcoded secrets |
| JS / TS | `eslint-plugin-security` + `semgrep` | XSS, prototype pollution |
| Dart | `dart analyze` + custom semgrep rules | Insecure storage, http:// |
| All | `semgrep` (OWASP ruleset) | Universal SAST |
| Git history | `gitleaks` | Leaked API keys, tokens, passwords |

**Output:**
```markdown
### Security Notes
- ⚠️ [MEDIUM] Line 47: User input passed to SQL query without sanitization
  Rule: B608 (bandit) — use parameterized queries
- ⚠️ [LOW] Line 12: Hardcoded timeout — consider moving to config
- ✅ No secrets found in git history
```

---

## Output Structure

```
project/
  .claude/
    docs/
      src/
        auth.py.md
        models/user.py.md
        api/routes.py.md
      SUMMARY.md           # full project overview
      SECURITY_REPORT.md   # all security issues in one place
    get_context.py         # helper script for Claude Code
  CLAUDE.md                # instructions for Claude Code
```

### Per-file .md format

```markdown
# src/auth.py

## Overview
Authentication module. Handles login, token validation, session management.

## Historical Insights
- [Bug Fix] 2024-03-15: Session fails on UTC+0 timezone
  Fix: Always use datetime.timezone.utc

## Edit Checklist
- Run: `pytest tests/test_auth.py -v`
- Check constant: SESSION_TIMEOUT (config/settings.py)
- Update API docs if public signature changes

## Pitfalls
- Never call authenticate() before db.init()
  Why: connection pool not initialized → RuntimeError

## Key Constructs
- **authenticate(email, password)** → JWT token
  Callers: api/routes.py:42 (login_handler)

## Related Files
- tests/test_auth.py [co-change: 92%]
- models/user.py [co-change: 67%]
- middleware/session.py [co-change: 45%]

## Security Notes
- ✅ No issues found
```

---

## CLI

```bash
# Analyze current repository
codeprep analyze

# Analyze a specific repo
codeprep analyze --repo /path/to/project

# Security audit only
codeprep security

# Incremental update (only changed files)
codeprep update --since HEAD~10

# Get context for a specific file (used by Claude Code)
codeprep context src/auth.py
```

---

## Claude Code Integration

### CLAUDE.md (add to project root)
```markdown
## Project Context

Before editing any file, run:
```bash
python .claude/get_context.py <file_path>
```
This gives you historical bugs, pitfalls, related files and security notes.
```

### .claude/get_context.py
```python
#!/usr/bin/env python3
"""Print context for a file before Claude Code edits it."""
import sys, pathlib

file = sys.argv[1] if len(sys.argv) > 1 else "."
doc = pathlib.Path(f".claude/docs/{file}.md")

if doc.exists():
    print(doc.read_text())
else:
    print(f"No context for {file}. Run: codeprep analyze")
```

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| CLI | Python 3.11+ (click) |
| Git mining | GitPython |
| Python AST | `ast` + `rope` |
| JS/TS/Dart AST | `tree-sitter` |
| Security — Python | `bandit` |
| Security — Universal | `semgrep` |
| Secret scanning | `gitleaks` |
| Output format | Markdown |
| Config | `.codeprep.yml` |

---

## Roadmap

### v0.1 — MVP
- [x] Git history mining (bug fix commits + co-change matrix)
- [x] Python AST analysis
- [x] Markdown file generation
- [x] CLI: `codeprep analyze`

### v0.2 — Multi-language
- [x] TypeScript / JavaScript support
- [x] Dart / Flutter support
- [x] Go support
- [x] semgrep integration

### v0.3 — Intelligence
- [x] Incremental updates (changed files only)
- [x] LLM-enhanced summaries via Claude Haiku
- [x] `codeprep watch` (auto-update on new commits)

### v0.4 — Integrations
- [x] GitHub Action
- [x] Pre-commit hook (`codeprep install-hook`)
- [ ] VS Code extension (shows context when file is opened) — future

---

## Security Principles

### What we scan for
- SQL injection, XSS, command injection
- Hardcoded secrets (API keys, passwords, tokens)
- Dangerous functions (`eval`, `exec`, `pickle.loads`, `dangerouslySetInnerHTML`)
- Unprotected HTTP endpoints
- Weak cryptography (MD5 / SHA1 for passwords)
- Insecure dependencies (via `pip-audit`, `npm audit`)

### What we never do
- No code is sent to any external API
- All analysis runs locally
- Output files contain only metadata, not raw source code

---

## References

- [semgrep](https://semgrep.dev) — SAST engine
- [bandit](https://bandit.readthedocs.io) — Python security linter
- [tree-sitter](https://tree-sitter.github.io) — multi-language AST parser
- [gitleaks](https://gitleaks.io) — secret scanning
- [GitPython](https://gitpython.readthedocs.io) — git history access
- [SWE-Bench](https://swebench.com) — coding agent benchmark
