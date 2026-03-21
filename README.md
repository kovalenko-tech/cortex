# cortex

Project knowledge base for Claude Code. Analyzes git history, code structure, and security — generates `.claude/docs/` context files your coding agent reads automatically.

## Install

```bash
curl -fsSL https://raw.githubusercontent.com/kovalenko-tech/cortex/main/install.sh | bash
```

## Quick start

```bash
cd your-project
cortex analyze
git add .claude/
git commit -m "add cortex context"
```

## Commands

```
cortex analyze                 analyze full project
cortex analyze --since HEAD~20 only changed files
cortex context src/auth.py     show context for one file
cortex security                security audit only
cortex install-hook            auto-update on every commit
cortex watch                   auto-update when commits arrive
```

## AI summaries

```bash
export ANTHROPIC_API_KEY=sk-ant-...
cortex analyze
```

Optional. Without it, all other features still work.

## License

MIT
