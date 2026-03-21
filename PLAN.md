# CodePrep — Project Knowledge Base Generator for Claude Code

> Аналог Codeset.ai — відкритий, локальний, безкоштовний.  
> Генерує `.claude/docs/` контекст для кожного файлу проекту на основі git history, статичного аналізу та security audit.

---

## Мета

Коли Claude Code відкриває файл — він повинен одразу знати:
- Які баги були в цьому файлі і як їх фіксили
- Які тести запускати після змін
- Які підводні камені та залежності
- Які файли зазвичай ламаються разом
- Чи є security проблеми в цьому файлі

---

## Алгоритм (4 модулі)

### 1. Git History Mining
**Що робимо:** аналізуємо всі коміти що торкались кожного файлу

```
git log --follow --diff-filter=M --format="%H|%s|%ae|%ad" -- <file>
git show <commit> -- <file>  # отримуємо diff
```

**Витягуємо:**
- Bug fix коміти (ключові слова: fix, bug, hotfix, patch, resolve)
- Refactor коміти (refactor, cleanup, improve)
- Причина зміни з commit message
- Diff — що саме змінилось

**Output:**
```markdown
### Historical Insights
- [Bug Fix] 2024-03-15: Null pointer on session init
  Commit: "fix: session fails on UTC+0 timezone"
  Change: Added .timezone.utc to datetime comparison
```

---

### 2. Co-change Analysis
**Що робимо:** знаходимо файли які змінювались разом

```
git log --name-only --format="" | build_cochange_matrix()
```

**Алгоритм:**
1. Для кожного коміту — список змінених файлів
2. Будуємо матрицю: скільки разів файл A і файл B змінювались разом
3. Нормалізуємо: `score = co_changes / min(changes_A, changes_B)`
4. Якщо score > 0.3 — файли пов'язані

**Output:**
```markdown
### Related Files
- `auth/session.py` [co-change: 78%] — якщо змінюєш auth.py, перевір session.py
- `tests/test_auth.py` [co-change: 92%] — тести для цього файлу
```

---

### 3. Static Analysis (AST + Call Graph)
**Що робимо:** аналізуємо структуру коду без виконання

**Per language:**
- **Python:** `ast` модуль + `rope` або `jedi` для call graph
- **JavaScript/TypeScript:** `@typescript-eslint/parser` + `madge` для dependencies
- **Dart/Flutter:** `dart analyze` + власний AST парсер через `analyzer` package
- **Go:** `go/ast` + `go/callgraph`

**Витягуємо:**
- Функції та їх callers/callees
- Імпорти та залежності
- Публічний API файлу
- Тести що покривають цей файл

**Output:**
```markdown
### Key Constructs
- **authenticate()**: Validates credentials, returns JWT
  Called by: api/routes.py:42, middleware/auth.py:18
  Tests: tests/test_auth.py::test_login_success

### Edit Checklist
Tests to run: `pytest tests/test_auth.py -q`
Constants: `SESSION_TIMEOUT` in config/settings.py
```

---

### 4. Security Audit
**Що робимо:** SAST аналіз кожного файлу

**Інструменти per language:**
- **Python:** `bandit` — SQL injection, hardcoded secrets, unsafe eval
- **JS/TS:** `eslint-plugin-security` + `semgrep`
- **Dart:** `dart analyze` + custom rules для Flutter
- **All:** `semgrep` з OWASP ruleset — universal SAST
- **Secrets:** `gitleaks` або `truffleHog` — API keys в git history

**Output:**
```markdown
### Security Notes
- ⚠️ [MEDIUM] Line 47: User input passed to SQL query without sanitization
  Rule: B608 (bandit) — Use parameterized queries
- ⚠️ [LOW] Line 12: Hardcoded timeout value — consider moving to config
- ✅ No secrets found in git history
```

---

## Структура output

```
project/
  .claude/
    docs/
      src/
        auth.py.md
        models/user.py.md
        api/routes.py.md
      SUMMARY.md          # огляд всього проекту
      SECURITY_REPORT.md  # всі security issues в одному місці
    get_context.py        # helper script для Claude Code
```

### Формат кожного .md файлу

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
- Update: API docs if public signature changes

## Pitfalls
- Never call authenticate() before db.init()
  Why: Connection pool not initialized → RuntimeError

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

## CLI Interface

```bash
# Аналіз поточного проекту
codeprep analyze

# Аналіз конкретного репо
codeprep analyze --repo /path/to/project

# Тільки security audit
codeprep security

# Оновити тільки змінені файли (incremental)
codeprep update --since HEAD~10

# Отримати контекст для конкретного файлу (для Claude Code)
codeprep context src/auth.py
```

---

## Інтеграція з Claude Code

### CLAUDE.md (додати в корінь проекту)
```markdown
## Project Context

Before editing any file, run:
```bash
python .claude/get_context.py <file_path>
```
This gives you historical bugs, pitfalls, related files and security notes.
```

### get_context.py
```python
#!/usr/bin/env python3
"""Helper: prints context for a file before Claude Code edits it."""
import sys, pathlib

file = sys.argv[1] if len(sys.argv) > 1 else "."
doc = pathlib.Path(f".claude/docs/{file}.md")

if doc.exists():
    print(doc.read_text())
else:
    print(f"No context for {file}. Run: codeprep analyze")
```

---

## Стек

| Компонент | Технологія |
|-----------|-----------|
| CLI | Python 3.11+ (click) |
| Git mining | GitPython |
| Python AST | ast + rope |
| JS/TS AST | tree-sitter |
| Dart AST | tree-sitter-dart |
| Security (Python) | bandit |
| Security (Universal) | semgrep |
| Secret scanning | gitleaks |
| Output | Markdown |
| Config | pyproject.toml / .codeprep.yml |

---

## Roadmap

### v0.1 — MVP
- [ ] Git history mining (bug fixes, co-change)
- [ ] Python підтримка (AST + bandit)
- [ ] Генерація .md файлів
- [ ] CLI: `codeprep analyze`

### v0.2 — Multi-language
- [ ] JavaScript/TypeScript підтримка
- [ ] Dart/Flutter підтримка
- [ ] Go підтримка
- [ ] semgrep integration

### v0.3 — Intelligence
- [ ] Incremental updates (тільки змінені файли)
- [ ] LLM-enhanced summaries (через claude haiku)
- [ ] `codeprep update --watch` (авто-оновлення при коміті)

### v0.4 — Integration
- [ ] GitHub Action
- [ ] Pre-commit hook
- [ ] VS Code extension (показує контекст при відкритті файлу)

---

## Безпека

### Що аналізуємо
- SQL injection, XSS, command injection
- Hardcoded secrets (API keys, passwords, tokens)
- Небезпечні функції (eval, exec, pickle.loads)
- Незахищені HTTP endpoints
- Слабка криптографія (MD5, SHA1 для паролів)

### Що НЕ відправляємо нікуди
- Код залишається локально
- Ніяких cloud API calls для аналізу
- Всі інструменти запускаються локально

---

## Referенс

- [Codeset.ai](https://codeset.ai) — інспірація
- [semgrep](https://semgrep.dev) — SAST engine
- [bandit](https://bandit.readthedocs.io) — Python security
- [tree-sitter](https://tree-sitter.github.io) — multi-lang AST
- [gitleaks](https://gitleaks.io) — secret scanning
- [SWE-Bench](https://swebench.com) — benchmark для coding agents
