# @kovalenko-tech/cortex-ai

Project knowledge base for Claude Code.

Analyzes git history, risk scores, PR decisions and security — generates `.claude/docs/` context files Claude Code reads automatically.

## Usage

```bash
npx @kovalenko-tech/cortex-ai analyze
```

No install needed. Requires Python 3.11+.

## Commands

```
npx @kovalenko-tech/cortex-ai setup
npx @kovalenko-tech/cortex-ai analyze
npx @kovalenko-tech/cortex-ai analyze --since HEAD~20
npx @kovalenko-tech/cortex-ai context src/auth.py
npx @kovalenko-tech/cortex-ai status
npx @kovalenko-tech/cortex-ai risks
npx @kovalenko-tech/cortex-ai security
npx @kovalenko-tech/cortex-ai deps
npx @kovalenko-tech/cortex-ai mine-prs
```

## Full docs

https://kovalenko-tech.github.io/cortex/
