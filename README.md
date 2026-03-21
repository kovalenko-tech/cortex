# cortex

Project knowledge base for Claude Code. Analyzes git history, risk, PR decisions, and security — generates `.claude/docs/` context files your coding agent reads automatically.

## Install

```bash
curl -fsSL https://raw.githubusercontent.com/kovalenko-tech/cortex/main/install.sh | bash
```

Or with npx (requires Python 3.11+):
```bash
npx cortex-ai analyze
```

## Quick start

```bash
cd your-project
cortex setup    # interactive wizard
```

Or manually:
```bash
cortex analyze
git add .claude/
git commit -m "add cortex context"
```

## What Claude Code sees per file

```
> ⚡ Fresh — analyzed 2026-03-21 21:50 UTC
> 🔴 HIGH RISK (score: 65/100) — 12 bug fixes · no test coverage

## Historical Insights
- [Bug Fix] 2024-03-15: Session fails on UTC+0 timezone

## Decisions & Context
- ✅ Chose Redis over Memcached because we need persistence
  PR #234 — @john
- 🚫 Don't cache this endpoint — caused stale data bugs
  PR #198 — @maria

## Edit Checklist
- Run: pytest tests/test_auth.py -v

## Security Notes
- ✅ No issues found
```

## Commands

```
cortex setup                   interactive setup wizard
cortex analyze                 analyze full project
cortex analyze --since HEAD~20 only changed files
cortex analyze --no-llm        skip AI summaries
cortex analyze --no-cache      force full re-analysis
cortex analyze --max-files 100 limit files analyzed
cortex init                    generate CLAUDE.md
cortex context src/auth.py     show context for one file
cortex security                security audit
cortex deps                    scan dependencies for vulnerabilities
cortex risks                   show risk scores for all files
cortex freshness               show how stale the context is
cortex mine-prs                mine GitHub PR decisions
cortex diff main               update context for changed files
cortex status                  show analysis status
cortex clean                   remove all context files
cortex install-hook            auto-update on every commit
cortex watch                   auto-update when commits arrive
cortex mcp                     start MCP server for Claude Code
```

## Claude Code integration (MCP)

Add to `.claude/settings.json`:
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

## GitHub PR knowledge

Mine implicit decisions from PR discussions:

```bash
export GITHUB_TOKEN=ghp_...
cortex mine-prs
cortex analyze
```

## AI summaries

```bash
export ANTHROPIC_API_KEY=sk-ant-...
cortex analyze
```

## License

MIT
