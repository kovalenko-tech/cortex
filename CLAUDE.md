# CLAUDE.md

This file provides context for Claude Code working in this repository.

## Project Overview
**Languages:** Python

## Commands

## Project Context

Before editing any file, get its full context:
```bash
python .claude/get_context.py <file_path>
```

This shows historical bugs, pitfalls, related files and security notes.

## Guidelines

- Always run tests after making changes
- Check `.claude/docs/` for context before editing a file
- Run `cortex analyze --since HEAD~1` after significant changes to update context
