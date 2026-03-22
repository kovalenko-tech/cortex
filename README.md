# Cortex

**Project knowledge base for Claude Code.**

Cortex analyzes your repository and writes `.claude/docs/` — structured context files Claude Code reads before touching any file. It knows which parts of the codebase break most often, why certain decisions were made, and where the security risks are.

Not documentation you write. Knowledge extracted from your actual project history.

---

## Install

```bash
curl -fsSL https://raw.githubusercontent.com/kovalenko-tech/cortex/main/install.sh | bash
```

Or with npx — no install required:

```bash
npx @kovalenko-tech/cortex-ai analyze
```

Requires Python 3.11+.

---

## Quick start

```bash
cd your-project
cortex setup    # interactive wizard
```

Or directly:

```bash
cortex analyze
git add .claude/
git commit -m "add cortex context"
```

---

## What Claude Code sees

Before writing a single line of code, Claude Code gets this for every file:

```
> ⚡ Fresh — analyzed 2026-03-22 UTC
> 🔴 HIGH RISK (score: 65/100) — 12 bug fixes · no test coverage

## Historical Insights
- [Bug Fix] 2024-03-15: Session fails on UTC+0 timezone
  Fix: Always use datetime.timezone.utc

## Decisions & Context
- ✅ Chose JWT over sessions for stateless auth — PR #234 @john
- 🚫 Don't call authenticate() before db.init() — PR #156 @maria

## Edit Checklist
- Run: pytest tests/test_auth.py -v
- Check: SESSION_TIMEOUT in config/settings.py

## Related Files
- tests/test_auth.py [co-change: 92%]
- middleware/session.py [co-change: 67%]

## Security Notes
- ✅ No issues found
```

---

## Commands

```
cortex setup                      interactive setup wizard
cortex analyze                    analyze full project
cortex analyze --since HEAD~20    only changed files
cortex analyze --no-llm           skip AI summaries
cortex analyze --no-cache         force full re-analysis
cortex init                       generate CLAUDE.md
cortex context src/auth.py        show context for one file
cortex status                     analysis status + freshness + risk
cortex risks                      files sorted by risk score
cortex freshness                  context staleness per file
cortex security                   security audit only
cortex deps                       dependency vulnerability scan
cortex mine-prs                   mine GitHub PR decisions
cortex diff main                  update changed files vs branch
cortex install-hook               auto-update on every commit
cortex watch                      auto-update on new commits
cortex clean                      remove all context files
cortex mcp                        start MCP server for Claude Code
```

---

## Claude Code integration

Add to `.claude/settings.json` for automatic context injection:

```json
{
  "mcpServers": {
    "cortex": {
      "command": "cortex",
      "args": ["mcp"]
    }
  }
}
```

---

## GitHub PR knowledge

Mine implicit decisions from PR discussions:

```bash
export GITHUB_TOKEN=ghp_...
cortex mine-prs
cortex analyze
```

---

## AI summaries

```bash
export ANTHROPIC_API_KEY=sk-ant-...
cortex analyze
```

Uses Claude Haiku to generate a 2–3 sentence technical overview per file. Optional — all other features work without an API key.

---

## Docs

Full documentation: **https://kovalenko-tech.github.io/cortex/docs.html**

---

## License

MIT — [kovalenko-tech/cortex](https://github.com/kovalenko-tech/cortex)
