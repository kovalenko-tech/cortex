# Cortex

Give Claude Code full knowledge of your project — instantly.

Cortex analyzes your repository and generates context files that Claude Code reads before touching any file. It knows which bugs occurred, which tests to run, which files break together, and where the security risks are.

## Install

```bash
curl -fsSL https://raw.githubusercontent.com/kovalenko-tech/cortex/main/install.sh | bash
```

## Usage

```bash
cd your-project
cortex analyze
```

That's it. Commit `.claude/` to your repo.

## What Claude Code gets per file

- Past bugs and how they were fixed
- Which tests to run after changes
- Files that historically break together
- Security issues and hidden pitfalls
- AI-generated overview of what the file does

## Options

```bash
cortex analyze --since HEAD~20   # only changed files
cortex context src/auth.py       # show context for one file
cortex security                  # security audit only
cortex install-hook              # auto-update on every commit
cortex watch                     # auto-update when new commits arrive
```

## LLM summaries

Set `ANTHROPIC_API_KEY` to get AI-generated file overviews:

```bash
export ANTHROPIC_API_KEY=sk-ant-...
cortex analyze
```

## GitHub Action

Drop `.github/workflows/cortex.yml` in your repo to auto-update context on every push. See [example](.github/workflows/cortex.yml).

## License

MIT
