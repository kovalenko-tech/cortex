"""CLI entry point."""
import click
from pathlib import Path
from rich.console import Console

console = Console()


@click.group()
@click.version_option()
def cli():
    """Cortex — generates .claude/docs/ context for Claude Code."""
    pass


@cli.command()
@click.option("--repo", default=".", show_default=True, help="Path to repository")
@click.option("--since", default=None, help="Analyze commits since (e.g. HEAD~50)")
@click.option("--lang", multiple=True, help="Filter languages: python, js, ts, dart, go")
def analyze(repo, since, lang):
    """Analyze repository and generate .claude/docs/ context."""
    from .core import Cortex
    Cortex().analyze(repo_path=repo, since=since, languages=list(lang) or None)


@cli.command()
@click.argument("file_path")
def context(file_path):
    """Print context for a specific file."""
    import pathlib
    doc = pathlib.Path(f".claude/docs/{file_path}.md")
    if doc.exists():
        console.print(doc.read_text())
    else:
        console.print(f"[yellow]No context for {file_path}. Run: cortex analyze[/]")


@cli.command()
@click.option("--repo", default=".", show_default=True)
def security(repo):
    """Run security audit only."""
    import os
    from .core import discover_files
    from .security.bandit_runner import run_bandit
    from .security.semgrep_runner import run_semgrep

    repo_root = os.path.abspath(repo)
    files = discover_files(repo_root, ['python'])
    issues_total = 0
    for f in files:
        issues = run_bandit(f) + run_semgrep(f)
        if issues:
            rel = os.path.relpath(f, repo_root)
            for issue in issues:
                console.print(f"[red]{rel}:{issue.line}[/] [{issue.severity}] {issue.message}")
                issues_total += 1
    if issues_total == 0:
        console.print("[green]✅ No security issues found.[/]")


@cli.command()
@click.option("--repo", default=".", show_default=True)
def install_hook(repo):
    """Install git pre-commit hook to auto-update .claude/docs/ on each commit."""
    import stat
    hook_path = Path(repo) / ".git" / "hooks" / "pre-commit"
    hook_content = """#!/bin/bash
# Cortex: update context for staged files
STAGED=$(git diff --cached --name-only --diff-filter=ACM)
if [ -n "$STAGED" ]; then
    cortex analyze --since HEAD 2>/dev/null || true
    git add .claude/docs/ 2>/dev/null || true
fi
"""
    hook_path.write_text(hook_content)
    hook_path.chmod(hook_path.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    console.print(f"[green]✓[/] Pre-commit hook installed at {hook_path}")
    console.print("[dim]Now .claude/docs/ will auto-update on every commit.[/]")


@cli.command()
@click.option("--repo", default=".", show_default=True)
@click.option("--interval", default=30, show_default=True, help="Poll interval in seconds")
def watch(repo, interval):
    """Watch for file changes and auto-update context."""
    import time
    console.print(f"[blue]Watching[/] {repo} every {interval}s... (Ctrl+C to stop)")
    last_hash = ""
    while True:
        try:
            import git
            r = git.Repo(repo, search_parent_directories=True)
            current_hash = r.head.commit.hexsha
            if current_hash != last_hash:
                if last_hash:
                    console.print(f"[dim]New commit detected, updating...[/]")
                    from .core import Cortex
                    Cortex().analyze(repo_path=repo, since=f"{last_hash[:8]}..HEAD")
                last_hash = current_hash
            time.sleep(interval)
        except KeyboardInterrupt:
            console.print("\n[yellow]Watch stopped.[/]")
            break
        except Exception:
            time.sleep(interval)


if __name__ == "__main__":
    cli()
