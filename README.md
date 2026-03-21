# cortex

Project knowledge base for Claude Code. Analyzes git history, code structure, and security — generates `.claude/docs/` context files your coding agent reads automatically.

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
cortex analyze
git add .claude/
git commit -m "add cortex context"
```

## Interactive setup

```bash
cortex setup
```

Walks you through: analyze → generate CLAUDE.md → configure MCP → install git hook.

## Commands

```
cortex analyze                 analyze full project
cortex analyze --since HEAD~20 only changed files
cortex analyze --no-llm        skip AI summaries (faster)
cortex analyze --max-files 100 limit files analyzed
cortex analyze --no-cache      force full re-analysis
cortex init                    generate CLAUDE.md for your project
cortex context src/auth.py     show context for one file
cortex security                security audit only
cortex deps                    scan dependencies for vulnerabilities
cortex diff main               update context for files changed vs branch
cortex status                  show analysis status
cortex clean                   remove all generated context files
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

Claude Code will automatically get context for every file you open.

## AI summaries

```bash
export ANTHROPIC_API_KEY=sk-ant-...
cortex analyze
```

Optional. Without it, all other features still work.

## GitHub PR knowledge

Mine implicit decisions from PR discussions:

```bash
export GITHUB_TOKEN=ghp_...
cortex mine-prs
cortex analyze  # context now includes PR decisions
```

Claude Code will see in each file's context:

```
## Decisions & Context
- ✅ Chose Redis over Memcached because we need persistence across restarts
  PR #234 — @john
- 🚫 Don't cache this endpoint — caused stale data bugs in production
  PR #198 — @maria
```

## License

MIT
