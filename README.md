# CodePrep

> Open-source alternative to [Codeset.ai](https://codeset.ai) — generates `.claude/docs/` knowledge base for your project from git history, static analysis and security audit.

When Claude Code opens a file, it immediately knows:
- **Historical bugs** in that file and how they were fixed
- **Tests to run** after making changes
- **Pitfalls** — what breaks and why
- **Co-change relationships** — files that historically break together
- **Security issues** — SAST results per file

## Quick Start

```bash
pip install codeprep
cd your-project
codeprep analyze
```

This generates `.claude/docs/` — commit it to your repo. Now Claude Code has full project context on every session.

## How it works

See [PLAN.md](./PLAN.md) for full algorithm and roadmap.

## Supported Languages

| Language | AST | Security |
|----------|-----|----------|
| Python | ✅ ast + rope | ✅ bandit |
| TypeScript/JS | 🔜 tree-sitter | 🔜 semgrep |
| Dart/Flutter | 🔜 tree-sitter | 🔜 semgrep |
| Go | 🔜 go/ast | 🔜 semgrep |

## Security

All analysis runs **locally**. No code is sent to external APIs.

## License

MIT
