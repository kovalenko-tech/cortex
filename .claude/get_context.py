#!/usr/bin/env python3
"""Print context for a file — used by Claude Code."""
import sys, pathlib
file = sys.argv[1] if len(sys.argv) > 1 else "."
doc = pathlib.Path(f".claude/docs/{file}.md")
if doc.exists():
    print(doc.read_text())
else:
    print(f"No context for {file}. Run: cortex analyze")
